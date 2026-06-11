import socket
import time
import json
import random
from datetime import datetime

# --- CONFIGURATION ---
MULTICAST_GROUP = '239.0.0.1'
PORT = 5001
TTL = 1

def start_multicast_sender():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)

    symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN']
    prices = {sym: random.uniform(150, 500) for sym in symbols}

    print(f"Starting Multicast Sender to {MULTICAST_GROUP}:{PORT}...")
    print("Press Ctrl+C to stop.\n")

    sequence = 0

    try:
        while True:
            sequence += 1

            symbol = random.choice(symbols)
            change = random.uniform(-1.0, 1.0)
            prices[symbol] = round(prices[symbol] + change, 2)

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            payload = {
                "sequence": sequence,
                "timestamp": current_time,
                "symbol": symbol,
                "price": prices[symbol]
            }

            message = json.dumps(payload).encode('utf-8')
            sock.sendto(message, (MULTICAST_GROUP, PORT))
            print(f"[{current_time}] Sent #{sequence}: {symbol} @ {prices[symbol]}")

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\nStopping sender...")
    finally:
        sock.close()

if __name__ == '__main__':
    start_multicast_sender()