"""
This module defines various trading strategy classes for the stock market simulation.
Each strategy encapsulates a decision-making rule for trading based on price signals.
"""
import random

class TradingStrategy:
    """Base class for trading strategies. Child classes should implement decide_action."""
    def decide_action(self, agent, model):
        """
        Determine the trading action for the given agent and model state.
        Returns:
            A tuple (action, units) where action is "buy" or "sell", and units is an integer amount to trade,
            or None if no action (hold).
        """
        raise NotImplementedError("decide_action must be implemented by TradingStrategy subclasses.")

class TrendFollowingStrategy(TradingStrategy):
    """
    Trend Following Strategy: Buy when price is rising, sell when it is falling.
    This strategy assumes that trends will continue.
    It uses the latest price movement as the signal.
    """
    def __init__(self, threshold=None, sensitivity=None):
        # threshold: minimum price change to trigger a trade (absolute difference)
        # sensitivity: scaling factor for trade size per unit of price change beyond threshold
        self.threshold = threshold if threshold is not None else random.uniform(0.1, 1.0)
        self.sensitivity = sensitivity if sensitivity is not None else random.uniform(0.5, 1.5)
    def decide_action(self, agent, model):
        # Price change from last tick
        price_diff = model.price - model.last_price
        if abs(price_diff) < self.threshold:
            # Change too small => hold
            return None
        # Determine base units proportional to difference
        units = int(self.sensitivity * max(0, abs(price_diff) - self.threshold)) + 1
        if price_diff > 0:
            # Price increased enough -> buy
            return ("buy", units)
        elif price_diff < 0:
            # Price decreased enough -> sell
            return ("sell", units)
        return None

class MeanReversionStrategy(TradingStrategy):
    """
    Mean Reversion Strategy: Assume price will revert to a mean.
    Buy when price has fallen significantly (expecting a rise), sell when price has risen significantly (expecting a fall).
    """
    def __init__(self, threshold=None, sensitivity=None):
        self.threshold = threshold if threshold is not None else random.uniform(0.1, 1.0)
        self.sensitivity = sensitivity if sensitivity is not None else random.uniform(0.5, 1.5)
    def decide_action(self, agent, model):
        price_diff = model.price - model.last_price
        if abs(price_diff) < self.threshold:
            return None
        units = int(self.sensitivity * max(0, abs(price_diff) - self.threshold)) + 1
        if price_diff < 0:
            # Price dropped significantly -> buy (expect revert up)
            return ("buy", units)
        elif price_diff > 0:
            # Price rose significantly -> sell (expect revert down)
            return ("sell", units)
        return None

class MomentumStrategy(TradingStrategy):
    """
    Momentum Strategy: Buy or sell based on recent multi-period price trends.
    If the price has moved consistently upward over a lookback period, continue to buy; if downward, sell.
    """
    def __init__(self, lookback=None, threshold=None, sensitivity=None):
        # lookback: number of ticks to look back for momentum
        self.lookback = lookback if lookback is not None else random.randint(3, 10)
        self.threshold = threshold if threshold is not None else random.uniform(0.5, 2.0)
        self.sensitivity = sensitivity if sensitivity is not None else random.uniform(0.5, 1.5)
    def decide_action(self, agent, model):
        # Ensure enough history for momentum calculation
        if len(model.price_history) < self.lookback + 1:
            return None  # not enough data yet
        past_index = -1 - self.lookback  # index in price_history corresponding to lookback ticks ago
        old_price = model.price_history[past_index]
        current_price = model.price  # current price in this tick (after random movement, before trading)
        price_change = current_price - old_price
        if abs(price_change) < self.threshold:
            return None
        units = int(self.sensitivity * max(0, abs(price_change) - self.threshold)) + 1
        if price_change > 0:
            # Price gained significantly over lookback period -> buy (momentum up)
            return ("buy", units)
        elif price_change < 0:
            # Price fell significantly over lookback period -> sell (momentum down)
            return ("sell", units)
        return None

