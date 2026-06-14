# chaos/01_feed_blackout.py
"""
Chaos Test 01: Feed Blackout

Simulates the multicast sender process dying unexpectedly.

Usage:
    python3 chaos/01_feed_blackout.py inject
    python3 chaos/01_feed_blackout.py recover

Expected impact:
    feed_alive -> 0 within ~5s (FEED_TIMEOUT_SECONDS in feed_monitor.py)
    feed_packets_total stops incrementing
    pre_market checks.py -> Multicast Feed check FAILS

Related runbook: runbooks/market_data_gap.md
"""

import subprocess
import sys


def inject():
    print("Injecting failure: killing multicast_sender.py")
    result = subprocess.run(
        ["pkill", "-f", "multicast_sender.py"]
    )
    if result.returncode == 0:
        print("Sender process killed.")
    else:
        print("No matching sender process found (already down?).")
    print("Watch Grafana 'Trading Feed Health' dashboard:")
    print("  feed_alive should drop to 0 within ~5 seconds")


def recover():
    print("Recovering: restarting multicast_sender.py")
    subprocess.Popen(
        ["python3", "network/multicast_sender.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("Sender restarted in background.")
    print("feed_alive should return to 1 within ~15 seconds (next scrape)")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("inject", "recover"):
        print("Usage: python3 01_feed_blackout.py [inject|recover]")
        sys.exit(1)

    if sys.argv[1] == "inject":
        inject()
    else:
        recover()
