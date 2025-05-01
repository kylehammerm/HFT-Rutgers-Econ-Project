# run.py

from model import AssetMarket
import matplotlib.pyplot as plt
import pandas as pd

# Initialize and run the model
model = AssetMarket(initial_price=100.0, price_impact=0.001, num_agents=100, num_arbitrage_agents=1)
for _ in range(2000):
    model.step()

# Export price and wealth
price_data = model.datacollector.get_model_vars_dataframe()
agent_data = model.datacollector.get_agent_vars_dataframe()
price_data.to_csv("Data/price_data.csv", index=True)
wealth_data = agent_data.unstack(level=1)['Wealth']
wealth_data.to_csv("Data/agent_wealth.csv", index=True)

# Export the detailed trade ledger
ledger_df = pd.DataFrame(model.logger.records)
ledger_df.to_csv("Data/trade_ledger_detailed.csv", index=False)

# Plot the asset price
plt.figure(figsize=(10, 5))
plt.plot(price_data.index, price_data["Price"], marker="o", label="Asset Price")
plt.axhline(y=1.1 * model.initial_price, color='r', linestyle='--', label='Upper ±10% (baseline)')
plt.axhline(y=0.9 * model.initial_price, color='r', linestyle='--', label='Lower ±10% (baseline)')
plt.xlabel("Tick")
plt.ylabel("Price")
plt.title("Asset Price Over Time")
plt.legend()
plt.show()
