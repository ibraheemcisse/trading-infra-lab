import socket
import struct
import time

# --- CONFIGURATION ---
# Must match the sender's configuration exactly
MULTICAST_GROUP = '239.0.0.1'
PORT = 5001

def start_multicast_receiver():
    # 1. Create a standard UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    # 2. Allow multiple applications to bind to the same port on this host
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # 3. Bind to the wildcard interface ('') and the specific port
    sock.bind(('', PORT))
    
    # 4. Join the multicast group using struct.pack
    # '4s4s' formats two 4-byte strings (IPv4 addresses converted to packed binary format)
    # INADDR_ANY ('0.0.0.0') tells the kernel to listen on all available network interfaces
    group_packed = socket.inet_aton(MULTICAST_GROUP)
    interface_packed = socket.inet_aton('0.0.0.0')
    mreq = struct.pack('4s4s', group_packed, interface_packed)
    
    # Tell the kernel to add this socket to the multicast membership
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    print(f"Listening for multicast packets on {MULTICAST_GROUP}:{PORT}...")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            # 5. Block until a packet arrives (buffer size 1024 bytes)
            data, sender_address = sock.recvfrom(1024)
            
            # Record the exact arrival time
            received_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            # 6. Decode and display the payload
            try:
                message = data.decode('utf-8')
                print(f"[{received_time}] Recv from {sender_address}: {message}")
            except UnicodeDecodeError:
                print(f"[{received_time}] Recv raw bytes (undecodable): {data}")
                
    except KeyboardInterrupt:
        print("\nStopping receiver...")
    finally:
        # 7. Clean up and leave the group
        # Though the OS cleans up on exit, dropping explicitly is best practice
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        sock.close()

if __name__ == '__main__':
    start_multicast_receiver()
