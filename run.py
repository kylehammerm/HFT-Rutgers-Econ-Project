from model import AssetMarket
import matplotlib.pyplot as plt

# Initialize the model with desired parameters (including one arbitrage agent by default).
model = AssetMarket(initial_price=100.0, price_impact=.01, num_agents=100, num_arbitrage_agents=1)

for _ in range(2000):
    model.step()

# Retrieve collected data.
price_data = model.datacollector.get_model_vars_dataframe()
agent_data = model.datacollector.get_agent_vars_dataframe()

price_data.to_csv("Data/price_data.csv", index=True)
wealth_data = agent_data.unstack(level=1)['Wealth']
wealth_data.to_csv("Data/agent_wealth.csv", index=True)

plt.figure(figsize=(10, 5))
plt.plot(price_data.index, price_data["Price"], marker="o", label="Asset Price")

# The dashed lines indicate ±10% of the initial price. Note: The model resets its baseline every 10 ticks.
plt.axhline(y=1.1 * model.initial_price, color='r', linestyle='--', label='Upper ±10% (initial baseline)')
plt.axhline(y=0.9 * model.initial_price, color='r', linestyle='--', label='Lower ±10% (initial baseline)')
plt.xlabel("Tick")
plt.ylabel("Price")
plt.title("Asset Price Over Time")
plt.legend()
plt.show()

# The global trade log of all transactions is available as model.trade_log (or model.logger.records).
