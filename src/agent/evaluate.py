import numpy as np
import sys
import os

# Add the project root to the path so we can use absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agent.agent import RummikubAgent
from src.agent.train import RummikubEnvironment

def evaluate_agent(agent_path, num_games=100):
    """
    Evaluate the performance of a trained agent
    
    Args:
        agent_path: Path to the saved agent model
        num_games: Number of games to play for evaluation
        
    Returns:
        Dictionary of performance metrics
    """
    env = RummikubEnvironment()
    
    # Initialize agent
    agent = RummikubAgent(
        state_size=65 + 65 + env.num_players - 1,
        device="cpu"
    )
    
    # Load trained model
    agent.load_model(agent_path)
    
    # Set epsilon to 0 for deterministic policy
    agent.epsilon = 0
    
    # Track metrics
    wins = 0
    total_rewards = []
    steps_to_win = []
    moves_made = []
    passes_made = []
    
    for game in range(num_games):
        state = env.reset()
        encoded_state = agent.encode_state(
            state['player_tiles'], 
            state['board'], 
            state['opponents_tile_counts']
        )
        
        done = False
        total_reward = 0
        step_count = 0
        game_moves = 0
        game_passes = 0
        
        while not done and step_count < 200:  # limit to prevent infinite games
            # Get valid moves using the solver
            valid_moves = env.find_valid_moves(state['player_tiles'], state['board'])
            
            # Select action
            action_type, selected_move = agent.select_action(encoded_state, valid_moves)
            
            # Track action types
            if action_type == 0:
                game_passes += 1
            else:
                game_moves += 1
            
            # Take action
            next_state, reward, done = env.step(action_type, selected_move)
            
            # Encode next state
            encoded_next_state = agent.encode_state(
                next_state['player_tiles'], 
                next_state['board'], 
                next_state['opponents_tile_counts']
            )
            
            total_reward += reward
            encoded_state = encoded_next_state
            state = next_state
            step_count += 1
            
            if done:
                # Check if the agent won
                if len(state['player_tiles']) == 0:
                    wins += 1
                    steps_to_win.append(step_count)
                break
        
        total_rewards.append(total_reward)
        moves_made.append(game_moves)
        passes_made.append(game_passes)
        
        # Print progress
        if (game + 1) % 10 == 0:
            print(f"Evaluated {game + 1}/{num_games} games")
    
    # Calculate metrics
    win_rate = wins / num_games
    avg_reward = np.mean(total_rewards)
    avg_steps = np.mean(steps_to_win) if steps_to_win else 0
    avg_moves = np.mean(moves_made)
    avg_passes = np.mean(passes_made)
    
    metrics = {
        "win_rate": win_rate,
        "average_reward": avg_reward,
        "average_steps_to_win": avg_steps,
        "average_moves_per_game": avg_moves,
        "average_passes_per_game": avg_passes,
        "total_games": num_games
    }
    
    print(f"Evaluation Results:")
    print(f"Win Rate: {win_rate:.2f}")
    print(f"Average Reward: {avg_reward:.2f}")
    print(f"Average Steps to Win: {avg_steps:.2f}")
    print(f"Average Moves Per Game: {avg_moves:.2f}")
    print(f"Average Passes Per Game: {avg_passes:.2f}")
    
    return metrics

if __name__ == "__main__":
    evaluate_agent("models/rummikub_agent_final.pt")
