import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from collections import deque, namedtuple
from ..rummikub.CardCollection import Color, CardCollection, CardSequence, CardGroup

# Define constants for the agent
BATCH_SIZE = 64
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.1
EPSILON_DECAY = 0.995
LEARNING_RATE = 0.001
MEMORY_SIZE = 10000
TARGET_UPDATE = 10

# Define Experience tuple for replay buffer
Experience = namedtuple('Experience', ('state', 'action', 'reward', 'next_state', 'done'))

class RummikubDQN(nn.Module):
    def __init__(self, state_size, action_size):
        super(RummikubDQN, self).__init__()
        # Network architecture
        self.fc1 = nn.Linear(state_size, 256)
        self.fc2 = nn.Linear(256, 256)
        self.fc3 = nn.Linear(256, action_size)
        
    def forward(self, state):
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        return self.fc3(x)  # Q-values for each action

class ReplayBuffer:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)
        
    def push(self, *args):
        self.memory.append(Experience(*args))
        
    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)
    
    def __len__(self):
        return len(self.memory)

class RummikubAgent:
    def __init__(self, state_size, device='cpu'):
        self.state_size = state_size
        self.device = device
        self.epsilon = EPSILON_START
        
        # The action size will be 2 - representing "make a move" (1) or "pass" (0)
        self.action_size = 2
        
        # Q Networks (policy and target)
        self.policy_net = RummikubDQN(state_size, self.action_size).to(device)
        self.target_net = RummikubDQN(state_size, self.action_size).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=LEARNING_RATE)
        
        # Replay memory
        self.memory = ReplayBuffer(MEMORY_SIZE)
        
        # Training step counter
        self.steps_done = 0
        
        # For move selection when action=1 (make a move)
        self.move_selection_model = MoveSelectionDQN(state_size + 20).to(device)  # +20 for move features
        self.move_optimizer = optim.Adam(self.move_selection_model.parameters(), lr=LEARNING_RATE)
        
    def select_action(self, state, valid_moves):
        """
        Select whether to make a move or pass
        
        Args:
            state: Current state tensor
            valid_moves: List of valid moves from the solver
            
        Returns:
            Tuple of (action_type, selected_move)
            - action_type: 0 for pass, 1 for make a move
            - selected_move: The move object if action_type=1, None otherwise
        """
        sample = random.random()
        
        # First decide whether to make a move or pass
        if sample > self.epsilon:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                action_type = q_values.max(1)[1].item()
        else:
            action_type = random.randint(0, 1)
        
        # If we decide to make a move and there are valid moves available
        selected_move = None
        if action_type == 1 and valid_moves:
            # Use the move selection model to choose which move to make
            selected_move = self.select_best_move(state, valid_moves)
        else:
            action_type = 0  # Force to pass if no valid moves
            
        return action_type, selected_move
    
    def select_best_move(self, state, valid_moves):
        """
        Select the best move from a list of valid moves
        
        Args:
            state: Current state tensor
            valid_moves: List of valid moves from the solver
            
        Returns:
            Selected move object
        """
        if not valid_moves:
            return None
            
        if random.random() < self.epsilon:
            return random.choice(valid_moves)
            
        # Encode state and moves together
        move_values = []
        state_tensor = torch.FloatTensor(state).to(self.device)
        
        with torch.no_grad():
            for move in valid_moves:
                # Encode the move into a feature vector
                move_features = self.encode_move(move)
                move_tensor = torch.FloatTensor(move_features).to(self.device)
                
                # Combine state and move features
                combined = torch.cat((state_tensor, move_tensor))
                
                # Get Q-value for this state-move pair
                q_value = self.move_selection_model(combined.unsqueeze(0))
                move_values.append(q_value.item())
        
        # Select the move with highest Q-value
        best_move_idx = np.argmax(move_values)
        return valid_moves[best_move_idx]
    
    def encode_move(self, move):
        """
        Encode a move into a feature vector
        
        Args:
            move: A move object from the solver
            
        Returns:
            Feature vector representing the move
        """
        # Extract features that might be relevant for evaluating a move
        # For example:
        # - Number of cards being played
        # - Sum of card values
        # - Is it adding to existing collection or creating new one
        # - etc.
        cards_to_play = move["cardsToPlay"]
        card_collection = move["cardCollection"]
        
        # Initialize feature vector (20 features)
        features = np.zeros(20)
        
        # Number of cards being played
        features[0] = len(cards_to_play)
        
        # Sum of card values
        features[1] = sum(card[1] for card in cards_to_play if card[0] != Color.WILD)
        
        # Type of collection (0 for sequence, 1 for group)
        features[2] = 1 if isinstance(card_collection, CardGroup) else 0
        
        # Number of cards in the resulting collection
        features[3] = len(card_collection.cards)
        
        # Number of wild cards in the play
        features[4] = sum(1 for card in cards_to_play if card[0] == Color.WILD)
        
        # Return normalized features
        return features
            
    def encode_state(self, player_tiles, board, opponents_tile_counts):
        """
        Encode the game state into a fixed-size vector
        
        Args:
            player_tiles: List of player's tiles as (Color, number) tuples
            board: List of CardCollection objects on the table
            opponents_tile_counts: List of tile counts for opponents
            
        Returns:
            Encoded state vector
        """
        # Encode player tiles (13x5 one-hot encoding: 13 numbers, 5 colors)
        player_tiles_encoding = np.zeros((13, 5))
        for color, number in player_tiles:
            color_idx = [c.value for c in Color].index(color.value)
            player_tiles_encoding[number-1, color_idx] = 1
        
        # Encode board state (simplified: count of each tile on board)
        board_encoding = np.zeros((13, 5))
        for collection in board:
            for color, number in collection.cards:
                if color != Color.WILD:  # Handle wilds separately
                    color_idx = [c.value for c in Color].index(color.value)
                    board_encoding[number-1, color_idx] = 1
        
        # Opponents' tile counts
        opponents_encoding = np.array(opponents_tile_counts)
        
        # Combine all encodings
        state = np.concatenate([
            player_tiles_encoding.flatten(),
            board_encoding.flatten(),
            opponents_encoding
        ])
        
        return state
        
    def optimize_model(self):
        """Train the model with a batch from replay memory"""
        if len(self.memory) < BATCH_SIZE:
            return
        
        experiences = self.memory.sample(BATCH_SIZE)
        batch = Experience(*zip(*experiences))
        
        # Convert to tensors - properly convert numpy arrays first
        states = np.array(batch.state)
        next_states = np.array(batch.next_state)
        
        state_batch = torch.FloatTensor(states).to(self.device)
        action_batch = torch.LongTensor(batch.action).unsqueeze(1).to(self.device)
        reward_batch = torch.FloatTensor(batch.reward).to(self.device)
        next_state_batch = torch.FloatTensor(next_states).to(self.device)
        done_batch = torch.FloatTensor(batch.done).to(self.device)
        
        # Compute Q(s_t, a) - the model computes Q(s_t), then we select the columns of actions taken
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)
        
        # Compute V(s_{t+1}) for all next states
        next_state_values = torch.zeros(BATCH_SIZE, device=self.device)
        next_state_values = self.target_net(next_state_batch).max(1)[0].detach()
        
        # Compute the expected Q values
        expected_state_action_values = reward_batch + (GAMMA * next_state_values * (1 - done_batch))
        
        # Compute Huber loss
        loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))
        
        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        # Clip gradients to stabilize training
        for param in self.policy_net.parameters():
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step()
        
    def optimize_move_selection(self, state, move, reward, next_state, done):
        """
        Train the move selection model
        
        Args:
            state: State tensor
            move: Selected move object
            reward: Reward received
            next_state: Next state tensor
            done: Whether the episode is done
        """
        if move is None:
            return  # Skip optimization if no move was made
            
        # Encode the move
        move_features = self.encode_move(move)
        
        # Convert to tensors
        state_tensor = torch.FloatTensor(state).to(self.device)
        move_tensor = torch.FloatTensor(move_features).to(self.device)
        next_state_tensor = torch.FloatTensor(next_state).to(self.device)
        reward_tensor = torch.FloatTensor([reward]).to(self.device)
        done_tensor = torch.FloatTensor([done]).to(self.device)
        
        # Combine state and move
        combined = torch.cat((state_tensor, move_tensor)).unsqueeze(0)
        
        # Compute current Q value
        current_q = self.move_selection_model(combined)
        
        # Compute target Q value (simplified - just use reward for now)
        target_q = reward_tensor
        
        # If not done, add discounted future rewards (assuming best future move)
        if not done:
            # This is simplified - ideally would use target network
            # and evaluate all possible next moves
            target_q += GAMMA * 10  # Placeholder for future rewards
            
        # Compute loss
        loss = F.smooth_l1_loss(current_q, target_q.unsqueeze(0))
        
        # Optimize
        self.move_optimizer.zero_grad()
        loss.backward()
        # Clip gradients
        for param in self.move_selection_model.parameters():
            param.grad.data.clamp_(-1, 1)
        self.move_optimizer.step()
    
    def update(self, state, action_type, move, reward, next_state, done):
        """
        Update both models with a transition
        
        Args:
            state: Current state tensor
            action_type: 0 for pass, 1 for make a move
            move: Selected move object (if action_type=1)
            reward: Reward received
            next_state: Next state tensor
            done: Whether the episode is done
        """
        # Update main decision model
        self.memory.push(state, action_type, reward, next_state, done)
        self.optimize_model()
        
        # Update move selection model if a move was made
        if action_type == 1:
            self.optimize_move_selection(state, move, reward, next_state, done)
        
        self.steps_done += 1
        if self.steps_done % TARGET_UPDATE == 0:
            self.update_target_network()
            self.decay_epsilon()
    
    def update_target_network(self):
        """Update the target network with the policy network weights"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def decay_epsilon(self):
        """Decay exploration rate"""
        self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)
    
    def save_model(self, path):
        """Save the model weights"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps_done': self.steps_done
        }, path)
    
    def load_model(self, path):
        """Load the model weights"""
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
        self.steps_done = checkpoint['steps_done']

# Additional model for selecting which move to make
class MoveSelectionDQN(nn.Module):
    def __init__(self, input_size):
        super(MoveSelectionDQN, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 1)  # Output a single Q-value for the move
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)
