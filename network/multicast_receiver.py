import socket
import struct
import time
import json
from datetime import datetime

# --- CONFIGURATION ---
MULTICAST_GROUP = '239.0.0.1'
PORT = 5001

def start_multicast_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))

    group_packed = socket.inet_aton(MULTICAST_GROUP)
    interface_packed = socket.inet_aton('0.0.0.0')
    mreq = struct.pack('4s4s', group_packed, interface_packed)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Listening for multicast packets on {MULTICAST_GROUP}:{PORT}...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            data, sender_address = sock.recvfrom(1024)
            received_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            try:
                message = data.decode('utf-8')
                payload = json.loads(message)

                sent_time = datetime.strptime(payload['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
                recv_time = datetime.now()
                latency_ms = (recv_time - sent_time).total_seconds() * 1000

                print(f"[{received_time}] {payload['symbol']} @ {payload['price']} | latency: {latency_ms:.2f}ms | from {sender_address}")

            except UnicodeDecodeError:
                print(f"[{received_time}] Recv raw bytes (undecodable): {data}")

    except KeyboardInterrupt:
        print("\nStopping receiver...")
    finally:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        sock.close()

if __name__ == '__main__':
    start_multicast_receiver()