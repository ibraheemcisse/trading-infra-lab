#!/usr/bin/env python3
"""
Chaos 04: Consumer Crash
Simulates a Kafka consumer crash (e.g., trade_persister dies).
Verifies that the pre-market gate detects feed breakdown.

Failure Mode:
- Consumer consuming trades from Kafka crashes
- Database stops receiving new trade records
- Gate should detect stale trades (no new trades in X seconds)
- Recovery: restart consumer

Metrics:
- Time to gate detection (pre_market checks should fail)
- Feed staleness detection accuracy
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
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
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

def inject(duration_sec=30):
    """Kill the trade_persister consumer."""
    print("[INJECT] Killing trade_persister consumer...")
    
    # Get baseline metrics
    baseline = get_metrics()
    print(f"Baseline metrics: {baseline}")
    
    # Kill trade_persister
    run_cmd("pkill -f 'python3 kafka/trade_persister.py'", shell=True)
    print("[INJECT] Trade persister killed")
    
    # Monitor for gate detection
    print(f"\n[MONITOR] Watching for gate detection over {duration_sec}s...")
    start = time.time()
    detection_time = None
    
    while time.time() - start < duration_sec:
        output, code = run_cmd(["python3", "pre_market/checks.py"], shell=False)
        
        # Check if gate is BLOCKED
        if "BLOCKED" in output and detection_time is None:
            detection_time = time.time() - start
            print(f"\n[DETECT] Gate triggered BLOCKED at {detection_time:.1f}s")
            print(f"Output:\n{output}\n")
        
        # Print metrics snapshot
        metrics = get_metrics()
        if metrics:
            print(f"[{time.time() - start:.1f}s] Feed alive: {metrics.get('feed_alive', 'N/A')}, "
                  f"Latency: {metrics.get('feed_latency_ms', 'N/A')}ms")
        
        time.sleep(2)
    
    print(f"\n[RESULT] Detection latency: {detection_time:.1f}s" if detection_time else "[RESULT] No detection")
    return detection_time

def recover():
    """Restart the trade_persister consumer."""
    print("\n[RECOVER] Restarting trade_persister...")
    
    # Source env and restart
    run_cmd(
        "export DB_USER=trading_user DB_PASSWORD=change_me_locally DB_NAME=trading_lab DB_HOST=localhost DB_PORT=5432; "
        "python3 kafka/trade_persister.py > /tmp/trade_persister.log 2>&1 &",
        shell=True
    )
    
    print("[RECOVER] Trade persister restarted (backgrounded)")
    time.sleep(5)
    
    # Verify gate is APPROVED
    output, code = run_cmd(["python3", "pre_market/checks.py"], shell=False)
    if "APPROVED" in output:
        print("[RECOVER] Gate back to APPROVED ✓")
    else:
        print("[RECOVER] Gate status unclear:")
        print(output)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 chaos/04_consumer_crash.py <inject|recover>")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "inject":
        detection_time = inject(duration_sec=30)
        print(f"\n{'='*60}")
        print(f"CHAOS 04 RESULT: Consumer crash detected in {detection_time:.1f}s" if detection_time else "CHAOS 04: No detection")
        print(f"{'='*60}")
    elif action == "recover":
        recover()
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
