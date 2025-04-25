# agents.py

from mesa import Agent
from strategies import (
    TrendFollowingStrategy, MeanReversionStrategy, MomentumStrategy,
    BreakoutStrategy, ValueInvestingStrategy, ArbitrageStrategy
)

class TraderAgent(Agent):
    def __init__(self, unique_id, model, strategy):
        super().__init__(model)
        self.unique_id = unique_id
        self.cash = 1000.0
        self.holdings = 0
        self.strategy = strategy
        self.trade_history = []

    @property
    def wealth(self):
        return self.cash + self.holdings * self.model.price

    def step(self):
        decision = self.strategy.decide_action(self, self.model)
        if decision is None:
            return
        action, units = decision
        if units <= 0:
            return

        # Pre-trade snapshot
        cash_before = self.cash
        holdings_before = self.holdings
        best_bid = self.model.price - self.model.price_impact
        best_ask = self.model.price + self.model.price_impact

        start_price = self.model.price
        actual_units = 0

        if action == "buy":
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
            units_to_sell = min(units, self.holdings)
            while actual_units < units_to_sell and self.holdings > 0:
                self.holdings -= 1
                self.cash += self.model.price
                self.model.trades_this_tick += 1
                self.model.price -= self.model.price_impact
                if self.model.price < 0:
                    self.model.price = 0
                actual_units += 1

        else:
            return

        if actual_units <= 0:
            return

        # Post-trade snapshot
        cash_after = self.cash
        holdings_after = self.holdings

        # Log with enhanced logger
        self.model.logger.log(
            self.model.tick,
            self.unique_id,
            type(self.strategy).__name__,
            action,
            actual_units,
            start_price,
            best_bid,
            best_ask,
            cash_before,
            cash_after,
            holdings_before,
            holdings_after
        )

        # Local trade history (optional)
        self.trade_history.append((
            self.model.tick,
            self.unique_id,
            type(self.strategy).__name__,
            action,
            actual_units,
            start_price
        ))
