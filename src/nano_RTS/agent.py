from game_state import GameState
import numpy as np
from path_finding import BFS, PathFinding
from pos import Pos, next_int_pos, is_in_range, distance_int_pos, int_pos_to_pos, int_pos_in_range

class AI:
    def __init__(self, player_id:int):
        self.player_id = player_id
    
    def get_action(self, game_state:GameState):
        return (None,None,None,None)
    
    def get_action_list(self, game_state:GameState):
        return []
    
    def get_random_action(self, gs:GameState):
        gs.get_units_pos()
        units = gs.get_player_available_units(self.player_id)
        if len(units) == 0:
            return (None,None,None,None)
        all_available_actions = []
        for unit_id in units:
            available_actions = gs.get_available_actions(unit_id)
            if len(available_actions) == 0:
                continue
            all_available_actions.extend(available_actions)
        if len(all_available_actions) == 0:
            return (None,None,None,None)
        return all_available_actions[np.random.randint(len(all_available_actions))]
    
    def get_random_action_list(self,gs:GameState):
        gs.get_units_pos()
        units = gs.get_player_available_units(self.player_id)
        action_list = []
        if len(units) == 0:
            return []
        for unit_id in units:
            unit_available_actions = gs.get_available_actions(unit_id)
            if len(unit_available_actions) == 0:
                continue
            action_list.append(unit_available_actions[np.random.randint(len(unit_available_actions))])
        return action_list
    
    def get_all_availiable_actions(self,gs:GameState):
        gs.get_units_pos()
        units = gs.get_player_available_units(self.player_id)
        availiable_action_list = []
        if len(units) == 0:
            return []
        for unit_id in units:
            unit_available_actions = gs.get_available_actions(unit_id)
            if len(unit_available_actions) == 0:
                continue
            availiable_action_list.extend(unit_available_actions)
        return availiable_action_list
    
