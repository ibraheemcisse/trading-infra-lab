# Postmortem 002: Latency Injection (Chaos Test 02)

**Date:** 2026-06-14
**Type:** Deliberate chaos test
**Chaos script:** `chaos/02_latency_injection.py`
**Runbook used:** `runbooks/high_latency.md`

## Summary

Chaos test 02 set out to answer: *can the pre-market gate detect a
feed that is alive but no longer trustworthy (degraded latency)?*

The test produced two unplanned findings, both more valuable than
the original question:

1. A **topology limitation** in same-host chaos testing — injected
   network latency had zero effect on the measured path
2. A **statistical design flaw** in the `Pricing Feeds` check —
   a ~77% false-failure rate that had been silently affecting every
   prior test run, including postmortem 001

## Finding 1: Same-host multicast bypasses tc netem

`tc qdisc add dev ens5 root netem delay 250ms` was applied and
confirmed active (`tc qdisc show` showed the rule). `feed_latency_ms`
remained at ~0.25ms — completely unaffected. The same result occurred
when the rule was applied to `lo` instead.

**Root cause:** `multicast_sender.py` and `feed_monitor.py` run on
the same host. With `IP_MULTICAST_LOOP` enabled (the default), the
kernel delivers multicast packets to local subscribers via an
internal path that bypasses the `tc` qdisc on both `ens5` and `lo`
entirely.

**Implication:** network-layer fault injection (`tc netem`) cannot
simulate degraded latency for same-host multicast consumers on this
lab setup. This is a genuine constraint of single-instance chaos
testing, not a misconfiguration.

**Action items:**
- [ ] Add application-level delay injection to `feed_monitor.py`
      (e.g. `--inject-delay-ms` flag that sleeps before processing)
      to properly exercise the "degraded but alive" scenario
- [ ] Document this topology constraint in `runbooks/high_latency.md`

## Finding 2: Pricing Feeds check had a ~77% false-failure rate

While investigating Finding 1, `pre_market/checks.py` was run 5x
consecutively with **no chaos active**. `Pricing Feeds` failed 5/5
times with varying "missing symbols."

**Root cause:** the original check listened for 5 seconds while the
sender picks 1 random symbol per second from a set of 4. The
probability that all 4 symbols appear in ~5 random draws is:

surjections(5, 4) / 4^5 = 240 / 1024 ≈ 23.4%

So the check failed by pure chance **~77% of the time**, even on a
fully healthy system. Observing 5/5 failures (probability ≈ 26% for
exactly that outcome) is consistent with this.

**This retroactively reframes postmortem 001** — the "Missing AMZN"
observation at 07:15:54 was not a settling-time artifact as
originally concluded. It was this same statistical flaw.

**Fix:** `check_pricing_feeds` was rewritten to query
`feed_monitor.py`'s existing `feed_symbols_active` metric (60-second
rolling window) instead of running an independent short sample. With
a 60-second window:
surjections(60, 4) / 4^60 ≈ 100%

**Validation — 5 consecutive runs, no chaos active:**
Run 1: [PASS] Pricing Feeds  4/4 symbols active (60s window)

Run 2: [PASS] Pricing Feeds  4/4 symbols active (60s window)

Run 3: [PASS] Pricing Feeds  4/4 symbols active (60s window)

Run 4: [PASS] Pricing Feeds  4/4 symbols active (60s window)

Run 5: [PASS] Pricing Feeds  4/4 symbols active (60s window)

5/5 PASS — fix confirmed.

## Finding 3: Market Data Latency check was blind to feed_monitor degradation

With application-level injection working (Finding 1's resolution),
the original chaos 02 question was finally tested: *can the gate
detect a feed that is alive but degraded?*

**Initial result: no.** With 150ms injected into `feed_monitor`'s
processing loop:
feed_latency_ms 150.459        (feed_monitor correctly reports it)

feed_injected_delay_ms 150.0

[PASS] Market Data Latency 1.88ms   <- gate missed it entirely

**Root cause:** `check_market_data_latency()` opened its own fresh
multicast socket and measured wire latency directly, never consulting
`feed_monitor`. This measures a *different* thing (raw network
latency to a brand-new listener) than `feed_monitor`'s reported
latency (its own processing latency, including injected/real delay).
The check happened to measure the metric unaffected by this failure
mode.

**Why this matters:** `feed_monitor` is the system's primary feed
health exporter - Grafana and Prometheus alerting are built on it. If
`feed_monitor` itself degrades (GC pause, CPU contention - a very
real scenario on a t3.micro, see postmortem 003), the pre-market
gate's latency check would not reflect that degradation at all.

**Fix:** `check_market_data_latency` now queries `feed_monitor`'s
`feed_latency_ms` metric in addition to its own measurement, and uses
whichever is worse.

**Validation after fix:**
With injection:  [FAIL] Market Data Latency  150.46ms (feed_monitor) — exceeds 100ms threshold

After recovery:  [PASS] Market Data Latency  2.09ms (own measurement)

Gate correctly fails during degradation and correctly passes (using
its own measurement) once `feed_monitor` recovers.

## Chaos 02 - final status: COMPLETE

All three findings from this chaos test are resolved:
1. Topology limitation documented, application-level injection built
2. Pricing Feeds statistical bug fixed and validated
3. Market Data Latency blind spot found, fixed, and validated

This chaos test - originally a simple "inject latency, check the
gate" exercise - ended up finding and fixing two independent defects
in the safety gate itself. Both defects shared a root cause pattern:
**checks that bypass `feed_monitor` and take their own independent
measurements can disagree with `feed_monitor`'s view of system
health, and the gate was trusting the wrong one.**

## Final action items

- [x] Application-level latency injection (Finding 1)
- [x] Pricing Feeds fix + validation (Finding 2)
- [x] Market Data Latency fix + validation (Finding 3)
- [ ] Audit `check_stale_prices` for the same pattern - does it also
      do an independent fresh read that could disagree with
      `feed_monitor`'s view?


## What this means for the project

A pre-trade safety gate that fails ~77% of the time on a healthy
system is, in practice, **worse than no gate at all** — operators
learn to ignore it ("the gate cries wolf"), so a *real* failure gets
the same shrug as the constant false positives. Finding and fixing
this is arguably the single most valuable result of the entire chaos
testing effort so far, and it was found through honest
investigation, not by design.


