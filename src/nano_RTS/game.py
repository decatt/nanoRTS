from game_state import GameState
from units import Unit, UnitType, load_unit_types
from pos import Pos
from agent import AI
import numpy as np
import pygame
import time

class Game:
    def __init__(self, map_path:str):
        self.gs = GameState(map_path)
        self.map_path = map_path

        pygame.init()
        self.shape_size = 32
        self.bordersize = self.shape_size // 8
        self.line_width = self.shape_size // 8
        self.vacant = 20

        self.viewer = None

    def step(self, action):
        unit_id, action_type, target_pos, produce_type = action
        if action_type == 'move':
            self.gs.begin_move_unit(unit_id, target_pos)
        elif action_type == 'attack':
            self.gs.begin_attack_unit(unit_id, target_pos)
        elif action_type == 'harvest':
            self.gs.begin_harvest_unit(unit_id, target_pos)
        elif action_type == 'return':
            self.gs.begin_return_unit(unit_id, target_pos)
        elif action_type == 'produce':
            self.gs.begin_produce_unit(unit_id, target_pos, produce_type)

        while True:
            self.gs.update()
            player1_available_units = self.gs.get_player_available_units(0)
            player2_available_units = self.gs.get_player_available_units(1)
            if len(player1_available_units) > 0 or len(player2_available_units) > 0:
                break
            self.gs.update()
    
    def step_action_list(self, action_list):
        for action in action_list:
            unit_id, action_type, target_pos, produce_type = action
            if action_type == 'move':
                self.gs.begin_move_unit(unit_id, target_pos)
            elif action_type == 'attack':
                self.gs.begin_attack_unit(unit_id, target_pos)
            elif action_type == 'harvest':
                self.gs.begin_harvest_unit(unit_id, target_pos)
            elif action_type == 'return':
                self.gs.begin_return_unit(unit_id, target_pos)
            elif action_type == 'produce':
                self.gs.begin_produce_unit(unit_id, target_pos, produce_type)
        r = self.gs.update()
        result = self.gs.game_result()
        done = False
        if result is not None:
            self.reset()
            done = True
            if result == "player0":
                r += 10
        return r, done, result

    def render(self):
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

        viewer_height = self.gs.height * self.shape_size + self.vacant * 2
        viewer_width = self.gs.width * self.shape_size + self.vacant * 2
        if self.viewer is None:
            self.viewer = pygame.display.set_mode((viewer_width, viewer_height))
        self.viewer.fill((0,0,0))
        x_start = self.vacant
        x_end = self.vacant + self.gs.width * self.shape_size
        y_start = self.vacant
        y_end = self.vacant + self.gs.height * self.shape_size
        for i in range(self.gs.width+1):
            x = x_start + i * self.shape_size
            pygame.draw.line(self.viewer, (255,255,255), (x, y_start), (x, y_end))
        for i in range(self.gs.height+1):
            y = y_start + i * self.shape_size
            pygame.draw.line(self.viewer, (255,255,255), (x_start, y), (x_end, y))
        for unit in self.gs.units.values():
            unit_name = unit.unit_type.name
            unit_player_id = unit.player_id
            unit_int_pos = unit.pos
            unit_pos = Pos(unit_int_pos % self.gs.width, unit_int_pos // self.gs.width, self.gs.width)
            x = x_start + unit_pos.x * self.shape_size
            y = y_start + unit_pos.y * self.shape_size    
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
                target_pos = Pos(target_pos_int % self.gs.width, target_pos_int // self.gs.width, self.gs.width)
                target_x = x_start + target_pos.x * self.shape_size + self.shape_size // 2
                target_y = y_start + target_pos.y * self.shape_size + self.shape_size // 2
                pygame.draw.line(self.viewer, (255,255,255), (x + self.shape_size // 2, y + self.shape_size // 2), (target_x, target_y),width=self.line_width)
            # if unit is carrying resource show number of resource on its center
            if unit.carried_resource > 0:
                font = pygame.font.SysFont('Arial', 20)
                text = font.render(str(unit.carried_resource), True, (255,255,255))
                self.viewer.blit(text, (x + self.shape_size // 2, y + self.shape_size // 2))
            # if unit is base show number of player's resource on its center
            if unit_name == 'Base':
                font = pygame.font.SysFont('Arial', 20)
                text = font.render(str(self.gs.players[unit.player_id].resource), True, (255,255,255))
                self.viewer.blit(text, (x + self.shape_size // 2, y + self.shape_size // 2))
            # if unit current hp is less than max hp show hp bar on it
            if unit.current_hp < unit.unit_type.hp:
                max_hp_bar_width = self.shape_size
                hp_bar_width = self.shape_size * unit.current_hp // unit.unit_type.hp
                pygame.draw.rect(self.viewer, (255,0,0), (x, y, max_hp_bar_width, self.line_width))
                pygame.draw.rect(self.viewer, (0,255,0), (x, y, hp_bar_width, self.line_width))
            if unit.current_action == "produce":
                target_pos_int = unit.current_action_target
                target_pos_x = target_pos_int % self.gs.width
                target_pos_y = target_pos_int // self.gs.width
                target_x = x_start + target_pos_x * self.shape_size
                target_y = y_start + target_pos_y * self.shape_size
                left_produce_time = unit.execute_current_action_time
                left_time_bar = self.shape_size * left_produce_time // unit.unit_type.produceTime
                pygame.draw.rect(self.viewer, (0,255,0), (target_x, target_y, left_time_bar, self.line_width))
        pygame.display.update()

    def reset(self):
        self.gs = GameState(self.map_path)


if __name__ == "__main__":
    map_path = 'maps\\16x16\\basesWorkers16x16.xml'
    ai1 = AI(0)
    ai2 = AI(1)
    game = Game(map_path)
    step = 0
    start_time = time.time()
    while True:
        step += 1
        action_list1 = ai1.get_random_action_list(game.gs)
        action_list2 = ai2.get_random_action_list(game.gs)
        all_actions = action_list1+action_list2
        done, result = game.step_action_list(all_actions)
        if done:
            print(result)
            print(step)
            print(time.time() - start_time)
            print((time.time() - start_time)/step)
            


        
        

