# Postmortem 001: Multicast Feed Blackout (Chaos Test)

**Date:** 2026-06-14
**Type:** Deliberate chaos test
**Chaos script:** `chaos/01_feed_blackout.py`
**Runbook used:** `runbooks/market_data_gap.md`

## Summary

The `multicast_sender.py` process was deliberately killed to simulate
a market data feed outage. The pre-market gate correctly detected
the failure and cascading downstream impacts, returning BLOCKED.
Recovery was successful — restarting the sender restored all
multicast-dependent checks within approximately 30 seconds.

## Timeline

| Time (UTC) | Event |
|---|---|
| ~07:13:30 | `chaos/01_feed_blackout.py inject` run — sender process killed |
| 07:13:46 | `pre_market/checks.py` run — **BLOCKED**, 6/11 checks failed |
| ~07:15:40 | `chaos/01_feed_blackout.py recover` run — sender restarted |
| 07:15:54 | `pre_market/checks.py` run — multicast checks PASS, but `Pricing Feeds` still FAIL (rolling window not yet populated) |
| 07:16:10 | `pre_market/checks.py` run — **8/11 PASS**, all multicast checks PASS |

**Approximate time to detect:** immediate (pre_market check fails on next run)
**Approximate time to recover (multicast layer):** ~30 seconds total,
of which ~15 seconds was the `Pricing Feeds` rolling-window settling time

## Impact

When the feed was down, the pre-market gate correctly identified
**cascading failure** across four dependent checks:

- `Multicast Feed` — no packets received
- `Market Data Latency` — cannot measure latency with no packets
- `Stale Prices` — cannot determine quote age with no packets
- `Pricing Feeds` — no symbols observed in rolling window

This matches the "pricing integrity failure" framing in
`runbooks/market_data_gap.md` — a feed outage doesn't just trigger
one alert, it invalidates an entire category of downstream checks.

## What went well

- Pre-market gate caught the failure immediately and correctly
  returned BLOCKED rather than a partial/ambiguous status
- Cascading failures were all attributed correctly — no false
  "everything is fine" signals from unrelated checks
- Recovery via `chaos/01_feed_blackout.py recover` was simple and fast

## What did not go well / gaps identified

1. **No automatic restart.** The sender has no supervisor/systemd
   unit with `Restart=always`. A real outage would require manual
   intervention exactly as performed here.

2. **Recovery verification has a settling delay.** `Pricing Feeds`
   uses a 5-second rolling window, so immediately after recovery it
   can still report FAIL even though the feed itself is healthy.
   An operator following the runbook needs to know this is expected
   and not a second incident.

3. **No state reconciliation step.** As noted in
   `runbooks/market_data_gap.md`, recovery of the feed does not
   verify that the order book / matching engine state is still
   consistent. This chaos test did not exercise the matching engine,
   so this gap remains theoretical for now but should be tested in
   a future chaos scenario once the exchange is wired into the live
   feed.

## Additional findings (unrelated to this chaos test)

During this test run, the pre-market gate also surfaced two
pre-existing issues:

- **FIX Sessions: FAIL** — the FIX simulator (ports 9876/9877) was
  not running, likely from a previous session/instance restart.
  Needs a supervisor process to persist across reboots.
- **System Resources: FAIL (Disk 85.5%)** — Docker images
  (Kafka, Prometheus, Grafana, Node Exporter, renderer) are consuming
  significant disk on a t3.micro. Needs `docker system prune` and
  monitoring of disk growth over time.

These were not caused by the chaos test but were caught by the same
gate, which is itself a useful demonstration of the gate's value —
it surfaces real operational debt, not just injected failures.

## Resolution

Both additional findings were fixed the same day:

- **FIX Sessions:** Moved the FIX simulator from `/tmp` (ephemeral) into
  the repo at `fix_protocol/simulator/fix_session_simulator.py`, and
  created a systemd unit (`fix-simulator.service`) with `Restart=always`.

- **Disk usage:** Ran `docker system prune -af`, reducing disk usage
  from 85.5% to 77.9%.

- **Multicast sender persistence:** Created a systemd unit
  (`multicast-sender.service`) with `Restart=always`, addressing
  action item #1 — the original chaos scenario (sender death) will
  now self-recover within ~2 seconds without manual intervention.

### Post-fix verification
Results   : 10 passed | 0 failed | 1 skipped

MARKET OPEN STATUS : WARNING - SKIPPED CHECKS PRESENT

The remaining `SKIP` is `Database` — connection env vars
(`DB_USER`, `DB_PASSWORD`, `DB_NAME`) are not persisted across
shell sessions. Tracked as a new action item below.

## Updated action items

- [x] Add systemd unit for `multicast_sender.py` with `Restart=always`
- [x] Add systemd unit for the FIX simulator
- [x] Run `docker system prune` — disk 85.5% → 77.9%
- [ ] Document the `Pricing Feeds` settling-time behavior in
      `runbooks/market_data_gap.md` verification section
- [ ] Future chaos test: feed blackout while exchange/matching engine
      is actively processing orders — verify state reconciliation
- [ ] Add `EnvironmentFile` for database credentials so `Database`
      check doesn't SKIP on fresh sessions
- [ ] Re-test chaos 01 — with `multicast-sender.service` now active,
      `pkill -f multicast_sender.py` should self-recover within ~2s
      without manual `recover`
