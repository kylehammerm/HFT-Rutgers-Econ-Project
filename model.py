import mesa
from agents import Spice, Sugar, Trader

class SugarScapeG1mt(mesa.Model):
    '''
    A model class to manage Sugarscape with Traders
    '''
    def __init__(self):
        self.spice = Spice()
        self.sugar = Sugar()
        self.trader = Trader()

if __name__ == "__main__":
    model = SugarScapeG1mt()
