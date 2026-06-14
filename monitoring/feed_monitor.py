#!/usr/bin/env python3

"""
monitoring/feed_monitor.py

Market data feed monitor with Prometheus metrics.
"""

import json
import socket
import struct
import threading
import time

from datetime import datetime

from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import start_http_server

MULTICAST_GROUP = "239.0.0.1"
MULTICAST_PORT = 5001
PROMETHEUS_PORT = 8000
SYMBOL_TTL_SECONDS = 60
FEED_TIMEOUT_SECONDS = 5

feed_latency = Gauge("feed_latency_ms", "Last packet latency in ms")
feed_packets_total = Counter("feed_packets_total", "Total packets received")
feed_packets_dropped = Counter("feed_packets_dropped_total", "Total packets dropped")
feed_alive = Gauge("feed_alive", "1 if feed is active 0 if silent")
feed_symbols_active = Gauge("feed_symbols_active", "Symbols seen in last 60s")
feed_decode_errors = Counter("feed_decode_errors_total", "JSON decode or packet parsing failures")
feed_gap_events = Counter("feed_gap_events_total", "Number of sequence gaps detected")
feed_last_sequence = Gauge("feed_last_sequence", "Most recent sequence number")

last_sequence = None
last_packet_time = 0.0
symbol_last_seen = {}
state_lock = threading.Lock()


def parse_packet(data: bytes):
    payload = json.loads(data.decode("utf-8"))
    sequence = int(payload["sequence"])
    symbol = str(payload["symbol"])
    sent_time = datetime.strptime(payload["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
    latency_ms = (datetime.now() - sent_time).total_seconds() * 1000
    return sequence, latency_ms, symbol


def process_packet(data: bytes):
    global last_sequence, last_packet_time

    try:
        sequence, latency_ms, symbol = parse_packet(data)
    except Exception as exc:
        feed_decode_errors.inc()
        print(f"decode error: {exc}")
        return

    feed_packets_total.inc()
    feed_latency.set(latency_ms)
    feed_last_sequence.set(sequence)

    if last_sequence is not None:
        expected_sequence = last_sequence + 1
        if sequence > expected_sequence:
            dropped = sequence - expected_sequence
            feed_packets_dropped.inc(dropped)
            feed_gap_events.inc()
        elif sequence < last_sequence:
            print(f"out-of-order packet: current={sequence} last={last_sequence}")

    last_sequence = sequence
    last_packet_time = time.time()

    with state_lock:
        symbol_last_seen[symbol] = time.time()


def symbol_cleanup_loop():
    while True:
        now = time.time()
        cutoff = now - SYMBOL_TTL_SECONDS
        with state_lock:
            expired = [s for s, ts in symbol_last_seen.items() if ts < cutoff]
            for s in expired:
                del symbol_last_seen[s]
            feed_symbols_active.set(len(symbol_last_seen))
        time.sleep(5)


def feed_health_loop():
    while True:
        now = time.time()
        if last_packet_time > 0 and now - last_packet_time <= FEED_TIMEOUT_SECONDS:
            feed_alive.set(1)
        else:
            feed_alive.set(0)
        time.sleep(1)


def create_multicast_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MULTICAST_PORT))
    membership_request = struct.pack(
        "4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY
    )
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_request)
    return sock


def receive_loop():
    sock = create_multicast_socket()
    print(f"Listening on {MULTICAST_GROUP}:{MULTICAST_PORT}")
    while True:
        try:
            data, addr = sock.recvfrom(65535)
            process_packet(data)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"receiver error: {exc}")


def main():
    print(f"Starting Prometheus exporter on :{PROMETHEUS_PORT}")
    start_http_server(PROMETHEUS_PORT)
    threading.Thread(target=symbol_cleanup_loop, daemon=True).start()
    threading.Thread(target=feed_health_loop, daemon=True).start()
    receive_loop()


if __name__ == "__main__":
    main()
