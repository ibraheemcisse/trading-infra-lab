# trading-infra-lab

![Trading Infra Lab Architecture](./docs/arch.png)

A single-host trading systems lab that recreates core components of electronic trading infrastructure: market data distribution, FIX order flow, a matching engine with pre-trade risk controls, observability, and controlled failure injection.

This system is intentionally operated under constrained resources and real failure conditions to study production behavior, not just build features.

---

## What this is

A working simulation of a simplified trading stack:

- market data feed (UDP multicast)
- FIX-style order entry
- matching engine with order book
- pre-trade risk checks
- event streaming via Kafka
- Prometheus + Grafana observability
- chaos engineering scenarios
- real incident postmortems

Everything runs on a single Ubuntu server.

---

## Why it exists

This project reconstructs trading infrastructure patterns from first principles, based on experience in production trading and exchange environments.

The goal is not correctness in isolation, but **operational behavior under stress**:

- What fails first?
- What fails silently?
- What breaks under resource constraints?
- How do cascading failures emerge?

---

## Architecture (simplified)

![Trading Infra Lab Architecture simplified](./docs/trading-infra-mechanism.jpg)


All components run on a single Ubuntu 22.04 instance.

---

## Core components

### Market Data
UDP multicast feed publishing JSON price updates with sequence tracking and latency measurement.

### FIX Layer
Basic FIX 4.4 order sender + session simulator for structured order entry over TCP.

### Matching Engine
Price-time priority order book with:

- partial fills
- deterministic matching
- O(1) cancel lookup

### Risk Engine (pre-trade)
All orders must pass validation before execution:

- kill switch
- max order size limits
- fat-finger protection
- position limits
- audit logging

### Kafka Event Stream
Trade lifecycle events:

- NEW_ORDER
- EXECUTION_REPORT
- TRADE

Keyed by order ID across partitions.

---

## Observability

- Feed Monitor (Prometheus exporter)
- Prometheus scraping system metrics
- Grafana dashboards:
  - feed latency
  - packet loss
  - sequence gaps
  - system health

---

## Pre-Market Gate

A system health gate that runs before trading activity.

Checks include:
- multicast feed health
- FIX session availability
- database connectivity
- Redis availability
- queue depth
- system resource usage
- log error thresholds

Outputs:
- APPROVED
- WARNING
- BLOCKED

---

## Chaos Engineering

Controlled failure injection system used to test resilience.

Examples:
- feed blackout
- latency injection
- packet loss simulation
- Kafka shutdown
- risk kill switch activation
- stale feed conditions

Each scenario has:
- inject script
- recovery steps
- postmortem

---

## Postmortems

Real operational incidents from running the system:

- Feed blackout → cascading failure detection improvements
- Latency injection → discovered multicast loopback blind spot, fixed two safety-gate defects
- CPU exhaustion on t3.micro → resource overcommit + recovery via AWS API

---

## Tech stack

Ubuntu 22.04 · Python 3 · systemd · Docker · Kafka (KRaft) · Prometheus · Grafana · PostgreSQL · Redis · simplefix

---

## Running

```bash
# market data + monitoring
python3 network/multicast_sender.py &
python3 monitoring/feed_monitor.py &

# pre-market checks
python3 pre_market/checks.py

# exchange test
cd exchange && python3 test_exchange.py
```

---

## Key lessons

- Burstable instances are not safe for multi-service always-on stacks
- Restart policies without resource limits amplify failures
- Observability cannot compensate for system overload
- Same-host networking can invalidate fault injection assumptions
- Small errors (file mixups) can cascade into system-wide instability

---

## Status

This is an active experimental system. Components are continuously being tested, broken, and improved.

The primary output of this project is not uptime — it is understanding failure modes in trading infrastructure.

