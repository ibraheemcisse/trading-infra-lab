# 📘 Runbook: Market Data Feed Gap

---

## Alert

One of the following conditions is true:

- `feed_alive == 0` continuously for **> 5 seconds**
- `feed_packets_dropped_total` increases at a sustained rate (> N packets/sec over 3–5 scrapes)
- `feed_latency_ms` is stale (no update within expected scrape interval + buffer)

---

## Severity

**Critical**

This is a hard dependency failure for:

- Matching engine pricing validity
- Risk engine (fat-finger protection becomes unreliable)
- Pre-market gate (blocks session open)
- Market data consumers (strategies, monitors, position valuation)

If this occurs during market hours:
> The system is effectively trading without reliable price input and must be considered unsafe.

---

## What this means

The multicast market data pipeline has failed at one or more layers:

### 1. Sender failure
- process stopped
- crash loop
- event loop blocked or deadlocked

### 2. Network transmission failure
- UDP multicast not leaving host
- NIC/kernel-level packet loss
- traffic shaping applied (`tc netem`)

### 3. Receiver desynchronization
- multicast group membership lost
- socket buffer overflow
- consumer not reading fast enough

---

### System-level impact

When this occurs:

- Best bid/ask becomes stale or frozen
- Mid-price used by:
  - fat-finger protection
  - risk engine
  - mark-to-market valuation  
  becomes invalid
- Matching engine may continue operating on outdated pricing unless explicitly gated

---

## Diagnosis steps

### 1. Check sender process

```bash
ps aux | grep multicast_sender

Look for:

missing process → hard failure
stuck or high CPU → soft failure (event loop blocked)
2. Check metrics (Grafana / Prometheus)

Inspect:

feed_alive
1 → healthy
0 → feed dead or fully disconnected
feed_latency_ms
flatline → upstream stall
spikes → congestion or queue buildup
feed_packets_dropped_total
increasing → receiver overload or network loss

Also verify no scrape gaps in Prometheus (can mimic feed failure).

3. Receiver sanity check
python3 network/multicast_receiver.py

Expected:

continuous packet stream within ~1–2 seconds

If no packets:

sender failure OR network isolation

If packets appear here but not in system:

consumer-layer issue (not infra)
4. Network validation
sudo tcpdump -i any udp port 5001

Interpretation:

No packets → sender or network path broken
Packets visible but not consumed → application issue
Intermittent drops → NIC/kernel buffer pressure

Check multicast group membership:

ip maddr show
5. Check traffic shaping / injected faults
sudo tc qdisc show dev eth0

Look for:

delay injection
packet loss rules
bandwidth shaping
Recovery steps
Case 1: sender process is dead
cd ~/trading-infra-lab
python3 network/multicast_sender.py &

Preferred:

run via systemd or supervisor with auto-restart enabled
Case 2: sender alive but feed degraded

Remove network emulation:

sudo tc qdisc del dev eth0 root

Then verify CPU and network health of sender host.

Case 3: receiver desynced or stuck

Restart dependent consumers:

python3 monitoring/feed_monitor.py &
python3 exchange/matching_engine.py &

If frequent:

indicates consumer backpressure or blocking I/O, not a feed issue

Case 4: multicast group membership lost
restart consumer processes
verify socket joins multicast group (IP_ADD_MEMBERSHIP)
confirm kernel routing for multicast traffic
Verification

Do not rely on logs alone.

Confirm system recovery via metrics:

feed_alive == 1 within one scrape interval (~15s)
feed_packets_total resumes monotonic increase
feed_packets_dropped_total stops increasing
feed_latency_ms returns to baseline
No gaps in Grafana feed timeline

Then validate system gates:

python3 pre_market/checks.py

Expected:

Multicast Feed → PASS
Risk Engine → PASS (mid-price now valid again)
Prevention
1. Sender auto-restart

Use systemd:

Restart=always
RestartSec=2
2. Feed watchdog
alert if feed_alive == 0 for >5s
escalate if repeated within 5 minutes
3. Risk engine dependency protection

If feed is stale:

disable mid-price dependent checks OR
block trading entirely
4. Circuit breaker for matching engine

Trigger if:

feed gap exceeds threshold
or price staleness detected

Actions:

reject incoming orders
or switch to read-only mode
Related
Chaos test: chaos/01_feed_blackout.py
Metrics:
feed_alive
feed_packets_total
feed_packets_dropped_total
feed_latency_ms
Dashboard: Trading Feed Health (Grafana)
Matching engine: exchange/matching_engine.py
Downstream dependency: Risk engine mid-price validation
