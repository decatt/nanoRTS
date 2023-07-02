from units import Unit, UnitType, load_unit_types
from player import Player
from pos import Pos, next_int_pos, is_in_range

import xml.etree.ElementTree as ET
import numpy as np

class GameState:
    def __init__(self,path) -> None:
        self.unit_types = load_unit_types() # unit_type_name -> unit_type
        self.units = dict() # unit_id -> unit
        self.units_pos = dict() # unit_int_pos -> unit
        self.players = dict() # player_id -> player
        self.buliding_pos = []
        self.width = 0
        self.height = 0
        self.produce_unit_id = 0
        self.load_map(path)
        self.game_time = 0
        self.get_units_pos()
        self.grid_state = np.zeros((self.height, self.width, 27), dtype=np.int32)

    def load_map(self, path='maps//bases8x8.xml'):
        tree = ET.parse(path)
        root = tree.getroot()
        self.width = int(root.get('width'))
        self.height = int(root.get('height'))
        players = root.find('players')
        for player in players.findall('rts.Player'):
            player_id = int(player.get('ID'))
            resources = int(player.get('resources'))
            self.players[player_id] = Player(player_id, resources)
        us = root.find('units')
        for u in us.findall('rts.units.Unit'):
            unit_type = u.get('type')
            player_id = int(u.get('player'))
            x = int(u.get('x'))
            y = int(u.get('y'))
            carried_resource = int(u.get('resources'))
            unit_type = self.unit_types[unit_type]
            self.units[self.produce_unit_id] = Unit(self.produce_unit_id,player_id, Pos(x, y,self.width).int_pos, unit_type, carried_resource)
            self.produce_unit_id += 1

    def get_units_pos(self):
        self.units_pos = dict()
        for unit in self.units.values():
            self.units_pos[unit.pos] = unit

    """
    #0: hp 0
    #1: hp 1
    #2: hp 2
    #3: hp 3
    #4: hp > 3
    #5 resource 0
    #6 resource 1
    #7 resource 2
    #8 resource 3
    #9 resource > 3
    #10: player -1
    #11: player 0
    #12: player 1
    #13: no_unit
    #14: resource
    #15: base
    #16: barracks
    #17: worker
    #18: light
    #19: heavy
    #20: ranged
    #21: no_action
    #22: move
    #23: attack
    #24: harvest
    #25: return
    #26: produce"""
    def get_grid_state(self):
        for unit in self.units.values():
            x=unit.pos % self.width
            y=unit.pos // self.width
            if unit.current_hp == 0:
                self.grid_state[y][x][0] = 1
            elif unit.current_hp == 1:
                self.grid_state[y][x][1] = 1
            elif unit.current_hp == 2:
                self.grid_state[y][x][2] = 1
            elif unit.current_hp == 3:
                self.grid_state[y][x][3] = 1
            else:
                self.grid_state[y][x][4] = 1
            if unit.carried_resource == 0:
                self.grid_state[y][x][5] = 1
            elif unit.carried_resource == 1:
                self.grid_state[y][x][6] = 1
            elif unit.carried_resource == 2:
                self.grid_state[y][x][7] = 1
            elif unit.carried_resource == 3:
                self.grid_state[y][x][8] = 1
            else:
                self.grid_state[y][x][9] = 1
            if unit.player_id == -1:
                self.grid_state[y][x][10] = 1
            elif unit.player_id == 0:
                self.grid_state[y][x][11] = 1
            else:
                self.grid_state[y][x][12] = 1
            if unit.unit_type.isResource:
                self.grid_state[y][x][14] = 1
            elif unit.unit_type.isStockpile:
                self.grid_state[y][x][15] = 1
            elif unit.unit_type.name == 'Barracks':
                self.grid_state[y][x][16] = 1
            elif unit.unit_type.name == 'Worker':
                self.grid_state[y][x][17] = 1
            elif unit.unit_type.name == 'Light':
                self.grid_state[y][x][18] = 1
            elif unit.unit_type.name == 'Heavy':
                self.grid_state[y][x][19] = 1
            elif unit.unit_type.name == 'Ranged':
                self.grid_state[y][x][20] = 1
            if unit.current_action is None:
                self.grid_state[y][x][21] = 1
            elif unit.current_action == 'move':
                self.grid_state[y][x][22] = 1
            elif unit.current_action == 'attack':
                self.grid_state[y][x][23] = 1
            elif unit.current_action == 'harvest':
                self.grid_state[y][x][24] = 1
            elif unit.current_action == 'return':
                self.grid_state[y][x][25] = 1
            elif unit.current_action == 'produce':
                self.grid_state[y][x][26] = 1

    def begin_move_unit(self, unit_id:int, target_pos:int):
        # if unit cannot move, do nothing
        unit:Unit = self.units[unit_id]
        if not unit.unit_type.canMove:
            return
        # if unit is not in range, do nothing
        if not is_in_range(unit.pos, target_pos, self.width,1):
            return
        unit.current_action = 'move'
        unit.current_action_target = target_pos
        unit.execute_current_action_time = unit.unit_type.moveTime
        self.units[unit_id] = unit

    def begin_attack_unit(self, unit_id:int, target_pos:int):
        unit:Unit = self.units[unit_id]
        # if unit cannot attack, do nothing
        if not unit.unit_type.canAttack:
            return
        # if unit is not in range, do nothing
        if not is_in_range(unit.pos, target_pos, self.width,unit.unit_type.attackRange):
            return
        unit.current_action = 'attack'
        unit.current_action_target = target_pos
        unit.execute_current_action_time = unit.unit_type.attackTime
        self.units[unit.unit_id] = unit

    def begin_harvest_unit(self, unit_id:int, target_pos:int):
        unit:Unit = self.units[unit_id]
        # if unit cannot harvest, do nothing
        if not unit.unit_type.canHarvest:
            return
        # if unit is not in range, do nothing
        if not is_in_range(unit.pos, target_pos, self.width,1):
            return
        if self.units_pos[target_pos].unit_type.name != 'Resource':
            return
        if unit.carried_resource > 0:
            return
        unit.current_action = 'harvest'
        unit.current_action_target = target_pos
        unit.execute_current_action_time = unit.unit_type.harvestTime
        self.units[unit_id] = unit

    def begin_return_unit(self, unit_id:int, target_pos:int):
        unit:Unit = self.units[unit_id]
        # if unit cannot return, do nothing
        if unit.carried_resource == 0:
            return
        # if unit is not in range, do nothing
        if not is_in_range(unit.pos, target_pos, self.width,1):
            return
        if not self.units_pos[target_pos].unit_type.isStockpile:
            return
        if self.units_pos[target_pos].player_id != unit.player_id:
            return
        unit.current_action = 'return'
        unit.current_action_target = target_pos
        unit.execute_current_action_time = unit.unit_type.returnTime
        self.units[unit_id] = unit

    def begin_produce_unit(self, unit_id:int, target_pos:int, produce_type_name:str):
        unit:Unit = self.units[unit_id]
        produce_type:UnitType = self.unit_types[produce_type_name]
        # if unit cannot produce, do nothing
        if len(unit.unit_type.produces)==0:
            return
        # if unit is not in range, do nothing
        if not is_in_range(unit.pos, target_pos, self.width,1):
            return
        if self.players[unit.player_id].resource < produce_type.cost:
            return
        self.players[unit.player_id].resource -= produce_type.cost
        unit.current_action = 'produce'
        unit.current_action_target = target_pos
        unit.execute_current_action_time = produce_type.produceTime
        unit.building_unit_type = self.unit_types[produce_type_name]
        self.buliding_pos.append(target_pos)
        self.units[unit_id] = unit

    def begin_noop_action(self, unit:Unit):
        unit.current_action = 'NOOP'
        unit.current_action_target = -1
        unit.execute_current_action_time = 1
        self.units[unit.unit_id] = unit

    def stop_unit_action(self, unit:Unit):
        unit.building_unit_type = None
        unit.current_action = None
        unit.current_action_target = -1
        unit.execute_current_action_time = 0
        self.units[unit.unit_id] = unit

    def execute_action(self, unit:Unit):
        self.get_units_pos()
        if unit.current_action == 'move':
            self.execute_move_action(unit)
        elif unit.current_action == 'attack':
            self.execute_attack_action(unit)
        elif unit.current_action == 'harvest':
            self.execute_harvest_action(unit)
        elif unit.current_action == 'return':
            self.execute_return_action(unit)
        elif unit.current_action == 'produce':
            self.execute_produce_action(unit)
        elif unit.current_action == 'NOOP':
            self.execute_noop_action(unit)

    def execute_move_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return
        target_pos = unit.current_action_target
        if target_pos in list(self.units_pos.keys()):
            self.stop_unit_action(unit)
            return
        unit.pos = unit.current_action_target
        self.stop_unit_action(unit)

    def execute_attack_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return
        target_pos = unit.current_action_target
        if target_pos not in list(self.units_pos.keys()):
            self.stop_unit_action(unit)
            return
        target_unit = self.units_pos[target_pos]
        if target_unit.player_id == unit.player_id:
            self.stop_unit_action(unit)
            return
        target_unit.current_hp -= np.random.randint(unit.unit_type.minDamage, unit.unit_type.maxDamage+1)
        if target_unit.current_hp <= 0:
            self.units.pop(target_unit.unit_id)
            self.units_pos.pop(target_unit.pos)
        self.stop_unit_action(unit)

    def execute_harvest_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return
        target_pos = unit.current_action_target
        if target_pos not in list(self.units_pos.keys()):
            self.stop_unit_action(unit)
            return
        target_unit:Unit = self.units_pos[target_pos]
        if target_unit.unit_type.name != 'Resource':
            self.stop_unit_action(unit)
            return
        if unit.carried_resource > 0:
            self.stop_unit_action(unit)
            return
        unit.carried_resource = unit.unit_type.harvestAmount
        target_unit.carried_resource -= unit.unit_type.harvestAmount
        if target_unit.carried_resource <= 0:
            self.units.pop(target_unit.unit_id)
            self.units_pos.pop(target_unit.pos)
        unit.current_action = None
        unit.current_action_target = -1
        unit.execute_current_action_time = 0
        self.units[unit.unit_id] = unit

    def execute_return_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return
        target_pos = unit.current_action_target
        if self.units_pos[target_pos] is None:
            self.stop_unit_action(unit)
            return
        target_unit:Unit = self.units_pos[target_pos]
        if not target_unit.unit_type.isStockpile:
            self.stop_unit_action(unit)
            return
        if target_unit.player_id != unit.player_id:
            self.stop_unit_action(unit)
            return
        if unit.carried_resource == 0:
            self.stop_unit_action(unit.unit_id)
            return
        self.players[unit.player_id].resource += unit.carried_resource
        unit.carried_resource = 0
        self.stop_unit_action(unit)

    def execute_produce_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return
        target_pos = unit.current_action_target
        if target_pos in list(self.units_pos.keys()):
            self.buliding_pos.remove(target_pos)
            self.stop_unit_action(unit)
            return
        if unit.building_unit_type is None:
            self.buliding_pos.remove(target_pos)
            self.stop_unit_action(unit)
            return
        self.units[self.produce_unit_id] = Unit(self.produce_unit_id,unit.player_id, target_pos, unit.building_unit_type)
        self.produce_unit_id += 1
        self.buliding_pos.remove(target_pos)
        self.stop_unit_action(unit)

    def execute_noop_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return
        self.stop_unit_action(unit)

    def update(self):
        self.game_time += 1
        action_units = [unit for unit in self.units.values() if unit.current_action is not None]
        for unit in action_units:
            self.execute_action(unit)
        self.get_units_pos()
        
    def get_player_available_units(self, player_id:int):
        available_units = []
        for unit_id in list(self.units.keys()):
            unit = self.units[unit_id]
            if unit.player_id == player_id and unit.current_action is None:
                available_units.append(unit_id)
        return available_units
    
    def get_available_actions(self, unit_id:int):
        self.get_units_pos()
        unit:Unit = self.units[unit_id]
        if unit.current_action is not None:
            return []
        available_actions = [(unit.unit_id, 'NOOP', None, None)]
        if unit.unit_type.canMove:
            available_actions.extend(self.get_available_move_actions(unit))
        if unit.unit_type.canAttack:
            available_actions.extend(self.get_available_attack_actions(unit))
        if unit.unit_type.canHarvest:
            available_actions.extend(self.get_available_harvest_actions(unit))
        if unit.unit_type.canHarvest:
            available_actions.extend(self.get_available_return_actions(unit))
        if len(unit.unit_type.produces) > 0:
            available_actions.extend(self.get_available_produce_actions(unit))
        return available_actions
    
    def get_available_move_actions(self, unit:Unit):
        available_actions = []
        for dir in [Pos(0,1), Pos(1,0), Pos(0,-1), Pos(-1,0)]:
            next_pos = next_int_pos(unit.pos, dir, self.width)
            if next_pos < 0 or next_pos >= self.width * self.height:
                continue
            if next_pos in self.buliding_pos:
                continue
            if next_pos not in list(self.units_pos.keys()):
                available_actions.append((unit.unit_id, 'move', next_pos, None))
        return available_actions
    
    def get_available_attack_actions(self, unit:Unit):
        available_actions = []
        for i in range(-unit.unit_type.attackRange, unit.unit_type.attackRange+1):
            for j in range(-unit.unit_type.attackRange, unit.unit_type.attackRange+1):
                if abs(i) + abs(j) > unit.unit_type.attackRange:
                    continue
                d = Pos(i,j)
                next_pos = next_int_pos(unit.pos, d, self.width)
                if next_pos not in list(self.units_pos.keys()):
                    continue
                target_unit = self.units_pos[next_pos]
                if target_unit.player_id == unit.player_id or target_unit.player_id == -1:
                    continue
                available_actions.append((unit.unit_id, 'attack', next_pos, None))
        return available_actions
    
    def get_available_harvest_actions(self, unit:Unit):
        if unit.carried_resource > 0:
            return []
        available_actions = []
        for dir in [Pos(0,1), Pos(1,0), Pos(0,-1), Pos(-1,0)]:
            next_pos = next_int_pos(unit.pos, dir, self.width)
            if next_pos in list(self.units_pos.keys()):
                target_unit = self.units_pos[next_pos]
                if target_unit.unit_type.name == 'Resource' and target_unit.carried_resource > 0:
                    available_actions.append((unit.unit_id, 'harvest', next_pos, None))
        return available_actions
    
    def get_available_return_actions(self, unit:Unit):
        if unit.carried_resource == 0:
            return []
        available_actions = []
        for dir in [Pos(0,1), Pos(1,0), Pos(0,-1), Pos(-1,0)]:
            next_pos = next_int_pos(unit.pos, dir, self.width)
            if next_pos in list(self.units_pos.keys()):
                target_unit = self.units_pos[next_pos]
                if target_unit.unit_type.isStockpile and target_unit.player_id == unit.player_id:
                    available_actions.append((unit.unit_id, 'return', next_pos, None))
        return available_actions
    
    def get_available_produce_actions(self, unit:Unit):
        available_actions = []
        for dir in [Pos(0,1), Pos(1,0), Pos(0,-1), Pos(-1,0)]:
            next_pos = next_int_pos(unit.pos, dir, self.width)
            if next_pos < 0 or next_pos >= self.width * self.height:
                continue
            if next_pos in self.buliding_pos:
                continue
            if next_pos not in list(self.units_pos.keys()):
                for produce_type in unit.unit_type.produces:
                    if self.unit_types[produce_type].cost > self.players[unit.player_id].resource:
                        continue
                    available_actions.append((unit.unit_id, 'produce', next_pos, produce_type))
        return available_actions
    
    def game_result(self, max_step = None):
        if max_step is not None:
            if self.game_time >= max_step:
                return 'draw'
        unit_player0 = []
        unit_player1 = []
        for unit in self.units.values():
            if unit.player_id == 0:
                unit_player0.append(unit)
            if unit.player_id == 1:
                unit_player1.append(unit)
        if len(unit_player0) == 0:
            return 'player1'
        if len(unit_player1) == 0:
            return 'player0'
        return None
        

            
        



