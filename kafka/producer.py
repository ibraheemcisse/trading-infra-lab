# kafka/producer.py

import json
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer


BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "trade-events"


producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def now():
    return datetime.now(timezone.utc).isoformat()


def new_order(symbol, qty, price):
    order_id = str(uuid.uuid4())

    return {
        "event_type": "NEW_ORDER",
        "timestamp": now(),
        "order_id": order_id,
        "symbol": symbol,
        "side": "BUY",
        "quantity": qty,
        "price": price,
        "status": "NEW",
    }


def execution_report(order_event, executed_qty):
    return {
        "event_type": "EXECUTION_REPORT",
        "timestamp": now(),
        "order_id": order_event["order_id"],
        "symbol": order_event["symbol"],
        "executed_quantity": executed_qty,
        "execution_price": order_event["price"],
        "exec_type": "FILL",
        "status": "FILLED",
    }


def publish(event):
    future = producer.send(
        TOPIC,
        key=event["order_id"].encode("utf-8"),
        value=event,
    )

    metadata = future.get(timeout=10)

    print(
        f"Published topic={metadata.topic} "
        f"partition={metadata.partition} "
        f"offset={metadata.offset}"
    )
    print(json.dumps(event, indent=2))
    print("-" * 60)


def main():
    orders = [
        ("AAPL", 100, 185.50),
        ("MSFT", 50, 420.25),
        ("GOOG", 25, 175.75),
        ("TSLA", 10, 205.10),
    ]

    try:
        for symbol, qty, price in orders:
            order = new_order(symbol, qty, price)
            publish(order)

            time.sleep(1)

            report = execution_report(order, qty)
            publish(report)

            time.sleep(1)

    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
