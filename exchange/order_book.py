# order_book.py

from typing import Dict, List, Optional

from order_types import Order
from order_types import Side


class OrderBook:
    def __init__(self):
        self.bids: List[Order] = []
        self.asks: List[Order] = []

        # Fast order lookup for cancellation
        self.order_map: Dict[str, Order] = {}

    def add_order(self, order: Order) -> None:
        """
        Add an order and maintain price-time priority.
        """

        self.order_map[order.order_id] = order

        if order.side == Side.BUY:
            self.bids.append(order)

            # Highest price first
            # Earliest timestamp first
            self.bids.sort(
                key=lambda o: (-o.price, o.timestamp)
            )

        elif order.side == Side.SELL:
            self.asks.append(order)

            # Lowest price first
            # Earliest timestamp first
            self.asks.sort(
                key=lambda o: (o.price, o.timestamp)
            )

    def cancel_order(self, order_id: str) -> bool:
        """
        Remove an order from the book.

        Returns:
            True if cancelled
            False if order not found
        """

        order = self.order_map.get(order_id)

        if order is None:
            return False

        if order.side == Side.BUY:
            self.bids = [
                o for o in self.bids
                if o.order_id != order_id
            ]

        else:
            self.asks = [
                o for o in self.asks
                if o.order_id != order_id
            ]

        del self.order_map[order_id]

        return True

    def get_best_bid(self) -> Optional[Order]:
        """
        Highest-priority buy order.
        """

        if not self.bids:
            return None

        return self.bids[0]

    def get_best_ask(self) -> Optional[Order]:
        """
        Lowest-priority sell order.
        """

        if not self.asks:
            return None

        return self.asks[0]

    def display(self) -> None:
        """
        Print current order book.
        """

        print("\n" + "=" * 70)
        print("ORDER BOOK")
        print("=" * 70)

        print("\nASKS (SELL ORDERS)")
        print("-" * 70)

        if not self.asks:
            print("EMPTY")
        else:
            for order in self.asks:
                print(
                    f"{order.symbol:8} "
                    f"{order.quantity:8} @ "
                    f"{order.price:10.2f} "
                    f"{order.order_id}"
                )

        print("\nBIDS (BUY ORDERS)")
        print("-" * 70)

        if not self.bids:
            print("EMPTY")
        else:
            for order in self.bids:
                print(
                    f"{order.symbol:8} "
                    f"{order.quantity:8} @ "
                    f"{order.price:10.2f} "
                    f"{order.order_id}"
                )

        print("=" * 70)

    def __len__(self) -> int:
        return len(self.bids) + len(self.asks)
