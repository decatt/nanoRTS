from game_state import GameState
from units import Unit, UnitType, load_unit_types
from pos import Pos, int_pos_to_pos
from agent import AI
import numpy as np
import pygame
import time

class Game:
    def __init__(self, map_path:str, max_steps:int = 1000):
        self.gs = GameState(map_path)
        self.map_path = map_path
        self.max_steps = max_steps

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
            if unit_id is None:
                continue
            if unit_id not in list(self.gs.units.keys()):
                continue
            if self.gs.units[unit_id].current_action is not None:
                continue
            if target_pos is None:
                continue
            if target_pos < 0 or target_pos>=self.gs.width*self.gs.height:
                continue
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
        r, result, game_time = self.gs.update()
        done = False
        if game_time >= self.max_steps:
            done = True
            self.reset()
        if result is not None:
            self.reset()
            done = True
            if result == "player0":
                r += 10
        return r, done, result
    
    def step_action(self, action_list):
        r = 0
        for action in action_list:
            unit_id, action_type, target_pos, produce_type = action
            if unit_id is None:
                continue
            if unit_id not in list(self.gs.units.keys()):
                continue
            if self.gs.units[unit_id].current_action is not None:
                continue
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
        while self.gs.get_player_available_units(0) == []:
            r += self.gs.update()
            result = self.gs.game_result()
            if result is not None:
                self.reset()
                if result == "player0":
                    r += 10
                return r, True, result
        return r, False, None
        
        

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

    #1 NOOP, move, harvest, return, produce, attack
    #2 move: up, right, down, left
    #3 harvest: up, right, down, left
    #4 return: up, right, down, left
    #5 produce: up, right, down, left
    #6 produce_type: resource, base, barracks, worker, light, heavy, ranged
    #7 attack_pos: 1~7*7
    def vector_to_action(self, vector):
        unit_pos_int = vector[0]
        unit_pos = int_pos_to_pos(unit_pos_int, self.gs.width)
        unit_id = None
        next_pos = [unit_pos_int-self.gs.width, unit_pos_int+1, unit_pos_int+self.gs.width, unit_pos_int-1]
        if unit_pos_int in list(self.gs.units_pos.keys()):
            unit = self.gs.units_pos[unit_pos_int]
            unit_id = unit.unit_id
        dir = None
        produce_type = None
        target_pos = None
        if vector[1] == 1:
            unit_action_type = 'move'
            target_pos = next_pos[vector[2]]
        elif vector[1] == 2:
            unit_action_type = 'harvest'
            target_pos = next_pos[vector[3]]
        elif vector[1] == 3:
            unit_action_type = 'return'
            target_pos = next_pos[vector[4]]
        elif vector[1] == 4:
            unit_action_type = 'produce'
            target_pos = next_pos[vector[5]]
            if vector[6] == 0:
                produce_type = 'Resource'
            elif vector[6] == 1:
                produce_type = 'Base'
            elif vector[6] == 2:
                produce_type = 'Barracks'
            elif vector[6] == 3:
                produce_type = 'Worker'
            elif vector[6] == 4:
                produce_type = 'Light'
            elif vector[6] == 5:
                produce_type = 'Heavy'
            elif vector[6] == 6:
                produce_type = 'Ranged'
        elif vector[1] == 5:
            unit_action_type = 'attack'
        else:
            unit_action_type = 'NOOP'

        if unit_action_type == 'attack':
            atk_x = vector[6] % 7 - 3
            atk_y = vector[6] // 7 - 3
            target_pos = (unit_pos + Pos(atk_x, atk_y)).int_pos
        return (unit_id, unit_action_type, target_pos, produce_type)


if __name__ == "__main__":
    map_path = 'maps\\16x16\\basesWorkers16x16.xml'
    ai1 = AI(0)
    ai2 = AI(1)
    game = Game(map_path)
    step = 0
    start_time = time.time()
    while True:
        game.render()
        step += 1
        action_list1 = ai1.get_random_action_list(game.gs)
        action_list2 = ai2.get_random_action_list(game.gs)
        all_actions = action_list1+action_list2
        done, result, _ = game.step_action_list(all_actions)
        if done:
            print(result)
            print(step)
            print(time.time() - start_time)
            print((time.time() - start_time)/step)
            


        
        

