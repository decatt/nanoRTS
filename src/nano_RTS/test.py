from agent import Agent
from game import Game
import time

if __name__ == "__main__":
    map_path = 'maps\melee4x4light2.xml'
    ai1 = Agent(0)
    ai2 = Agent(1)
    game = Game(map_path)
    start_time = time.time()
    while True:
        game.render()
        action_list1 = ai1.get_random_action_list(game.gs)
        action_list2 = ai2.get_random_action_list(game.gs)
        all_actions = action_list1+action_list2
        game.step_action_list(all_actions)
