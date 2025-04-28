# main.py

import csv
from rules import AggressiveBuyRule, AggressiveSellRule, CycleAlignmentRule, DeviationRule
import config

# Instantiate rule objects
rule_list = [
    AggressiveBuyRule(),
    AggressiveSellRule(),
    CycleAlignmentRule(),
    DeviationRule()
]

def load_trades(file_path):
    """
    Load trades from a CSV file into a nested dictionary:
    trades_by_tick[tick][agent_id] = list of trade dicts.
    """
    trades_by_tick = {}
    agents = set()
    min_tick = float('inf')
    max_tick = 0
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tick = int(row['tick'])
            agent = int(row['agent_id'])
            action = row['action'].strip().lower()
            # Convert numeric fields; handle missing deviation as 0.0
            try:
                units = float(row['units'])
            except:
                units = 0.0
            try:
                price = float(row['price'])
            except:
                price = 0.0
            try:
                cash_before = float(row['cash_before'])
            except:
                cash_before = 0.0
            try:
                holdings_before = float(row['holdings_before'])
            except:
                holdings_before = 0.0
            # Deviation may be blank or NaN in early ticks
            dev_str = row.get('deviation', '')
            try:
                deviation = float(dev_str) if dev_str != '' else 0.0
            except:
                deviation = 0.0
            # Build trade record
            trade = {
                'tick': tick,
                'agent_id': agent,
                'action': action,
                'units': units,
                'price': price,
                'cash_before': cash_before,
                'holdings_before': holdings_before,
                'deviation': deviation
            }
            # Insert into nested dict
            trades_by_tick.setdefault(tick, {}).setdefault(agent, []).append(trade)
            agents.add(agent)
            if tick < min_tick:
                min_tick = tick
            if tick > max_tick:
                max_tick = tick
    return trades_by_tick, sorted(agents), min_tick, max_tick

def compute_suspicion(trades_by_tick, agents, min_tick, max_tick):
    """
    Compute suspicion scores for each tick and agent.
    Returns a list of rows, each row: [tick, prob_agent0, prob_agent1, ...].
    """
    rows = []
    for tick in range(min_tick, max_tick + 1):
        # Prepare row with default 0.0 for all agents
        row_probs = {agent: 0.0 for agent in agents}
        if tick in trades_by_tick:
            for agent, trades in trades_by_tick[tick].items():
                # Compute weighted score across rules
                score_sum = 0.0
                for rule in rule_list:
                    # Average rule score over multiple trades (if any) at this tick
                    if len(trades) > 1:
                        rule_score = sum(rule.score(trade) for trade in trades) / len(trades)
                    else:
                        rule_score = rule.score(trades[0])
                    weight = config.WEIGHTS.get(rule.__class__.__name__, 0.0)
                    score_sum += weight * rule_score
                # Cap final score at 1.0
                row_probs[agent] = min(1.0, score_sum)
        # Format row: tick followed by probabilities in agent order
        row = [tick] + [row_probs[agent] for agent in agents]
        rows.append(row)
    return rows

def write_output(rows, agents, output_file):
    """
    Write the suspicion probabilities to a CSV file.
    """
    header = ['tick'] + [str(agent) for agent in agents]
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

def main():
    # Load trade data
    trades_by_tick, agents, min_tick, max_tick = load_trades(config.TRADE_LEDGER_FILE)
    # Compute suspicion probabilities
    rows = compute_suspicion(trades_by_tick, agents, min_tick, max_tick)
    # Write to CSV output
    write_output(rows, agents, config.OUTPUT_FILE)
    print(f"Suspicion probabilities written to {config.OUTPUT_FILE}")

if __name__ == "__main__":
    main()
