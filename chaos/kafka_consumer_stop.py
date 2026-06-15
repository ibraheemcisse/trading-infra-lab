#!/usr/bin/env python3
"""
Chaos 05: Kafka Container Stop
Simulates Kafka broker failure by stopping the container.
Verifies feed becomes unavailable and gate detects it.
Measures detection latency and recovery time.

Failure Mode:
- Kafka broker (running in docker) stops/crashes
- Producers/consumers cannot connect
- Feed monitor should detect broker unavailability
- Market data feed should appear stale/dead

Metrics:
- Time to feed failure detection
- Time to gate BLOCKED state
- Recovery latency when Kafka restarts
"""

import subprocess
import time
import sys
import json
from datetime import datetime

def run_cmd(cmd, shell=False):
    """Execute shell command, return output."""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", 1
    except Exception as e:
        return str(e), 1

def get_metrics():
    """Fetch current metrics from feed_monitor."""
    output, code = run_cmd(["curl", "-s", "http://localhost:8000/metrics"])
    if code != 0:
        return {}
    
    metrics = {}
    for line in output.split("\n"):
        if line.startswith("feed_"):
            parts = line.split()
            if len(parts) >= 2:
                key, val = parts[0], parts[1]
                try:
                    metrics[key] = float(val)
                except:
                    pass
    return metrics

def get_gate_status():
    """Check pre-market gate status."""
    output, code = run_cmd(["python3", "pre_market/checks.py"], shell=False)
    if "APPROVED" in output:
        return "APPROVED"
    elif "BLOCKED" in output:
        return "BLOCKED"
    elif "WARNING" in output:
        return "WARNING"
    return "UNKNOWN"

def inject(duration_sec=45):
    """Stop Kafka container and monitor for detection."""
    print("[INJECT] Stopping Kafka container...")
    
    baseline = get_metrics()
    baseline_gate = get_gate_status()
    print(f"Baseline: Gate={baseline_gate}, Feed alive={baseline.get('feed_alive', 'N/A')}")
    
    # Stop Kafka
    run_cmd("docker stop kafka", shell=True)
    print("[INJECT] Kafka container stopped")
    
    detection_time = None
    gate_blocked_time = None
    start = time.time()
    
    print(f"\n[MONITOR] Watching for failures over {duration_sec}s...")
    
    while time.time() - start < duration_sec:
        elapsed = time.time() - start
        
        # Check feed metrics
        metrics = get_metrics()
        feed_alive = metrics.get('feed_alive', -1)
        
        # Check gate
        gate = get_gate_status()
        
        print(f"[{elapsed:.1f}s] Feed alive: {feed_alive}, Gate: {gate}")
        
        # Detect when feed dies
        if feed_alive == 0 and detection_time is None:
            detection_time = elapsed
            print(f"  → Feed death detected at {detection_time:.1f}s")
        
        # Detect when gate blocks
        if gate == "BLOCKED" and gate_blocked_time is None:
            gate_blocked_time = elapsed
            print(f"  → Gate BLOCKED at {gate_blocked_time:.1f}s")
        
        time.sleep(2)
    
    print(f"\n[RESULT] Feed death detected at: {detection_time:.1f}s" if detection_time else "[RESULT] Feed did not die")
    print(f"[RESULT] Gate BLOCKED at: {gate_blocked_time:.1f}s" if gate_blocked_time else "[RESULT] Gate did not block")
    
    return detection_time, gate_blocked_time

def recover(max_wait_sec=60):
    """Restart Kafka and measure recovery."""
    print("\n[RECOVER] Restarting Kafka container...")
    
    run_cmd("docker start kafka", shell=True)
    print("[RECOVER] Kafka start command issued")
    
    # Wait for Kafka to be ready
    print("[RECOVER] Waiting for Kafka to be ready...")
    start = time.time()
    recovery_time = None
    
    while time.time() - start < max_wait_sec:
        elapsed = time.time() - start
        
        # Check if feed is alive again
        metrics = get_metrics()
        feed_alive = metrics.get('feed_alive', -1)
        
        # Check gate
        gate = get_gate_status()
        
        print(f"[{elapsed:.1f}s] Feed alive: {feed_alive}, Gate: {gate}")
        
        if feed_alive == 1 and recovery_time is None:
            recovery_time = elapsed
            print(f"  → Feed recovered at {recovery_time:.1f}s")
        
        if gate == "APPROVED" and recovery_time is not None:
            print(f"  → Gate back to APPROVED at {elapsed:.1f}s")
            break
        
        time.sleep(2)
    
    if recovery_time:
        print(f"\n[RECOVER] Total recovery latency: {recovery_time:.1f}s")
    else:
        print(f"\n[RECOVER] Kafka did not recover within {max_wait_sec}s")
    
    return recovery_time

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 chaos/05_kafka_container_stop.py <inject|recover>")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "inject":
        detection_time, gate_blocked_time = inject(duration_sec=45)
        print(f"\n{'='*60}")
        print(f"CHAOS 05 INJECT: Detection={detection_time:.1f}s, Gate block={gate_blocked_time:.1f}s" 
              if detection_time and gate_blocked_time else "CHAOS 05 INJECT: Incomplete detection")
        print(f"{'='*60}")
    elif action == "recover":
        recovery_time = recover(max_wait_sec=60)
        print(f"\n{'='*60}")
        print(f"CHAOS 05 RECOVER: Recovery latency={recovery_time:.1f}s" if recovery_time else "CHAOS 05 RECOVER: Failed")
        print(f"{'='*60}")
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
