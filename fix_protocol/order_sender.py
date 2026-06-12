import socket
import time
from datetime import datetime, timezone

import simplefix

HOST = "localhost"
PORT = 9876
SENDER_COMP_ID = "CLIENT1"
TARGET_COMP_ID = "SERVER1"


def build_new_order_single(clordid, symbol, side, qty, price):
    msg = simplefix.FixMessage()

    msg.append_pair(8,  "FIX.4.4")
    msg.append_pair(35, "D")
    msg.append_pair(49, SENDER_COMP_ID)
    msg.append_pair(56, TARGET_COMP_ID)
    msg.append_utc_timestamp(52)

    msg.append_pair(11, clordid)
    msg.append_pair(55, symbol)
    msg.append_pair(54, side)
    msg.append_pair(38, str(qty))
    msg.append_pair(40, "2")
    msg.append_pair(44, f"{price:.2f}")
    msg.append_pair(59, "0")
    msg.append_pair(60, datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3])

    return msg.encode()


def main():
    orders = [
        ("ORD0001", "AAPL", "1", 100, 185.50),
        ("ORD0002", "MSFT", "1",  50, 420.25),
        ("ORD0003", "GOOG", "2",  25, 175.75),
        ("ORD0004", "TSLA", "1",  10, 205.10),
        ("ORD0005", "AMZN", "2",  75, 185.00),
    ]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}")
        print("-" * 40)

        for clordid, symbol, side, qty, price in orders:
            raw = build_new_order_single(clordid, symbol, side, qty, price)
            sock.sendall(raw)

            side_name = {"1": "BUY", "2": "SELL"}.get(side, side)
            print(f"Sent {clordid} | {symbol} | {side_name} | {qty} @ {price:.2f}")
            print(raw.decode("ascii", errors="replace").replace("\x01", "|"))

            time.sleep(1)

        print("-" * 40)
        print("All orders sent")


if __name__ == "__main__":
    main()