class WorkerRush(AI):
    def __init__(self, player_id:int, width:int, height:int):
        super().__init__(player_id)
        self.bfs = BFS(width, height)
        self.used_resource = 0
        self.max_harvest_worker = 1
        self.allay_base = []
        self.allay_worker = []
        self.enemy_units = []
        self.resources = []
        self.reached_resources = []
        self.obstacles = set()

    def prepare(self, gs:GameState, player_id:int):
        self.used_resource = 0
        self.allay_base = []
        self.allay_worker = []
        self.enemy_units = []
        self.resources = []
        self.reached_resources = []
        self.obstacles = gs.get_obstacles()
        for unit in list(gs.units.values()):
            if unit.unit_type.isResource:
                self.resources.append(unit)
            if unit.player_id == player_id:
                if unit.unit_type.isStockpile:
                    self.allay_base.append(unit)
                elif unit.unit_type.canHarvest:
                    self.allay_worker.append(unit)
            elif unit.player_id != -1:
                self.enemy_units.append(unit)
        if len(self.allay_base)>0 and len(self.resources)>0:
            for resouce in self.resources:
                for base in self.allay_base:
                    if int_pos_in_range(resouce.pos, base.pos, gs.width, gs.width):
                        self.reached_resources.append(resouce)
                        break

    def worker_actions(self, game_state:GameState):
        if len(self.allay_worker) == 0:
            return []
        actions = []
        free_workers = []
        for worker in self.allay_worker:
            if not worker.busy():
                free_workers.append(worker)
        harvest_workers = []
        if len(self.reached_resources)>0:
            while len(harvest_workers) < self.max_harvest_worker and len(free_workers) > 0:
                # find the closest worker in free_workers to the resource
                closest_worker = None
                closest_score = 100000000
                for worker in self.allay_worker:
                    for resource in self.reached_resources:
                        score = distance_int_pos(worker.pos, resource.pos, game_state.width)
                        if score < closest_score:
                            closest_score = score
                            closest_worker = worker
                harvest_workers.append(closest_worker)
                if closest_worker in free_workers:
                    free_workers.remove(closest_worker)
        for worker in harvest_workers:
            if worker.busy():
                continue
            if worker.carried_resource == 0:
                # find the closest resource to the worker
                closest_resource = None
                closest_score = 100000000
                for resource in self.reached_resources:
                    score = distance_int_pos(worker.pos, resource.pos, game_state.width)
                    if score < closest_score:
                        closest_score = score
                        closest_resource = resource
                # if closest_resource is next to the worker, harvest it
                if int_pos_in_range(worker.pos, closest_resource.pos, game_state.width, 1):
                    actions.append((worker.unit_id, "harvest", closest_resource.pos, None))
                else:
                    worker_pos = int_pos_to_pos(worker.pos,game_state.width)
                    resource_pos = int_pos_to_pos(closest_resource.pos,game_state.width)
                    next_pos = self.bfs.next_pos(worker_pos, resource_pos, self.obstacles)
                    if next_pos is not None:
                        actions.append((worker.unit_id, "move", next_pos.int_pos, None))
                        self.obstacles.add(next_pos)
            else:
                closest_base = None
                closest_score = 100000000
                for base in self.allay_base:
                    score = distance_int_pos(worker.pos, base.pos, game_state.width)
                    if score < closest_score:
                        closest_score = score
                        closest_base = base
                if int_pos_in_range(worker.pos, closest_base.pos, game_state.width, 1):
                    actions.append((worker.unit_id, "return", closest_base.pos, None))
                else:
                    next_pos = self.bfs.next_pos(int_pos_to_pos(worker.pos,game_state.width), int_pos_to_pos(closest_base.pos,game_state.width), self.obstacles)
                    if next_pos is not None:
                        actions.append((worker.unit_id, "move", next_pos.int_pos, None))
                        self.obstacles.add(next_pos)
        if len(free_workers)>0:
            for worker in free_workers:
                closest_enemy = None
                closest_score = 100000000
                for enemy in self.enemy_units:
                    score = distance_int_pos(worker.pos, enemy.pos, game_state.width)
                    if score < closest_score:
                        closest_score = score
                        closest_enemy = enemy
                if int_pos_in_range(worker.pos, closest_enemy.pos, game_state.width, worker.unit_type.attackRange):
                    actions.append((worker.unit_id, "attack", closest_enemy.pos, None))
                else:
                    next_pos = self.bfs.next_pos(int_pos_to_pos(worker.pos,game_state.width), int_pos_to_pos(closest_enemy.pos,game_state.width), self.obstacles)
                    if next_pos is not None:
                        actions.append((worker.unit_id, "move", next_pos.int_pos, None))
                        self.obstacles.add(next_pos)
        return actions
    
    def base_actions(self, game_state:GameState):
        if len(self.allay_base) == 0:
            return []
        actions = []
        for base in self.allay_base:
            if not base.busy() and game_state.players[self.player_id].resource >= game_state.unit_types["Worker"].cost + self.used_resource:
                # find the colset enemy to the base
                closest_enemy = None
                closest_score = 100000000
                for enemy in self.enemy_units:
                    score = distance_int_pos(base.pos, enemy.pos, game_state.width)
                    if score < closest_score:
                        closest_score = score
                        closest_enemy = enemy
                next_pos = self.bfs.get_neighbors_closest_to_target(int_pos_to_pos(base.pos,game_state.width), int_pos_to_pos(closest_enemy.pos,game_state.width), self.obstacles)
                if next_pos is not None:
                    actions.append((base.unit_id, "produce", next_pos.int_pos, "Worker"))
                    self.obstacles.add(next_pos)
                    self.used_resource += game_state.unit_types["Worker"].cost
        return actions
    
    def get_action_list(self, game_state:GameState):
        game_state.get_units_pos()
        self.prepare(game_state, self.player_id)
        actions = []
        actions.extend(self.worker_actions(game_state))
        actions.extend(self.base_actions(game_state))
        return actions
            
