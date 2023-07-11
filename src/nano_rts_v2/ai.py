from game import Game
from action import Action
from path_finding import BFS
from pos import distance
from units import Unit
import copy

import random

class AI:
    def __init__(self, player_id:int):
        self.player_id = player_id
        self.opponent_id = 1 - player_id
    
    def get_random_action(self, game:Game):
        available_actions = game.get_player_available_actions(self.player_id)
        if len(available_actions) == 0:
            return Action(None, None, None, None)
        return random.choice(available_actions)
    
class RushAI(AI):
    def __init__(self, player_id:int, melee_unit_type:str, width:int, height:int):
        super().__init__(player_id)
        self.melee_uit_type = melee_unit_type
        self.max_harvest_worker = 1
        self.max_barracks = 1
        self.max_worker = 100
        if melee_unit_type == "Worker":
            self.num_barracks = 0
            self.max_worker = 100
            self.max_harvest_worker = 1
        else:
            self.num_barracks = 1
            self.max_worker = 5
            self.max_harvest_worker = 2
        self.allay_base = []
        self.allay_barracks = []
        self.allay_worker = []
        self.allay_melee = []
        self.enemy_units = []
        self.resources = []
        self.reached_resources = []
        self.pos_to_build_barracks = []
        self.pos_to_build_base = []
        self.obstacles = set()
        self.pf = BFS(width, height)
        self.used_resource = 0
        self.bulid_barracks_pos = []

    def perpare(self, game:Game):
        self.allay_base = []
        self.allay_barracks = []
        self.allay_worker = []
        self.allay_melee = []
        self.enemy_units = []
        self.resources = []
        self.reached_resources = []
        self.obstacles = set()
        for unit in list(game.units.values()):
            self.obstacles.add(unit.pos)
            if unit.building_unit_type is not None:
                self.obstacles.add(unit.current_action_target)
            if unit.player_id == self.player_id:
                if unit.unit_type.name == 'Base':
                    self.allay_base.append(unit.pos)
                elif unit.unit_type.name == 'Barracks':
                    self.allay_barracks.append(unit.pos)
                elif unit.unit_type.name == 'Worker':
                    self.allay_worker.append(unit.pos)
                else:
                    self.allay_melee.append(unit.pos)
            elif unit.player_id == 1 - self.player_id:
                self.enemy_units.append(unit.pos)
            elif unit.unit_type.name == 'Resource':
                self.resources.append(unit.pos)
        if len(self.allay_base)>0 and len(self.resources)>0:
            for resouce in self.resources:
                for base in self.allay_base:
                    if distance(resouce, base, game.width) <= game.width-2:
                        self.reached_resources.append(resouce)
                        break
        self.pos_to_build_barracks = []
        self.pos_to_build_base = []
        self.used_resource = 0
        self.bulid_barracks_pos = []
    
    def get_random_action(self, game:Game):
        available_actions = game.get_player_available_actions(self.player_id)
        if len(available_actions) == 0:
            return Action(None, None, None, None)
        for action in available_actions:
            if action.action_type == 'move':
                return action
        return random.choice(available_actions)
    
    def find_pos_to_bulid_barracks(self,gs:Game):
        self.pos_to_build_barracks = []
        potential_pos = []

        for pos in range(gs.width*gs.height):
            if pos in self.obstacles:
                continue
            score = 0
            for enemy in self.enemy_units:
                # if any enemy is in range of the pos, range = 3, score -= 10
                if distance(pos, enemy, gs.width) <= 3:
                    score -= 10
                    continue
            for resource in self.reached_resources:
                # if any resource is in range of the pos, range = 1, score -= 10
                if distance(pos, resource, gs.width) <= 1:
                    score -= 10
                    continue
            for base in self.allay_base:
                # if any base is in range of the pos, range = 2, score += 5
                if distance(pos, base, gs.width) <= 2:
                    score += 5
                    continue
            for worker in self.allay_worker:
                # if any worker is in range of the pos, range = 2, score += 8
                if distance(pos, worker, gs.width) <= 2:
                    score += 8
                    continue
            potential_pos.append((pos,score))
        # sort the potential_pos by score from high to low
        potential_pos.sort(key=lambda x:x[1], reverse=True)
        for i in range(min(self.num_barracks,len(potential_pos))):
            self.pos_to_build_barracks.append(potential_pos[i][0])

    def get_unit_action(self, unit_pos:int, target_pos:int, gs:Game):
        if unit_pos not in list(gs.units.keys()):
            return Action(-1, None, None, None)
        if target_pos is None:
            return Action(-1, None, None, None)
        unit:Unit = gs.units[unit_pos]
        if unit.player_id != self.player_id:
            return Action(-1, None, None, None)
        if target_pos not in list(gs.units.keys()):
            if distance(unit_pos, target_pos, gs.width) == 1:
                if "Barracks" in unit.unit_type.produces:
                    if target_pos in self.pos_to_build_barracks and gs.players[self.player_id].resource - self.used_resource >= gs.unit_types["Barracks"].cost:
                        return Action(unit_pos, 'produce', target_pos, "Barracks")
                if "Base" in unit.unit_type.produces:
                    if target_pos in self.pos_to_build_base and gs.players[self.player_id].resources - self.used_resource >= gs.unit_types["Base"].cost:
                        return Action(unit_pos, 'produce', target_pos, "Base")
                if self.melee_uit_type in unit.unit_type.produces:
                    if gs.players[self.player_id].resource - self.used_resource >= gs.unit_types[self.melee_uit_type].cost:
                        return Action(unit_pos, 'produce', target_pos, self.melee_uit_type)
                if "Worker" in unit.unit_type.produces:
                    if gs.players[self.player_id].resource - self.used_resource >= gs.unit_types["Worker"].cost:
                        return Action(unit_pos, 'produce', target_pos, "Worker")
            if unit.unit_type.canMove:
                move_pos = self.pf.get_move_pos(unit_pos, target_pos, self.obstacles)
                return Action(unit_pos, 'move', move_pos, None)
            else:
                return Action(-1, None, None, None)
        target:Unit = gs.units[target_pos]
        if target.player_id == 1-self.player_id:
            if distance(unit_pos, target_pos, gs.width) <= unit.unit_type.attackRange and unit.unit_type.canAttack:
                return Action(unit_pos, 'attack', target_pos, None)
            else:
                move_pos = self.pf.get_move_pos(unit.pos, target.pos, self.obstacles)
                return Action(unit.pos, 'move', move_pos, None)
        if distance(unit_pos, target_pos, gs.width) == 1:
            if unit.unit_type.canHarvest:
                if target.unit_type.isResource and unit.carried_resource < 1:
                    return Action(unit_pos, 'harvest', target_pos, None)
                elif target.unit_type.isStockpile and unit.carried_resource > 0 and target.player_id == self.player_id:
                    return Action(unit_pos, 'return', target_pos, None)
        else:
            move_pos = self.pf.get_move_pos(unit_pos, target_pos, self.obstacles)
            return Action(unit_pos, 'move', move_pos, None)
        
        return Action(-1, None, None, None)
    
    def worker_actions(self, game:Game):
        if len(self.allay_worker) == 0:
            return []
        actions = []
        free_workers = copy.deepcopy(self.allay_worker)
        harvest_workers = []
        if len(self.reached_resources)>0:
            while len(harvest_workers) < self.max_harvest_worker and len(free_workers) > 0:
                # find the closest worker in free_workers to the resource
                closest_worker = None
                closest_score = 100000000
                for worker_pos in free_workers:
                    for resource in self.reached_resources:
                        score = distance(worker_pos, resource, game.width)
                        if score < closest_score:
                            closest_score = score
                            closest_worker = worker_pos
                if closest_worker is not None:
                    harvest_workers.append(closest_worker)
                if closest_worker in free_workers:
                    free_workers.remove(closest_worker)
        for worker_pos in harvest_workers:
            if worker_pos not in list(game.units.keys()):
                continue
            worker:Unit = game.units[worker_pos]
            if worker.busy():
                continue
            if worker.carried_resource == 0:
                # find the closest resource to the worker
                closest_resource = None
                closest_score = 100000000
                for resource in self.reached_resources:
                    score = distance(worker_pos, resource, game.width)
                    if score < closest_score:
                        closest_score = score
                        closest_resource = resource
                if closest_resource is not None:
                    actions.append(self.get_unit_action(worker_pos,closest_resource,game))
            else:
                closest_base = None
                closest_score = 100000000
                for base in self.allay_base:
                    score = distance(worker_pos, base, game.width)
                    if score < closest_score:
                        closest_score = score
                        closest_base = base
                if closest_base is not None:
                    actions.append(self.get_unit_action(worker_pos,closest_base,game))
        if len(free_workers)>0:
            if len(self.allay_barracks) + len(self.bulid_barracks_pos) < self.num_barracks and game.players[self.player_id].resource >= game.unit_types["Barracks"].cost + self.used_resource:
                self.find_pos_to_bulid_barracks(game)
                if len(self.pos_to_build_barracks) > 0:
                    closest_bulid_worker = None
                    closest_score = 100000000
                    target_pos = self.pos_to_build_barracks[0]
                    for worker_pos in free_workers:
                        if worker_pos not in list(game.units.keys()):
                            continue
                        worker:Unit = game.units[worker_pos]
                        if worker.busy():
                            continue
                        score = distance(worker_pos, target_pos, game.width)
                        if score < closest_score:
                            closest_score = score
                            closest_bulid_worker = worker.pos
                    if closest_bulid_worker is not None:
                        action = self.get_unit_action(closest_bulid_worker, target_pos, game)
                        actions.append(action)
                        self.used_resource += game.unit_types["Barracks"].cost
                        if closest_bulid_worker in free_workers:
                            free_workers.remove(closest_bulid_worker)
                        if action.action_type == "produce":
                            self.pos_to_build_barracks.remove(target_pos)
                            self.bulid_barracks_pos.append(target_pos)
            for worker_pos in free_workers:
                if worker_pos not in list(game.units.keys()):
                    continue
                worker:Unit = game.units[worker_pos]
                if worker.busy():
                    continue
                if worker.carried_resource == 0:
                    closest_enemy = None
                    closest_score = 100000000
                    for enemy in self.enemy_units:
                        score = distance(worker_pos, enemy, game.width)
                        if score < closest_score:
                            closest_score = score
                            closest_enemy = enemy
                    if closest_enemy is not None:
                        actions.append(self.get_unit_action(worker_pos,closest_enemy,game))
                else:
                    closest_base = None
                    closest_score = 100000000
                    for base in self.allay_base:
                        score = distance(worker_pos, base, game.width)
                        if score < closest_score:
                            closest_score = score
                            closest_base = base
                    actions.append(self.get_unit_action(worker_pos,closest_base,game))
        return actions
    
    def melee_actions(self, game:Game):
        actions =[]
        for melee_pos in self.allay_melee:
            if melee_pos not in list(game.units.keys()):
                continue
            melee:Unit = game.units[melee_pos]
            if melee.busy():
                continue
            closest_enemy = None
            closest_score = 100000000
            for enemy in self.enemy_units:
                score = distance(melee_pos, enemy, game.width)
                if score < closest_score:
                    closest_score = score
                    closest_enemy = enemy
            actions.append(self.get_unit_action(melee_pos,closest_enemy,game))
        return actions
    
    def barracks_actions(self, game:Game):
        actions = []
        for barracks_pos in self.allay_barracks:
            if barracks_pos not in list(game.units.keys()):
                continue
            barracks:Unit = game.units[barracks_pos]
            if barracks.busy():
                continue
            closest_enemy = None
            closest_score = 100000000
            for enemy in self.enemy_units:
                score = distance(barracks_pos, enemy, game.width)
                if score < closest_score:
                    closest_score = score
                    closest_enemy = enemy
            if closest_enemy is not None:
                next_pos = self.pf.get_move_pos(barracks_pos, closest_enemy, self.obstacles)
                actions.append(self.get_unit_action(barracks_pos,next_pos,game))
        return actions
    
    def base_actions(self, game:Game):
        actions = []
        for base_pos in self.allay_base:
            if base_pos not in list(game.units.keys()):
                continue
            base:Unit = game.units[base_pos]
            if base.busy():
                continue
            if len(self.allay_worker) <= self.max_harvest_worker:
                closest_resource = None
                closest_score = 100000000
                for resource in self.resources:
                    score = distance(base_pos, resource, game.width)
                    if score < closest_score:
                        closest_score = score
                        closest_resource = resource
                if closest_resource is not None:
                    next_pos = self.pf.get_move_pos(base_pos, closest_resource, self.obstacles)
                    actions.append(self.get_unit_action(base_pos,next_pos,game))
            else:
                closest_enemy = None
                closest_score = 100000000
                for enemy in self.enemy_units:
                    score = distance(base_pos, enemy, game.width)
                    if score < closest_score:
                        closest_score = score
                        closest_enemy = enemy
                if closest_enemy is not None:
                    next_pos = self.pf.get_move_pos(base_pos, closest_enemy, self.obstacles)
                    actions.append(self.get_unit_action(base_pos,next_pos,game))
                else:
                    actions.append(Action(base_pos, None, None, None))
        return actions
    
    def get_action(self, game:Game):
        self.perpare(game)
        actions = []
        actions.extend(self.worker_actions(game))
        actions.extend(self.melee_actions(game))
        actions.extend(self.barracks_actions(game))
        actions.extend(self.base_actions(game))
        if len(actions) == 0:
            return self.get_random_action(game)
        return random.choice(actions)
    
    def get_action_list(self, game:Game):
        self.perpare(game)
        actions = []
        actions.extend(self.worker_actions(game))
        actions.extend(self.melee_actions(game))
        actions.extend(self.barracks_actions(game))
        actions.extend(self.base_actions(game))
        return actions
               