import json
from datetime import datetime, timezone


class AuditLogger:
    def __init__(self, path="logs/risk_rejections.log"):
        self.path = path

    def log_rejection(self, order, reason: str):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "order_id": order.order_id,
            "symbol": order.symbol,
            "reason": reason,
        }

        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")
