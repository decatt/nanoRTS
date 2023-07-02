from agent import Agent
from game import Game

if __name__ == "__main__":
    map_path = 'maps\EightBasesWorkers16x12.xml'
    ai1 = Agent(0)
    ai2 = Agent(1)
    game = Game(map_path)
    num_draw = 0
    num_win1 = 0
    num_win2 = 0
    for _ in range(1000):
        while True:
            action_list1 = ai1.get_random_action_list(game.gs)
            action_list2 = ai2.get_random_action_list(game.gs)
            all_actions = action_list1+action_list2
            game.step_action_list(all_actions)
            if game.gs.game_result() is not None:
                result = game.gs.game_result()
                if result == 'draw':
                    num_draw += 1
                elif result == 'player0':
                    num_win1 += 1
                elif result == 'player1':
                    num_win2 += 1
                print('player0 win: ', num_win1)
                print('player1 win: ', num_win2)
                print('draw: ', num_draw)
                break
        game.reset()