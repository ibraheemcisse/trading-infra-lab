# kafka/consumer.py

import json

from kafka import KafkaConsumer


BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "trade-events"
GROUP_ID = "trade-event-consumers"


def handle_new_order(event):
    print("\n[NEW ORDER]")
    print(f"Order ID : {event.get('order_id')}")
    print(f"Symbol   : {event.get('symbol')}")
    print(f"Side     : {event.get('side')}")
    print(f"Quantity : {event.get('quantity')}")
    print(f"Price    : {event.get('price')}")
    print(f"Status   : {event.get('status')}")
    print(f"Time     : {event.get('timestamp')}")


def handle_execution_report(event):
    print("\n[EXECUTION REPORT]")
    print(f"Order ID      : {event.get('order_id')}")
    print(f"Symbol        : {event.get('symbol')}")
    print(f"Executed Qty  : {event.get('executed_quantity')}")
    print(f"Execution Px  : {event.get('execution_price')}")
    print(f"Exec Type     : {event.get('exec_type')}")
    print(f"Status        : {event.get('status')}")
    print(f"Time          : {event.get('timestamp')}")


def handle_unknown(event):
    print("\n[UNKNOWN EVENT]")
    print(json.dumps(event, indent=2))


def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    print(f"Connected to Kafka: {BOOTSTRAP_SERVERS}")
    print(f"Subscribed to topic: {TOPIC}")
    print("Waiting for events...\n")

    try:
        for message in consumer:
            event = message.value

            print("-" * 60)
            print(
                f"Partition={message.partition} "
                f"Offset={message.offset}"
            )

            event_type = event.get("event_type")

            if event_type == "NEW_ORDER":
                handle_new_order(event)

            elif event_type == "EXECUTION_REPORT":
                handle_execution_report(event)

            else:
                handle_unknown(event)

    except KeyboardInterrupt:
        print("\nShutting down consumer...")

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
