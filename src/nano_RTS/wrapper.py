from game import Game
import numpy as np
from game_state import GameState
from torch.multiprocessing import Process
from agent import Agent
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
    def __init__(self, map_paths:str, obs_mode = 'grid'):
        self.map_path = map_paths
        self.process = None
        self.games = []
        self.obs_mode = obs_mode
        for map_path in map_paths:
            self.games.append(Game(map_path))
    
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
        for i in range(len(self.games)):
            done, result = self.games[i].step_action_list(action_lists[i])
            dones.append(done)
            results.append(result)
        if self.obs_mode == 'grid':
            return self.get_grid_obs(), dones, results
        else:
            return self.get_grid_obs(), dones, results
    
    def reset(self):
        for game in self.games:
            game.reset()
        if self.obs_mode == 'grid':
            return self.get_grid_obs()
        else:
            return self.get_grid_obs()
    
    def render(self):
        self.games[0].render()


if __name__ == "__main__":
    num_games = 32
    map_paths = ['maps\\16x16\\basesWorkers16x16.xml' for _ in range(num_games)]
    game_envs = GameEnvs(map_paths)
    ai0 = Agent(0)
    ai1 = Agent(1)
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
    




