"""
This module defines the rule-based detection methods for arbitrage behavior.
Each rule is implemented as a class inheriting from DetectionRule, with a `detect` 
method that analyzes trade data and returns suspicion probabilities.
"""

from collections import defaultdict
import config  # import the configuration constants

class DetectionRule:
    """Base class for arbitrage detection rules. New rules should inherit from this."""
    def __init__(self, name, fields):
        """
        Initialize a detection rule.
        :param name: Name of the rule (string).
        :param fields: List of trade log fields that this rule uses (must be a subset of observable fields).
        """
        self.name = name
        # Ensure the rule only uses allowed observable fields
        self.fields = fields  # fields required by this rule's logic (for configuration/verification)

    def detect(self, trades_by_agent, price_by_tick):
        """
        Analyze trades and return a mapping of suspicious probabilities.
        Must be implemented by subclasses.
        :param trades_by_agent: dict of agent_id -> list of trade records (each a dict with allowed fields).
        :param price_by_tick: dict mapping tick -> price (constructed from observable data).
        :return: dict where keys are agent IDs and values are dicts {tick: probability} for suspicious events.
        """
        raise NotImplementedError("Subclasses should implement the detect method.")

class RoundTripProfitRule(DetectionRule):
    """
    Detect fast profitable round-trip trades (buy followed by sell) within a short time window.
    This rule flags instances where an agent opens a position and closes it quickly for a profit, 
    which is a common arbitrage pattern【】.
    """
    def __init__(self, time_window=None, profit_threshold=None):
        # Use defaults from config if not provided
        self.time_window = time_window if time_window is not None else config.TIME_WINDOW
        self.profit_threshold = profit_threshold if profit_threshold is not None else config.PROFIT_THRESHOLD
        super().__init__(name="RoundTripProfitRule", 
                         fields=["tick", "agent_id", "action", "units", "price"])

    def detect(self, trades_by_agent, price_by_tick):
        # Prepare output: nested dictionary {agent: {tick: probability}}
        suspicions = {}
        for agent, trades in trades_by_agent.items():
            # Sort trades by tick (should already be sorted if input log is chronological)
            trades.sort(key=lambda x: x["tick"])
            agent_suspicions = {}
            position = 0           # current position (units held by agent)
            entry_cost = 0.0       # total cost of current open position (sum of buy costs)
            entry_units = 0        # total units of current open position
            entry_tick = None      # tick when the current position was opened
            realized_profit = 0.0  # cumulative realized profit during the round-trip (for partial closes)

            for trade in trades:
                action = trade["action"].lower()
                units = trade["units"]
                price = trade["price"]
                tick = trade["tick"]

                if position == 0:
                    # No open position currently
                    if action == "buy":
                        # Start a new position (opening a round-trip)
                        position += units
                        entry_units = units
                        entry_cost = units * price  # cost of purchased units
                        entry_tick = tick
                        realized_profit = 0.0
                        # (If action == "sell" with position 0, that would imply short selling, which is not expected here.)
                else:
                    # There is an open position
                    if action == "buy":
                        # Add to the existing position (accumulating more, though arbitrageurs typically open in one go)
                        position += units
                        entry_units += units
                        entry_cost += units * price
                        # (The round-trip start remains at entry_tick)
                    elif action == "sell":
                        # Selling part or all of the open position
                        if units < position:
                            # Partial close: realize profit on the portion sold
                            # Calculate profit for this portion: (sell_price - average_cost) * units
                            avg_cost_per_unit = entry_cost / entry_units if entry_units > 0 else 0
                            realized_profit += (price - avg_cost_per_unit) * units
                            # Update remaining position and cost basis
                            entry_cost -= avg_cost_per_unit * units
                            entry_units -= units
                            position -= units
                        elif units == position:
                            # Full close: selling all remaining units to close the round-trip
                            avg_cost_per_unit = entry_cost / entry_units if entry_units > 0 else 0
                            realized_profit += (price - avg_cost_per_unit) * units
                            position = 0
                            # Check round-trip criteria: profit and time window
                            if realized_profit > self.profit_threshold * avg_cost_per_unit * units:
                                # Calculate holding duration
                                duration = tick - entry_tick if entry_tick is not None else 0
                                if duration <= self.time_window:
                                    # Flag this round-trip as arbitrage-like
                                    # Assign a probability: 1.0 for the closing trade tick (high confidence at closure)
                                    agent_suspicions[tick] = max(agent_suspicions.get(tick, 0), 1.0)
                                    # Also mark the opening trade tick with a lower probability (the start of suspicious behavior)
                                    if entry_tick is not None:
                                        agent_suspicions[entry_tick] = max(agent_suspicions.get(entry_tick, 0), 0.5)
                            # Reset for next potential round-trip
                            entry_cost = 0.0
                            entry_units = 0
                            realized_profit = 0.0
                            entry_tick = None
            if agent_suspicions:
                suspicions[agent] = agent_suspicions
        return suspicions

class PredictiveTradeRule(DetectionRule):
    """
    Detect trades that are quickly followed by favorable price movements.
    This rule flags instances where an agent buys right before a price increase or sells 
    right before a price decrease (within a short window), suggesting the agent predicted 
    the price move【】.
    """
    def __init__(self, window=None, threshold=None):
        # Use defaults from config if not provided
        self.window = window if window is not None else config.PREDICT_WINDOW
        self.threshold = threshold if threshold is not None else config.PREDICT_THRESHOLD
        super().__init__(name="PredictiveTradeRule", 
                         fields=["tick", "agent_id", "action", "price"])  # 'units' not needed for this rule's logic

    def detect(self, trades_by_agent, price_by_tick):
        suspicions = {}
        for agent, trades in trades_by_agent.items():
            trades.sort(key=lambda x: x["tick"])
            agent_suspicions = {}
            for trade in trades:
                action = trade["action"].lower()
                price = trade["price"]
                tick = trade["tick"]
                # Only analyze if we have future prices to look at
                for future_tick in range(tick + 1, tick + 1 + self.window):
                    if future_tick in price_by_tick:
                        future_price = price_by_tick[future_tick]
                        if action == "buy":
                            # If price rises above buy price by threshold within window
                            if future_price >= price * (1 + self.threshold):
                                # Mark the buy trade tick as suspicious (agent likely anticipated rise)
                                agent_suspicions[tick] = max(agent_suspicions.get(tick, 0), 1.0)
                                break  # no need to check further into the future for this trade
                        elif action == "sell":
                            # If price falls below sell price by threshold within window
                            if future_price <= price * (1 - self.threshold):
                                # Mark the sell trade tick as suspicious (agent likely anticipated drop)
                                agent_suspicions[tick] = max(agent_suspicions.get(tick, 0), 1.0)
                                break
                    else:
                        # If we have no price data for a future tick (e.g., beyond simulation), break
                        break
            if agent_suspicions:
                suspicions[agent] = agent_suspicions
        return suspicions
