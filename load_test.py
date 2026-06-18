# load_test.py
import socket
import time
import statistics
from collections import defaultdict

def send_order(rate_per_sec, duration_seconds):
    """Generate orders at specified rate."""
    latencies = []
    
    for rate in [100, 500, 1000, 5000]:
        print(f"\n=== Testing {rate} orders/sec ===")
        latencies = []
        
        for _ in range(rate * duration_seconds):
            start = time.time()
            
            # Send order to FIX simulator (port 9876)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', 9876))
            sock.send(b"D\x01100\x012AAPL\x0110\x01100.00\x01")
            response = sock.recv(1024)
            sock.close()
            
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)
            
            time.sleep(1 / rate)  # Rate limiter
        
        # Calculate percentiles
        p50 = statistics.quantiles(latencies, n=100)[49]
        p95 = statistics.quantiles(latencies, n=100)[94]
        p99 = statistics.quantiles(latencies, n=100)[98]
        p999 = statistics.quantiles(latencies, n=100)[998] if len(latencies) > 1000 else "N/A"
        
        print(f"P50: {p50:.2f}ms | P95: {p95:.2f}ms | P99: {p99:.2f}ms | P99.9: {p999}")

if __name__ == "__main__":
    send_order(rate_per_sec=100, duration_seconds=60)
