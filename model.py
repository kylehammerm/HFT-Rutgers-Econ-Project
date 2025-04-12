import random
from mesa import Model
from mesa.datacollection import DataCollector
from agents import TraderAgent
from strategies import TrendFollowingStrategy, MeanReversionStrategy, MomentumStrategy, BreakoutStrategy, ValueInvestingStrategy, ArbitrageStrategy
from logger import TradeLogger

class AssetMarket(Model):
    def __init__(self, initial_price=100.0, price_impact=1, num_agents=100, num_arbitrage_agents=1):
        super().__init__()
        self.initial_price = initial_price
        self.price = initial_price
        self.last_price = initial_price
        self.price_impact = price_impact
        self.bias_direction = 0
        self.bias_active = False
        self.tick = 0
        self.trades_this_tick = 0
        self.baseline_price = initial_price
        # Keep price history for computing trends and averages
        self.price_history = [initial_price]
        # Initialize trade logger for global transaction logging
        self.logger = TradeLogger()
        self.trade_log = self.logger.records  # reference to global trade records list

        # Create trading agents with a mix of strategies
        strategy_classes = [TrendFollowingStrategy, MeanReversionStrategy, MomentumStrategy, BreakoutStrategy, ValueInvestingStrategy]
        for i in range(num_agents):
            StratClass = strategy_classes[i % len(strategy_classes)]
            strategy = StratClass()
            agent = TraderAgent(i, self, strategy)
            self.agents.add(agent)
        # Create arbitrage agents with special strategy
        for j in range(num_arbitrage_agents):
            agent_id = num_agents + j
            strategy = ArbitrageStrategy()
            agent = TraderAgent(agent_id, self, strategy)
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
            # Start of a new 10-tick cycle: reset baseline and introduce a bias
            self.baseline_price = self.price
            self.bias_direction = random.choice([1, -1])
            self.bias_active = True

        self.last_price = self.price
        price_change = random.gauss(0, 1)
        if self.bias_active:
            price_change += 0.5 * self.bias_direction
        self.price = max(self.price + price_change, 0)

        if self.bias_active:
            # Turn off bias if price moves beyond ±10% of baseline
            if self.price >= 1.1 * self.baseline_price or self.price <= 0.9 * self.baseline_price:
                self.bias_active = False

        self.trades_this_tick = 0
        for agent_set in self.agents_by_type.values():
            agent_set.shuffle_do("step")

        # Collect data after all agents have acted
        self.datacollector.collect(self)
        # Log the price at the end of this tick for history
        self.price_history.append(self.price)
        # Every 10 ticks, reset advantage and rebaseline for next cycle
        if self.tick % 10 == 0:
            self.bias_active = False
            self.bias_direction = 0
