"""
Main module for running the arbitrage detection system.
Reads an enhanced trade log, applies detection rules, and outputs a CSV of arbitrage probability per agent per tick.

README: 
This arbitrage detection framework is designed to be modular and extensible. It uses rule-based detectors 
that analyze trade logs post-hoc (after the trades have occurred) to identify patterns indicative of arbitrage behavior. 

**Structure:**
- **config.py:** Contains configuration such as which fields are considered observable (and thus allowed for use 
  in detection) and default parameters for the detection rules. You can adjust these settings (e.g., time windows, 
  thresholds) to fine-tune the detectors.
- **rules.py:** Defines the base `DetectionRule` class and specific rule implementations. Initially, we provide:
  - `RoundTripProfitRule`: Flags quick buy-sell round trips with profit (a common arbitrage signature).
  - `PredictiveTradeRule`: Flags trades that are followed by favorable price moves, implying the trader anticipated the move.
  New rules can be added by subclassing `DetectionRule` and implementing the `detect` method.
- **main.py:** Orchestrates the detection process. It reads the trade log, filters fields to ensure only allowed data 
  is used, then applies each rule and combines their outputs into final probabilities per agent per tick. 
  Finally, it writes the results to a CSV file.

**Extensibility:**
- *Adding a new rule:* Create a new class in `rules.py` inheriting `DetectionRule`. Implement its `detect` method 
  to output a suspicion score (0.0 to 1.0) for any agent at any tick where your rule finds arbitrage-like behavior. 
  Specify which fields it uses (to ensure compliance with observable data only). Then include an instance of 
  your rule in the list of rules in `main.py`.
- *Integrating ML or statistical models:* You can wrap a trained machine learning model or statistical detector in 
  a class inheriting `DetectionRule`. For example, `MLModelDetector` could load a model (in its constructor) and in 
  `detect()` iterate over the timeline or use windowed features of the trade log to assign probabilities for each agent 
  at each tick. The system will treat it just like a rule-based detector. Ensure that any features used by the model 
  are derived from allowed fields (or other real-world observable data like public price feeds).
- *Configuring input fields per model:* The `fields` attribute in each `DetectionRule` subclass indicates which trade log 
  fields that rule uses. This makes it clear what data influences each detection method. The framework checks that these 
  fields are a subset of ALLOWED_FIELDS from config. If you want to experiment with a detector that uses a different set 
  of inputs (say, excluding volume or including an observable order book metric), you can adjust the rule's fields and 
  ensure `ALLOWED_FIELDS` in config is updated accordingly (still avoiding any non-public data).
- *Combining multiple detectors:* Currently, the system combines multiple rules by assuming independence and using a 
  probabilistic OR formula: `P_combined = 1 - Π(1 - P_rule_i)` for each agent at each tick across all rules. This means 
  if any rule flags an event strongly, the combined probability will be high (up to 1.0). You can easily modify the 
  combination logic (e.g., to a simple average or weighted sum) in the code where indicated.

**Usage:**
- Prepare the trade log data (as a CSV or in-memory list of trades). Ensure it contains only the allowed fields or that 
  disallowed fields are filtered out.
- Adjust configurations or rules as needed, then run this script. It will produce an output CSV where each row corresponds 
  to a tick in the simulation/market timeline, each column is an agent, and each cell is the probability that the agent 
  was engaging in arbitrage at that tick.
- Rows (ticks) with no activity will have probability 0.0 for all agents (meaning no evidence of arbitrage at those times).
"""

import csv
from collections import defaultdict
import config
from rules import DetectionRule, RoundTripProfitRule, PredictiveTradeRule

