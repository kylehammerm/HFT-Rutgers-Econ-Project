from mesa import Agent

class TradingStrategy:
    def decide_action(self, agent, model):
        raise NotImplementedError

class TrendFollowingStrategy(TradingStrategy):
    def decide_action(self, agent, model):
        if model.price > model.last_price:
            return "buy"
        elif model.price < model.last_price:
            return "sell"
        else:
            return None

class MeanReversionStrategy(TradingStrategy):
    def decide_action(self, agent, model):
        if model.price < model.last_price:
            return "buy"
        elif model.price > model.last_price:
            return "sell"
        else:
            return None

class TraderAgent(Agent):
    def __init__(self, unique_id, model, strategy):
        super().__init__(model)  
        self.cash = 1000.0
        self.holdings = 0
        self.strategy = strategy

    @property
    def wealth(self):
        return self.cash + self.holdings * self.model.price

    def step(self):
        action = self.strategy.decide_action(self, self.model)
        if action == "buy" and self.cash >= self.model.price:
            self.cash -= self.model.price
            self.holdings += 1
            self.model.price += self.model.price_impact
            self.model.trades_this_tick += 1
        elif action == "sell" and self.holdings > 0:
            self.holdings -= 1
            self.cash += self.model.price
            self.model.price -= self.model.price_impact
            if self.model.price < 0:
                self.model.price = 0
            self.model.trades_this_tick += 1
