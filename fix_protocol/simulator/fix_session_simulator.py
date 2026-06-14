"""
fix_session_simulator.py

Minimal TCP listener simulating FIX session ports.
Real FIX session management (Logon, Heartbeat, sequence numbers)
is documented as a known limitation - see README.

Used by pre_market checks.py to verify FIX ports are listening.
"""

import socket
import threading
import time

FIX_PORTS = [9876, 9877]


def handle_client(conn, addr):
    conn.close()


def start_server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("localhost", port))
    s.listen(5)
    print(f"FIX simulator listening on port {port}")
    while True:
        conn, addr = s.accept()
        threading.Thread(
            target=handle_client, args=(conn, addr), daemon=True
        ).start()


if __name__ == "__main__":
    for port in FIX_PORTS:
        threading.Thread(
            target=start_server, args=(port,), daemon=True
        ).start()

    while True:
        time.sleep(60)
