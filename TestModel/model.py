import mesa
import numpy as np
import matplotlib.pyplot as plt

from TestModel.agents import Spice, Sugar, Trader

class SugarScapeG1mt(mesa.Model):
    '''
    A model class to manage Sugarscape with Traders
    '''
    def __init__(self,width=50,height=50):

        super().__init__()

        self.width = width
        self.height = height

        self.grid = mesa.space.MultiGrid(self.width,self.height,torus=False)

        sugar_distribution = np.genfromtxt("maps/sugar-map.txt")
        spice_distribution = np.flip(sugar_distribution,1)
        
        

        agent_id = 0

        # This is a built in mesa function to loop through a whole grid
        for _, (x,y) in self.grid.coord_iter():
            max_sugar = sugar_distribution[x,y]
            if max_sugar>0:
                sugar = Sugar(agent_id,self,(x,y),max_sugar)
                self.grid.place_agent(sugar,(x,y))
                agent_id += 1
            
            max_spice = spice_distribution[x,y]
            if max_spice >0:
                spice = Spice(agent_id,self,(x,y),max_spice)
                self.grid.place_agent(spice,(x,y))
                agent_id += 1
        
        for _, (x,y) in self.grid.coord_iter():
            print(_,(x,y))



if __name__ == "__main__":
    model = SugarScapeG1mt()
