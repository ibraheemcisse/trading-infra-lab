# 📘 Runbook: High Market Data Latency

---

## Alert

- `feed_latency_ms > threshold` (e.g. > 100ms sustained for 3–5 scrapes)
- `feed_alive == 1` (feed still operational)
- packet flow continues but delayed

---

## Severity

**High (can escalate to Critical)**

This is a degraded state, not a failure.

Impact:
- stale or delayed pricing
- fat-finger checks may pass incorrect risk thresholds
- mid-price becomes unreliable
- execution decisions lag behind market reality

---

## What this means

The market data feed is still running, but **timeliness is broken**.

This typically indicates:

### 1. Network congestion
- NIC saturation
- kernel buffer delays
- multicast queue buildup

### 2. Consumer lag
- feed_monitor not processing fast enough
- CPU contention
- blocking operations in downstream pipeline

### 3. Broker / sender delay (if applicable)
- upstream batching or throttling
- delayed publish cycles

---

## Diagnosis steps

### 1. Check latency metric trend

Verify if latency is:
- steadily increasing → backpressure
- spiking intermittently → network jitter
- flat but high → systemic bottleneck

---

### 2. Check system CPU and memory

```bash
top

Look for:

feed_monitor pegged at 100% CPU
memory pressure causing GC pauses (if applicable)
3. Check packet flow stability
python3 network/multicast_receiver.py

Verify:

packets still arriving
delay between updates increased
4. Check network-level congestion
sudo tcpdump -i any udp port 5001

Compare:

wire arrival time vs application processing time
5. Check downstream lag amplification
matching engine delay
risk engine stale mid-price usage
order book update backlog
Recovery steps
Case 1: CPU bottleneck
restart feed consumer
remove blocking operations in feed path
reduce logging overhead
Case 2: network congestion
sudo tc qdisc del dev eth0 root

Then verify NIC throughput and kernel buffer sizing.

Case 3: consumer overload
scale feed_monitor horizontally (if architecture allows)
decouple parsing from ingestion (queue-based design)
Case 4: upstream throttling
check sender process load
verify publish rate stability
Verification

Latency must return to normal band:

feed_latency_ms < threshold
stable over multiple scrapes
no backlog growth in downstream systems
mid-price updates align with real-time feed
Prevention
add explicit latency SLO alerts (not just feed_alive)
separate ingestion thread from processing thread
introduce queue buffering with backpressure visibility
monitor:
latency trend slope (not just value)
CPU per ingestion pipeline stage
Key insight

This is a silent degradation mode:

system appears healthy (feed_alive == 1)
but decision quality is already corrupted

In real trading systems, this is often more dangerous than a full outage.

Related
fix_disconnect.md
risk_kill_switch.md
kafka_lag.md
exchange/monitoring/feed_monitor.py
