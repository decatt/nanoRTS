from game_state import GameState
import numpy as np

class Agent:
    def __init__(self, player_id:int):
        self.player_id = player_id
    
    
    def get_action(self, game_state:GameState):
        return (None,None,None,None)
    
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
    
    def get_biased_random_action(self, gs:GameState):
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
        # for an action in all_available_actions if action[1] == 'attack' do it
        for action in all_available_actions:
            if action[1] == 'attack':
                return action
            elif action[1] == 'return':
                return action
            elif action[1] == 'harvest':
                return action
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