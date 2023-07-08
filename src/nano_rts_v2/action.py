from units import Unit, UnitType

class Action:
    def __init__(self, unit_pos:int, action_type:str, target_pos:int, produced_unit_type:UnitType=None):
        self.unit_pos = unit_pos
        self.action_type = action_type
        self.target_pos = target_pos
        self.produced_unit_type = produced_unit_type
        