# Postmortem 005: Chaos 05 — Kafka Decoupling Architectural Validation

**Date**: 2026-06-15  
**Test**: Chaos 05 (Kafka Container Stop)  
**Severity**: Low (test design issue, architecture working as intended)

---

## Summary

Chaos 05 (Kafka container stop) failed to trigger feed failure or gate blocking. Investigation revealed this is **correct behavior**: the multicast market data feed and Kafka database are architecturally decoupled. Stopping Kafka does not affect live market data availability.

This is a **design validation**, not a failure.

---

## Timeline

| Time | Event |
|------|-------|
| 2026-06-15 16:04 | Run chaos 05 inject (stop Kafka container) |
| 2026-06-15 16:04 | Observe: feed_alive=1.0, Gate=APPROVED (unchanged) |
| 2026-06-15 16:10 | Monitor for 45s: no feed death, no gate block |
| 2026-06-15 16:10 | Conclude: Kafka failure ≠ feed failure |
| 2026-06-15 16:11 | Restart Kafka, gate remains APPROVED |

---

## Root Cause

**Architectural Decoupling** (intentional):

```
MARKET DATA FLOW:
Multicast Sender → Network (UDP) → Feed Monitor → Metrics → Gate Checks
↓
No Kafka involvement

TRADE PERSISTENCE FLOW:
Kafka Consumer (trade_persister) → PostgreSQL
↓
Independent of feed; asynchronous

```

**System Components:**

| Component | Source | Monitoring | Failure Mode |
|-----------|--------|------------|--------------|
| Market Data Feed | Multicast UDP packets | feed_monitor (network-level) | Network/sender failure |
| Trade Persistence | Kafka → PostgreSQL | trade_persister logs | Consumer/broker failure |
| Pre-market Gate | Combines feed + process checks | pre_market/checks.py | Feed OR process health |

**Why Kafka Stop Didn't Kill Feed:**
- feed_monitor reads multicast packets directly from the network layer
- trade_persister subscribes to Kafka *independently*
- Gate checks feed_alive (multicast) and pricing feeds (feed_monitor metrics)
- Gate does **not** check Kafka broker health or trade_persister status

---

## Impact

**Positive (Correct Design):**
- ✅ Market data feed survives database outage
- ✅ Can serve stale trades but live market data
- ✅ Decoupling reduces SPOF (single point of failure)
- ✅ Appropriate for trading infrastructure (data delivery > persistence)

**Negative (Missing Observability):**
- ❌ Cannot detect Kafka broker failure via gate checks
- ❌ Trade persistence loss is silent (only detectable via trade_persister logs)
- ❌ No alerting if Kafka consumer crashes

---

## Analysis: Test Design Flaw

**Original Assumption:** Kafka = critical feed path
**Reality:** Kafka = async trade recording, not feed delivery

Chaos 05 was designed to test feed resilience to broker failure. But the actual feed (multicast) bypasses Kafka entirely. The test measured the wrong thing.

**Correct Test Candidates:**
1. **Chaos 06: Multicast Sender Stop** — Tests actual feed failure (realistic)
2. **Chaos 07: Feed Monitor Crash** — Tests metrics collection failure
3. **Add Kafka Health Check to Gate** — Catch trade_persister crashes

---

## Learnings

1. **Decoupling is Real**: Architectural separation of data feed (network) from persistence (database) works as designed. Market data is independent of trade persistence.

2. **Observability Gap**: No gate visibility into Kafka/trade_persister health. A crashed consumer = silent data loss. Should add:
   ```python
   # In pre_market/checks.py:
   - Check trade_persister process is running
   - Check Kafka broker health (broker API)
   - Check trade_persister lag (Kafka consumer group offset)
   ```

3. **Appropriate Failure Mode**: If Kafka dies:
   - Gate stays APPROVED (feed lives)
   - Trades stop persisting (acceptable; feed is primary)
   - Alerts should be on trade_persister health, not feed

4. **Architecture Validation**: The lab correctly implements the pattern: **prioritize data delivery > data persistence**. This is production-appropriate for trading systems.

---

## Decisions Made

- ✅ Keep Kafka decoupled (correct design)
- ✅ Document as architectural validation (portfolio artifact)
- ⏳ Defer: Add Kafka health check to gate (nice-to-have, not blocking)
- ⏳ Defer: Chaos 06 (Multicast feed stop test)

---

## Action Items

- [x] Run chaos 05 inject/recover
- [x] Identify architectural decoupling
- [x] Document finding
- [ ] (Optional) Add trade_persister health check to gate
- [ ] (Optional) Create chaos 06: Multicast sender stop
- [ ] Update README: explain feed vs. persistence separation

---

## Conclusion

Chaos 05 "failure" is actually a **success**: it validates that the system correctly decouples live market data from database persistence. In production trading, this is the right call. The test was designed for the wrong component; the architecture is sound.

**Portfolio Value**: Demonstrates understanding of:
- Decoupled system design
- Resilience patterns (failure modes)
- Appropriate observability trade-offs
- Trading infrastructure priorities (data > storage)
