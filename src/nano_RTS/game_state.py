from units import Unit, UnitType, load_unit_types
from player import Player
from pos import Pos, next_int_pos, is_in_range, distance_int_pos, int_pos_to_pos
from collections import deque

import xml.etree.ElementTree as ET
import numpy as np

class GameState:
    def __init__(self,path,reward_weight=[10,0,0,0,0]) -> None:
        self.unit_types = load_unit_types() # unit_type_name -> unit_type
        self.units = dict() # unit_id -> unit
        self.units_pos = dict() # unit_int_pos -> unit
        self.players = dict() # player_id -> player
        self.buliding_pos = []
        self.width = 0
        self.height = 0
        self.produce_unit_id = 0 # id for next new unit
        self.terrain = None
        self.load_map(path)
        self.game_time = 0
        self.get_units_pos()
        self.reward_weight = reward_weight

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
            self.units[self.produce_unit_id] = Unit(self.produce_unit_id,player_id, Pos(x, y,self.width).int_pos, self.width, unit_type, carried_resource)
            self.produce_unit_id += 1
        terrain = root.find('terrain').text
        self.terrain = np.zeros((self.height, self.width), dtype=np.int32)
        for i in range(self.height):
            for j in range(self.width):
                t = int(terrain[i*self.width+j])
                if t == 1:
                    self.terrain[i,j] = 1
                    unit_type = self.unit_types['terrain']
                    self.units[self.produce_unit_id] = Unit(self.produce_unit_id,-1, Pos(j, i,self.width).int_pos, self.width, unit_type)
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
    def unit_to_vector(self, unit):
        vector = np.zeros(27)
        if unit.current_hp == 0:
            vector[0] = 1
        elif unit.current_hp == 1:
            vector[1] = 1
        elif unit.current_hp == 2:
            vector[2] = 1
        elif unit.current_hp == 3:
            vector[3] = 1
        else:
            vector[4] = 1
        if unit.carried_resource == 0:
            vector[5] = 1
        elif unit.carried_resource == 1:
            vector[6] = 1
        elif unit.carried_resource == 2:
            vector[7] = 1
        elif unit.carried_resource == 3:
            vector[8] = 1
        else:
            vector[9] = 1
        if unit.player_id == -1:
            vector[10] = 1
        elif unit.player_id == 0:
            vector[11] = 1
        else:
            vector[12] = 1
        if unit.unit_type.isResource:
            vector[14] = 1
        elif unit.unit_type.isStockpile:
            vector[15] = 1
        elif unit.unit_type.name == 'Barracks':
            vector[16] = 1
        elif unit.unit_type.name == 'Worker':
            vector[17] = 1
        elif unit.unit_type.name == 'Light':
            vector[18] = 1
        elif unit.unit_type.name == 'Heavy':
            vector[19] = 1
        elif unit.unit_type.name == 'Ranged':
            vector[20] = 1
        if unit.current_action is None:
            vector[21] = 1
        elif unit.current_action == 'move':
            vector[22] = 1
        elif unit.current_action == 'attack':
            vector[23] = 1
        elif unit.current_action == 'harvest':
            vector[24] = 1
        elif unit.current_action == 'return':
            vector[25] = 1
        elif unit.current_action == 'produce':
            vector[26] = 1
        return vector

    def get_grid_state(self):
        grid_state = np.zeros((self.height, self.width, 27), dtype=np.int32)
        for unit in self.units.values():
            x=unit.pos % self.width
            y=unit.pos // self.width
            grid_state[y,x,:] = self.unit_to_vector(unit)
        return grid_state
    
    def get_vector_state(self, player_id, num_closest_units=16):
        available_units = self.get_player_available_units(player_id)
        if len(available_units) == 0:
            return None
        vector_state = dict()
        for unit_id in available_units:
            unit_pos = self.units[unit_id].pos
            vector_state[unit_pos] = []
        for unit in list(self.units.values()):
            unit_feature = np.zeros(29)
            unit_feature[:27] = self.unit_to_vector(unit)
            unit_feature[27] = unit.pos % self.width
            unit_feature[28] = unit.pos // self.width

            for unit_pos in list(vector_state.keys()):
                d = distance_int_pos(unit_pos, unit.pos, self.width)
                vector_state[unit_pos].append((d,unit_feature))

        for unit_pos in list(vector_state.keys()):
            vector_state[unit_pos].sort(key=lambda x:x[0])
            if len(vector_state[unit_pos]) > num_closest_units:
                vector_state[unit_pos] = vector_state[unit_pos][:num_closest_units]
            if len(vector_state[unit_pos]) < num_closest_units:
                for _ in range(num_closest_units - len(vector_state[unit_pos])):
                    vector_state[unit_pos].append((-1,np.zeros(29)))
        return vector_state
    
    def get_grid_and_vector_state(self, player_id, num_closest_units=16):
        grid_state = self.get_grid_state()
        vector_state = dict()
        available_units = self.get_player_available_units(player_id)
        if len(available_units) == 0:
            return None
        for unit_id in available_units:
            unit_pos = self.units[unit_id].pos
            vector_state[unit_pos] = []
        for unit in list(self.units.values()):
            unit_feature = np.zeros(29)
            unit_x = unit.pos % self.width
            unit_y = unit.pos // self.width
            unit_feature[:27] = grid_state[unit_y,unit_x,:]
            unit_feature[27] = unit_x
            unit_feature[28] = unit_y

            for unit_pos in list(vector_state.keys()):
                d = distance_int_pos(unit_pos, unit.pos, self.width)
                vector_state[unit_pos].append((d,unit_feature))

        for unit_pos in list(vector_state.keys()):
            vector_state[unit_pos].sort(key=lambda x:x[0])
            if len(vector_state[unit_pos]) > num_closest_units:
                vector_state[unit_pos] = vector_state[unit_pos][:num_closest_units]
            if len(vector_state[unit_pos]) < num_closest_units:
                for _ in range(num_closest_units - len(vector_state[unit_pos])):
                    vector_state[unit_pos].append((-1,np.zeros(29)))
        return vector_state, grid_state

    def get_obstacles(self):
        obstacles = set()
        for unit in list(self.units.values()):
            obstacle = int_pos_to_pos(unit.pos, self.width)
            obstacles.add(obstacle)
        for building_pos in self.buliding_pos:
            obstacle = int_pos_to_pos(building_pos, self.width)
            obstacles.add(obstacle)
        return obstacles

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
            return self.execute_move_action(unit)
        elif unit.current_action == 'attack':
            return self.execute_attack_action(unit)
        elif unit.current_action == 'harvest':
            return self.execute_harvest_action(unit)
        elif unit.current_action == 'return':
            return self.execute_return_action(unit)
        elif unit.current_action == 'produce':
            return self.execute_produce_action(unit)
        elif unit.current_action == 'NOOP':
            return self.execute_noop_action(unit)

    def execute_move_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return 0
        target_pos = unit.current_action_target
        if target_pos in list(self.units_pos.keys()):
            self.stop_unit_action(unit)
            return 0
        if target_pos in self.buliding_pos:
            self.stop_unit_action(unit)
            return 0
        unit.pos = unit.current_action_target
        self.stop_unit_action(unit)
        return 0

    def execute_attack_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return 0
        target_pos = unit.current_action_target
        if target_pos not in list(self.units_pos.keys()):
            self.stop_unit_action(unit)
            return 0
        target_unit = self.units_pos[target_pos]
        if target_unit.player_id == unit.player_id:
            self.stop_unit_action(unit)
            return 0
        target_unit.current_hp -= np.random.randint(unit.unit_type.minDamage, unit.unit_type.maxDamage+1)
        if target_unit.current_hp < 1:
            self.units.pop(target_unit.unit_id)
            self.units_pos.pop(target_unit.pos)
        self.stop_unit_action(unit)
        if unit.player_id == 0:
            return self.reward_weight[4]
        else:
            return 0

    def execute_harvest_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return 0
        target_pos = unit.current_action_target
        if target_pos not in list(self.units_pos.keys()):
            self.stop_unit_action(unit)
            return 0
        target_unit:Unit = self.units_pos[target_pos]
        if target_unit.unit_type.name != 'Resource':
            self.stop_unit_action(unit)
            return 0
        if unit.carried_resource > 0:
            self.stop_unit_action(unit)
            return 0
        unit.carried_resource = unit.unit_type.harvestAmount
        target_unit.carried_resource -= unit.unit_type.harvestAmount
        if target_unit.carried_resource <= 0:
            self.units.pop(target_unit.unit_id)
            self.units_pos.pop(target_unit.pos)
        unit.current_action = None
        unit.current_action_target = -1
        unit.execute_current_action_time = 0
        self.units[unit.unit_id] = unit
        if unit.player_id == 0:
            return self.reward_weight[1]
        else:
            return 0

    def execute_return_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return 0
        target_pos = unit.current_action_target
        if target_pos not in list(self.units_pos.keys()):
            self.stop_unit_action(unit)
            return 0
        target_unit:Unit = self.units_pos[target_pos]
        if not target_unit.unit_type.isStockpile:
            self.stop_unit_action(unit)
            return 0
        if target_unit.player_id != unit.player_id:
            self.stop_unit_action(unit)
            return 0
        if unit.carried_resource == 0:
            self.stop_unit_action(unit.unit_id)
            return 0
        self.players[unit.player_id].resource += unit.carried_resource
        unit.carried_resource = 0
        self.stop_unit_action(unit)
        if unit.player_id == 0:
            return self.reward_weight[2]
        else:
            return 0

    def execute_produce_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return 0
        target_pos = unit.current_action_target
        if target_pos in list(self.units_pos.keys()):
            self.buliding_pos.remove(target_pos)
            self.stop_unit_action(unit)
            return 0
        if unit.building_unit_type is None:
            self.buliding_pos.remove(target_pos)
            self.stop_unit_action(unit)
            return 0
        self.units[self.produce_unit_id] = Unit(self.produce_unit_id,unit.player_id, target_pos, self.width, unit.building_unit_type)
        self.produce_unit_id += 1
        self.buliding_pos.remove(target_pos)
        self.stop_unit_action(unit)
        if unit.player_id == 0:
            return self.reward_weight[3]
        else:
            return 0

    def execute_noop_action(self, unit:Unit):
        if unit.execute_current_action_time > 0:
            unit.execute_current_action_time -= 1
            return 0
        self.stop_unit_action(unit)
        return 0

    def update(self):
        self.game_time += 1
        action_units = [unit for unit in self.units.values() if unit.current_action is not None]
        r = 0
        for unit in action_units:
            r += self.execute_action(unit)
        self.get_units_pos()
        return r
        
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
    
    #[0:6] NOOP, move, harvest, return, produce, attack
    #[6:10] move: up, right, down, left
    #[10:14] harvest: up, right, down, left
    #[14:18] return: up, right, down, left
    #[18:22] produce: up, right, down, left
    #[22:29] produce_type: resource, base, barracks, worker, light, heavy, ranged
    #[29:78] attack_pos: 1~7*7
    def get_action_masks(self, unit_pos):
        action_masks = np.zeros(78)
        action_masks[0] = 1
        if unit_pos not in list(self.units_pos.keys()):
            return action_masks
        unit_id = self.units_pos[unit_pos].unit_id
        unit:Unit = self.units[unit_id]
        up_pos = next_int_pos(self.units[unit_id].pos, Pos(0,1), self.width)
        right_pos = next_int_pos(self.units[unit_id].pos, Pos(1,0), self.width)
        down_pos = next_int_pos(self.units[unit_id].pos, Pos(0,-1), self.width)
        left_pos = next_int_pos(self.units[unit_id].pos, Pos(-1,0), self.width)
        if up_pos >= 0 and up_pos < self.width * self.height:
            if up_pos in list(self.units_pos.keys()):
                up_unit_id = self.units_pos[up_pos].unit_id
                if up_unit_id in list(self.units.keys()):
                    up_unit = self.units[up_unit_id]
                    if unit.unit_type.canHarvest and up_unit.unit_type.name == 'Resource' and up_unit.carried_resource > 0 and unit.carried_resource == 0:
                        action_masks[2] = 1
                        action_masks[10] = 1
                    if unit.unit_type.canReturn and up_unit.unit_type.isStockpile and up_unit.player_id == unit.player_id and unit.carried_resource > 0:
                        action_masks[3] = 1
                        action_masks[14] = 1
            elif up_pos not in self.buliding_pos:
                if len(unit.unit_type.produces) > 0:
                    action_masks[4] = 1
                    action_masks[18] = 1
                    for produce_type in unit.unit_type.produces:
                        if produce_type == "Resource":
                            action_masks[22] = 1
                        elif produce_type == "Base":
                            action_masks[23] = 1
                        elif produce_type == "Barracks":
                            action_masks[24] = 1
                        elif produce_type == "Worker":
                            action_masks[25] = 1
                        elif produce_type == "Light":
                            action_masks[26] = 1
                        elif produce_type == "Heavy":
                            action_masks[27] = 1
                        elif produce_type == "Ranged":
                            action_masks[28] = 1
                    if unit.unit_type.canMove:
                        action_masks[1] = 1
                        action_masks[6] = 1
        if right_pos >= 0 and right_pos < self.width * self.height:
            if right_pos in list(self.units_pos.keys()):
                right_unit_id = self.units_pos[right_pos].unit_id
                if right_unit_id in list(self.units.keys()):
                    right_unit = self.units[right_unit_id]
                    if unit.unit_type.canHarvest and right_unit.unit_type.name == 'Resource' and right_unit.carried_resource > 0 and unit.carried_resource == 0:
                        action_masks[2] = 1
                        action_masks[11] = 1
                    if unit.unit_type.canReturn and right_unit.unit_type.isStockpile and right_unit.player_id == unit.player_id and unit.carried_resource > 0:
                        action_masks[3] = 1
                        action_masks[15] = 1
            elif right_pos not in self.buliding_pos:
                if len(unit.unit_type.produces) > 0:
                    action_masks[4] = 1
                    action_masks[19] = 1
                    for produce_type in unit.unit_type.produces:
                        if produce_type == "Resource":
                            action_masks[22] = 1
                        elif produce_type == "Base":
                            action_masks[23] = 1
                        elif produce_type == "Barracks":
                            action_masks[24] = 1
                        elif produce_type == "Worker":
                            action_masks[25] = 1
                        elif produce_type == "Light":
                            action_masks[26] = 1
                        elif produce_type == "Heavy":
                            action_masks[27] = 1
                        elif produce_type == "Ranged":
                            action_masks[28] = 1
                    if unit.unit_type.canMove:
                        action_masks[1] = 1
                        action_masks[7] = 1
        if down_pos >= 0 and down_pos < self.width * self.height:
            if down_pos in list(self.units_pos.keys()):
                down_unit_id = self.units_pos[down_pos].unit_id
                if down_unit_id in list(self.units.keys()):
                    down_unit = self.units[down_unit_id]
                    if unit.unit_type.canHarvest and down_unit.unit_type.name == 'Resource' and down_unit.carried_resource > 0 and unit.carried_resource == 0:
                        action_masks[2] = 1
                        action_masks[12] = 1
                    if unit.unit_type.canReturn and down_unit.unit_type.isStockpile and down_unit.player_id == unit.player_id and unit.carried_resource > 0:
                        action_masks[3] = 1
                        action_masks[16] = 1
            elif down_pos not in self.buliding_pos:
                if len(unit.unit_type.produces) > 0:
                    action_masks[4] = 1
                    action_masks[20] = 1
                    for produce_type in unit.unit_type.produces:
                        if produce_type == "Resource":
                            action_masks[22] = 1
                        elif produce_type == "Base":
                            action_masks[23] = 1
                        elif produce_type == "Barracks":
                            action_masks[24] = 1
                        elif produce_type == "Worker":
                            action_masks[25] = 1
                        elif produce_type == "Light":
                            action_masks[26] = 1
                        elif produce_type == "Heavy":
                            action_masks[27] = 1
                        elif produce_type == "Ranged":
                            action_masks[28] = 1
                    if unit.unit_type.canMove:
                        action_masks[1] = 1
                        action_masks[8] = 1
        if left_pos >= 0 and left_pos < self.width * self.height:
            if left_pos in list(self.units_pos.keys()):
                left_unit_id = self.units_pos[left_pos].unit_id
                if left_unit_id in list(self.units.keys()):
                    left_unit = self.units[left_unit_id]
                    if unit.unit_type.canHarvest and left_unit.unit_type.name == 'Resource' and left_unit.carried_resource > 0 and unit.carried_resource == 0:
                        action_masks[2] = 1
                        action_masks[13] = 1
                    if unit.unit_type.canReturn and left_unit.unit_type.isStockpile and left_unit.player_id == unit.player_id and unit.carried_resource > 0:
                        action_masks[3] = 1
                        action_masks[17] = 1
            elif left_pos not in self.buliding_pos:
                if len(unit.unit_type.produces) > 0:
                    action_masks[4] = 1
                    action_masks[21] = 1
                    for produce_type in unit.unit_type.produces:
                        if produce_type == "Resource":
                            action_masks[22] = 1
                        elif produce_type == "Base":
                            action_masks[23] = 1
                        elif produce_type == "Barracks":
                            action_masks[24] = 1
                        elif produce_type == "Worker":
                            action_masks[25] = 1
                        elif produce_type == "Light":
                            action_masks[26] = 1
                        elif produce_type == "Heavy":
                            action_masks[27] = 1
                        elif produce_type == "Ranged":
                            action_masks[28] = 1
                    if unit.unit_type.canMove:
                        action_masks[1] = 1
                        action_masks[9] = 1
        if unit.unit_type.canAttack:
            for i in range(-unit.unit_type.attackRange, unit.unit_type.attackRange+1):
                for j in range(-unit.unit_type.attackRange, unit.unit_type.attackRange+1):
                    if abs(i) + abs(j) > unit.unit_type.attackRange:
                        continue
                    d = Pos(i,j)
                    next_pos = next_int_pos(unit.pos, d, self.width)
                    if next_pos not in list(self.units_pos.keys()):
                        continue
                    target_unit_id = self.units_pos[next_pos]
                    if target_unit_id in list(self.units.keys()):
                        target_unit = self.units[target_unit_id]
                        if target_unit.player_id == unit.player_id or target_unit.player_id == -1:
                            continue
                        action_masks[5] = 1
                        action_masks[29+i+3+(j+3)*7] = 1
        return action_masks
