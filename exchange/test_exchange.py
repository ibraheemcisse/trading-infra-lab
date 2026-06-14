# test_exchange.py

from order_book import OrderBook
from order_types import Order, OrderType, Side, OrderStatus
from matching_engine import MatchingEngine

from risk.kill_switch import KillSwitch
from risk.max_order_size import MaxOrderSizeRule, MaxOrderSizeConfig
from risk.fat_finger import FatFingerRule, FatFingerConfig
from risk.position_limit import PositionLimitRule, PositionLimitConfig
from risk.audit_log import AuditLogger
from risk.risk_engine import RiskEngine

from datetime import datetime, timezone
from uuid import uuid4


def make_order(symbol, side, order_type, quantity, price=None):
    return Order(
        order_id=str(uuid4())[:8],
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        timestamp=datetime.now(timezone.utc),
    )


def main():
    order_book = OrderBook()

    kill_switch = KillSwitch()
    audit_logger = AuditLogger(path="logs/risk_rejections.log")

    rules = [
        MaxOrderSizeRule(MaxOrderSizeConfig(max_size=1000)),
        FatFingerRule(FatFingerConfig(max_deviation_pct=0.10)),
        PositionLimitRule(PositionLimitConfig(max_position=500)),
    ]

    risk_engine = RiskEngine(rules, kill_switch, audit_logger)
    engine = MatchingEngine(order_book, risk_engine)

    print("=" * 70)
    print("TEST 1: Resting limit orders (no match)")
    print("=" * 70)

    # Seed the book with resting orders
    sell1 = make_order("AAPL", Side.SELL, OrderType.LIMIT, 100, 185.50)
    sell2 = make_order("AAPL", Side.SELL, OrderType.LIMIT, 200, 185.60)
    buy1 = make_order("AAPL", Side.BUY, OrderType.LIMIT, 150, 185.00)

    engine.process_order(sell1)
    engine.process_order(sell2)
    engine.process_order(buy1)

    order_book.display()

    print("\n" + "=" * 70)
    print("TEST 2: Crossing limit order (partial fill)")
    print("=" * 70)

    # This buy crosses sell1 (185.50) — should fill 100, rest at 185.55 stays
    buy2 = make_order("AAPL", Side.BUY, OrderType.LIMIT, 250, 185.55)
    trades = engine.process_order(buy2)

    for t in trades:
        print(f"TRADE: {t.quantity} @ {t.price} "
              f"(buyer={t.buyer_order_id}, seller={t.seller_order_id})")

    order_book.display()

    print("\n" + "=" * 70)
    print("TEST 3: Market order consumes book")
    print("=" * 70)

    market_buy = make_order("AAPL", Side.BUY, OrderType.MARKET, 100)
    trades = engine.process_order(market_buy)

    for t in trades:
        print(f"TRADE: {t.quantity} @ {t.price} "
              f"(buyer={t.buyer_order_id}, seller={t.seller_order_id})")

    order_book.display()

    print("\n" + "=" * 70)
    print("TEST 4: Risk rejection - max order size")
    print("=" * 70)

    huge_order = make_order("AAPL", Side.BUY, OrderType.LIMIT, 5000, 185.00)
    trades = engine.process_order(huge_order)
    print(f"Order status: {huge_order.status}")
    print(f"Trades generated: {len(trades)}")

    print("\n" + "=" * 70)
    print("TEST 5: Risk rejection - fat finger")
    print("=" * 70)

    # mid price is around 185.5x, this is way off
    fat_finger_order = make_order("AAPL", Side.BUY, OrderType.LIMIT, 10, 999.00)
    trades = engine.process_order(fat_finger_order)
    print(f"Order status: {fat_finger_order.status}")
    print(f"Trades generated: {len(trades)}")

    print("\n" + "=" * 70)
    print("TEST 6: Kill switch")
    print("=" * 70)

    kill_switch.trigger()

    normal_order = make_order("AAPL", Side.BUY, OrderType.LIMIT, 10, 185.50)
    trades = engine.process_order(normal_order)
    print(f"Order status: {normal_order.status}")
    print(f"Trades generated: {len(trades)}")

    kill_switch.reset()

    print("\n" + "=" * 70)
    print("AUDIT LOG (logs/risk_rejections.log)")
    print("=" * 70)

    try:
        with open("logs/risk_rejections.log") as f:
            for line in f:
                print(line.strip())
    except FileNotFoundError:
        print("No rejections logged")


if __name__ == "__main__":
    main()
