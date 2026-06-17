# Postmortem 006: check_stale_prices Audit

**Date**: 2026-06-15
**Audit**: check_stale_prices independent-measurement pattern
**Finding**: Dual-measurement pattern (postmortem 002) NOT applicable here

## Analysis

check_stale_prices measures quote age by receiving one multicast packet and comparing timestamp to now.

feed_monitor exports: latency_ms, packets, gaps, alive status but **NOT quote age**.

## Conclusion

check_stale_prices is already optimal. It's the ONLY perspective on quote freshness. No observability gap.

## Design Note

Quote staleness is inherently local to the receiver (depends on their clock, processing). Global metrics are packet-level (gaps, loss) not timestamp-level.

## Action Items

- [x] Audit check_stale_prices
- [ ] (Optional) Add feed_quote_age_ms to feed_monitor for future observability
