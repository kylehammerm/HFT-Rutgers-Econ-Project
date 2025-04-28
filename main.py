# main.py

"""
Main script to combine heuristic rule scores and compute smoothed suspicion probabilities.
"""
import math
import pandas as pd
from config import ALPHA_SMOOTHING, WEIGHTS, INPUT_FILE, OUTPUT_FILE
from rules import (
    RoundTripProfitRule,
    SpreadCaptureRule,
    VWAPArbitrageRule,
    PriceImpactRule,
    InventoryTurnoverRule
)

def logistic(x):
    """Logistic function mapping real x to (0,1)."""
    return 1 / (1 + math.exp(-x))

def main():
    # Load trade ledger data
    df = pd.read_csv(INPUT_FILE)
    # Ensure sorted by tick for sequential processing
    df = df.sort_values('tick').reset_index(drop=True)
    
    # List of all agents in data
    agents = sorted(df['agent_id'].unique())
    max_tick = int(df['tick'].max())
    
    # Prepare a mapping of tick to trades
    tick_groups = {tick: group for tick, group in df.groupby('tick')}
    
    # Initialize rule instances
    rt_rule = RoundTripProfitRule()
    sc_rule = SpreadCaptureRule()
    vwap_rule = VWAPArbitrageRule()
    pi_rule = PriceImpactRule()
    it_rule = InventoryTurnoverRule()
    
    # Initialize previous probabilities (for smoothing) for each agent
    prev_prob = {agent: 0.0 for agent in agents}
    
    # Store output rows
    output_rows = []
    
    # Iterate through each tick in sequence
    for tick in range(1, max_tick + 1):
        # Initialize combined linear scores for this tick
        combined_scores = {agent: 0.0 for agent in agents}
        
        # Process trades at this tick, if any
        if tick in tick_groups:
            group = tick_groups[tick]
            # Iterate each trade in this tick
            for _, trade in group.iterrows():
                agent = trade['agent_id']
                action = trade['action']
                units = trade['units']
                price = trade['price']
                spread = trade['spread']
                holdings_before = trade['holdings_before']
                
                # Compute each heuristic score for this trade
                score_rt = rt_rule.score(agent, action, units, price)
                score_sc = sc_rule.score(action, price, spread)
                score_vwap = vwap_rule.score(action, price, units)
                score_pi = pi_rule.score(action, price)
                score_it = it_rule.score(units, holdings_before)
                
                # Accumulate weighted sum
                combined_scores[agent] += (
                    WEIGHTS.get('RoundTripProfitRule', 1.0) * score_rt +
                    WEIGHTS.get('SpreadCaptureRule', 1.0) * score_sc +
                    WEIGHTS.get('VWAPArbitrageRule', 1.0) * score_vwap +
                    WEIGHTS.get('PriceImpactRule', 1.0) * score_pi +
                    WEIGHTS.get('InventoryTurnoverRule', 1.0) * score_it
                )
        
        # Compute probabilities after logistic and apply smoothing
        row = {'tick': tick}
        for agent in agents:
            linear_score = combined_scores[agent]
            # Logistic transform
            prob = logistic(linear_score)
            # Exponential smoothing
            smoothed = ALPHA_SMOOTHING * prob + (1 - ALPHA_SMOOTHING) * prev_prob[agent]
            # Clip to [0,1] just in case
            smoothed = max(0.0, min(1.0, smoothed))
            # Record
            row[agent] = smoothed
            # Update previous probability
            prev_prob[agent] = smoothed
        
        output_rows.append(row)
    
    # Convert to DataFrame for output
    output_df = pd.DataFrame(output_rows)
    # Ensure columns order: tick then agents
    cols = ['tick'] + agents
    output_df = output_df[cols]
    
    # Write to CSV
    output_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Suspicion probabilities saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