class BreakoutStrategy(TradingStrategy):
    """
    Breakout Strategy: Enters trades when price breaks out of a recent range.
    Buy if price exceeds recent resistance; sell if price drops below recent support.
    """
    def __init__(self, window=None, threshold=None):
        # window: number of past ticks to define support/resistance
        self.window = window if window is not None else random.randint(5, 15)
        # threshold: minimum amount beyond the high/low to consider a valid breakout
        self.threshold = threshold if threshold is not None else random.uniform(0.5, 2.0)
    def decide_action(self, agent, model):
        history_len = len(model.price_history)
        if history_len < 2:
            return None  # not enough history
        # Determine the range over the last `window` ticks (or all available if fewer)
        window_size = min(self.window, history_len - 1)  # exclude current tick's price which is not appended yet
        recent_prices = model.price_history[-window_size:]
        if not recent_prices:
            return None
        recent_high = max(recent_prices)
        recent_low = min(recent_prices)
        current_price = model.price
        # Check for breakout above recent high
        if current_price > recent_high + self.threshold:
            # Upward breakout -> buy
            # Trade size can be proportional to how far above the breakout level
            excess = current_price - (recent_high + self.threshold)
            units = int(1 + excess)  # at least 1, plus more if significantly above
            return ("buy", units)
        # Check for breakout below recent low
        if current_price < recent_low - self.threshold:
            # Downward breakout -> sell
            excess = (recent_low - self.threshold) - current_price
            units = int(1 + excess)
            return ("sell", units)
        return None

class ValueInvestingStrategy(TradingStrategy):
    """
    Value Investing Strategy: Buy when the asset appears undervalued, sell when overvalued.
    Here we use a moving average price as a proxy for intrinsic value.
    """
    def __init__(self, window=None, threshold=None, sensitivity=None):
        # window: period over which to compute average (fair value estimate)
        self.window = window if window is not None else random.randint(10, 50)
        # threshold: minimum deviation from fair value (as absolute amount) to trigger trade
        self.threshold = threshold if threshold is not None else random.uniform(1.0, 5.0)
        self.sensitivity = sensitivity if sensitivity is not None else random.uniform(0.5, 1.5)
    def decide_action(self, agent, model):
        history_len = len(model.price_history)
        if history_len < 2:
            return None
        # Use all available data up to last tick or the specified window, whichever is smaller
        window_size = min(self.window, history_len - 1)
        recent_prices = model.price_history[-window_size:]
        if not recent_prices:
            return None
        fair_value = sum(recent_prices) / len(recent_prices)
        # Compute deviation of current price from fair value
        deviation = model.price - fair_value
        if abs(deviation) < self.threshold:
            return None
        units = int(self.sensitivity * max(0, abs(deviation) - self.threshold)) + 1
        if deviation < 0:
            # Price is below fair value (undervalued) -> buy
            return ("buy", units)
        elif deviation > 0:
            # Price is above fair value (overvalued) -> sell
            return ("sell", units)
        return None

class ArbitrageStrategy(TradingStrategy):
    """
    Arbitrage Strategy: Uses an informational edge (e.g., known market bias) to trade for profit.
    This agent knows the market's bias direction and baseline thresholds, simulating an insider edge.
    It will exploit these signals by buying ahead of upward biases and selling ahead of downward biases.
    This strategy can be extended with more complex arbitrage logic in the future.
    """
    def __init__(self, aggressiveness=None):
        # aggressiveness factor: fraction of available resources to use (0.5 to 1.0)
        self.aggressiveness = aggressiveness if aggressiveness is not None else random.uniform(0.8, 1.0)
        # Keep track of last bias state to react when bias ends
        self.last_bias_active = False
        self.last_bias_direction = 0
    def decide_action(self, agent, model):
        action = None
        units = 0
        # Check if a new bias cycle has just started this tick
        if (model.tick - 1) % 10 == 0 and model.bias_active:
            # New bias signal at beginning of cycle
            if model.bias_direction == 1:
                # Upward bias started: buy aggressively
                # Determine units as a fraction of available cash
                price = model.price
                affordable_units = int(agent.cash // price)  # max units agent can afford
                units = int(self.aggressiveness * affordable_units)
                if units > 0:
                    action = "buy"
            elif model.bias_direction == -1:
                # Downward bias started: sell holdings to avoid losses
                if agent.holdings > 0:
                    units = int(self.aggressiveness * agent.holdings)
                    if units == 0:
                        units = 1  # sell at least one if any holdings
                    action = "sell"
        # If bias is active (mid-cycle) and hasn't just started, generally hold position
        # (Arbitrage took action at start; will wait for exit conditions)
        # Check if bias just ended this tick (either via threshold or cycle completion)
        if self.last_bias_active and not model.bias_active:
            # Bias was active last tick, now it's off
            if self.last_bias_direction == 1:
                # Upward bias ended -> take profit by selling all holdings
                if agent.holdings > 0:
                    action = "sell"
                    units = agent.holdings  # sell everything
            elif self.last_bias_direction == -1:
                # Downward bias ended -> asset likely at a low, buy with available cash
                price = model.price
                affordable_units = int(agent.cash // price)
                units = int(self.aggressiveness * affordable_units)
                if units > 0:
                    action = "buy"
        # Update last bias state for next tick
        self.last_bias_active = model.bias_active
        self.last_bias_direction = model.bias_direction if model.bias_active else 0
        if action:
            return (action, units)
        return None
