import socket
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, List

import psutil


class CheckStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str

    @property
    def passed(self):
        return self.status == CheckStatus.PASS


# ---------------------------------------------------------------------------
# System Health
# ---------------------------------------------------------------------------

def check_system_resources() -> CheckResult:
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    issues = []
    if cpu > 80:
        issues.append(f"CPU {cpu}%")
    if memory.percent > 80:
        issues.append(f"Memory {memory.percent}%")
    if disk.percent > 80:
        issues.append(f"Disk {disk.percent}%")

    if issues:
        return CheckResult(
            name="System Resources",
            status=CheckStatus.FAIL,
            message=f"High usage: {', '.join(issues)}",
        )
    return CheckResult(
        name="System Resources",
        status=CheckStatus.PASS,
        message=f"CPU {cpu}% | Memory {memory.percent}% | Disk {disk.percent}%",
    )


def check_processes() -> CheckResult:
    required_processes = ["sshd", "systemd"]

    running = {
        (proc.info.get("name") or "").lower()
        for proc in psutil.process_iter(["name"])
    }

    missing = [p for p in required_processes if p.lower() not in running]

    if missing:
        return CheckResult(
            name="Trading Processes",
            status=CheckStatus.FAIL,
            message=f"Missing: {', '.join(missing)}",
        )
    return CheckResult(
        name="Trading Processes",
        status=CheckStatus.PASS,
        message="All required processes running",
    )


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------

def check_network_connectivity() -> CheckResult:
    endpoints = [
        ("8.8.8.8", 53, "DNS"),
        ("google.com", 443, "Google"),
    ]

    failed = []
    for host, port, name in endpoints:
        try:
            socket.create_connection((host, port), timeout=3)
        except Exception:
            failed.append(name)

    if failed:
        return CheckResult(
            name="Network Connectivity",
            status=CheckStatus.FAIL,
            message=f"Unreachable: {', '.join(failed)}",
        )
    return CheckResult(
        name="Network Connectivity",
        status=CheckStatus.PASS,
        message="All endpoints reachable",
    )


def check_multicast_feed() -> CheckResult:
    MULTICAST_GROUP = "239.0.0.1"
    MULTICAST_PORT = 5001
    TIMEOUT_SECONDS = 3

    sock = None
    try:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP,
        )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", MULTICAST_PORT))

        membership = struct.pack(
            "4sL",
            socket.inet_aton(MULTICAST_GROUP),
            socket.INADDR_ANY,
        )
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        sock.settimeout(TIMEOUT_SECONDS)

        data, addr = sock.recvfrom(65535)
        return CheckResult(
            name="Multicast Feed",
            status=CheckStatus.PASS,
            message=f"Received {len(data)} bytes from {addr[0]}",
        )
    except socket.timeout:
        return CheckResult(
            name="Multicast Feed",
            status=CheckStatus.FAIL,
            message=f"No packets received within {TIMEOUT_SECONDS}s",
        )
    except Exception as exc:
        return CheckResult(
            name="Multicast Feed",
            status=CheckStatus.FAIL,
            message=f"Error: {exc}",
        )
    finally:
        if sock is not None:
            sock.close()


def check_fix_sessions() -> CheckResult:
    return CheckResult(
        name="FIX Sessions",
        status=CheckStatus.SKIP,
        message="Not yet implemented",
    )


# ---------------------------------------------------------------------------
# Market Data
# ---------------------------------------------------------------------------

def check_market_data_latency() -> CheckResult:
    return CheckResult(
        name="Market Data Latency",
        status=CheckStatus.SKIP,
        message="Not yet implemented",
    )


def check_stale_prices() -> CheckResult:
    return CheckResult(
        name="Stale Prices",
        status=CheckStatus.SKIP,
        message="Not yet implemented",
    )


def check_pricing_feeds() -> CheckResult:
    return CheckResult(
        name="Pricing Feeds",
        status=CheckStatus.SKIP,
        message="Not yet implemented",
    )


# ---------------------------------------------------------------------------
# Application Health
# ---------------------------------------------------------------------------

def check_log_errors() -> CheckResult:
    log_file = "/var/log/syslog"
    error_count = 0

    try:
        with open(log_file, "r") as f:
            for line in f:
                if "ERROR" in line or "CRITICAL" in line:
                    error_count += 1
    except FileNotFoundError:
        return CheckResult(
            name="Log Errors",
            status=CheckStatus.SKIP,
            message=f"{log_file} not found",
        )

    if error_count > 10:
        return CheckResult(
            name="Log Errors",
            status=CheckStatus.FAIL,
            message=f"{error_count} errors found in {log_file}",
        )
    return CheckResult(
        name="Log Errors",
        status=CheckStatus.PASS,
        message=f"{error_count} errors in {log_file}",
    )


def check_database_connectivity() -> CheckResult:
    return CheckResult(
        name="Database Connectivity",
        status=CheckStatus.SKIP,
        message="Not yet implemented",
    )


def check_queue_depths() -> CheckResult:
    return CheckResult(
        name="Queue Depths",
        status=CheckStatus.SKIP,
        message="Not yet implemented",
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

CHECKS: List[Callable[[], CheckResult]] = [
    check_system_resources,
    check_processes,
    check_network_connectivity,
    check_multicast_feed,
    check_fix_sessions,
    check_market_data_latency,
    check_stale_prices,
    check_pricing_feeds,
    check_log_errors,
    check_database_connectivity,
    check_queue_depths,
]


def run_all_checks() -> int:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print("=" * 80)
    print("PRE-MARKET HEALTH CHECK")
    print(f"Timestamp : {timestamp}")
    print("=" * 80)

    results: List[CheckResult] = []

    for check in CHECKS:
        try:
            result = check()
        except Exception as exc:
            result = CheckResult(
                name=check.__name__,
                status=CheckStatus.FAIL,
                message=f"Unhandled exception: {exc}",
            )
        results.append(result)
        print(
            f"[{result.status.value:<4}] "
            f"{result.name:<25} "
            f"{result.message}"
        )

    has_failures = any(r.status == CheckStatus.FAIL for r in results)
    has_skipped = any(r.status == CheckStatus.SKIP for r in results)

    passed = sum(1 for r in results if r.status == CheckStatus.PASS)
    failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
    skipped = sum(1 for r in results if r.status == CheckStatus.SKIP)

    print("-" * 80)
    print(f"Results   : {passed} passed | {failed} failed | {skipped} skipped")
    print("-" * 80)

    if has_failures:
        print("MARKET OPEN STATUS : BLOCKED - ESCALATE IMMEDIATELY")
        return 1
    elif has_skipped:
        print("MARKET OPEN STATUS : WARNING - SKIPPED CHECKS PRESENT")
        return 2
    else:
        print("MARKET OPEN STATUS : APPROVED")
        return 0


if __name__ == "__main__":
    raise SystemExit(run_all_checks())