from agent import AI, WorkerRush, LightRushAI
from path_finding import BFS
from game import Game
import time

if __name__ == "__main__":
    map_path = 'maps\\16x16\\basesWorkers16x16.xml'
    #ai1 = WorkerRush(0, 16, 16)
    all_sample_actions = []
    ai1 = AI(0)
    ai2 = LightRushAI(1, 16, 16, BFS)
    game = Game(map_path)
    start_time = time.time()
    while True:
        #game.render()
        #action_list1 = ai1.get_action_list(game.gs)
        action_list1 = ai1.get_random_action_list(game.gs)
        action_list2 = ai2.get_action_list(game.gs)
        all_actions = action_list1+action_list2
        game.step_action_list(all_actions)
        all_sample_actions.extend(all_actions)
        if len(all_sample_actions) > 32*512:
            break
    print(time.time() - start_time)
    print((time.time() - start_time)/len(all_sample_actions))