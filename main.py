import sys
import os
from pathlib import Path
import argparse
from src.agent.train import train_agent
from src.agent.evaluate import evaluate_agent

# Get project root directory and add to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import your modules
from src.rummikub.Game import Game
from src.rummikub.CardCollection import Color, Card
from src.rummikub.util import visualize_board, visualize_player_hand
from src.solver.ILP import find_moves

def visualize_test():
    g = Game()
    g.place_cards([Card(Color.RED, 1), Card(Color.RED, 2), Card(Color.RED, 3)])
   
    
    
    # Player has BLUE:1, YELLOW:1, BLACK:4, RED:4
    player_cards = [
        Card(Color.RED, 5),Card(Color.WILD, 0)
    ]
        
    new_board = find_moves(g.board, player_cards)
    g.board = new_board
    visualize_board(g)
        


def main():
    parser = argparse.ArgumentParser(description='Train or evaluate a Rummikub agent')
    parser.add_argument('action', choices=['train', 'evaluate'], help='Action to perform')
    parser.add_argument('--model-path', help='Path to model for evaluation', default="models/rummikub_agent_final.pt")
    parser.add_argument('--episodes', type=int, default=1000, help='Number of episodes for training')
    parser.add_argument('--games', type=int, default=100, help='Number of games for evaluation')
    
    args = parser.parse_args()
    
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    if args.action == 'train':
        print(f"Training agent for {args.episodes} episodes...")
        train_agent(episodes=args.episodes)
        print("Training complete.")
    elif args.action == 'evaluate':
        print(f"Evaluating agent using model {args.model_path}...")
        evaluate_agent(args.model_path, num_games=args.games)
        print("Evaluation complete.")

if __name__ == "__main__":
    visualize_test()
