# Baseline Latency Measurements

## Baseline (No Load, 100 Orders)

Matching engine latency distribution at baseline load (single-threaded, no contention).

| Percentile | Latency (µs) |
|---|---|
| P50 | 4.53 |
| P95 | 12.02 |
| P99 | 26.71 |
| Min | 3.01 |
| Max | 26.85 |

## Observations

- P99 is **5.9x** P50 (tail latency exists even at baseline)
- Max is **8.9x** P50 (outliers present)
- Headroom for SLO (10ms = 10,000 µs): **99.7x** above P99

## Next Steps

- Measure under load (1k, 5k orders)
- Profile to find bottlenecks
- Measure queue depth behavior
