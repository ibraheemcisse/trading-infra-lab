# order_types.py

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(Enum):
    NEW = "NEW"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    order_id: str
    symbol: str
    side: Side
    order_type: OrderType
    quantity: int
    price: Optional[float]
    timestamp: datetime
    status: OrderStatus = OrderStatus.NEW


@dataclass
class Trade:
    trade_id: str
    symbol: str
    buyer_order_id: str
    seller_order_id: str
    quantity: int
    price: float
    timestamp: datetime
