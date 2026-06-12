import json
import os
import re
import socket
import statistics
import subprocess
import threading
import time
from datetime import datetime

def percentile(values, pct):
    if not values:
        return None

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    k = (len(values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(values) - 1)

    if f == c:
        return values[f]

    return values[f] + (values[c] - values[f]) * (k - f)


def measure_ping_latency(count=100):
    cmd = [
        "ping",
        "-c",
        str(count),
        "127.0.0.1",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    latencies = []
    pattern = re.compile(r"time=([\d.]+)")

    for line in result.stdout.splitlines():
        match = pattern.search(line)
        if match:
            latencies.append(float(match.group(1)))

    if not latencies:
        raise RuntimeError("No ping latency samples collected")

    return {
        "samples": len(latencies),
        "min_ms": min(latencies),
        "avg_ms": statistics.mean(latencies),
        "max_ms": max(latencies),
        "p99_ms": percentile(latencies, 99),
    }


def udp_echo_server(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.bind(("127.0.0.1", port))

        while True:
            data, addr = sock.recvfrom(4096)

            if data == b"STOP":
                break

            sock.sendto(data, addr)

    finally:
        sock.close()


def measure_udp_latency(samples=100):
    port = 9999

    server_thread = threading.Thread(
        target=udp_echo_server,
        args=(port,),
        daemon=True,
    )

    server_thread.start()
    time.sleep(0.2)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    latencies = []

    try:
        sock.settimeout(1)

        for _ in range(samples):
            start = time.perf_counter_ns()

            sock.sendto(b"PING", ("127.0.0.1", port))

            sock.recvfrom(4096)

            end = time.perf_counter_ns()

            latency_us = (end - start) / 1000.0
            latencies.append(latency_us)

        sock.sendto(b"STOP", ("127.0.0.1", port))

    finally:
        sock.close()

    return {
        "samples": len(latencies),
        "min_us": min(latencies),
        "avg_us": statistics.mean(latencies),
        "max_us": max(latencies),
        "p99_us": percentile(latencies, 99),
    }


def read_sysctl(key):
    try:
        result = subprocess.run(
            ["sysctl", "-n", key],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def cpu_governor():
    path = (
        "/sys/devices/system/cpu/"
        "cpu0/cpufreq/scaling_governor"
    )

    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return "unknown"


def irqbalance_status():
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "irqbalance"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def system_snapshot():
    return {
        "rmem_max": read_sysctl("net.core.rmem_max"),
        "wmem_max": read_sysctl("net.core.wmem_max"),
        "tcp_low_latency": read_sysctl("net.ipv4.tcp_low_latency"),
        "cpu_governor": cpu_governor(),
        "irqbalance": irqbalance_status(),
    }


def main():
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "host": socket.gethostname(),
        "loopback_ping": measure_ping_latency(),
        "udp_roundtrip": measure_udp_latency(),
        "system_snapshot": system_snapshot(),
    }

    print(json.dumps(report, indent=2))

    with open("baseline_results.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\nSaved baseline_results.json")


if __name__ == "__main__":
    main()
