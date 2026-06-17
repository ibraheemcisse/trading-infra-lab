# Architecture Decision Records (ADRs)

This document captures key architectural decisions, alternatives considered, rationale, and accepted trade-offs for the trading infrastructure laboratory environment.

---

# ADR-001: UDP Multicast for Market Data Distribution

**Status:** Accepted

## Decision

Use UDP multicast for market data distribution instead of TCP unicast or HTTP-based delivery.

## Context

Market data is consumed simultaneously by multiple components. The primary requirement is efficient one-to-many distribution with minimal overhead.

Options considered:

* UDP multicast
* TCP unicast
* HTTP/gRPC

## Rationale

UDP multicast aligns well with market data dissemination requirements:

* One transmission can serve multiple consumers.
* Sender overhead remains constant as receivers increase.
* Lower protocol overhead than connection-oriented alternatives.
* Common pattern in electronic trading environments.

## Alternatives Considered

### TCP Unicast

Advantages:

* Reliable delivery
* Simpler debugging

Disadvantages:

* Separate connection per consumer
* Increased CPU and network overhead

### HTTP/gRPC

Advantages:

* Developer familiarity
* Easier integration

Disadvantages:

* Additional protocol overhead
* Not optimized for high-frequency market data dissemination

## Consequences

Positive:

* Efficient one-to-many distribution
* Reduced sender-side resource usage

Negative:

* Best-effort delivery only
* Packet loss must be tolerated or handled downstream
* More difficult troubleshooting than TCP-based protocols

## Trade-off Accepted

Efficiency and simplicity of distribution are prioritized over guaranteed delivery.

---

# ADR-002: FIX 4.4 for Order Entry

**Status:** Accepted

## Decision

Use FIX 4.4 over TCP for order entry communication.

## Context

Order flow requires:

* Reliable delivery
* Session management
* Standardized message formats
* Realistic exposure to industry protocols

Options considered:

* FIX protocol
* Custom binary protocol
* REST API
* gRPC

## Rationale

FIX provides:

* Standardized message structures
* Session-level sequencing
* Acknowledgment mechanisms
* Industry relevance and interoperability

Although more complex than alternatives, it better reflects real-world trading workflows.

## Alternatives Considered

### Custom Binary Protocol

Advantages:

* Potentially lower latency
* Full control over message format

Disadvantages:

* No interoperability
* Limited transferability of knowledge

### REST/gRPC

Advantages:

* Simpler implementation

Disadvantages:

* Less representative of traditional trading infrastructure
* Additional serialization overhead

## Consequences

Positive:

* Industry-standard workflow
* Reliable session handling
* Realistic operational experience

Negative:

* Higher implementation complexity
* Additional protocol knowledge required

## Trade-off Accepted

Protocol complexity is justified by realism and learning value.

---

# ADR-003: Kafka for Trade Event Streaming

**Status:** Accepted

## Decision

Use Kafka for trade-event streaming and persistence workflows, but not for market data distribution.

## Context

Executed orders and trade lifecycle events require durable storage and replay capability.

Market data is transient and continuously refreshed.

## Rationale

Kafka provides:

* Event durability
* Replay capability
* Consumer decoupling
* Ordered processing when partitioned appropriately

Market data does not require historical replay and would incur unnecessary overhead through Kafka.

## Alternatives Considered

### Direct Database Writes

Advantages:

* Simpler architecture

Disadvantages:

* Tighter coupling between matching and persistence

### RabbitMQ

Advantages:

* Simpler operational model

Disadvantages:

* Less natural fit for event replay workflows

## Consequences

Positive:

* Decoupled consumers
* Historical event replay
* Clear separation between execution and persistence

Negative:

* Additional operational complexity
* Broker management requirements
* Potential consumer lag under load

## Trade-off Accepted

Operational complexity is accepted in exchange for durability and replayability.

---

# ADR-004: PostgreSQL for Durable Trade Storage

**Status:** Accepted

## Decision

Use PostgreSQL as the system of record for trades and executions.

## Context

Trade data requires:

* Strong consistency
* Durable storage
* Relational querying
* Auditability

## Rationale

PostgreSQL provides:

* ACID transactions
* Mature operational tooling
* Flexible SQL querying
* Strong ecosystem support

## Alternatives Considered

### NoSQL Databases

Advantages:

* Horizontal scalability

Disadvantages:

* Additional complexity not required for project scope

### In-Memory Databases

Advantages:

* Lower latency

Disadvantages:

* Durability concerns

