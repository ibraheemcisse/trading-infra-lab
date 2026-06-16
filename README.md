# Trading Infra Lab

![Trading Infra Lab Architecture](./docs/arch.png)

A single-host trading systems laboratory that recreates the critical infrastructure found in electronic trading environments:

* Market data distribution (UDP multicast)
* FIX order entry
* Pre-trade risk controls
* Matching engine execution
* Kafka event streaming
* Trade persistence
* Monitoring and alerting
* Chaos engineering and recovery testing

The system runs on a single Ubuntu host and is intentionally operated under constrained resources to study reliability, observability, failure detection, and recovery behavior.

The goal is not to build a feature-complete exchange.

The goal is to understand how trading infrastructure behaves when things break.

---

# Architecture

![Trading Infra Lab Mechanism](./docs/trading-infra-mechanism.jpg)

## System Flow

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

# Chaos Control Panel

The lab includes a lightweight web interface for running failure scenarios and recovery workflows.

![Chaos Control Panel](./docs/chaos%20dash%20recover.png)

The control panel provides:

* One-click failure injection
* Recovery actions
* Live execution logs
* Repeatable operational testing
* Demo-friendly chaos execution

Supported scenarios:

| Scenario | Description       |
| -------- | ----------------- |
| Chaos 01 | Feed blackout     |
| Chaos 02 | Latency injection |
| Chaos 04 | Consumer crash    |
| Chaos 05 | Kafka broker stop |

Example:

```text
Inject Failure
      ↓
System Degrades
      ↓
Metrics Change
      ↓
Gate Detects Issue
      ↓
Trading Blocked
      ↓
Recovery Triggered
      ↓
System Returns To Normal
```

The control panel is intentionally simple. Its purpose is to make operational testing repeatable without manually executing every scenario from the command line.

---

# Core Components

## Market Data Feed

A multicast-based market data simulator used to reproduce feed distribution and monitoring patterns.

Features:

* UDP multicast transport
* Sequence tracking
* Gap detection
* Feed latency measurement
* Multi-symbol publishing

Current instruments:

* AAPL
* MSFT
* GOOG
* TSLA

Example update:

```json
{
  "symbol": "AAPL",
  "price": 211.42,
  "seq": 10421,
  "timestamp": 1750012345.182
}
```

---

## FIX Protocol Layer

Simplified FIX 4.4 order entry environment.

Capabilities:

* NewOrderSingle
* ExecutionReport
* Session simulation
* Auto-restart via systemd

Ports:

```text
9876 - FIX sender
9877 - FIX receiver
```

---

## Pre-Trade Risk Gate

Orders are validated before entering the matching engine.

Implemented controls:

* Kill switch
* Maximum order size
* Fat-finger protection
* Position limits
* Audit logging

Validation flow:

```text
New Order
     ↓
Risk Checks
     ↓
Approved / Rejected
```

---

## Matching Engine

Price-time priority matching engine.

Features:

* Limit orders
* Partial fills
* Deterministic execution
* O(1) cancellation lookup
* Per-symbol order books

Supported actions:

* Submit order
* Cancel order
* Partial execution
* Full execution

---

## Kafka Event Pipeline

Trade lifecycle events are published to Kafka.

Topics:

```text
NEW_ORDER
EXECUTION_REPORT
TRADE
```

Pipeline:

```text
Order
  ↓
NEW_ORDER
  ↓
Matching Engine
  ↓
EXECUTION_REPORT
  ↓
TRADE
  ↓
PostgreSQL
```

Consumer:

```text
trade_persister.py
```

---

# Operational Validation Loop

The most important aspect of this project is not the matching engine.

It is the closed-loop process used to validate system behavior during failure conditions.

```text
Chaos Injection
       ↓
System Failure
       ↓
Observability
       ↓
Gate Detection
       ↓
Postmortem
       ↓
Remediation
```

Every completed scenario follows this workflow.

---

## 1. Chaos Injection

Failures are intentionally introduced into running services.

Examples:

* Feed blackout
* Consumer crash
* Kafka broker stop
* Latency injection
* Stale market data
* Resource pressure

CLI execution:

```bash
python3 chaos/01_feed_blackout.py inject
python3 chaos/01_feed_blackout.py recover
```

Or via the control panel:

```bash
python3 chaos/control_panel.py
```

```text
http://<server-ip>:8080
```

---

## 2. Observability

Prometheus and Grafana provide visibility into system behavior during failures.

