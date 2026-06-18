Market Data Feed
- SLI: Feed freshness (time since last update)
- SLO: 99.95% of updates within 50ms
- Error budget: 0.05%

Order Gateway
- SLI: Order acceptance latency P99
- SLO: < 10ms
- Error budget: 0.01%

Trade Persistence
- SLI: Trade write success rate
- SLO: 99.99%
- Error budget: 0.01%

## Order Gateway

**SLI:** How fast are orders accepted? (P99 latency)

**SLO:** P99 order acceptance latency < 10ms

**Error Budget:** We can fail 0.01% of the time (8.6 minutes/month)

---

## Trade Persistence

**SLI:** What % of trades are successfully saved to database?

**SLO:** 99.99% of trades persisted

**Error Budget:** We can fail 0.01% of the time (8.6 minutes/month)
