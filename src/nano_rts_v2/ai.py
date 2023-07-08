from game import Game
from player import Player
from units import Unit
from action import Action

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