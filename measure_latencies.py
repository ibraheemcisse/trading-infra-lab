import time
import statistics
import json
from datetime import datetime, timezone
from uuid import uuid4
import sys
import os

# Add repo to path
sys.path.insert(0, '/home/ubuntu/trading-infra-lab')
sys.path.insert(0, '/home/ubuntu/trading-infra-lab/exchange')
sys.path.insert(0, '/home/ubuntu/trading-infra-lab/risk')

from exchange.order_book import OrderBook
from exchange.order_types import Order, Side, OrderType, OrderStatus, Trade
from exchange.matching_engine import MatchingEngine
from risk.risk_engine import RiskEngine

def measure_baseline_latencies(num_orders=100):
    """Measure matching engine latencies at baseline load."""
    
    try:
        order_book = OrderBook()
        risk_engine = RiskEngine()
        matcher = MatchingEngine(order_book, risk_engine)
    except Exception as e:
        print(f"Error initializing: {e}")
        return None
    
    latencies = []
    
    print(f"Measuring {num_orders} orders...")
    
    for i in range(num_orders):
        try:
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
        except Exception as e:
            print(f"Error processing order {i}: {e}")
            continue
    
    if not latencies:
        print("No measurements collected")
        return None
    
    # Calculate percentiles
    sorted_latencies = sorted(latencies)
    p50 = statistics.quantiles(latencies, n=100)[49]
    p95 = statistics.quantiles(latencies, n=100)[94]
    p99 = statistics.quantiles(latencies, n=100)[98]
    p999 = statistics.quantiles(latencies, n=100)[998] if len(latencies) > 1000 else max(latencies)
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "num_orders": len(latencies),
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
    print(f"P50:   {results['latencies_us']['p50']:.2f} µs")
    print(f"P95:   {results['latencies_us']['p95']:.2f} µs")
    print(f"P99:   {results['latencies_us']['p99']:.2f} µs")
    print(f"P99.9: {results['latencies_us']['p999']:.2f} µs")
    print(f"Min:   {results['latencies_us']['min']:.2f} µs")
    print(f"Max:   {results['latencies_us']['max']:.2f} µs")
    print(f"Mean:  {results['latencies_us']['mean']:.2f} µs")
    
    # Save results
    with open('/tmp/baseline_latencies.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to /tmp/baseline_latencies.json")
    
    return results

if __name__ == "__main__":
    measure_baseline_latencies(num_orders=100)
