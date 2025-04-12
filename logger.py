"""
This module defines a simple logger for recording trade transactions globally.
"""
class TradeLogger:
    """Logger to record trades with details like tick, trader, strategy, action, units, and price."""
    def __init__(self):
        # List of trade records; each record is a tuple (tick, trader_id, strategy, action, units, price)
        self.records = []
    def log(self, tick, trader_id, strategy_name, action, units, price):
        """Add a trade record to the log."""
        self.records.append((tick, trader_id, strategy_name, action, units, price))
