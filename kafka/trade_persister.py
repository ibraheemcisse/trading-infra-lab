#!/usr/bin/env python3
"""
kafka/trade_persister.py

Consumes TRADE events from the trade-events Kafka topic and persists
them to PostgreSQL as a durable execution record (trade blotter).

This is intentionally decoupled from the matching engine - in a real
system, the matching engine's job is to match orders correctly and
publish events; persistence, reporting, and reconciliation are
downstream concerns handled by separate consumers.

Requires environment variables (see /etc/trading-lab.env):
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

Schema (see docs or README for full DDL):
    CREATE TABLE trades (
        id SERIAL PRIMARY KEY,
        trade_id UUID NOT NULL UNIQUE,
        symbol VARCHAR(10) NOT NULL,
        buyer_order_id VARCHAR(64) NOT NULL,
        seller_order_id VARCHAR(64) NOT NULL,
        quantity INTEGER NOT NULL,
        price NUMERIC(12, 4) NOT NULL,
        trade_timestamp TIMESTAMPTZ NOT NULL,
        received_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

Usage:
    set -a; source /etc/trading-lab.env; set +a
    python3 kafka/trade_persister.py
"""

import json
import os
from datetime import datetime

import psycopg2
from kafka import KafkaConsumer

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "trade-events"
GROUP_ID = "trade-persister"

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DB_NAME"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def parse_timestamp(value: str) -> datetime:
    """
    Handles both formats seen in this project:
    - "2026-06-14 16:23:45.123456" (naive, from multicast/matching engine)
    - "2026-06-14T16:23:45.123456+00:00" (ISO-8601 UTC, from market_data_publisher)
    """
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")


def persist_trade(conn, event: dict):
    sent = parse_timestamp(event["timestamp"])

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO trades (
                trade_id, symbol, buyer_order_id, seller_order_id,
                quantity, price, trade_timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (trade_id) DO NOTHING
            """,
            (
                event["trade_id"],
                event["symbol"],
                event["buyer_order_id"],
                event["seller_order_id"],
                event["quantity"],
                event["price"],
                sent,
            ),
        )
    conn.commit()


def main():
    if not all([DB_CONFIG["user"], DB_CONFIG["password"], DB_CONFIG["dbname"]]):
        raise SystemExit(
            "DB_USER, DB_PASSWORD, DB_NAME must be set "
            "(source /etc/trading-lab.env first)"
        )

    conn = get_connection()
    print(f"Connected to PostgreSQL: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}")

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    print(f"Subscribed to {TOPIC}, persisting TRADE events to PostgreSQL")
    print("Waiting for events...\n")

    try:
        for message in consumer:
            event = message.value
            if event.get("event_type") == "TRADE":
                persist_trade(conn, event)
                print(
                    f"Persisted trade {event['trade_id']} "
                    f"{event['symbol']} {event['quantity']}@{event['price']}"
                )
    except KeyboardInterrupt:
        print("\nShutting down trade persister...")
    finally:
        consumer.close()
        conn.close()


if __name__ == "__main__":
    main()
