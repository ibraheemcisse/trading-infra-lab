from dataclasses import dataclass
from order_types import Order, OrderType


@dataclass
class FatFingerConfig:
    max_deviation_pct: float  # e.g. 0.1 = 10%


class FatFingerRule:
    def __init__(self, config: FatFingerConfig):
        self.config = config

    def check(self, order: Order, mid_price=None):
        if order.order_type == OrderType.MARKET:
            return True, ""

        if mid_price is None or mid_price <= 0:
            return True, ""

        if order.price is None:
            return False, "Limit order missing price"

        deviation = abs(order.price - mid_price) / mid_price

        if deviation > self.config.max_deviation_pct:
            return False, f"Price deviation {deviation:.2%} exceeds limit"

        return True, ""
