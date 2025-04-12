from mesa import Agent
from strategies import TrendFollowingStrategy, MeanReversionStrategy, MomentumStrategy, BreakoutStrategy, ValueInvestingStrategy, ArbitrageStrategy

class TraderAgent(Agent):
    def __init__(self, unique_id, model, strategy):
        super().__init__(model)
        # Ensure unique_id is stored (Mesa Agent may not handle it automatically)
        self.unique_id = unique_id
        self.cash = 1000.0
        self.holdings = 0
        self.strategy = strategy  # instance of a TradingStrategy subclass
        self.trade_history = []  # record of this agent's trades (each entry: (tick, action, units, price))

    @property
    def wealth(self):
        return self.cash + self.holdings * self.model.price

    def step(self):
        decision = self.strategy.decide_action(self, self.model)
        if decision is None:
            # No trade action this tick
            return
        action, units = decision
        if units <= 0:
            return  # no units to trade
        # Record the price at start of trade action
        start_price = self.model.price
        actual_units = 0
        if action == "buy":
            # Determine how many units we can actually buy with available cash, execute sequentially
            while actual_units < units and self.cash >= self.model.price and self.model.price > 0:
                cost = self.model.price
                if self.cash < cost:
                    break
                self.cash -= cost
                self.holdings += 1
                self.model.trades_this_tick += 1
                self.model.price += self.model.price_impact
                actual_units += 1
        elif action == "sell":
            # Determine how many units we can actually sell (cannot sell more than holdings)
            units_to_sell = min(units, self.holdings)
            while actual_units < units_to_sell and self.holdings > 0:
                self.holdings -= 1
                # Cash gained from sale is current price
                self.cash += self.model.price
                self.model.trades_this_tick += 1
                self.model.price -= self.model.price_impact
                if self.model.price < 0:
                    self.model.price = 0
                actual_units += 1
        else:
            # Unrecognized action
            return
        if actual_units <= 0:
            # If no trade executed (e.g., not enough cash or holdings), do nothing
            return
        # Log the transaction in agent's history and global log
        trade_record = (self.model.tick, self.unique_id, type(self.strategy).__name__, action, actual_units, start_price)
        self.trade_history.append(trade_record)
        # If model has a logger, record globally as well
        if hasattr(self.model, "logger"):
            self.model.logger.log(self.model.tick, self.unique_id, type(self.strategy).__name__, action, actual_units, start_price)
        else:
            # Fallback: store in model's trade_log list if exists
            if hasattr(self.model, "trade_log"):
                self.model.trade_log.append(trade_record)
