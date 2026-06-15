# Postmortem 004: Instance Upsizing — Memory Constraint

**Date**: 2026-06-15  
**Duration**: t3.micro → t3.small (instance i-0c5681866042d1ceb)  
**Severity**: Medium (blocked next work item)

---

## Summary

Instance t3.micro became memory-constrained (86% usage), blocking the trade_persister end-to-end test from queue item 2. Decision to upsize to t3.small (2GB → 2vCPU, 2GB RAM).

---

## Timeline

| Time | Event |
|------|-------|
| 2026-06-15 13:01 | Pre-market checks report DISK 86.4%, System Resources [FAIL] |
| 2026-06-15 13:10 | Chaos 03 packet loss test eliminated due to same-host multicast limitation |
| 2026-06-15 13:15 | Identified: Kafka + full stack (Postgres, Redis, Prometheus, Grafana, Node Exporter, 3 daemons) cannot fit comfortably on t3.micro RAM |
| 2026-06-15 13:20 | Decision: upsize to t3.small |

---

## Root Cause

**Original constraint (postmortem 003)**: t3.micro chosen for cost sensitivity; CPU credit exhaustion identified and addressed via Kafka stop/defer.

**Current blocker**: Full trading infrastructure stack requires baseline memory:
- Kafka JVM: 256–512 MB (configured `-Xmx256m -Xms128m` per postmortem 003)
- PostgreSQL: ~100–150 MB (trading_lab database)
- Redis: ~50 MB
- Prometheus + Grafana + Node Exporter: ~200–300 MB combined
- Python daemons (multicast sender/receiver, FIX simulator, feed monitor): ~100 MB combined
- Ubuntu base OS: ~200 MB

**Total**: ~1.1–1.5 GB at baseline + headroom = exceeds 1GB RAM limit.

Memory pressure at 86% prevented stable Kafka restart (queue item 2: trade_persister end-to-end test).

---

## Impact

- **Blocked**: Trade persister end-to-end test (next queue item)
- **Blocked**: Chaos 04/05 (requires stable Kafka)
- **Risk**: Out-of-memory kills, systemd restarts, cascading failures (similar pattern to postmortem 001)

---

## Resolution

Upsize instance: **t3.micro → t3.small**

- 2 vCPU (was 1)
- 2GB RAM (was 1GB)
- Cost: ~$0.024/hr on-demand (~$17/month); negligible on AWS Community Builder credits

**Validation post-upsize:**
```bash
free -h
docker-compose ps
systemctl status multicast-sender fix-simulator feed-monitor
curl -s http://localhost:8000/metrics | grep ^feed_alive
python3 pre_market/checks.py
```

---

## Root Cause Analysis (5 Why)

1. **Why was t3.micro chosen?** Cost sensitivity; initially assumed minimal stack.
2. **Why did CPU credits exhaust first?** Postmortem 003: CPU burst capacity finite under continuous JVM + Prometheus load.
3. **Why wasn't memory the blocker earlier?** Kafka was stopped (defer per postmortem 003); full stack never ran together on t3.micro.
4. **Why does full stack need Kafka?** Trade persister (queue item 2) requires end-to-end Kafka → PostgreSQL persistence test.
5. **Why wasn't this caught in design?** t3.micro capacity analysis incomplete; burstable instances unsuitable for sustained multi-service workloads.

---

## Learnings

1. **Burstable instances (t3.micro) work for minimal stacks** (single service, light load). Full infrastructure labs need baseline compute.

2. **Cost vs. portfolio quality trade-off**: t3.micro saved ~$15/month but created operational friction blocking work queue. t3.small removes blockers for negligible cost (AWS Community Builder credits cover it).

3. **Postmortem 003 partial resolution**: CPU credit fix (stop Kafka) was a temporary patch, not a root solution. Memory constraint always existed but surfaced once Kafka restart was attempted.

4. **Systemd hardening + CPU/memory limits**: Future labs should set explicit resource limits in systemd unit files (MemoryMax, CPUQuota) to fail gracefully rather than OOM kill. Not applicable to this lab (already on t3.small), but noted for next iteration.

---

## Action Items

- [x] Upsize to t3.small
- [ ] Verify all services restart cleanly post-upsize
- [ ] Resume queue item 2 (trade persister end-to-end test with Kafka constrained heap)
- [ ] Update README capacity expectations: "Requires t3.small or larger; t3.micro insufficient for full stack
