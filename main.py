import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rummikub.Game import Game
from src.rummikub.CardCollection import Color, Card
from src.rummikub.util import visualize_board, visualize_player_hand
from src.rummikub.Player import Player
from src.agent.policies.GreedyPolicy import GreedyPolicy
from src.agent.policies.ManualPolicy import ManualPolicy
from src.solver.ILP import find_moves
from src.solver.solver import Solver


def visualize_test():
    g = Game()
    g.place_cards([Card(Color.YELLOW, 7),Card(Color.RED, 7), Card(Color.BLUE, 7)])
    # g.place_cards([Card(Color.BLACK, 6), Card(Color.BLACK, 7), Card(Color.BLACK, 8), Card(Color.BLACK, 9), Card(Color.BLACK, 10)])
    # g.place_cards([Card(Color.YELLOW, 11), Card(Color.BLACK, 11), Card(Color.RED, 11)])
    # Player has BLUE:1, YELLOW:1, BLACK:4, RED:4
    player_cards = [Card(Color.WILD, 0)]
        
    new_board = find_moves(g.board, player_cards)
    g.board = new_board
    visualize_board(g)
        


def train_agent():
    solver = Solver()

    policy = GreedyPolicy()

    players = [Player(f"Me", policy=ManualPolicy(port=5001))]+[Player(f"Player {i+1}", policy=policy) for i in range(3)]

    game = Game(solver=solver, players=players)

    winner = game.play(verbose=True)
    if winner is None:
        print("No winner")
        return
    print(f"Winner: {winner.name}")
 
    


if __name__ == "__main__":
    #visualize_test()
    train_agent()
