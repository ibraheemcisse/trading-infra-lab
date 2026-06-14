import os
import json
import socket
import struct
import requests
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, List


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG = {
    "multicast_group": "239.0.0.1",
    "multicast_port": 5001,
    "latency_warn_ms": 10,
    "latency_fail_ms": 100,
    "stale_price_ms": 5000,
    "required_symbols": ["AAPL", "MSFT", "GOOG", "AMZN"],
    "fix_ports": [9876, 9877],
    "feed_monitor_url": "http://localhost:8000/metrics",
    "queue_limits": {
        "market_data": 1000,
        "orders": 500,
        "risk": 500,
    },
}

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DB_NAME"),
}


# ---------------------------------------------------------------------------
# Status model
# ---------------------------------------------------------------------------

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
# Multicast helper — single persistent socket
# ---------------------------------------------------------------------------

def _make_multicast_socket(timeout: float = 3) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", CONFIG["multicast_port"]))
    membership = struct.pack(
        "4sL",
        socket.inet_aton(CONFIG["multicast_group"]),
        socket.INADDR_ANY,
    )
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    sock.settimeout(timeout)
    return sock


def _receive_one(sock: socket.socket):
    data, sender = sock.recvfrom(4096)
    return json.loads(data.decode()), sender


# ---------------------------------------------------------------------------
# System Health
# ---------------------------------------------------------------------------

def check_system_resources() -> CheckResult:
    import psutil
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    issues = []
    if cpu > 80:
        issues.append(f"CPU {cpu}%")
    if mem > 80:
        issues.append(f"MEM {mem}%")
    if disk > 80:
        issues.append(f"DISK {disk}%")

    if issues:
        return CheckResult(
            "System Resources",
            CheckStatus.FAIL,
            f"High usage: {', '.join(issues)}"
        )
    return CheckResult(
        "System Resources",
        CheckStatus.PASS,
        f"CPU {cpu}% | MEM {mem}% | DISK {disk}%"
    )


def check_processes() -> CheckResult:
    import psutil
    required = ["sshd", "systemd"]
    running = {
        (p.info.get("name") or "").lower()
        for p in psutil.process_iter(["name"])
    }
    missing = [p for p in required if p.lower() not in running]

    if missing:
        return CheckResult(
            "Trading Processes",
            CheckStatus.FAIL,
            f"Missing: {', '.join(missing)}"
        )
    return CheckResult(
        "Trading Processes",
        CheckStatus.PASS,
        "All required processes running"
    )


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------

def check_network() -> CheckResult:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return CheckResult("Network", CheckStatus.PASS, "Internet reachable")
    except Exception as e:
        return CheckResult("Network", CheckStatus.FAIL, str(e))


def check_multicast() -> CheckResult:
    sock = None
    try:
        sock = _make_multicast_socket(timeout=3)
        payload, _ = _receive_one(sock)
        return CheckResult(
            "Multicast Feed",
            CheckStatus.PASS,
            f"Received {payload.get('symbol')} seq#{payload.get('sequence')}"
        )
    except socket.timeout:
        return CheckResult(
            "Multicast Feed",
            CheckStatus.FAIL,
            "No packets received within 3s"
        )
    except Exception as e:
        return CheckResult("Multicast Feed", CheckStatus.FAIL, str(e))
    finally:
        if sock:
            sock.close()


# ---------------------------------------------------------------------------
# Market Data
# ---------------------------------------------------------------------------

