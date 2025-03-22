import random
import numpy as np
import torch
import sys
import os

# Add the project root to the path so we can use absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agent.agent import RummikubAgent
from src.rummikub.CardCollection import Color, CardCollection, CardSequence, CardGroup
from src.solver.ILP import find_moves

# Simplified environment for training
class RummikubEnvironment:
    def __init__(self, num_players=2):
        self.num_players = num_players
        self.reset()
    
    def reset(self):
        """Initialize a new game"""
        # Create a standard Rummikub tile set
        colors = [Color.RED, Color.BLUE, Color.YELLOW, Color.BLACK]
        self.all_tiles = []
        
        # Create 2 sets of tiles from 1-13 in 4 colors
        for _ in range(2):
            for color in colors:
                for number in range(1, 14):
                    self.all_tiles.append((color, number))
        
        # Add jokers (wild tiles)
        self.all_tiles.append((Color.WILD, 0))
        self.all_tiles.append((Color.WILD, 0))
        
        # Shuffle tiles
        random.shuffle(self.all_tiles)
        
        # Deal 14 tiles to each player
        self.player_hands = []
        for _ in range(self.num_players):
            hand = []
            for _ in range(14):
                if self.all_tiles:
                    hand.append(self.all_tiles.pop())
            self.player_hands.append(hand)
        
        # Initialize empty board
        self.board = []
        
        # Current player
        self.current_player = 0
        
        # First move flag for each player (30 points rule)
        self.first_move_made = [False] * self.num_players
        
        return self._get_state()
    
    def _get_state(self):
        """Get the current state for the active player"""
        opponents_tile_counts = [len(hand) for i, hand in enumerate(self.player_hands) 
                               if i != self.current_player]
        
        # Get the agent to encode the state
        return {
            'player_tiles': self.player_hands[self.current_player],
            'board': self.board,
            'opponents_tile_counts': opponents_tile_counts,
            'current_player': self.current_player,
            'first_move_made': self.first_move_made[self.current_player]
        }
    
    def find_valid_moves(self, player_tiles, board):
        """Use the solver to find valid moves"""
        return find_moves(board, player_tiles)
    
    def step(self, action_type, selected_move=None):
        """
        Execute action and return new state, reward, and done flag
        
        Args:
            action_type: 0 for pass, 1 for make a move
            selected_move: The move to make if action_type=1
        """
        player_tiles = self.player_hands[self.current_player]
        
        reward = 0
        
        # Pass action
        if action_type == 0:
            # Draw a tile and pass
            if self.all_tiles:
                player_tiles.append(self.all_tiles.pop())
            reward = -1  # Small penalty for passing
        else:  # Make a move
            if selected_move:
                # Remove the cards played from the player's hand
                cards_to_play = selected_move["cardsToPlay"]
                for card in cards_to_play:
                    if card in player_tiles:
                        player_tiles.remove(card)
                
                # Add the new/modified collection to the board
                collection = selected_move["cardCollection"]
                
                # Check if this is extending an existing collection or creating a new one
                existing_collection = None
                for idx, board_collection in enumerate(self.board):
                    # Check if the cards in board_collection are a subset of the new collection
                    if all(card in collection.cards for card in board_collection.cards):
                        existing_collection = idx
                        break
                
                if existing_collection is not None:
                    # Replace the existing collection
                    self.board[existing_collection] = collection
                else:
                    # Add as a new collection
                    self.board.append(collection)
                
                # Reward based on number of cards played
                reward = 5 * len(cards_to_play)
            else:
                # Invalid move (should never happen if valid moves are properly filtered)
                reward = -10
        
        # Check if the player has won
        done = len(player_tiles) == 0
        if done:
            reward += 100  # Big reward for winning
        
        # Move to next player if not done
        if not done:
            self.current_player = (self.current_player + 1) % self.num_players
        
        return self._get_state(), reward, done

def train_agent(episodes=1000, max_steps=100):
    """Train the Rummikub agent"""
    env = RummikubEnvironment()
    
    # Determine state size from environment
    init_state = env.reset()
    agent = RummikubAgent(
        state_size=65 + 65 + env.num_players - 1,  # Player tiles + board + opponents
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    # Training loop
    for episode in range(episodes):
        state = env.reset()
        encoded_state = agent.encode_state(
            state['player_tiles'], 
            state['board'], 
            state['opponents_tile_counts']
        )
        
        total_reward = 0
        
        for step in range(max_steps):
            # Get valid moves using the solver
            valid_moves = env.find_valid_moves(state['player_tiles'], state['board'])
            
            # Select action
            action_type, selected_move = agent.select_action(encoded_state, valid_moves)
            
            # Take action
            next_state, reward, done = env.step(action_type, selected_move)
            
            # Encode next state
            encoded_next_state = agent.encode_state(
                next_state['player_tiles'], 
                next_state['board'], 
                next_state['opponents_tile_counts']
            )
            
            # Update agent
            agent.update(encoded_state, action_type, selected_move, reward, encoded_next_state, done)
            
            total_reward += reward
            encoded_state = encoded_next_state
            state = next_state
            
            if done:
                break
        
        # Print progress
        if episode % 10 == 0:
            print(f"Episode: {episode}, Total Reward: {total_reward}, Epsilon: {agent.epsilon:.4f}")
        
        # Save model periodically
        if episode % 500 == 0:
            agent.save_model(f"models/rummikub_agent_ep{episode}.pt")
    
    # Save final model
    agent.save_model("models/rummikub_agent_final.pt")
    
    return agent

if __name__ == "__main__":
    train_agent()
