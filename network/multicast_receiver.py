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

    expected_sequence = None
    total_received = 0
    total_dropped = 0

    try:
        while True:
            data, sender_address = sock.recvfrom(1024)
            received_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            try:
                message = data.decode('utf-8')
                payload = json.loads(message)

                # Latency measurement
                sent_time = datetime.strptime(
                    payload['timestamp'], "%Y-%m-%d %H:%M:%S.%f"
                )
                recv_time = datetime.now()
                latency_ms = (recv_time - sent_time).total_seconds() * 1000

                # Packet loss detection
                seq = payload.get('sequence')
                if expected_sequence is not None and seq != expected_sequence:
                    dropped = seq - expected_sequence
                    total_dropped += dropped
                    print(f"  *** PACKET LOSS: {dropped} packet(s) dropped "
                          f"(expected #{expected_sequence}, got #{seq}) ***")
                expected_sequence = seq + 1
                total_received += 1

                print(
                    f"[{received_time}] #{seq} {payload['symbol']} @ {payload['price']} "
                    f"| latency: {latency_ms:.2f}ms "
                    f"| received: {total_received} dropped: {total_dropped}"
                )

            except UnicodeDecodeError:
                print(f"[{received_time}] Recv raw bytes (undecodable): {data}")

    except KeyboardInterrupt:
        print("\nStopping receiver...")
        print(f"\nSession Summary:")
        print(f"  Total received : {total_received}")
        print(f"  Total dropped  : {total_dropped}")
        if total_received + total_dropped > 0:
            loss_pct = (total_dropped / (total_received + total_dropped)) * 100
            print(f"  Packet loss    : {loss_pct:.2f}%")
    finally:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        sock.close()

if __name__ == '__main__':
    start_multicast_receiver()