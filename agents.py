import mesa

class Sugar(mesa.Agent):
    '''
    Sugar :
        -contains an amount of sugar
        -grows one amount of sugar at each turn
    '''

    def __init__(self):
        print("I am sugar")


class Spice(mesa.Agent):
    '''
    Spice:
    - contains an amount of spice
    - grows 1 amount of spice at each turn
    
    '''

    def __init__(self):
        print("I am spice")


class Trader(mesa.Agent):
    '''
    Trader
    -has a metabolism for sugar and spice
    -harvest and trade sugar and spice
    '''

    def __init__(self):
        print("I am trader")