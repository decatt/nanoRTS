from units import Unit, UnitType
from numpy import ndarray
import numpy as np

class Action:
    def __init__(self, unit_pos:int, action_type:str, target_pos:int, produced_unit_type:UnitType=None):
        self.unit_pos = unit_pos
        self.action_type = action_type
        self.target_pos = target_pos
        self.produced_unit_type = produced_unit_type

    def action_to_vector(self, map_width:int)->ndarray:
        vector = np.zeros(8)
        vector[0] = self.unit_pos
        unit_x = self.unit_pos % map_width
        unit_y = self.unit_pos // map_width
        target_x = self.target_pos % map_width
        target_y = self.target_pos // map_width
        dir = (target_x - unit_x, target_y - unit_y)
        d = 0
        if dir == (0,-1):
            d = 0
        elif dir == (1,0):
            d = 1
        elif dir == (0,1):
            d = 2
        elif dir == (-1,0):
            d = 3
        
        if self.action_type == 'move':
            vector[1] = 1
            vector[2] = d
        elif self.action_type == 'harvest':
            vector[1] = 2
            vector[3] = d
        elif self.action_type == 'return':
            vector[1] = 3
            vector[4] = d
        elif self.action_type == 'produce':
            vector[1] = 4
            vector[5] = d
            vector[6] = self.produced_unit_type.id
        elif self.action_type == 'attack':
            vector[1] = 5
            vector[7] = dir[0]+3 + 7*(dir[1]+3)
        return vector


        