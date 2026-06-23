# Load Test Results

## Latency Under Increasing Load

| Orders | P50 (µs) | P95 (µs) | P99 (µs) | Max (µs) | P50 Degradation |
|---|---|---|---|---|---|
| 100 | 4.53 | 12.02 | 26.71 | 26.85 | baseline |
| 1,000 | 12.20 | 17.41 | 23.82 | 127.29 | 2.7x |
| 5,000 | 31.11 | 66.07 | 76.89 | 185.56 | 6.9x |

## Key Observations

1. **P50 degrades faster than P99** — suggests queue depth is the bottleneck
2. **Max outliers spike** — some orders hit long tail (127µs, 185µs)
3. **Still well below SLO** — P99 at 5k is 76.89µs vs 10,000µs SLO (130x headroom)

## Hypothesis

Queue is building up as load increases. P50 latency means "typical order", but queue depth increases, so typical order waits longer.

## Next Steps

- Measure actual queue depth vs latency
- Profile to find CPU bottleneck
- Determine saturation point
