# logger.py

from collections import deque
import statistics

class TradeLogger:
    """
    A logger for recording detailed trade-level information in a single-asset market simulation.
    Each log entry captures trade details, agent state changes, and market conditions for downstream analysis.
    """
    def __init__(self, initial_endowments=None, volatility_window=10, ma_window=50):
        self.records = []
        self.price_history = deque(maxlen=ma_window)
        self.volatility_window = volatility_window
        self.ma_window = ma_window
        self.initial_endowments = initial_endowments or {}
        self._last_tick_logged = None
        self._last_price_logged = None

    def log(self,
            tick, agent_id, agent_strategy, action, units, price,
            best_bid, best_ask,
            agent_cash_before, agent_cash_after,
            agent_holdings_before, agent_holdings_after):
        # Update price history once per unique tick/price
        if self._last_tick_logged != tick or self._last_price_logged != price:
            self.price_history.append(price)
            self._last_tick_logged = tick
            self._last_price_logged = price

        # Notional value
        notional = price * units

        # Mid-price & spread
        mid_price = (best_bid + best_ask) / 2 if (best_bid is not None and best_ask is not None) else None
        spread    = (best_ask - best_bid)   if (best_bid is not None and best_ask is not None) else None

        # Volatility over recent window
        N = min(self.volatility_window, len(self.price_history))
        if N > 1:
            window_prices = list(self.price_history)[-N:]
            volatility = statistics.pstdev(window_prices)
        else:
            volatility = 0.0

        # Moving average & deviation
        sma = None
        deviation = None
        if len(self.price_history) >= self.ma_window:
            sma = sum(self.price_history) / len(self.price_history)
            deviation = price - sma

        # Initialize P&L baseline
        if agent_id not in self.initial_endowments:
            self.initial_endowments[agent_id] = agent_cash_before + agent_holdings_before * price

        # Compute portfolio value & cumulative P&L
        pv_after = agent_cash_after + agent_holdings_after * price
        pnl      = pv_after - self.initial_endowments[agent_id]

        # Append record
        self.records.append({
            "tick": tick,
            "agent_id": agent_id,
            "strategy": agent_strategy,
            "action": action,
            "units": units,
            "price": price,
            "notional": notional,
            "cash_before": agent_cash_before,
            "cash_after": agent_cash_after,
            "holdings_before": agent_holdings_before,
            "holdings_after": agent_holdings_after,
            "portfolio_value": pv_after,
            "cumulative_pnl": pnl,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid_price": mid_price,
            "spread": spread,
            "volatility": volatility,
            "vol_window": N,
            "sma": sma,
            "ma_window": self.ma_window,
            "deviation": deviation
        })
