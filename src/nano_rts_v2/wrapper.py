from game import Game
from player import Player
from units import Unit
from action import Action
from ai import AI, RushAI
import pygame
import numpy as np

class GameEnv:
    def __init__(self, map_paths, reward_wrights, max_steps, skip_frames=5):
        self.games:list[Game] = []
        self.map_paths = map_paths
        self.reward_wrights = reward_wrights
        self.max_steps = max_steps
        for map_path in map_paths:
            self.games.append(Game(map_path, reward_wrights))
        self.num_envs = len(self.games)
        self.skip_frames = skip_frames

        pygame.init()
        self.shape_size = 32
        self.bordersize = self.shape_size // 8
        self.line_width = self.shape_size // 8
        self.vacant = 20
        self.info_height = 100
        self.viewer = None

    def step(self, actions0:Action, actions1:Action)->tuple[list[np.ndarray], list[int], list[bool], list]:
        states = []
        rewards = []
        dones = []
        winners = []
        for i in range(len(self.games)):
            game:Game = self.games[i]
            action0:Action = actions0[i]
            action1:Action = actions1[i]
            state = game.get_grid_state()

            for player_id in [0,1]:
                action = action0 if player_id == 0 else action1
                unit_pos = action.unit_pos
                if unit_pos is None:
                    continue
                action_type = action.action_type
                target_pos = action.target_pos
                produced_unit_type = action.produced_unit_type
                if unit_pos not in list(game.units.keys()):
                    continue
                unit:Unit = game.units[unit_pos]
                if unit.player_id != player_id:
                    continue
                if action_type == 'move':
                    game.begin_move(unit_pos, target_pos)
                elif action_type == 'harvest':
                    game.begin_harvest(unit_pos, target_pos)
                elif action_type == 'return':
                    game.begin_return(unit_pos, target_pos)
                elif action_type == 'produce':
                    game.begin_produce(unit_pos, target_pos, produced_unit_type)
                elif action_type == 'attack':
                    game.begin_attack(unit_pos, target_pos)
            reward,done,winner = game.run()
            if done:
                state = game.reset()
            if game.game_time >= self.max_steps:
                done = True
                state = game.reset()
            states.append(state)
            rewards.append(reward)
            dones.append(done)
            winners.append(winner)
        return states, rewards, dones, winners

    def step_action_lists(self, action_lists:list[list[Action]])->tuple[list[np.ndarray], list[int], list[bool], list]:
        states = []
        rewards = []
        dones = []
        winners = []
        for i in range(len(self.games)):
            game:Game = self.games[i]
            if game.game_time % self.skip_frames != 0:
                game.run()
            state = game.get_grid_state()
            action_list = action_lists[i]
            for action in action_list:
                unit_pos = action.unit_pos
                if unit_pos is None:
                    continue
                action_type = action.action_type
                target_pos = action.target_pos
                produced_unit_type = action.produced_unit_type
                if unit_pos not in list(game.units.keys()):
                    continue
                if action_type == 'move':
                    game.begin_move(unit_pos, target_pos)
                elif action_type == 'harvest':
                    game.begin_harvest(unit_pos, target_pos)
                elif action_type == 'return':
                    game.begin_return(unit_pos, target_pos)
                elif action_type == 'produce':
                    game.begin_produce(unit_pos, target_pos, produced_unit_type)
                elif action_type == 'attack':
                    game.begin_attack(unit_pos, target_pos)
            reward,done,winner = game.run()
            if done:
                state = game.reset()
            if game.game_time >= self.max_steps:
                done = True
                state = game.reset()
            states.append(state)
            rewards.append(reward)
            dones.append(done)
            winners.append(winner)
        return states, rewards, dones, winners

    def reset(self)->np.ndarray:
        states = []
        for i in range(len(self.games)):
            state = self.games[i].reset()
            states.append(state)
        return np.array(states)
    
    def render(self)->None:
        game:Game = self.games[0]
        PLAYER_COLORS = {-1:(0,255,0), 0:(255,0,0), 1:(0,0,255)}
        UNIT_TYPE_COLORS = {
            'Base': (128, 128, 128),
            'Worker': (128, 128, 128),
            'Barracks': (64, 64, 64),
            'Light': (255, 255, 0),
            'Heavy': (0, 255, 255),
            'Ranged': (255, 0, 255),
            'Resource': (0, 255, 0),
            'terrain': (0, 128, 0)
        }
        RECT_UNITS = {'Base', 'Barracks', 'Resource', 'terrain'}
        CIRCLE_UNITS = {'Worker', 'Light', 'Heavy', 'Ranged'}

        viewer_height = game.height * self.shape_size + self.vacant * 2 + self.info_height
        viewer_width = game.width * self.shape_size + self.vacant * 2
        if self.viewer is None:
            self.viewer = pygame.display.set_mode((viewer_width, viewer_height))
        self.viewer.fill((0,0,0))
        x_start = self.vacant
        x_end = self.vacant + game.width * self.shape_size
        y_start = self.vacant
        y_end = self.vacant + game.height * self.shape_size
        for i in range(game.width+1):
            x = x_start + i * self.shape_size
            pygame.draw.line(self.viewer, (255,255,255), (x, y_start), (x, y_end))
        for i in range(game.height+1):
            y = y_start + i * self.shape_size
            pygame.draw.line(self.viewer, (255,255,255), (x_start, y), (x_end, y))
        for unit in game.units.values():
            unit_name = unit.unit_type.name
            unit_player_id = unit.player_id
            unit_int_pos = unit.pos
            unit_pos_x = unit_int_pos % game.width
            unit_pos_y = unit_int_pos // game.width
            x = x_start + unit_pos_x * self.shape_size
            y = y_start + unit_pos_y * self.shape_size    
            player_color = PLAYER_COLORS[unit_player_id]
            unit_type_color = UNIT_TYPE_COLORS[unit_name]
            if unit_name in RECT_UNITS:
                pygame.draw.rect(self.viewer, player_color, (x, y, self.shape_size, self.shape_size))
                pygame.draw.rect(self.viewer, unit_type_color, (x + self.bordersize, y + self.bordersize, self.shape_size - self.bordersize * 2, self.shape_size - self.bordersize * 2))
            elif unit_name in CIRCLE_UNITS:
                pygame.draw.circle(self.viewer, player_color, (x + self.shape_size // 2, y + self.shape_size // 2), self.shape_size // 2)
                pygame.draw.circle(self.viewer, unit_type_color, (x + self.shape_size // 2, y + self.shape_size // 2), self.shape_size // 2 - self.bordersize)
            else:
                raise Exception("unit_name is not valid")
            # if unit is doing action draw a line to target
            if unit.current_action is not None:
                target_pos_int = unit.current_action_target
                target_x = x_start + (target_pos_int % game.width) * self.shape_size + self.shape_size // 2
                target_y = y_start + (target_pos_int // game.width) * self.shape_size + self.shape_size // 2
                pygame.draw.line(self.viewer, (255,255,255), (x + self.shape_size // 2, y + self.shape_size // 2), (target_x, target_y),width=self.line_width)
            # if unit is carrying resource show number of resource on its center
            if unit.carried_resource > 0:
                font = pygame.font.SysFont('Arial', 20)
                text = font.render(str(unit.carried_resource), True, (255,255,255))
                self.viewer.blit(text, (x + self.shape_size // 2, y + self.shape_size // 2))
            # if unit is base show number of player's resource on its center
            if unit_name == 'Base':
                font = pygame.font.SysFont('Arial', 20)
                text = font.render(str(game.players[unit.player_id].resource), True, (255,255,255))
                self.viewer.blit(text, (x + self.shape_size // 2, y + self.shape_size // 2))
            # if unit current hp is less than max hp show hp bar on it
            if unit.current_hp < unit.unit_type.hp:
                max_hp_bar_width = self.shape_size
                hp_bar_width = self.shape_size * unit.current_hp // unit.unit_type.hp
                pygame.draw.rect(self.viewer, (255,0,0), (x, y, max_hp_bar_width, self.line_width))
                pygame.draw.rect(self.viewer, (0,255,0), (x, y, hp_bar_width, self.line_width))
            if unit.current_action == "produce":
                target_pos_int = unit.current_action_target
                target_pos_x = target_pos_int % game.width
                target_pos_y = target_pos_int // game.width
                target_x = x_start + target_pos_x * self.shape_size
                target_y = y_start + target_pos_y * self.shape_size
                left_produce_time = unit.execute_current_action_time
                left_time_bar = self.shape_size * left_produce_time // unit.unit_type.produceTime
                pygame.draw.rect(self.viewer, (0,255,0), (target_x, target_y, left_time_bar, self.line_width))
        # show info: player0 resource
        #            player1 resource
        #            game time
        font = pygame.font.SysFont('Arial', 20)
        text = font.render("Player0 resource: " + str(game.players[0].resource), True, (255,255,255))
        self.viewer.blit(text, (self.vacant, self.vacant + game.height * self.shape_size))
        text = font.render("Player1 resource: " + str(game.players[1].resource), True, (255,255,255))
        self.viewer.blit(text, (self.vacant, self.vacant + game.height * self.shape_size + self.info_height // 3))
        text = font.render("Game time: " + str(game.game_time), True, (255,255,255))
        self.viewer.blit(text, (self.vacant, self.vacant + game.height * self.shape_size + self.info_height // 3 * 2))
        pygame.display.update()

    def get_unit_masks(self,player_id:int)->np.ndarray:
        unit_masks = []
        for i in range(len(self.games)):
            game:Game = self.games[i]
            unit_mask = game.get_vector_units_mask(player_id)
            unit_masks.append(unit_mask)
        return np.array(unit_masks)

    def get_action_masks(self, units, player_id=0)->np.ndarray:
        action_masks = []
        for i in range(len(self.games)):
            game:Game = self.games[i]
            action_mask = game.get_vector_action_mask(units[i], player_id)
            action_masks.append(action_mask)
        return np.array(action_masks)

if __name__ == "__main__":
    rewards_wrights = {'win': 10, 'harvest': 1, 'return': 1, 'produce': 1, 'attack': 1}
    num_envs = 1
    map_paths = ['maps\\16x16\\basesWorkers16x16.xml' for _ in range(num_envs)]
    max_steps=5000
    env = GameEnv(map_paths, rewards_wrights, max_steps)
    
    width = 16
    height = 16
    ai0 = AI(0)
    ai1 = RushAI(1, "Light", width, height)

    for _ in range(10000):
        env.render()
        action_lists = []
        for i in range(len(env.games)):
            action_list = []
            game = env.games[i]
            # action: Action(unit_pos:int, action_type:str, target_pos:int, produced_unit_type:UnitType=None)
            action_list.append(ai0.get_random_action(game))
            action_list.append(ai1.get_action(game))
            action_lists.append(action_list)
        #action_lists: List[List[Action]]
        states, rewards, dones, winners = env.step_action_lists(action_lists)
