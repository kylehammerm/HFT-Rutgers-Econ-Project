from model import AssetMarket
import matplotlib.pyplot as plt

# Initialize the model.
model = AssetMarket(initial_price=100.0, price_impact=1, num_agents=100)


for _ in range(250):
    model.step()

# Retrieve collected data.
price_data = model.datacollector.get_model_vars_dataframe()
agent_data = model.datacollector.get_agent_vars_dataframe()


price_data.to_csv("Data/price_data.csv", index=True)

wealth_data = agent_data.unstack(level=1)['Wealth']
wealth_data.to_csv("Data/agent_wealth.csv", index=True)


plt.figure(figsize=(10, 5))
plt.plot(price_data.index, price_data["Price"], marker="o", label="Asset Price")
plt.axhline(y=1.1 * model.initial_price, color='r', linestyle='--', label='Upper ±10%')
plt.axhline(y=0.9 * model.initial_price, color='r', linestyle='--', label='Lower ±10%')
plt.xlabel("Tick")
plt.ylabel("Price")
plt.title("Asset Price Over Time")
plt.legend()
plt.show()
