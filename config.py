# Configuration parameters for ArbitrageStrategy detection rules

# Trading cycle parameters (tuned to known cycle length and offsets)
CYCLE_LENGTH = 10
# Offsets within the cycle considered likely points of high activity (e.g., start/end of cycles)
CYCLE_OFFSETS = [1, 9]

# Weights for combining rule scores (should sum to 1.0 ideally)
WEIGHTS = {
    'AggressiveBuyRule': 0.25,
    'AggressiveSellRule': 0.25,
    'CycleAlignmentRule': 0.25,
    'DeviationRule': 0.25
}

# Input and output file paths
TRADE_LEDGER_FILE = 'data/trade_ledger_detailed.csv'
OUTPUT_FILE = 'data/arbitrage_probabilities.csv'
