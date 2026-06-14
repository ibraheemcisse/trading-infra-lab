from dataclasses import dataclass
from order_types import Order


@dataclass
class MaxOrderSizeConfig:
    max_size: int


class MaxOrderSizeRule:
    def __init__(self, config: MaxOrderSizeConfig):
        self.config = config

    def check(self, order: Order, mid_price=None):
        if order.quantity > self.config.max_size:
            return False, f"Order size {order.quantity} exceeds max {self.config.max_size}"
        return True, ""