class ArbitrageDetectionEngine:
    """
    Engine to run arbitrage detection using a set of detection rules on a trade log.
    """
    def __init__(self, rules, allowed_fields):
        """
        Initialize the detection engine with a list of rules and allowed fields.
        :param rules: list of DetectionRule instances to apply.
        :param allowed_fields: list or set of fields allowed from the trade log.
        """
        self.rules = rules
        self.allowed_fields = set(allowed_fields)
        # Verify that each rule only uses allowed fields
        for rule in self.rules:
            rule_fields = set(rule.fields)
            if not rule_fields.issubset(self.allowed_fields):
                raise ValueError(f"Rule '{rule.name}' requires fields {rule_fields} which are not all in allowed fields {self.allowed_fields}.")

    def _load_trades(self, filepath):
        """
        Load trades from a CSV file, filtering out any disallowed fields.
        Expects the CSV to have a header with field names.
        :return: list of trade records (dicts) with only allowed fields.
        """
        trades = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter out fields not in allowed_fields
                filtered = {field: self._parse_value(field, row[field]) 
                            for field in row if field in self.allowed_fields}
                trades.append(filtered)
        return trades

    def _parse_value(self, field, value):
        """
        Helper to parse numeric fields from CSV (tick, units, price) into proper types.
        """
        if field == "tick" or field == "units":
            return int(value)
        if field == "price":
            return float(value)
        # agent_id might be numeric or string; leave as is (string) if not purely numeric
        try:
            return int(value)
        except:
            return value

    def _organize_trades(self, trades):
        """
        Organize flat list of trades into structures for analysis.
        :param trades: list of trade records (dicts) with allowed fields.
        :return: (trades_by_agent, price_by_tick, all_ticks, all_agents)
        """
        trades_by_agent = defaultdict(list)
        price_by_tick = {}
        all_ticks = set()
        all_agents = set()
        last_price = None

        for trade in trades:
            tick = trade.get("tick")
            agent = trade.get("agent_id")
            price = trade.get("price")
            action = trade.get("action")
            # Only consider trades with allowed fields (already filtered in load)
            # Record trade in per-agent structure
            trades_by_agent[agent].append(trade)
            all_ticks.add(tick)
            all_agents.add(agent)
            # Update price_by_tick (we assume the last trade price in a tick as the closing price for that tick)
            if tick not in price_by_tick or True:
                price_by_tick[tick] = price
                last_price = price

        # Fill in any gaps in price_by_tick by carrying forward the last known price (assuming price stays same if no trade)
        if all_ticks:
            for t in range(min(all_ticks), max(all_ticks) + 1):
                if t not in price_by_tick:
                    if last_price is not None:
                        price_by_tick[t] = last_price
                else:
                    last_price = price_by_tick[t]
        return trades_by_agent, price_by_tick, sorted(all_ticks), sorted(all_agents)

    def detect(self, trades):
        """
        Run all detection rules on the given trades.
        :param trades: list of trade records (dicts) with allowed fields.
        :return: dict of {agent: {tick: probability}} representing combined detection probabilities.
        """
        trades_by_agent, price_by_tick, all_ticks, all_agents = self._organize_trades(trades)
        # Apply each rule and combine results
        combined_suspicions = {agent: {} for agent in all_agents}
        for rule in self.rules:
            rule_output = rule.detect(trades_by_agent, price_by_tick)
            # Combine rule_output into combined_suspicions
            for agent, suspicions in rule_output.items():
                for tick, prob in suspicions.items():
                    # Combine probabilities using probabilistic OR: P_final = 1 - (1-P_old)*(1-P_new)
                    prev_prob = combined_suspicions[agent].get(tick, 0.0)
                    # Ensure probability is within [0,1]
                    new_prob = 1 - (1 - prev_prob) * (1 - prob)
                    combined_suspicions[agent][tick] = new_prob
        return combined_suspicions

    def save_to_csv(self, combined_suspicions, all_ticks, all_agents, filepath):
        """
        Save the combined suspicion probabilities to a CSV file.
        The CSV will have a header with agent IDs, and each row corresponds to a tick.
        """
        # Ensure agents are sorted for consistent column ordering
        all_agents = sorted(all_agents)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header: tick and each agent ID
            header = ["tick"] + [str(agent) for agent in all_agents]
            writer.writerow(header)
            # Write each tick row
            for tick in all_ticks:
                row = [tick]
                for agent in all_agents:
                    prob = combined_suspicions.get(agent, {}).get(tick, 0.0)
                    # Format probability to desired decimal places
                    row.append(f"{prob:.{config.OUTPUT_DECIMALS}f}")
                writer.writerow(row)

# If run as a script, execute the detection pipeline
if __name__ == "__main__":
    # Initialize detection rules
    rules = [
        RoundTripProfitRule(time_window=config.TIME_WINDOW, profit_threshold=config.PROFIT_THRESHOLD),
        PredictiveTradeRule(window=config.PREDICT_WINDOW, threshold=config.PREDICT_THRESHOLD)
    ]
    # Create the detection engine
    engine = ArbitrageDetectionEngine(rules=rules, allowed_fields=config.ALLOWED_FIELDS)
    # Load trade log from CSV
    trades = engine._load_trades(config.INPUT_FILE)
    # Run detection
    combined_suspicions = engine.detect(trades)
    # Get all ticks and agents for output formatting
    _, _, all_ticks, all_agents = engine._organize_trades(trades)
    # Save results to CSV
    engine.save_to_csv(combined_suspicions, all_ticks, all_agents, config.OUTPUT_FILE)
    print(f"Arbitrage detection complete. Results saved to {config.OUTPUT_FILE}")
