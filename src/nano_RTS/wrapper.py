from game import Game
import numpy as np
from game_state import GameState
from torch.multiprocessing import Process
from agent import AI
import time

class GameForMultiprocess:
    def __init__(self, map_paths:str, render:bool = False, slow_down_time:float = 0.0):
        self.map_path = map_paths
        self.do_render = render
        self.slow_down_time = slow_down_time
        self.process = None
        self.games = []
        for map_path in map_paths:
            self.games.append(Game(map_path, render, slow_down_time))

    
class GameEnvs:
    def __init__(self, map_paths:str, obs_mode = 'grid', max_steps = 1000):
        self.map_path = map_paths
        self.process = None
        self.games = []
        self.obs_mode = obs_mode
        self.max_steps = max_steps
        for map_path in map_paths:
            self.games.append(Game(map_path,max_steps = max_steps))
    
    def get_grid_obs(self):
        obs = []
        for game in self.games:
            obs.append(game.gs.get_grid_state())
        return obs
    
    # if w<24, h<24, then the grid obs is padded to 24x24
    def get_padded_grid_obs(self):
        obs = []
        for game in self.games:
            grid_state = game.gs.get_grid_state()
            w = grid_state.shape[0]
            h = grid_state.shape[1]
            if w < 24 and h < 24:
                padded_grid_state = np.zeros((24,24,27))
                padded_grid_state[:w,:h,:] = grid_state
                obs.append(padded_grid_state)
        return obs
    
    def get_vector_obs(self):
        obs = []
        for game in self.games:
            obs.append(game.gs.get_vector_state())
        return obs

    def step(self, action_lists):
        dones = []
        results = []
        rs = []
        for i in range(len(self.games)):
            r, done, result = self.games[i].step_action_list(action_lists[i])
            dones.append(done)
            results.append(result)
            rs.append(r)
        if self.obs_mode == 'grid':
            return self.get_grid_obs(), rs, dones, results
        else:
            return self.get_grid_obs(), rs, dones, results
        
    def one_action_step(self,action_list):
        dones = []
        results = []
        rs = []
        for i in range(len(self.games)):
            actions = action_list[i]
            game:Game = self.games[i]
            r = 0
            done = False
            result = None
            for action in actions:
                unit_id, action_type, target_pos, produce_type = action
                if unit_id is None:
                    continue
                if unit_id not in list(game.gs.units.keys()):
                    continue
                if game.gs.units[unit_id].current_action is not None:
                    continue
                if action_type == 'move':
                    game.gs.begin_move_unit(unit_id, target_pos)
                elif action_type == 'attack':
                    game.gs.begin_attack_unit(unit_id, target_pos)
                elif action_type == 'harvest':
                    game.gs.begin_harvest_unit(unit_id, target_pos)
                elif action_type == 'return':
                    game.gs.begin_return_unit(unit_id, target_pos)
                elif action_type == 'produce':
                    game.gs.begin_produce_unit(unit_id, target_pos, produce_type)
                
            while game.gs.get_player_available_units(0) == []:
                if i == 0:
                    game.render()
                r += game.gs.update()
                result = game.gs.game_result()
                if result is not None:
                    done = True
                    break
            dones.append(done)
            results.append(result)
            rs.append(r)
        if self.obs_mode == 'grid':
            return self.get_grid_obs(), rs, dones, results
        else:
            return self.get_grid_obs(), rs, dones, results
    
    def reset(self):
        for game in self.games:
            game.reset()
        if self.obs_mode == 'grid':
            return self.get_grid_obs()
        else:
            return self.get_grid_obs()
    
    def render(self):
        self.games[0].render()

    def get_unit_masks(self, player_id):
        masks = []
        for game in self.games:
            mask = np.zeros(game.gs.height*game.gs.width)
            for unit_id in list(game.gs.units.keys()):
                unit = game.gs.units[unit_id]
                if unit.player_id == player_id and not unit.busy():
                    mask[unit.pos] = 1
            masks.append(mask)
        return masks
    
    def get_action_masks(self, unit_list):
        masks = []
        for i in range(len(self.games)):
            mask = np.zeros(78)
            game = self.games[i]
            unit_pos = unit_list[i]
            mask = game.gs.get_action_masks(unit_pos,0)
            masks.append(mask)
        return masks
                    



if __name__ == "__main__":
    num_games = 32
    map_paths = ['maps\\16x16\\basesWorkers16x16.xml' for _ in range(num_games)]
    game_envs = GameEnvs(map_paths)
    ai0 = AI(0)
    ai1 = AI(1)
    start_time = time.time()
    for _ in range(2560):
        #game_envs.render()
        all_action_lists = []
        for game in game_envs.games:
            action_list = []
            action_list.extend(ai0.get_random_action_list(game.gs))
            action_list.extend(ai1.get_random_action_list(game.gs))
            #game.gs.get_vector_state(0)
            #game.gs.get_vector_state(1)
            all_action_lists.append(action_list)
        game_envs.step(all_action_lists)
    print(num_games)
    print(time.time() - start_time)
    




