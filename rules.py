import config

class AggressiveBuyRule:
    """
    Rule to detect aggressive buying: uses a large fraction of available cash.
    Score is the fraction of cash spent (0 to 1).
    """
    def score(self, trade):
        if trade.get('action', '').lower() != 'buy':
            return 0.0
        cash_before = trade.get('cash_before', 0.0)
        price = trade.get('price', 0.0)
        units = trade.get('units', 0.0)
        # If no cash, treat as maximum usage
        if cash_before <= 0:
            return 1.0
        usage = (price * units) / cash_before
        # Cap at 1.0
        return min(1.0, usage)

class AggressiveSellRule:
    """
    Rule to detect aggressive selling: sells a large fraction of holdings.
    Score is the fraction of holdings sold (0 to 1).
    """
    def score(self, trade):
        if trade.get('action', '').lower() != 'sell':
            return 0.0
        holdings_before = trade.get('holdings_before', 0.0)
        units = trade.get('units', 0.0)
        # If no holdings, treat as maximum usage
        if holdings_before <= 0:
            return 1.0
        usage = units / holdings_before
        return min(1.0, usage)

class CycleAlignmentRule:
    """
    Rule to detect trading aligned with known cycle points.
    If the trade tick modulo cycle length matches specified offsets, score = 1.
    """
    def score(self, trade):
        tick = trade.get('tick', 0)
        cycle_len = config.CYCLE_LENGTH
        offsets = config.CYCLE_OFFSETS
        if cycle_len <= 0:
            return 0.0
        remainder = tick % cycle_len
        return 1.0 if remainder in offsets else 0.0

class DeviationRule:
    """
    Rule based on price deviation from moving average (peak/trough detection).
    Buys at troughs (negative deviation) and sells at peaks (positive deviation).
    """
    def score(self, trade):
        action = trade.get('action', '').lower()
        deviation = trade.get('deviation', 0.0)
        if action == 'buy':
            # Price below average (negative deviation) suggests trough: reward buys
            if deviation < 0:
                return min(1.0, -deviation)
            else:
                return 0.0
        elif action == 'sell':
            # Price above average (positive deviation) suggests peak: reward sells
            if deviation > 0:
                return min(1.0, deviation)
            else:
                return 0.0
        return 0.0
