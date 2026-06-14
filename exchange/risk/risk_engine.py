from dataclasses import dataclass
from typing import List

from order_types import Order


@dataclass
class RiskCheckResult:
    approved: bool
    reason: str = ""


class RiskEngine:
    def __init__(self, rules: List, kill_switch, audit_logger):
        self.rules = rules
        self.kill_switch = kill_switch
        self.audit_logger = audit_logger

    def check(self, order: Order, mid_price=None) -> RiskCheckResult:
        if self.kill_switch.is_triggered():
            reason = "Kill switch active"
            self.audit_logger.log_rejection(order, reason)
            return RiskCheckResult(False, reason)

        for rule in self.rules:
            ok, reason = rule.check(order, mid_price)
            if not ok:
                self.audit_logger.log_rejection(order, reason)
                return RiskCheckResult(False, reason)

        return RiskCheckResult(True)