def check_market_data_latency() -> CheckResult:
    sock = None
    try:
        sock = _make_multicast_socket(timeout=3)
        payload, _ = _receive_one(sock)

        sent = datetime.strptime(payload["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
        latency_ms = (datetime.now() - sent).total_seconds() * 1000

        if latency_ms > CONFIG["latency_fail_ms"]:
            return CheckResult(
                "Market Data Latency",
                CheckStatus.FAIL,
                f"{latency_ms:.2f}ms — exceeds {CONFIG['latency_fail_ms']}ms threshold"
            )
        if latency_ms > CONFIG["latency_warn_ms"]:
            return CheckResult(
                "Market Data Latency",
                CheckStatus.PASS,
                f"{latency_ms:.2f}ms — above warn threshold {CONFIG['latency_warn_ms']}ms"
            )
        return CheckResult(
            "Market Data Latency",
            CheckStatus.PASS,
            f"{latency_ms:.2f}ms"
        )
    except socket.timeout:
        return CheckResult(
            "Market Data Latency",
            CheckStatus.FAIL,
            "No packets received within 3s"
        )
    except Exception as e:
        return CheckResult("Market Data Latency", CheckStatus.FAIL, str(e))
    finally:
        if sock:
            sock.close()


def check_stale_prices() -> CheckResult:
    sock = None
    try:
        sock = _make_multicast_socket(timeout=3)
        payload, _ = _receive_one(sock)

        sent = datetime.strptime(payload["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
        age_ms = (datetime.now() - sent).total_seconds() * 1000

        if age_ms > CONFIG["stale_price_ms"]:
            return CheckResult(
                "Stale Prices",
                CheckStatus.FAIL,
                f"Quote age {age_ms:.0f}ms — exceeds {CONFIG['stale_price_ms']}ms"
            )
        return CheckResult(
            "Stale Prices",
            CheckStatus.PASS,
            f"Quote age {age_ms:.0f}ms"
        )
    except socket.timeout:
        return CheckResult(
            "Stale Prices",
            CheckStatus.FAIL,
            "No packets received within 3s"
        )
    except Exception as e:
        return CheckResult("Stale Prices", CheckStatus.FAIL, str(e))
    finally:
        if sock:
            sock.close()


def check_pricing_feeds() -> CheckResult:
    """
    Checks which symbols are actively publishing prices.

    NOTE: This previously ran its own independent 5-second multicast
    listen, sampling ~5 packets from a 4-symbol random feed. The
    probability that all 4 symbols appear in 5 random draws is only
    ~23% (surjections(5,4)/4^5 = 240/1024), meaning this check failed
    by pure chance ~77% of the time even when the system was fully
    healthy.

    Fixed: reuse feed_monitor.py's existing 60-second rolling window
    (feed_symbols_active metric) instead of a fresh short sample.
    This requires feed_monitor.py to be running and exporting metrics
    on :8000 — see monitoring/feed_monitor.py.
    """
    try:
        resp = requests.get(CONFIG["feed_monitor_url"], timeout=2)
        resp.raise_for_status()

        active_count = None
        for line in resp.text.splitlines():
            if line.startswith("feed_symbols_active "):
                active_count = float(line.split()[-1])
                break

        if active_count is None:
            return CheckResult(
                "Pricing Feeds",
                CheckStatus.SKIP,
                "feed_symbols_active metric not found in feed_monitor output"
            )

        expected = len(CONFIG["required_symbols"])
        active_count = int(active_count)

        if active_count >= expected:
            return CheckResult(
                "Pricing Feeds",
                CheckStatus.PASS,
                f"{active_count}/{expected} symbols active (60s window)"
            )
        return CheckResult(
            "Pricing Feeds",
            CheckStatus.FAIL,
            f"Only {active_count}/{expected} symbols active in last 60s"
        )

    except requests.exceptions.ConnectionError:
        return CheckResult(
            "Pricing Feeds",
            CheckStatus.SKIP,
            "feed_monitor.py not reachable on :8000 (is it running?)"
        )
    except Exception as e:
        return CheckResult("Pricing Feeds", CheckStatus.FAIL, str(e))


# ---------------------------------------------------------------------------
# FIX Sessions
# ---------------------------------------------------------------------------

def check_fix_sessions() -> CheckResult:
    """
    Checks that configured FIX ports are in LISTEN state.
    Note: a production FIX check would also verify logon state,
    heartbeat age, and sequence number synchronization.
    This implementation verifies port availability only.
    """
    import psutil
    listening = set()
    for conn in psutil.net_connections(kind="tcp"):
        if conn.status == "LISTEN" and conn.laddr:
            listening.add(conn.laddr.port)

    missing = [str(p) for p in CONFIG["fix_ports"] if p not in listening]

    if missing:
        return CheckResult(
            "FIX Sessions",
            CheckStatus.FAIL,
            f"Ports not listening: {', '.join(missing)}"
        )
    return CheckResult(
        "FIX Sessions",
        CheckStatus.PASS,
        f"Ports listening: {', '.join(str(p) for p in CONFIG['fix_ports'])}"
    )


# ---------------------------------------------------------------------------
# Application Health
# ---------------------------------------------------------------------------

def check_database() -> CheckResult:
    if not all([DB_CONFIG["user"], DB_CONFIG["password"], DB_CONFIG["dbname"]]):
        return CheckResult(
            "Database",
            CheckStatus.SKIP,
            "DB_USER, DB_PASSWORD or DB_NAME not set"
        )
    try:
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=3)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return CheckResult("Database", CheckStatus.PASS, "Connected — SELECT 1 OK")
    except Exception as e:
        return CheckResult("Database", CheckStatus.FAIL, str(e))


def check_queue_depths() -> CheckResult:
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()

        issues = []
        depths = []

        for q, limit in CONFIG["queue_limits"].items():
            depth = int(r.get(f"queue:{q}") or 0)
            depths.append(f"{q}={depth}")
            if depth > limit:
                issues.append(f"{q}={depth} exceeds limit {limit}")

        if issues:
            return CheckResult(
                "Queue Depths",
                CheckStatus.FAIL,
                "; ".join(issues)
            )
        return CheckResult(
            "Queue Depths",
            CheckStatus.PASS,
            " | ".join(depths)
        )
    except Exception as e:
        return CheckResult("Queue Depths", CheckStatus.FAIL, str(e))


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
            "Log Errors",
            CheckStatus.SKIP,
            f"{log_file} not found"
        )
    if error_count > 10:
        return CheckResult(
            "Log Errors",
            CheckStatus.FAIL,
            f"{error_count} errors in {log_file}"
        )
    return CheckResult(
        "Log Errors",
        CheckStatus.PASS,
        f"{error_count} errors in {log_file}"
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

CHECKS: List[Callable[[], CheckResult]] = [
    check_system_resources,
    check_processes,
    check_network,
    check_multicast,
    check_market_data_latency,
    check_stale_prices,
    check_pricing_feeds,
    check_fix_sessions,
    check_database,
    check_queue_depths,
    check_log_errors,
]


def main() -> int:
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
                check.__name__,
                CheckStatus.FAIL,
                f"Unhandled exception: {exc}"
            )
        results.append(result)
        print(
            f"[{result.status.value:<4}] "
            f"{result.name:<25} "
            f"{result.message}"
        )

    passed = sum(1 for r in results if r.status == CheckStatus.PASS)
    failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
    skipped = sum(1 for r in results if r.status == CheckStatus.SKIP)

    has_failures = failed > 0
    has_skipped = skipped > 0

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
    raise SystemExit(main())
