# Trading Infra Lab

![Trading Infra Lab Architecture](./docs/arch.png)

A production-inspired trading infrastructure laboratory for studying latency, observability, and distributed systems under load.

This project recreates the core infrastructure found in modern electronic trading systems—including market data ingestion, FIX order routing, a matching engine, Kafka event streaming, PostgreSQL persistence, and full-stack observability—to investigate how latency emerges, how systems behave under stress, and where real bottlenecks occur.

Rather than building a feature-complete exchange, this lab focuses on **performance engineering**: measuring system behavior, validating assumptions with data, and documenting operational findings.

---

## Highlights

- Kubernetes-ready trading infrastructure
- FIX 4.4 order gateway
- Price-time priority matching engine
- Kafka event streaming pipeline
- PostgreSQL trade persistence
- Prometheus & Grafana observability
- Chaos engineering and failure injection
- SLI/SLO monitoring
- Queue-depth and latency analysis
- Performance measurement methodology

---

## System Overview

```text
                    Market Data Feed
                    (UDP Multicast)
                             |
                             v
                     Feed Monitor
                             |
                             v
                  Prometheus / Grafana


 FIX Client
      |
      v
+--------------+
|  Risk Gate   |
+--------------+
      |
      v
+--------------+
|   Matching   |
|    Engine    |
+--------------+
      |
      v
+--------------+
|    Kafka     |
+--------------+
      |
      v
+--------------+
| PostgreSQL   |
+--------------+
```

---

## Quick Start

### Prerequisites

- Ubuntu 22.04
- Python 3.10+
- Docker
- systemd

Install dependencies:

```bash
pip install kafka-python requests fastapi uvicorn prometheus-client
```

### Start Services

```bash
sudo systemctl start multicast-sender
sudo systemctl start feed-monitor
sudo systemctl start fix-simulator
docker compose up -d
```

### Verify System Health

```bash
python3 pre_market/checks.py
```

Expected output:

```text
APPROVED
```

### Run Load Test

```bash
cd exchange

python3 << 'EOF'
from matching_engine import MatchingEngine
from order_book import OrderBook
from order_types import Order, Side, OrderType
from datetime import datetime, timezone
from uuid import uuid4
import statistics
import time

order_book = OrderBook()
matcher = MatchingEngine(order_book)

for rate in [100, 500, 1000]:
    latencies = []

    for i in range(rate * 2):
        order = Order(
            order_id=str(uuid4()),
            symbol="AAPL",
            side=Side.BUY if i % 2 == 0 else Side.SELL,
            quantity=100,
            price=150 + (i % 10),
            order_type=OrderType.LIMIT,
            timestamp=datetime.now(timezone.utc),
        )

        start = time.perf_counter()
        matcher.process_order(order)
        elapsed = (time.perf_counter() - start) * 1_000_000
        latencies.append(elapsed)

        time.sleep(1 / rate)

    p50 = statistics.quantiles(latencies, n=100)[49]
    p99 = statistics.quantiles(latencies, n=100)[98]

    print(f"{rate} orders/sec | P50={p50:.2f}µs | P99={p99:.2f}µs")
EOF
```

### Grafana

```
http://<server-ip>:3000
```

Default credentials:

```
admin / admin
```

---

## Purpose

Most open-source trading projects focus on implementing exchange functionality.

This laboratory focuses on understanding **why systems slow down**.

Every experiment follows the same engineering process:

1. Measure a baseline.
2. Apply controlled load.
3. Observe system behavior.
4. Identify the real bottleneck.
5. Validate the improvement.
6. Document the findings.

---

## Technology Stack

| Area | Technology |
|------|------------|
| Language | Python |
| Messaging | Kafka |
| Database | PostgreSQL |
| Protocol | FIX 4.4 |
| Monitoring | Prometheus |
| Dashboards | Grafana |
| Containers | Docker |
| Infrastructure | Linux / systemd |
| Performance | Prometheus Histograms |
| Testing | Chaos Engineering |

---

## Core Components

### Market Data Feed

A UDP multicast simulator that reproduces market data distribution patterns.

**Features**

- Sequence tracking and gap detection
- Feed latency measurement
- Multi-symbol publishing
- Feed health monitoring

---

### FIX Gateway