class AbstractPathFindingAI(AI):
    def __init__(self,player_id:int, width:int, height:int, path_finding:PathFinding):
        super().__init__(player_id)
        self.path_finding = path_finding(width, height)
        self.width = width
        self.height = height
        self.obstacles = set()
        self.pos_to_build_barracks = []
        self.pos_to_build_base = []
        self.used_resource = 0
        self.barracks_prodece_type = "Light"
    
    def prepare(self, gs:GameState):
        self.obstacles = gs.get_obstacles()
        self.pos_to_build_barracks = []
        self.pos_to_build_base = []
        self.used_resource = 0
        self.barracks_prodece_type = "Light"

    def get_unit_action(self, gs:GameState, unit_id:int, target_pos:int):
        if unit_id not in list(gs.units.keys()):
            return (None,None,None,None)
        unit = gs.units[unit_id]
        if unit.busy():
            return (None,None,None,None)
        if target_pos not in list(gs.units_pos.keys()):
            # if target_pos next to the unit
            if is_in_range(unit.pos, target_pos, gs.width, 1):
                if target_pos in self.pos_to_build_barracks:
                    if "Barracks" in unit.unit_type.produces and gs.players[unit.player_id].resource >= gs.unit_types["Barracks"].cost + self.used_resource:
                        self.used_resource += gs.unit_types["Barracks"].cost
                        self.obstacles.add(target_pos)
                        return (unit_id, "produce", target_pos, "Barracks")
                elif target_pos in self.pos_to_build_base:
                    if "Base" in unit.unit_type.produces and gs.players[unit.player_id].resource >= gs.unit_types["Base"].cost + self.used_resource:
                        self.used_resource += gs.unit_types["Barracks"].cost
                        self.obstacles.add(target_pos)
                        return (unit_id, "produce", target_pos, "Base")
            #move to target_pos
            next_pos = self.path_finding.next_pos(int_pos_to_pos(unit.pos,gs.width), int_pos_to_pos(target_pos,gs.width), self.obstacles,ignore_target=False)
            if next_pos is not None:
                self.obstacles.add(next_pos)
                return (unit_id, "move", next_pos.int_pos, None)
            else:
                return (unit_id,"NOOP",None,None)
        elif unit.unit_type.canMove:
            target_unit = gs.units_pos[target_pos]
            if target_unit.player_id != self.player_id and target_unit.player_id != -1:
                # if target unit is in attack range, attack it
                if is_in_range(unit.pos, target_unit.pos, gs.width, unit.unit_type.attackRange):
                    return (unit_id, "attack", target_unit.pos, None)
                else:
                    # move to target unit
                    next_pos = self.path_finding.next_pos(int_pos_to_pos(unit.pos,gs.width), int_pos_to_pos(target_pos,gs.width), self.obstacles)
                    if next_pos is not None:
                        self.obstacles.add(next_pos)
                        return (unit_id, "move", next_pos.int_pos, None)
                    else:
                        return (unit_id,"NOOP",None,None)
            else:
                # if target unit is not close to the unit, move to it
                if not is_in_range(unit.pos, target_unit.pos, gs.width, 1):
                    next_pos = self.path_finding.next_pos(int_pos_to_pos(unit.pos,gs.width), int_pos_to_pos(target_pos,gs.width), self.obstacles)
                    if next_pos is not None:
                        self.obstacles.add(next_pos)
                        return (unit_id, "move", next_pos.int_pos, None)
                    else:
                        return (unit_id,"NOOP",None,None)
                else:
                    if target_unit.unit_type.isResource and unit.unit_type.canHarvest and unit.carried_resource == 0:
                        # harvest the resource
                        return (unit_id, "harvest", target_unit.pos, None)
                    elif target_unit.unit_type.isStockpile and unit.unit_type.canHarvest and unit.carried_resource > 0:
                        # return the resource
                        return (unit_id, "return", target_unit.pos, None)
                    else:
                        return (unit_id,"NOOP",None,None)
        else:
            next_pos = self.path_finding.next_pos(int_pos_to_pos(unit.pos,gs.width), int_pos_to_pos(target_pos,gs.width), self.obstacles)
            if next_pos is not None:
                if unit.unit_type.name == "Barracks":
                    if gs.players[unit.player_id].resource >= gs.unit_types[self.barracks_prodece_type].cost + self.used_resource:
                        self.used_resource += gs.unit_types[self.barracks_prodece_type].cost
                        self.obstacles.add(next_pos)
                        return (unit_id, "produce", next_pos.int_pos, self.barracks_prodece_type)
                    else:
                        return (unit_id,"NOOP",None,None)
                elif unit.unit_type.name == "Base":
                    if gs.players[unit.player_id].resource >= gs.unit_types["Worker"].cost + self.used_resource:
                        self.used_resource += gs.unit_types["Worker"].cost
                        self.obstacles.add(next_pos)
                        return (unit_id, "produce", next_pos.int_pos, "Worker")
                    else:
                        return (unit_id,"NOOP",None,None)
                else:
                    return (unit_id,"NOOP",None,None)
            else:
                return (unit_id,"NOOP",None,None)
            