Infrastructure metrics:

* CPU utilization
* Memory usage
* Disk usage
* Load average

Feed metrics:

* Feed availability
* Feed latency
* Packet throughput
* Sequence gaps
* Symbol activity

Feed monitor metrics:

```text
feed_alive
feed_latency_ms
feed_packets_total
feed_dropped_total
feed_gap_events_total
feed_symbols_active
```

The objective is not simply collecting metrics.

The objective is verifying that failures are visible and measurable.

Example:

```text
Feed Blackout
      ↓
feed_alive = 0
      ↓
Dashboard reflects outage
```

---

## 3. Pre-Market Gate

The pre-market gate acts as a trading readiness check.

Validation categories:

* Feed health
* FIX availability
* Database connectivity
* Queue depth
* Resource utilization
* Error thresholds

Possible outcomes:

```text
APPROVED
WARNING
BLOCKED
```

A successful chaos test demonstrates that degraded conditions are detected before trading activity continues.

---

## 4. Postmortems

Every completed scenario generates a documented incident review.

Each report includes:

* Timeline
* Root cause
* Detection
* Impact
* Recovery
* Corrective actions

Location:

```text
docs/postmortems/
```

The objective is continuous improvement rather than simple recovery.

---

# Example Scenario: Consumer Crash

Scenario:

```text
Kill trade_persister
```

Observed behavior:

```text
Consumer Stops
        ↓
Market Data Continues
        ↓
Feed Metrics Unchanged
        ↓
Dashboard Shows No Feed Impact
        ↓
Gate Detects Failure
        ↓
Trading Blocked
```

Detection latency:

```text
4.1 seconds
```

Finding:

The persistence layer remained isolated from the market data path. A consumer failure did not impact feed processing or latency, validating architectural separation between execution and persistence.

---

# Chaos Test Matrix

| Scenario              | Status   | Finding                                        |
| --------------------- | -------- | ---------------------------------------------- |
| Feed Blackout         | Complete | Detection validated                            |
| Latency Injection     | Complete | Monitoring blind spot identified and corrected |
| Consumer Crash        | Complete | Architectural isolation confirmed              |
| Kafka Broker Stop     | Complete | Feed path independent from persistence         |
| Quote Staleness Audit | Complete | Validation logic verified                      |
| Risk Kill Switch      | Planned  | Pending                                        |
| Disk Exhaustion       | Planned  | Pending                                        |
| Memory Pressure       | Planned  | Pending                                        |
| Dependency Failure    | Planned  | Pending                                        |

---

# Quick Start

## Prerequisites

* Ubuntu 22.04
* Python 3.10+
* Docker
* systemd

Install dependencies:

```bash
pip install kafka-python requests fastapi uvicorn prometheus-client
```

---

## Start Services

Core services:

```bash
sudo systemctl start multicast-sender
sudo systemctl start feed-monitor
sudo systemctl start fix-simulator
```

Infrastructure:

```bash
docker compose up -d
```

---

## Verify System Health

Run the pre-market gate:

```bash
python3 pre_market/checks.py
```

Expected output:

```text
APPROVED
```

---

## Run Exchange Tests

```bash
cd exchange
python3 test_exchange.py
```

Expected:

```text
6/6 tests passing
```

---

# Key Findings

### CPU Starvation Can Be More Dangerous Than Process Failure

Burstable instances degraded more severely from CPU exhaustion than isolated service crashes.

### Monitoring Requires Independent Validation

Single-point measurements created blind spots during latency investigations.

### Local Networking Behaves Differently

Localhost multicast traffic invalidated assumptions used during packet-loss testing.

### Restart Policies Can Amplify Failures

Aggressive restart behavior without resource controls increased contention during incidents.

### Small Configuration Errors Can Trigger Large Operational Impact

Permissions, service definitions, dependency mismatches, and environment variables frequently produced disproportionate failures.

---

# Roadmap

* [ ] Complete remaining chaos scenarios
* [ ] Linux networking deep dive
* [ ] Resource isolation experiments with cgroups
* [ ] Additional exchange simulation workloads
* [ ] Video walkthrough
* [ ] Public open-source release

---

# Status

Active experimental system.

Components are continuously tested, intentionally broken, recovered, and documented. The primary output is operational understanding of trading infrastructure under failure conditions.

---

# Author

**Ibrahim Cisse**

Infrastructure, reliability, and trading systems engineering focused on observability, resilience, and production operations.