A simplified FIX 4.4 environment for order submission and execution reporting.

**Features**

- NewOrderSingle messages
- ExecutionReport handling
- Session simulation
- Automatic reconnect
- Sender (9876) / Receiver (9877)

---

### Pre-Trade Risk Gate

A validation layer protecting the matching engine before order execution.

**Controls**

- Kill switch
- Position limits
- Maximum order size
- Fat-finger protection
- Audit logging

---

### Matching Engine

A deterministic price-time priority matching engine designed for latency analysis.

**Features**

- Limit orders
- Partial fills
- O(1) order cancellation
- Per-symbol order books
- Prometheus instrumentation

---

### Kafka Event Pipeline

Trade lifecycle events are streamed through Kafka.

```
NEW_ORDER
      ↓
EXECUTION_REPORT
      ↓
TRADE
      ↓
PostgreSQL
```

---

### Observability

Production-style monitoring with Prometheus and Grafana.

Metrics include:

- Feed latency
- Order latency
- Queue depth
- CPU
- Memory
- Disk
- Alerting
- System health

---

## Performance Analysis

### SLI / SLO Framework

| Component | SLI | SLO | Error Budget |
|-----------|-----|-----|--------------|
| Market Data | Feed Freshness | 99.95% within 50ms | 0.05% |
| Order Gateway | P99 Latency | <10ms | 0.01% |
| Trade Persistence | Write Success | 99.99% | 0.01% |

---

### Baseline Latency

```text
P50  4.53 µs
P95 12.02 µs
P99 26.71 µs
```

---

### Under Load (5,000 orders/sec)

```text
P50 31.11 µs
P95 66.07 µs
P99 76.89 µs
```

**Observation**

Latency degradation was driven primarily by queue growth rather than CPU saturation.

---

### Queue Depth

```text
Orders/sec    Avg Queue    Max Queue    P50
100               20           40       48.39µs
500              140          240       50.15µs
1000             440          640       63.96µs
```

Queue depth increased much faster than execution latency, indicating contention before matching rather than inside the matching engine itself.

---

# Operational Validation & Chaos Testing

![Chaos Control Panel](./docs/chaos%20dash%20recover.png)

Repeatable failure injection validates monitoring, recovery procedures, and operational assumptions.

| Scenario | Result |
|----------|--------|
| Feed Blackout | Detection latency measured |
| Network Latency | Monitoring blind spots identified |
| Consumer Crash | Service isolation verified |
| Kafka Failure | Feed path remained operational |
| Quote Staleness | Validation logic confirmed |

Testing workflow:

```text
Inject Failure
      ↓
System Degrades
      ↓
Metrics Change
      ↓
Detection
      ↓
Trading Blocked
      ↓
Recovery
      ↓
System Healthy
```

Every experiment generates a documented postmortem.

---

## Key Findings

- Queue growth is the dominant latency bottleneck.
- Individual order processing remains in the microsecond range.
- Throughput remains stable until queue saturation.
- Multiple telemetry sources provide better diagnostics than single metrics.
- Architectural improvements consistently outperform micro-optimizations.

---

## Documentation

- Architecture Decision Records
- SLI/SLO Framework
- Dependency Mapping
- Baseline Measurements
- Load Test Reports
- Queue Analysis
- Latency Forensics
- Incident Postmortems

---

## Roadmap

- [x] SLI/SLO framework
- [x] Baseline latency measurements
- [x] Load testing
- [x] Queue depth analysis
- [x] Prometheus instrumentation

---

## Engineering Methodology

Every improvement follows a repeatable process:

1. Measure.
2. Establish a baseline.
3. Apply controlled load.
4. Identify the constraint.
5. Optimize.
6. Measure again.
7. Document the outcome.

The objective is reproducible performance engineering rather than speculative optimization.

---

## Current Status

Actively developed as a performance engineering laboratory.

Current focus areas include:

- Latency profiling
- Queue analysis
- Observability
- Chaos engineering
- Distributed systems reliability

---

## Author

**Ibrahim Cisse**

Infrastructure Engineer specializing in Kubernetes, cloud platforms, observability, and performance engineering.

This laboratory explores distributed systems, trading infrastructure, latency analysis, and production reliability through repeatable engineering experiments.