class LightRushAI(AbstractPathFindingAI):
    def __init__(self, player_id:int, width:int, height:int, path_finding:PathFinding):
        super().__init__(player_id, width, height, path_finding)
        self.barracks_prodece_type = "Light"
        self.max_harvest_worker = 2
        self.num_barracks = 1
        self.allay_base = []
        self.allay_barracks = []
        self.allay_worker = []
        self.allay_melee = []
        self.enemy_units = []
        self.resources = []
        self.reached_resources = []

    def prepare(self, gs: GameState):
        super().prepare(gs)
        self.used_resource = 0
        self.allay_base = []
        self.allay_worker = []
        self.allay_melee = []
        self.allay_barracks = []
        self.enemy_units = []
        self.resources = []
        self.reached_resources = []
        self.obstacles = gs.get_obstacles()
        for unit in list(gs.units.values()):
            if unit.unit_type.isResource:
                self.resources.append(unit)
            if unit.player_id == self.player_id:
                if unit.unit_type.isStockpile:
                    self.allay_base.append(unit)
                elif unit.unit_type.canHarvest:
                    self.allay_worker.append(unit)
                elif unit.unit_type.name == "Barracks":
                    self.allay_barracks.append(unit)
                elif unit.unit_type.canAttack:
                    self.allay_melee.append(unit)
            elif unit.player_id != -1:
                self.enemy_units.append(unit)
        if len(self.allay_base)>0 and len(self.resources)>0:
            for resouce in self.resources:
                for base in self.allay_base:
                    if int_pos_in_range(resouce.pos, base.pos, gs.width, gs.width):
                        self.reached_resources.append(resouce)
                        break
        self.num_barracks = len(self.allay_base)
    
    def find_pos_to_bulid_barracks(self,gs:GameState):
        self.pos_to_build_barracks = []
        potential_pos = []
        self.bulid_barracks_pos = []

        for i in range(self.height):
            for j in range(self.width):
                pos = Pos(i,j,gs.width)
                int_pos = pos.int_pos
                if int_pos in self.obstacles:
                    continue
                score = 0
                for enemy in self.enemy_units:
                    # if any enemy is in range of the pos, range = 3, score -= 10
                    if is_in_range(int_pos, enemy.pos, gs.width, 3):
                        score -= 10
                        continue
                for resource in self.reached_resources:
                    # if any resource is in range of the pos, range = 1, score -= 10
                    if is_in_range(int_pos, resource.pos, gs.width, 1):
                        score -= 10
                        continue
                for base in self.allay_base:
                    # if any base is in range of the pos, range = 2, score += 5
                    if is_in_range(int_pos, base.pos, gs.width, 2):
                        score += 5
                        continue
                for worker in self.allay_worker:
                    # if any worker is in range of the pos, range = 2, score += 8
                    if is_in_range(int_pos, worker.pos, gs.width, 1):
                        if not worker.busy():
                            score += 100
                            continue
                potential_pos.append((int_pos,score))
        # sort the potential_pos by score from high to low
        potential_pos.sort(key=lambda x:x[1], reverse=True)
        # get the top 3 pos
        for i in range(min(self.num_barracks,len(potential_pos))):
            self.pos_to_build_barracks.append(potential_pos[i][0])

    def get_action_list(self, gs:GameState):
        gs.get_units_pos()
        self.prepare(gs)
        self.find_pos_to_bulid_barracks(gs)
        actions = []
        actions.extend(self.worker_actions(gs))
        actions.extend(self.base_actions(gs))
        actions.extend(self.barracks_actions(gs))
        actions.extend(self.melee_actions(gs))
        return actions

    def worker_actions(self, gs:GameState):
        if len(self.allay_worker) == 0:
            return []
        actions = []
        free_workers = self.allay_worker.copy()
        harvest_workers = []
        if len(self.reached_resources)>0:
            while len(harvest_workers) < self.max_harvest_worker and len(free_workers) > 0:
                # find the closest worker in free_workers to the resource
                closest_worker = None
                closest_score = 100000000
                for worker in free_workers:
                    for resource in self.reached_resources:
                        score = distance_int_pos(worker.pos, resource.pos, gs.width)
                        if score < closest_score:
                            closest_score = score
                            closest_worker = worker
                harvest_workers.append(closest_worker)
                if closest_worker in free_workers:
                    free_workers.remove(closest_worker)
        for worker in harvest_workers:
            if worker.busy():
                continue
            if worker.carried_resource == 0:
                # find the closest resource to the worker
                closest_resource = None
                closest_score = 100000000
                for resource in self.reached_resources:
                    score = distance_int_pos(worker.pos, resource.pos, gs.width)
                    if score < closest_score:
                        closest_score = score
                        closest_resource = resource
                actions.append(self.get_unit_action(gs, worker.unit_id, closest_resource.pos))
            else:
                closest_base = None
                closest_score = 100000000
                for base in self.allay_base:
                    score = distance_int_pos(worker.pos, base.pos, gs.width)
                    if score < closest_score:
                        closest_score = score
                        closest_base = base
                actions.append(self.get_unit_action(gs, worker.unit_id, closest_base.pos))
        if len(free_workers)>0:
            if len(self.allay_barracks) + len(self.bulid_barracks_pos) < self.num_barracks and gs.players[self.player_id].resource >= gs.unit_types["Barracks"].cost + self.used_resource:
                if len(self.pos_to_build_barracks) > 0:
                    closest_bulid_worker = None
                    closest_score = 100000000
                    target_pos = self.pos_to_build_barracks[0]
                    for worker in free_workers:
                        if worker.busy():
                            continue
                        score = distance_int_pos(worker.pos, target_pos, gs.width)
                        if score < closest_score:
                            closest_score = score
                            closest_bulid_worker = worker
                    if closest_bulid_worker is not None:
                        action = self.get_unit_action(gs, closest_bulid_worker.unit_id, target_pos)
                        actions.append(action)
                        self.used_resource += gs.unit_types["Barracks"].cost
                        free_workers.remove(closest_bulid_worker)
                        if action[1] == "produce":
                            self.pos_to_build_barracks.remove(target_pos)
                            self.bulid_barracks_pos.append(target_pos)
            for worker in free_workers:
                closest_enemy = None
                closest_score = 100000000
                for enemy in self.enemy_units:
                    score = distance_int_pos(worker.pos, enemy.pos, gs.width)
                    if score < closest_score:
                        closest_score = score
                        closest_enemy = enemy
                actions.append(self.get_unit_action(gs, worker.unit_id, closest_enemy.pos))
        return actions
    
    def base_actions(self, gs:GameState):
        if len(self.allay_base) == 0:
            return []
        actions = []
        for base in self.allay_base:
            if not base.busy() and gs.players[self.player_id].resource >= gs.unit_types["Worker"].cost + self.used_resource:
                # find the colset enemy to the base
                closest_enemy = None
                closest_score = 100000000
                for enemy in self.enemy_units:
                    score = distance_int_pos(base.pos, enemy.pos, gs.width)
                    if score < closest_score:
                        closest_score = score
                        closest_enemy = enemy
                actions.append(self.get_unit_action(gs, base.unit_id, closest_enemy.pos))
        return actions
    
    def barracks_actions(self, gs:GameState):
        if len(self.allay_barracks) == 0:
            return []
        actions = []
        for barracks in self.allay_barracks:
            if not barracks.busy() and gs.players[self.player_id].resource >= gs.unit_types[self.barracks_prodece_type].cost + self.used_resource:
                # find the colset enemy to the base
                closest_enemy = None
                closest_score = 100000000
                for enemy in self.enemy_units:
                    score = distance_int_pos(barracks.pos, enemy.pos, gs.width)
                    if score < closest_score:
                        closest_score = score
                        closest_enemy = enemy
                actions.append(self.get_unit_action(gs, barracks.unit_id, closest_enemy.pos))
        return actions
    
    def melee_actions(self,gs:GameState):
        if len(self.allay_melee) == 0:
            return []
        actions = []
        for melee in self.allay_melee:
            if not melee.busy():
                # find the colset enemy to the base
                closest_enemy = None
                closest_score = 100000000
                for enemy in self.enemy_units:
                    score = distance_int_pos(melee.pos, enemy.pos, gs.width)
                    if score < closest_score:
                        closest_score = score
                        closest_enemy = enemy
                actions.append(self.get_unit_action(gs, melee.unit_id, closest_enemy.pos))
        return actions
    
                    
                        
                        
            
        

                    
                
        
