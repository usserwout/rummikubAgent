from src.rummikub.CardCollection import CardCollection, CardSequence, CardGroup, Color, Card
from pulp import LpMaximize, LpProblem, LpVariable, LpBinary, lpSum, PULP_CBC_CMD, LpInteger
from itertools import combinations, product
import numpy as np
import time

def flatten_board(board):
    """Extract all cards from the board collections."""
    board_cards = []
    for collection in board:
        board_cards.extend(collection.cards)
    return board_cards

def direct_rummikub_solver(player_cards, board_cards):
    """Solve Rummikub using direct ILP modeling without pre-generating combinations."""
    # print(f"Player cards: {[f'{c.color.name}:{c.number}' for c in player_cards]}")
    # print(f"Board cards: {[f'{c.color.name}:{c.number}' for c in board_cards]}")
    
    if not player_cards and not board_cards:
        return [], []
    
    all_cards = player_cards + board_cards
    
    model = LpProblem("RummikubSolver", LpMaximize)
    
    MAX_GROUPS = len(all_cards) // 3 + 1  
    MAX_SEQUENCES = len(all_cards) // 3 + 1  
    
    # 1. Create variables
    
    # Card assignment variables: card i is in sequence j
    seq_assign = {}
    for i, card in enumerate(all_cards):
        for j in range(MAX_SEQUENCES):
            seq_assign[(i, j)] = LpVariable(f"seq_{i}_{j}", 0, 1, LpBinary)
    
    # Card assignment variables: card i is in group j
    group_assign = {}
    for i, card in enumerate(all_cards):
        for j in range(MAX_GROUPS):
            group_assign[(i, j)] = LpVariable(f"group_{i}_{j}", 0, 1, LpBinary)
    
    # variable to indicate if we have the sequence/group
    seq_active = {}
    for j in range(MAX_SEQUENCES):
        seq_active[j] = LpVariable(f"seq_active_{j}", 0, 1, LpBinary)
    
    group_active = {}
    for j in range(MAX_GROUPS):
        group_active[j] = LpVariable(f"group_active_{j}", 0, 1, LpBinary)
    
    # Assign which sequence a certain card belongs to and which place in the sequence. 
    seq_pos = {}
    for i, card in enumerate(all_cards):
        for j in range(MAX_SEQUENCES):
            seq_pos[(i, j)] = LpVariable(f"seq_pos_{i}_{j}", 0, 13, LpInteger)
    
    # 2. Objective: maximize the number of player cards used
    player_indices = [i for i, card in enumerate(all_cards) if card in player_cards]
    model += lpSum([lpSum(seq_assign[(i, j)] for j in range(MAX_SEQUENCES)) + 
                   lpSum(group_assign[(i, j)] for j in range(MAX_GROUPS)) 
                   for i in player_indices])
    
    # 3. Constraints
    
    # Each card can be used at most once
    for i in range(len(all_cards)):
        model += lpSum(seq_assign[(i, j)] for j in range(MAX_SEQUENCES)) + \
                lpSum(group_assign[(i, j)] for j in range(MAX_GROUPS)) <= 1
    
    # All board cards must be used
    board_indices = [i for i, card in enumerate(all_cards) if card in board_cards]
    for i in board_indices:
        model += lpSum(seq_assign[(i, j)] for j in range(MAX_SEQUENCES)) + \
                lpSum(group_assign[(i, j)] for j in range(MAX_GROUPS)) == 1
    
    # Sequence constraints
    for j in range(MAX_SEQUENCES):
        # A sequence must have at least 3 cards
        model += lpSum(seq_assign[(i, j)] for i in range(len(all_cards))) >= 3 * seq_active[j]
        
        # If sequence j is active, it must have cards
        model += lpSum(seq_assign[(i, j)] for i in range(len(all_cards))) <= len(all_cards) * seq_active[j]
        
        # All cards in a sequence must have the same color
        for color in set(card.color for card in all_cards if card.color != Color.WILD):
            color_indices = [i for i, card in enumerate(all_cards) if card.color == color]
            non_color_indices = [i for i, card in enumerate(all_cards) if card.color != color and card.color != Color.WILD]
            
            # If any card of this color is in the sequence, then all cards must be of this color
            if color_indices:
                # Create a variable that indicates if this sequence has this color
                has_color = LpVariable(f"seq_{j}_has_color_{color.name}", 0, 1, LpBinary)
                
                # Link the has_color variable to the actual card assignments
                model += has_color <= lpSum(seq_assign[(i, j)] for i in color_indices)
                model += has_color * len(color_indices) >= lpSum(seq_assign[(i, j)] for i in color_indices)
                
                # If active and has this color, then no cards of other colors can be in this sequence
                if non_color_indices:
                    model += lpSum(seq_assign[(i, j)] for i in non_color_indices) <= len(all_cards) * (1 - has_color)
                
                # Prevent duplicates in sequence - at most one card of each number per sequence per color
                number_groups = {}
                for i, card in enumerate(all_cards):
                    if card.color == color:
                        if card.number not in number_groups:
                            number_groups[card.number] = []
                        number_groups[card.number].append(i)
                
                for number, indices in number_groups.items():
                    if len(indices) > 1:
                        model += lpSum(seq_assign[(i, j)] for i in indices) <= 1
        
        # The numbers in a sequence must be consecutive
        # Each card in the sequence must have a position
        for i, card in enumerate(all_cards):
            if card.color != Color.WILD:
                # Assign the card's position in the sequence to be its number
                model += seq_pos[(i, j)] == card.number * seq_assign[(i, j)]
        
        # For each non-wild card in the sequence, there must be a card at position+1 
        # unless it's the highest number in the sequence
        for i1, card1 in enumerate(all_cards):
            if card1.color != Color.WILD and card1.number < 13:
                # Is there a card at position+1?
                next_pos_filled = LpVariable(f"seq_{j}_next_after_{i1}", 0, 1, LpBinary)
                
                # Connect this variable to the actual card assignments
                # next_pos_filled is 1 if any card is at position card1.number+1
                next_pos_candidates = []
                for i2, card2 in enumerate(all_cards):
                    if card2.number == card1.number + 1 and (card2.color == card1.color or card2.color == Color.WILD):
                        next_pos_candidates.append(i2)
                
                if next_pos_candidates:
                    model += next_pos_filled <= lpSum(seq_assign[(i2, j)] for i2 in next_pos_candidates)
                    model += next_pos_filled * len(next_pos_candidates) >= lpSum(seq_assign[(i2, j)] for i2 in next_pos_candidates)
                
                    # Either card1 is not in the sequence, or next_pos_filled must be 1, or it must be the highest card
                    highest_in_seq = LpVariable(f"seq_{j}_highest_{i1}", 0, 1, LpBinary)
                    model += seq_assign[(i1, j)] <= next_pos_filled + highest_in_seq
                    
                    # highest_in_seq can only be 1 if there are no cards with higher numbers in this sequence
                    higher_numbers = [i2 for i2, card2 in enumerate(all_cards) 
                                     if card2.color == card1.color and card2.number > card1.number]
                    
                    if higher_numbers:
                        model += highest_in_seq <= 1 - lpSum(seq_assign[(i2, j)] for i2 in higher_numbers) / len(higher_numbers)
        
        # Similarly, for each non-wild card in the sequence, there must be a card at position-1
        # unless it's the lowest number in the sequence
        for i1, card1 in enumerate(all_cards):
            if card1.color != Color.WILD and card1.number > 1:
                # Is there a card at position-1?
                prev_pos_filled = LpVariable(f"seq_{j}_prev_before_{i1}", 0, 1, LpBinary)
                
                # Connect this variable to the actual card assignments
                # prev_pos_filled is 1 if any card is at position card1.number-1
                prev_pos_candidates = []
                for i2, card2 in enumerate(all_cards):
                    if card2.number == card1.number - 1 and (card2.color == card1.color or card2.color == Color.WILD):
                        prev_pos_candidates.append(i2)
                
                if prev_pos_candidates:
                    model += prev_pos_filled <= lpSum(seq_assign[(i2, j)] for i2 in prev_pos_candidates)
                    model += prev_pos_filled * len(prev_pos_candidates) >= lpSum(seq_assign[(i2, j)] for i2 in prev_pos_candidates)
                
                    # Either card1 is not in the sequence, or prev_pos_filled must be 1, or it must be the lowest card
                    lowest_in_seq = LpVariable(f"seq_{j}_lowest_{i1}", 0, 1, LpBinary)
                    model += seq_assign[(i1, j)] <= prev_pos_filled + lowest_in_seq
                    
                    # lowest_in_seq can only be 1 if there are no cards with lower numbers in this sequence
                    lower_numbers = [i2 for i2, card2 in enumerate(all_cards) 
                                    if card2.color == card1.color and card2.number < card1.number]
                    
                    if lower_numbers:
                        model += lowest_in_seq <= 1 - lpSum(seq_assign[(i2, j)] for i2 in lower_numbers) / len(lower_numbers)
    
    # Group constraints
    for j in range(MAX_GROUPS):
        # A group must have at least 3 cards
        model += lpSum(group_assign[(i, j)] for i in range(len(all_cards))) >= 3 * group_active[j]
        
        # If group j is active, it must have cards
        model += lpSum(group_assign[(i, j)] for i in range(len(all_cards))) <= len(all_cards) * group_active[j]
        
        # All cards in a group must have the same number
        for number in set(card.number for card in all_cards if card.color != Color.WILD):
            number_indices = [i for i, card in enumerate(all_cards) if card.number == number and card.color != Color.WILD]
            non_number_indices = [i for i, card in enumerate(all_cards) if card.number != number and card.color != Color.WILD]
            
            # Create a variable that indicates if this group is for this number
            has_number = LpVariable(f"group_{j}_has_number_{number}", 0, 1, LpBinary)
            
            # Link the has_number variable to the actual card assignments
            if number_indices:
                model += has_number <= lpSum(group_assign[(i, j)] for i in number_indices)
                model += has_number * len(number_indices) >= lpSum(group_assign[(i, j)] for i in number_indices)
            
                # If group is active and has this number, then no cards of other numbers can be in it
                if non_number_indices:
                    model += lpSum(group_assign[(i, j)] for i in non_number_indices) <= len(all_cards) * (1 - has_number)
        
        # All cards in a group must have different colors
        for color in set(card.color for card in all_cards if card.color != Color.WILD):
            color_indices = [i for i, card in enumerate(all_cards) if card.color == color]
            if color_indices:
                model += lpSum(group_assign[(i, j)] for i in color_indices) <= 1
    
    # 4. Solve the model
    try:
        
        solver = PULP_CBC_CMD(msg=False, timeLimit=30)  # Set a time limit to prevent hanging
        
        status = model.solve(solver)
        
   
        solution_seqs = []
        solution_groups = []
        for j in range(MAX_SEQUENCES):
            if seq_active[j].value() and seq_active[j].value() > 0.5:
                seq_cards = []
                for i, card in enumerate(all_cards):
                    if seq_assign[(i, j)].value() and seq_assign[(i, j)].value() > 0.5:
                        seq_cards.append((card, seq_pos[(i, j)].value()))
                
                # Sort by position and extract just the cards
                seq_cards.sort(key=lambda x: x[1])
                seq = [card[0] for card in seq_cards]
                solution_seqs.append(seq)
                #print(f"Raw sequence from solver: {[f'{c.color.name}:{c.number}' for c in seq]}")
        
        
        for j in range(MAX_GROUPS):
            if group_active[j].value() and group_active[j].value() > 0.5:
                group_cards = []
                for i, card in enumerate(all_cards):
                    if group_assign[(i, j)].value() and group_assign[(i, j)].value() > 0.5:
                        group_cards.append(card)
                
                solution_groups.append(group_cards)
                #print(f"Raw group from solver: {[f'{c.color.name}:{c.number}' for c in group_cards]}")
                

       
        return solution_seqs, solution_groups
    
    except Exception as e:
        print(f"Error solving ILP: {e}")
        return [], []



def find_moves(board: list[CardCollection], player_cards: list[tuple[Color, int]]):
    """Find all valid moves for a player given the current board."""
    if not player_cards:
        return []
    
    board_cards = flatten_board(board)
    
    # Use direct ILP solver
    start_time = time.time()
    solution_seqs, solution_groups = direct_rummikub_solver(player_cards, board_cards)
    print(f"Solved in {time.time() - start_time:.4f} seconds")
    
    new_board = []
    for seq in solution_seqs:
        new_board.append(CardSequence(seq))
    for group in solution_groups:
        new_board.append(CardGroup(group))
    
    return new_board