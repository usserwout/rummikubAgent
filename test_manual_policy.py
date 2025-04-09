from src.rummikub.Game import Game
from src.agent.policies.ManualPolicy import ManualPolicy
from src.agent.policies.GreedyPolicy import GreedyPolicy
from src.rummikub.Player import Player

def main():
    # Create a manual policy for human player
    manual_policy = ManualPolicy()
    
    # Create AI players with the GreedyPolicy
    ai_policy = GreedyPolicy()
    
    # Create players
    human_player = Player("Human Player", policy=manual_policy)
    ai_player1 = Player("AI Player 1", policy=ai_policy)
    ai_player2 = Player("AI Player 2", policy=ai_policy)
    
    # Initialize the game with the players
    game = Game([human_player, ai_player1, ai_player2])
    
    # Play the game
    winner = game.play(verbose=True)
    
    if winner:
        print(f"Game finished! Winner: {winner.name}")
    else:
        print("Game finished with no winner.")


if __name__ == "__main__":
    main()