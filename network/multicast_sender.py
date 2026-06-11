import socket
import time
import json
import random

# --- CONFIGURATION ---
MULTICAST_GROUP = '239.0.0.1'  # Standard administrative/local multicast range
PORT = 5001
TTL = 1                         # 1 = Local network only; increase if routing across subnets

def start_multicast_sender():
    # 1. Create a standard UDP socket (SOCK_DGRAM)
    # AF_INET specifies IPv4 protocols
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    # 2. Configure Multicast TTL (Time To Live)
    # This prevents the packets from bouncing around the internet indefinitely
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)
    
    # Simulated stocks
    symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN']
    prices = {sym: random.uniform(150, 500) for sym in symbols}
    
    print(f"Starting Multicast Sender to {MULTICAST_GROUP}:{PORT}...")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            # 3. Simulate a random price movement
            symbol = random.choice(symbols)
            change = random.uniform(-1.0, 1.0)
            prices[symbol] = round(prices[symbol] + change, 2)
            
            # 4. Construct the payload with a timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            payload = {
                "timestamp": current_time,
                "symbol": symbol,
                "price": prices[symbol]
            }
            
            # Encode JSON data to raw bytes for network transmission
            message = json.dumps(payload).encode('utf-8')
            
            # 5. Broadcast to the multicast group
            sock.sendto(message, (MULTICAST_GROUP, PORT))
            
            # Print localized confirmation of what was sent
            print(f"[{current_time}] Sent: {payload}")
            
            # Throttling to simulate real-world message intervals
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nStopping sender...")
    finally:
        sock.close()

if __name__ == '__main__':
    start_multicast_sender()
