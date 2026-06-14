# Postmortem 003: CPU Credit Exhaustion and System Instability on t3.micro

**Date:** 2026-06-14
**Environment:** AWS EC2 t3.micro (1 vCPU, ~1GB RAM)
**Incident Type:** Production-like overload and cascading service failure
**Severity:** High (loss of SSH access + full service degradation)
**Trigger:** Kafka recreation during full-stack observability run

---

## 1. Summary

During a full-stack runtime test involving Kafka recreation alongside multiple always-on services (Prometheus, Grafana, Postgres, Redis, FIX engine, simulators, and Python monitoring daemons), the EC2 instance experienced sustained CPU saturation.

CPU utilization stabilized around ~63%, causing continuous CPU credit depletion on the burstable t3.micro instance type. Eventually, the system became unresponsive to SSH and EC2 Instance Connect due to resource exhaustion.

Recovery required an external `aws ec2 reboot-instances` action. Post-reboot, services resumed automatically based on their respective restart policies.

---

## 2. Timeline

| Time        | Event                                                         |
| ----------- | ------------------------------------------------------------- |
| ~22:30      | Kafka container recreated (KRaft mode, default JVM settings)  |
| ~22:30      | CPU utilization spikes from near idle to ~63% sustained       |
| ~22:30+     | CPU credits steadily decline in CloudWatch                    |
| ~22:35      | SSH becomes unresponsive                                      |
| ~22:35      | EC2 Instance Connect fails                                    |
| ~22:40      | Serial console accessed but unusable (no auth configured)     |
| ~22:45      | External reboot triggered via AWS CLI                         |
| Post-reboot | System recovers; services restart via systemd/Docker policies |

---

## 3. Impact

* Instance became unreachable via SSH and Instance Connect
* All running services degraded or stalled
* Monitoring reliability reduced due to system-wide resource contention
* Kafka restart re-triggered high CPU and memory pressure after recovery
* Observability stack generated misleading signals due to cascading failures

---

## 4. Root Cause Analysis

### Primary Cause: Resource Overcommitment

The system hosted too many always-on services for a single vCPU, including:

* Kafka (KRaft mode, JVM default heap)
* Prometheus, Grafana, Node Exporter
* PostgreSQL
* Redis
* FIX/multicast trading simulators
* Python-based feed-monitor and supporting services

This resulted in sustained CPU pressure far beyond burst capacity limits.

---

### Secondary Cause: Kafka JVM Resource Defaults

Kafka was deployed without memory or CPU constraints, leading to disproportionate resource consumption relative to system capacity.

Memory usage analysis indicated Kafka consumed ~300MB+ RAM, a significant portion of total available memory on the instance.

---

### Tertiary Cause: Inconsistent Service Isolation

No resource governance existed between services:

* No CPU quotas
* No memory limits
* No priority tiers
* No isolation between infrastructure and experimental components

This allowed all services to compete equally for limited resources.

---

### Quaternary Cause: Restart Policy Amplification

Several services used `Restart=always` or equivalent Docker restart policies.

This created:

* automatic recovery loops
* repeated resource pressure after reboot
* amplification of instability rather than mitigation

---

## 5. Secondary Incident: File Contamination

During recovery, `monitoring/feed_monitor.py` was found to contain incorrect content originating from `pre_market/checks.py`.

This caused:

* immediate crash-loop of feed-monitor service
* repeated systemd restarts (Restart=always, RestartSec=2)
* increased syslog load
* false-positive failure detection in monitoring checks

Root cause:

* cross-file editing error during multi-tab session
* insufficient validation before deployment
* lack of pre-commit or runtime sanity checks

---

## 6. Recovery Actions

* Kafka stopped temporarily to restore system stability
* System reboot performed via AWS CLI after loss of SSH access
* Services recovered automatically based on systemd and Docker policies
* Feed-monitor corrected manually on host system
* System returned to nominal operation post-reboot

---

## 7. Key Learnings

### 7.1 Burstable instances are not general-purpose production hosts

t3.micro is sufficient for lightweight workloads but not for:

* Kafka
* multi-service observability stacks
* concurrent always-on simulation environments

### 7.2 Resource governance is mandatory

Without CPU/memory limits per service, system behavior becomes non-deterministic under load.

### 7.3 Restart policies can amplify failures

“Restart always” without resource constraints can worsen instability during systemic overload.

### 7.4 Observability cannot compensate for structural overload

Monitoring tools correctly reported symptoms but could not prevent system collapse.

### 7.5 Human process errors propagate into system instability

File contamination incidents can directly trigger service-level cascading failures without safeguards.

---

## 8. Action Items

### Completed

* Kafka disabled temporarily during recovery
* Feed-monitor corrected on host system
* System restored after reboot

### Pending / Recommended

* Implement CPU and memory limits per service (systemd / Docker)
* Introduce service tiering (core vs observability vs experimental)
* Constrain Kafka JVM heap explicitly (e.g., -Xmx256m)
* Add pre-deployment validation checks for file integrity
* Standardize restart policies with resource-awareness
* Document instance sizing constraints for full-stack lab operation
* Consider upgrade to t3.small or higher for sustained multi-service operation

---

## 9. Conclusion

This incident was not caused by a single faulty service, but by systemic overcommitment of resources on an undersized instance combined with lack of isolation and governance.

The system failed predictably under sustained load due to architectural oversubscription rather than anomalous behavior.

The recovery demonstrated effective external intervention capability, but highlighted the need to shift from reactive debugging to proactive resource design.
