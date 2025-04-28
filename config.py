"""
Configuration for the arbitrage detection system, including which trade log fields 
are considered real-world observable and other default parameters.
"""

# Fields from the trade log that are considered "real-world observable" and thus 
# allowed for use in detection models.
# For example, 'strategy' or 'cumulative_pnl' are excluded because they are not 
# observable externally.
ALLOWED_FIELDS = ["tick", "agent_id", "action", "units", "price"]

# Default parameters for detection rules (can be adjusted as needed):
# - TIME_WINDOW: maximum interval (in ticks) for a round-trip trade to be considered fast.
# - PROFIT_THRESHOLD: minimum profit (as a fraction of buy price) to flag a round-trip trade.
# - PREDICT_WINDOW: look-ahead window (in ticks) to check for price movement after a trade.
# - PREDICT_THRESHOLD: minimum price change fraction to flag a trade as predictive.
TIME_WINDOW = 20             # e.g., 20 ticks maximum holding for arbitrage suspicion
PROFIT_THRESHOLD = 0.0       # e.g., require positive profit (>0) for round-trip arbitrage
PREDICT_WINDOW = 5           # e.g., examine 5 ticks after each trade for significant price change
PREDICT_THRESHOLD = 0.01     # e.g., 1% price move threshold for predictive trade detection

# Input and output file paths (for running the detection on a CSV log and saving output).
INPUT_FILE = "data/trade_ledger_detailed.csv"                        # Path to input trade log CSV
OUTPUT_FILE = "data/arbitrage_probabilities_output.csv"  # Path to save the output probability matrix

# Output formatting:
OUTPUT_DECIMALS = 3  # Number of decimal places for probability in output CSV