## Consequences

Positive:

* Strong transactional guarantees
* Rich analytical queries
* Well-understood operational model

Negative:

* Higher write latency than purely in-memory approaches
* Schema management responsibilities

## Trade-off Accepted

Consistency and auditability are prioritized over maximum write performance.

---

# ADR-005: Single-Host Deployment

**Status:** Accepted

## Decision

Deploy all components on a single Ubuntu host.

## Context

The objective is to understand trading infrastructure patterns rather than distributed systems operations.

## Rationale

A single-host environment:

* Simplifies debugging
* Accelerates iteration
* Keeps focus on trading workflows
* Reduces operational overhead

## Alternatives Considered

### Multi-Node Kubernetes

Advantages:

* Production-like deployment model

Disadvantages:

* Significant operational complexity

### Managed Services

Advantages:

* Reduced infrastructure burden

Disadvantages:

* Reduced visibility into system behavior

## Consequences

Positive:

* Faster development cycle
* Easier observability
* Lower infrastructure cost

Negative:

* Single points of failure
* Limited distributed-system realism

## Trade-off Accepted

Learning efficiency is prioritized over production-scale realism.

---

# ADR-006: Prometheus and Grafana for Observability

**Status:** Accepted

## Decision

Use Prometheus for metrics collection and Grafana for visualization.

## Context

The system requires visibility into:

* Feed latency
* Throughput
* Resource utilization
* Trade-processing performance

## Rationale

Prometheus provides a lightweight metrics platform with strong ecosystem support.

Grafana offers flexible dashboarding and alerting capabilities.

## Alternatives Considered

### ELK Stack

Advantages:

* Strong log analysis capabilities

Disadvantages:

* More infrastructure overhead

### Commercial APM Platforms

Advantages:

* Rich feature sets

Disadvantages:

* Cost and vendor dependency

## Consequences

Positive:

* Metrics-focused observability
* Open-source ecosystem
* Low operational overhead

Negative:

* Log analysis requires additional tooling

## Trade-off Accepted

Metrics are prioritized over comprehensive log analytics.

---

# ADR-007: Pre-Trade Health Gate

**Status:** Accepted

## Decision

Implement a health gate that evaluates critical system indicators before trading is allowed.

## Context

System degradation may not immediately produce visible failures.

Examples include:

* Elevated latency
* Resource exhaustion
* Delayed persistence

## Rationale

A health gate creates a clear operational boundary between acceptable and degraded states.

It provides:

* Consistent decision-making
* Auditable operational controls
* Reduced risk of trading under known unhealthy conditions

## Alternatives Considered

### Alert-Only Model

Advantages:

* Simpler implementation

Disadvantages:

* Reliance on manual intervention

## Consequences

Positive:

* Explicit operational safeguards
* Repeatable enforcement

Negative:

* Potential false positives
* Threshold tuning required

## Trade-off Accepted

Operational safety is prioritized over maximum availability.

---

# ADR-008: Failure Testing and Validation

**Status:** Accepted

## Decision

Validate architecture through controlled failure injection and recovery testing.

## Context

System behavior under failure conditions cannot be fully understood through code review alone.

## Rationale

Failure testing helps verify:

* Recovery procedures
* Isolation boundaries
* Monitoring effectiveness
* Operational assumptions

## Alternatives Considered

### Theory and Design Review Only

Advantages:

* Faster execution

Disadvantages:

* Lower confidence in runtime behavior

### Ad-Hoc Manual Testing

Advantages:

* Minimal setup

Disadvantages:

* Difficult to reproduce

## Consequences

Positive:

* Better understanding of failure modes
* Reproducible validation process
* Improved operational readiness

Negative:

* Additional engineering effort
* Some scenarios difficult to reproduce on a single host

## Trade-off Accepted

Additional testing effort is justified by improved confidence in system behavior.

---

# Summary

| ADR     | Decision                        |
| ------- | ------------------------------- |
| ADR-001 | UDP Multicast for Market Data   |
| ADR-002 | FIX 4.4 for Order Entry         |
| ADR-003 | Kafka for Trade Event Streaming |
| ADR-004 | PostgreSQL for Durable Storage  |
| ADR-005 | Single-Host Deployment          |
| ADR-006 | Prometheus + Grafana            |
| ADR-007 | Pre-Trade Health Gate           |
| ADR-008 | Failure Testing and Validation  |

These decisions emphasize clarity, operational visibility, realistic trading-system patterns, and deliberate trade-off management.
