# System Dependency Map

## Component Dependency Graph
Market Data Feed (UDP multicast)

               ↓

Pre-Market Health Gate (checks feed freshness)

               ↓

Matching Engine (processes orders if gate APPROVED)

               ↓

Risk Gate (validates trades)

               ↓

Kafka Topic (async event stream)

               ↓

PostgreSQL (persists trades)

## Failure Analysis

### If Market Data Feed Dies

**Detection latency:** 3 seconds (feed_alive check)

**Impact:** Gate blocks trading immediately (fail-safe)

**Acceptable?** YES — feed is critical path

---

### If Kafka Dies

**Detection latency:** 5+ seconds (consumer lag)

**Impact:** Trades not persisted, but matching continues

**Acceptable?** YES — feed delivery > persistence

---

### If PostgreSQL Dies

**Detection latency:** 10+ seconds (query timeout)

**Impact:** Trades queue in Kafka, matching slows

**Acceptable?** PARTIAL can tolerate short outage
