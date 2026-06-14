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

## What this means for the project

A pre-trade safety gate that fails ~77% of the time on a healthy
system is, in practice, **worse than no gate at all** — operators
learn to ignore it ("the gate cries wolf"), so a *real* failure gets
the same shrug as the constant false positives. Finding and fixing
this is arguably the single most valuable result of the entire chaos
testing effort so far, and it was found through honest
investigation, not by design.

## Action items

- [x] Rewrite `check_pricing_feeds` to use `feed_monitor`'s 60s
      rolling window via its `/metrics` endpoint
- [x] Validate fix with 5 consecutive clean runs
- [ ] Add a note to postmortem 001 referencing this finding
- [ ] Add application-level latency injection to properly complete
      chaos test 02's original goal
- [ ] Document `feed_monitor.py` as a hard dependency of
      `pre_market/checks.py` in the README architecture section
