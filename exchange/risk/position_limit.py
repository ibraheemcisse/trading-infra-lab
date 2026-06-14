from dataclasses import dataclass
from order_types import Order, Side


@dataclass
class PositionLimitConfig:
    max_position: int


class PositionLimitRule:
    def __init__(self, config: PositionLimitConfig):
        self.config = config
        self.positions = {}  # symbol -> net position

    def get_position(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

    def check(self, order: Order, mid_price=None):
        current = self.get_position(order.symbol)

        projected = current + (
            order.quantity if order.side == Side.BUY else -order.quantity
        )

        if abs(projected) > self.config.max_position:
            return False, f"Position limit breached: {projected}"

        return True, ""

    def on_trade_fill(self, symbol: str, side: Side, quantity: int):
        if symbol not in self.positions:
            self.positions[symbol] = 0

        if side == Side.BUY:
            self.positions[symbol] += quantity
        else:
            self.positions[symbol] -= quantity
