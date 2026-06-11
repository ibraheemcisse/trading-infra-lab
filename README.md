# trading-infra-lab

A hands-on trading infrastructure simulation environment built on Linux, designed to replicate the core operational patterns of production trading systems.

## Modules

### network — IP Multicast Market Data Feed
Simulates an exchange price feed using UDP multicast. One sender broadcasts price updates to a multicast group. Multiple receivers subscribe and consume the feed. Measures end-to-end latency and packet loss — the same patterns used by exchanges distributing market data via OPRA and ITCH protocols.

### latency — Linux Latency Tuning
Baseline latency measurement followed by systematic OS-level optimisation: CPU isolation, IRQ affinity pinning, network stack sysctl tuning, and interrupt coalescing. Before and after benchmarks documented as evidence of impact.

### fix_protocol — FIX Protocol Order Flow
Order flow simulation using QuickFIX. Sends and receives standard FIX messages (NewOrderSingle, ExecutionReport, OrderCancelRequest), parses message fields, and logs the full order lifecycle from submission to fill.

### pre_market — Pre-Market Automation
Python-based pre-market check sequence that verifies process health, network connectivity to exchange endpoints, disk and memory headroom, and overnight batch job results. Produces a structured summary report before simulated market open.

### monitoring — Operational Visibility
Real-time latency and feed health dashboards using Prometheus and Grafana. Tracks multicast feed latency, packet loss, and system health metrics across all modules.

### kafka — Trading Message Streaming
Kafka-based trade event streaming. Producers publish order and execution events. Consumers process the stream. Demonstrates the messaging backbone used in production trading infrastructure.

## Stack

| Component | Details |
|-----------|---------|
| OS | Ubuntu 22.04 |
| Language | Python 3.10+ |
| Protocols | UDP multicast, FIX 4.2, Kafka |
| Monitoring | Prometheus, Grafana |
| Infrastructure | AWS EC2 t3.micro |

## Why This Exists

Production trading infrastructure operates at a layer most cloud engineers never touch — network protocols, kernel tuning, and message flow between exchange, broker, and market maker. This lab builds hands-on familiarity with that layer through deliberate simulation and measurement.

## Modules Status

| Module | Status |
|--------|--------|
| network | In progress |
| latency | Planned |
| fix_protocol | Planned |
| pre_market | Planned |
| monitoring | Planned |
| kafka | Planned |# trading-infra-lab