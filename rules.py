"""
Heuristic rule classes for arbitrage detection.
Each rule computes a suspicion score for each trade.
"""

class RoundTripProfitRule:
    """
    Detects suspicious profit from round-trip trades by an agent.
    Tracks inventory cost basis to compute realized profit on sells.
    """
    def __init__(self):
        # Store holdings (units) and average cost per agent
        self.holdings = {}
        self.avg_cost = {}

    def score(self, agent_id, action, units, price):
        """
        Compute score for a trade: normalized profit fraction if realizing profit on a sale.
        Returns a score >= 0 or 0 if no profit or on buys.
        """
        score = 0.0
        # Initialize if first time
        if agent_id not in self.holdings:
            self.holdings[agent_id] = 0
            self.avg_cost[agent_id] = 0.0

        # BUY: update holdings and average cost
        if action.lower() == 'buy':
            old_units = self.holdings[agent_id]
            old_cost = self.avg_cost[agent_id]
            # New weighted average cost
            total_cost = old_cost * old_units + price * units
            new_units = old_units + units
            if new_units > 0:
                self.avg_cost[agent_id] = total_cost / new_units
            else:
                self.avg_cost[agent_id] = 0.0
            self.holdings[agent_id] = new_units
            # No profit realized on buy
            score = 0.0

        # SELL: compute realized profit and update holdings
        elif action.lower() == 'sell':
            old_units = self.holdings[agent_id]
            old_cost = self.avg_cost[agent_id]
            # Compute profit only if we have holdings to sell
            if old_units > 0:
                # Realized profit per unit
                profit_per_unit = price - old_cost
                profit = profit_per_unit * units
                if profit > 0 and (price * units) != 0:
                    # Normalize by trade notional (price * units) to get fraction
                    score = profit / (price * units)
                else:
                    score = 0.0
                # Update holdings after sale
                new_units = old_units - units
                if new_units > 0:
                    # Cost basis remains the same for remaining units
                    self.holdings[agent_id] = new_units
                else:
                    # Closed position
                    self.holdings[agent_id] = 0
                    self.avg_cost[agent_id] = 0.0
            else:
                score = 0.0

        else:
            # Unknown action: no score
            score = 0.0

        return score


class SpreadCaptureRule:
    """
    Detects potential spread capture by trading at advantageous prices.
    Here we define score as the spread relative to price.
    """
    def score(self, action, price, spread):
        """
        Compute score: fraction of the spread relative to price.
        If price is mid, larger spread yields higher score.
        """
        if price != 0:
            return spread / price
        else:
            return 0.0


class VWAPArbitrageRule:
    """
    Detects price deviations from VWAP (Volume Weighted Average Price).
    Tracks global VWAP and scores trades significantly away from VWAP.
    """
    def __init__(self):
        self.total_value = 0.0
        self.total_volume = 0.0

    def score(self, action, price, units):
        """
        Compute score: if buy below VWAP or sell above VWAP.
        Update VWAP state after scoring.
        """
        score = 0.0
        # Current VWAP prior to this trade
        vwap = (self.total_value / self.total_volume) if self.total_volume > 0 else price
        # First trade has no prior VWAP signal
        if self.total_volume > 0:
            if action.lower() == 'buy' and price < vwap:
                score = (vwap - price) / vwap
            elif action.lower() == 'sell' and price > vwap:
                score = (price - vwap) / vwap
        # Update VWAP state
        self.total_value += price * units
        self.total_volume += units
        return score


class PriceImpactRule:
    """
    Detects significant immediate price impact by a trade.
    Scores positive when a buy pushes the price up, or a sell pushes it down.
    """
    def __init__(self):
        self.prev_mid = None

    def score(self, action, price):
        """
        Compute score based on difference from previous mid-price.
        """
        score = 0.0
        if self.prev_mid is not None:
            if action.lower() == 'buy':
                diff = price - self.prev_mid
                if diff > 0 and self.prev_mid > 0:
                    score = diff / self.prev_mid
            elif action.lower() == 'sell':
                diff = self.prev_mid - price
                if diff > 0 and self.prev_mid > 0:
                    score = diff / self.prev_mid
        # Update previous mid-price
        self.prev_mid = price
        return score


class InventoryTurnoverRule:
    """
    Detects high inventory turnover: large trades relative to current holdings.
    """
    def score(self, units, holdings_before):
        """
        Compute score as trade size relative to holdings (plus trade).
        """
        denom = abs(units) + abs(holdings_before)
        if denom > 0:
            return abs(units) / denom
        else:
            return 0.0
