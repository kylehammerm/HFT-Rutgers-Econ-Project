"""
Configuration for arbitrage detection system
"""

# Smoothing factor for exponential smoothing (alpha in [0,1])
ALPHA_SMOOTHING = 0.5

# Weights for each heuristic rule in the combined score
WEIGHTS = {
    'RoundTripProfitRule': 1.0,
    'SpreadCaptureRule': 1.0,
    'VWAPArbitrageRule': 1.0,
    'PriceImpactRule': 1.0,
    'InventoryTurnoverRule': 1.0,
}

# Input and output file paths (optional customization)
INPUT_FILE = 'data/trade_ledger_detailed.csv'
OUTPUT_FILE = 'data/suspicion_scores.csv'
