import time
import statistics
import json
from datetime import datetime, timezone
from uuid import uuid4

# Import from your lab
import sys
sys.path.insert(0, '/home/ubuntu/trading-infra-lab')

from exchange.matching_engine import MatchingEngine
from exchange.order_book import OrderBook
from exchange.order_types import Order, Side, OrderType
from risk.risk_engine import RiskEngine

def measure_baseline_latencies(num_orders=100):
    """Measure matching engine latencies at baseline load."""
    
    order_book = OrderBook()
    risk_engine = RiskEngine()
    matcher = MatchingEngine(order_book, risk_engine)
    
    latencies = []
    
    print(f"Measuring {num_orders} orders...")
    
    for i in range(num_orders):
        # Create test order
        order = Order(
            order_id=str(uuid4()),
            symbol="AAPL",
            side=Side.BUY if i % 2 == 0 else Side.SELL,
            quantity=100,
            price=150.00 + (i % 10),
            order_type=OrderType.LIMIT,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Measure matching time
        start = time.perf_counter()
        trades = matcher.process_order(order)
        elapsed_us = (time.perf_counter() - start) * 1_000_000  # Convert to microseconds
        
        latencies.append(elapsed_us)
        
        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1} orders...")
    
    # Calculate percentiles
    p50 = statistics.quantiles(latencies, n=100)[49]
    p95 = statistics.quantiles(latencies, n=100)[94]
    p99 = statistics.quantiles(latencies, n=100)[98]
    p999 = statistics.quantiles(latencies, n=100)[998] if len(latencies) > 1000 else max(latencies)
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "num_orders": num_orders,
        "latencies_us": {
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "p999": round(p999, 2),
            "min": round(min(latencies), 2),
            "max": round(max(latencies), 2),
            "mean": round(statistics.mean(latencies), 2),
        }
    }
    
    print("\n=== Baseline Latency Distribution ===")
    print(f"P50:  {results['latencies_us']['p50']:.2f} µs")
    print(f"P95:  {results['latencies_us']['p95']:.2f} µs")
    print(f"P99:  {results['latencies_us']['p99']:.2f} µs")
    print(f"P99.9: {results['latencies_us']['p999']:.2f} µs")
    print(f"Min:  {results['latencies_us']['min']:.2f} µs")
    print(f"Max:  {results['latencies_us']['max']:.2f} µs")
    
    # Save results
    with open('/tmp/baseline_latencies.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    measure_baseline_latencies(num_orders=100)
