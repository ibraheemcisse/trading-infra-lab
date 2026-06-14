#!/usr/bin/env python3

"""
Chaos Test 02: Latency Injection

Injects artificial network latency using tc netem.

Usage:

    python3 chaos/02_latency_injection.py inject
    python3 chaos/02_latency_injection.py recover
    python3 chaos/02_latency_injection.py status
"""

import argparse
import subprocess
import sys

INTERFACE = "ens5"
DELAY_MS = 250


def run(cmd: str):
    print(f"$ {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout.strip())

    if result.stderr:
        print(result.stderr.strip())

    return result.returncode


def inject():
    print(f"Injecting {DELAY_MS}ms latency on {INTERFACE}")

    rc = run(
        f"sudo tc qdisc replace dev {INTERFACE} root "
        f"netem delay {DELAY_MS}ms"
    )

    sys.exit(rc)


def recover():
    print(f"Removing netem rules from {INTERFACE}")

    rc = run(
        f"sudo tc qdisc del dev {INTERFACE} root"
    )

    # tc returns non-zero if no qdisc exists
    sys.exit(0)


def status():
    rc = run(
        f"sudo tc qdisc show dev {INTERFACE}"
    )

    sys.exit(rc)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=["inject", "recover", "status"]
    )

    args = parser.parse_args()

    if args.action == "inject":
        inject()

    elif args.action == "recover":
        recover()

    else:
        status()


if __name__ == "__main__":
    main()
