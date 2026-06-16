# Trading Infra Lab

![Trading Infra Lab Architecture](./docs/arch.png)

A single-host trading systems laboratory that recreates the critical execution path of an electronic trading platform:

* Market data distribution (UDP multicast)
* FIX order entry
* Pre-trade risk validation
* Matching engine execution
* Event streaming with Kafka
* Trade persistence
* Monitoring and alerting
* Failure injection and recovery testing

The entire system runs on a single Ubuntu host and is intentionally operated under constrained resources to study reliability, observability, and operational behavior under failure conditions.

The goal is not to build a feature-rich exchange.

The goal is to understand how trading infrastructure behaves when components fail.

---

# Why This Project Exists

Many exchange simulators demonstrate order matching and protocol handling.

Far fewer explore operational questions:

* What happens when a critical service crashes?
* How quickly is the failure detected?
* Which monitoring signals become useful during incidents?
* Which failures are visible and which remain silent?
* Does the system recover correctly?

This lab was built to answer those questions through controlled experimentation, measurement, and postmortem analysis.

---

# Architecture

![Trading Infra Lab Mechanism](./docs/trading-infra-mechanism.jpg)

## System Components

```text
                        +------------------+
                        |  Market Data     |
                        | UDP Multicast    |
                        +--------+---------+
                                 |
                                 v
                        +------------------+
                        |  Feed Monitor    |
                        |  Prometheus      |
                        +--------+---------+
                                 |
                                 v
                             Grafana


 FIX Client
      |
      v
+-------------+
| Risk Gate   |
+-------------+
      |
      v
+-------------+
| Matching    |
| Engine      |
+-------------+
      |
      v
+-------------+
| Kafka       |
+-------------+
      |
      v
+-------------+
| PostgreSQL  |
+-------------+
```

## Trading Flow

```text
FIX Order
    ↓
Risk Validation
    ↓
Matching Engine
    ↓
Execution Event
    ↓
Kafka
    ↓
Persistence
```

## Monitoring Flow

```text
UDP Market Data
        ↓
Feed Monitor
        ↓
Prometheus
        ↓
Grafana
```

---

# Repository Structure

```text
trading-infra-lab/
│
├── exchange/
│   ├── matching_engine.py
│   ├── order_book.py
│   ├── risk_gate.py
│   └── test_exchange.py
│
├── market_data/
│   ├── sender.py
│   ├── receiver.py
│   └── feed_monitor.py
│
├── fix/
│   └── simulator.py
│
├── chaos/
│   ├── 01_feed_blackout.py
│   ├── 02_latency_injection.py
│   ├── 04_consumer_crash.py
│   └── control_panel.py
│
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   └── dashboards/
│
├── pre_market/
│   └── checks.py
│
├── docs/
│   ├── postmortems/
│   └── architecture/
│
└── README.md
```

---

# Core Components

## Market Data Feed

Simulated market data distributed over UDP multicast.

Features:

* Sequence tracking
* Gap detection
* Feed latency measurement
* Multi-symbol support

Current instruments:

* AAPL
* MSFT
* GOOG
* TSLA

Example message:

```json
{
  "symbol": "AAPL",
  "price": 211.42,
  "seq": 10421,
  "timestamp": 1750012345.182
}
```

---

## FIX Layer

Simplified FIX 4.4 order-entry environment.

Supported workflows:

* NewOrderSingle
* ExecutionReport
* Session simulation
* Auto-recovery via systemd

Services:

```text
9876 - FIX sender
9877 - FIX receiver
```

---

## Pre-Trade Risk Gate

All orders are validated before entering the matching engine.

Implemented controls:

* Kill switch
* Maximum order size
* Fat-finger protection
* Position limits
* Audit logging

Decision flow:

```text
Order
   ↓
Risk Checks
   ↓
Approved / Rejected
```

---

## Matching Engine

Price-time priority matching engine.

Capabilities:

* Limit orders
* Partial fills
* Deterministic execution
* O(1) order cancellation lookup

Supported operations:

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

Event flow:

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

# Failure Validation Workflow

The most important part of this project is not the matching engine.

It is the validation loop used to test operational resilience.

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

Every completed scenario follows this process.

---

## 1. Chaos Injection

Failures are intentionally introduced into running services.

Examples:

* Feed blackout
* Consumer crash
* Kafka broker stop
* Latency injection
* Stale market data
* Resource exhaustion

Trigger via CLI:

```bash
python3 chaos/01_feed_blackout.py inject
```

Recover:

```bash
python3 chaos/01_feed_blackout.py recover
```

Or use the web control panel:

```bash
python3 chaos/control_panel.py
```

```text
http://<server-ip>:8080
```

The control panel provides a simple interface for running failure scenarios and recovery actions.

---

## 2. Observability

Prometheus and Grafana provide visibility into system behavior during failures.

Infrastructure metrics:

* CPU utilization
* Memory usage
* Disk usage
* Load average

Market data metrics:

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

The objective is to verify that failures produce measurable signals.

Example:

```text
Feed Blackout
      ↓
feed_alive = 0
      ↓
Grafana reflects outage
```

---

## 3. Pre-Market Gate

The pre-market gate acts as a trading readiness check.

It evaluates:

* Feed health
* FIX session status
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

A successful chaos test demonstrates that the gate can identify degraded conditions and prevent trading when necessary.

---

## 4. Postmortems

Every completed scenario generates a documented incident review.

Each report includes:

* Timeline
* Root cause
* Impact
* Detection
* Recovery
* Corrective actions

Postmortems are stored in:

```text
docs/postmortems/
```

The objective is continuous improvement rather than simply restoring service.

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
Feed Latency Unchanged
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

The persistence layer was successfully isolated from the market-data path. A consumer failure did not impact feed processing, validating architectural separation between execution and persistence components.

---

# Chaos Test Matrix

| Scenario              | Status   | Result                                     |
| --------------------- | -------- | ------------------------------------------ |
| Feed Blackout         | Complete | Detection validated                        |
| Latency Injection     | Complete | Monitoring blind spot identified and fixed |
| Consumer Crash        | Complete | Architectural isolation confirmed          |
| Kafka Broker Stop     | Complete | Feed remains independent of persistence    |
| Quote Staleness Audit | Complete | Validation logic verified                  |
| Risk Kill Switch      | Planned  | Pending                                    |
| Disk Exhaustion       | Planned  | Pending                                    |
| Memory Pressure       | Planned  | Pending                                    |
| Dependency Failure    | Planned  | Pending                                    |

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

Market data and FIX:

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

Expected result:

```text
APPROVED
```

---

## Run Tests

Matching engine tests:

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

## CPU Starvation Can Be Worse Than Process Failure

On burstable instances, CPU exhaustion caused broader degradation than isolated service crashes.

## Monitoring Must Be Independently Verified

Single-point measurements created blind spots during latency investigations.

## Local Networking Behaves Differently

Multicast traffic on localhost invalidated assumptions used during packet-loss testing.

## Restart Policies Can Amplify Incidents

Aggressive restart behavior without resource controls increased contention and accelerated cascading failures.

## Small Configuration Errors Have Large Effects

Service definitions, permissions, environment variables, and dependency mismatches repeatedly produced disproportionate operational impact.

---

# Roadmap

* [ ] Complete remaining chaos scenarios
* [ ] Linux networking deep-dive
* [ ] cgroups and resource isolation experiments
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

Infrastructure, reliability, and trading-systems engineering focused on observability, operational resilience, and production systems.
