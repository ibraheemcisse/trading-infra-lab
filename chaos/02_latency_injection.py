#!/usr/bin/env python3
"""
Chaos Test 02: Latency Injection (application-level)

The original approach (tc netem on ens5/lo) had no measurable effect
on same-host multicast traffic - see postmortem 002. IP_MULTICAST_LOOP
delivers packets to local subscribers via an internal kernel path that
bypasses the qdisc on both interfaces.

This version injects delay inside feed_monitor.py itself, via a
control file. feed_monitor sleeps for the configured number of
milliseconds before processing each packet - simulating a slow
consumer (GC pause, CPU contention, blocked I/O), which is arguably
a more common real-world cause of degraded latency than network delay.

Usage:
    python3 chaos/02_latency_injection.py inject [delay_ms]
    python3 chaos/02_latency_injection.py recover
    python3 chaos/02_latency_injection.py status

Expected impact:
    feed_latency_ms increases to ~delay_ms within a few seconds
    pre_market checks.py -> Market Data Latency FAILs if delay
    exceeds latency_fail_ms (100ms)

Related runbook: runbooks/high_latency.md
Related postmortem: docs/postmortems/002-latency-injection.md
"""

import sys

CONTROL_FILE = "/tmp/feed_monitor_delay_ms"
DEFAULT_DELAY_MS = 250


def inject(delay_ms=DEFAULT_DELAY_MS):
    with open(CONTROL_FILE, "w") as f:
        f.write(str(delay_ms))
    print(f"Injected {delay_ms}ms application-level delay into feed_monitor.py")
    print(f"feed_latency_ms should rise to ~{delay_ms}ms within a few seconds")


def recover():
    with open(CONTROL_FILE, "w") as f:
        f.write("0")
    print("Removed injected delay (set to 0ms)")


def status():
    try:
        with open(CONTROL_FILE) as f:
            value = f.read().strip()
        print(f"Current injected delay: {value}ms")
    except FileNotFoundError:
        print("No delay injected (control file does not exist)")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("inject", "recover", "status"):
        print("Usage: python3 02_latency_injection.py [inject|recover|status] [delay_ms]")
        sys.exit(1)

    if sys.argv[1] == "inject":
        delay = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_DELAY_MS
        inject(delay)
    elif sys.argv[1] == "recover":
        recover()
    else:
        status()
