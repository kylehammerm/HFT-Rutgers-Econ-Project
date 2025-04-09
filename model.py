import random
from mesa import Model
from mesa.datacollection import DataCollector
from agents import TraderAgent, TrendFollowingStrategy, MeanReversionStrategy

class AssetMarket(Model):
    def __init__(self, initial_price=100.0, price_impact=0.5, num_agents=100):
        super().__init__()
        self.initial_price = initial_price
        self.price = initial_price
        self.last_price = initial_price
        self.price_impact = price_impact
        self.bias_direction = 0
        self.bias_active = False
        self.tick = 0
        self.trades_this_tick = 0

        for i in range(num_agents):
            strategy = TrendFollowingStrategy() if i % 2 == 0 else MeanReversionStrategy()
            agent = TraderAgent(i, self, strategy)
            self.agents.add(agent)

        self.datacollector = DataCollector(
            model_reporters={
                "Price": lambda m: m.price,
                "Trades": lambda m: m.trades_this_tick
            },
            agent_reporters={
                "Wealth": lambda a: a.wealth
            }
        )

    def step(self):
        self.tick += 1
        if (self.tick - 1) % 10 == 0:
            self.bias_direction = random.choice([1, -1])
            self.bias_active = True

        self.last_price = self.price
        price_change = random.gauss(0, 1)
        if self.bias_active:
            price_change += 0.5 * self.bias_direction
        self.price = max(self.price + price_change, 0)

        if self.bias_active:
            if self.price >= 1.1 * self.initial_price or self.price <= 0.9 * self.initial_price:
                self.bias_active = False

        self.trades_this_tick = 0
        for agent_set in self.agents_by_type.values():
            agent_set.shuffle_do("step")

        self.datacollector.collect(self)
