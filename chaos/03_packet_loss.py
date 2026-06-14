#!/usr/bin/env python3
"""
Chaos Test 03: Packet Loss

Injects packet loss at the sender via a control file - the sender
probabilistically skips sendto() for a percentage of packets while
still incrementing its sequence counter, creating real gaps that
feed_monitor.py detects via feed_packets_dropped_total and
feed_gap_events_total.

(tc netem loss was not used - see postmortem 002: same-host
multicast bypasses qdisc on both ens5 and lo.)

Usage:
    python3 chaos/03_packet_loss.py inject [loss_pct]
    python3 chaos/03_packet_loss.py recover
    python3 chaos/03_packet_loss.py status

Expected impact:
    feed_alive remains 1 (feed is not dead, just lossy)
    feed_latency_ms remains normal (packets that DO arrive are fast)
    feed_packets_dropped_total increases
    feed_gap_events_total increases

This is the subtle case described in chaos 02/03 planning: a feed
that looks healthy on latency/alive checks but is silently losing
data. The open question is at what loss percentage pricing integrity
becomes unacceptable - an operational policy decision, not purely
a code fix.

Related runbook: runbooks/market_data_gap.md
"""

import sys

CONTROL_FILE = "/tmp/multicast_sender_loss_pct"
DEFAULT_LOSS_PCT = 20


def inject(loss_pct=DEFAULT_LOSS_PCT):
    with open(CONTROL_FILE, "w") as f:
        f.write(str(loss_pct))
    print(f"Injected {loss_pct}% packet loss at multicast_sender")
    print("feed_packets_dropped_total and feed_gap_events_total should start increasing")
    print("feed_alive should remain 1 (feed is lossy, not dead)")


def recover():
    with open(CONTROL_FILE, "w") as f:
        f.write("0")
    print("Removed injected packet loss (set to 0%)")


def status():
    try:
        with open(CONTROL_FILE) as f:
            value = f.read().strip()
        print(f"Current injected loss: {value}%")
    except FileNotFoundError:
        print("No loss injected (control file does not exist)")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("inject", "recover", "status"):
        print("Usage: python3 03_packet_loss.py [inject|recover|status] [loss_pct]")
        sys.exit(1)

    if sys.argv[1] == "inject":
        loss = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_LOSS_PCT
        inject(loss)
    elif sys.argv[1] == "recover":
        recover()
    else:
        status()
