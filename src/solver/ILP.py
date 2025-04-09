from src.rummikub.CardCollection import CardCollection, CardSequence, CardGroup, Color
from pulp import LpMaximize, LpProblem, LpVariable, LpBinary, lpSum, PULP_CBC_CMD
from itertools import combinations

def flatten_board(board):
    """Extract all cards from the board collections."""
    board_cards = []
    for collection in board:
        board_cards.extend(collection.cards)
    return board_cards

def is_valid_sequence(cards):
    nonwild = [c for c in cards if c.color != Color.WILD]
    wild_count = len(cards) - len(nonwild)
    if not nonwild:
        return False
    nums = [c.number for c in nonwild]
    if len(nums) != len(set(nums)):
        return False
    color = nonwild[0].color
    if any(c.color != color for c in nonwild):
        return False
    nums_sorted = sorted(nums)
    missing = sum(nums_sorted[i+1] - nums_sorted[i] - 1 for i in range(len(nums_sorted)-1))
    return missing <= wild_count

def is_valid_group(cards):

    if len(cards) > 4: 
        return False
    nonwild = [c for c in cards if c.color != Color.WILD]
    wild_count = len(cards) - len(nonwild)
    if not nonwild:
        return False
    number = nonwild[0].number
    if any(c.number != number for c in nonwild):
        return False
    if len(set(c.color for c in nonwild)) != len(nonwild):
        return False
    if len(nonwild) + wild_count > 4:
        return False
    return True

def direct_rummikub_solver(player_cards, board_cards, verbose=False):
    if verbose:
        print(f"Player cards: {[f'{c.color.name}:{c.number}' for c in player_cards]}")
        print(f"Board cards: {[f'{c.color.name}:{c.number}' for c in board_cards]}")

    if not player_cards and not board_cards:
        return [], []

    all_cards = player_cards + board_cards
    n = len(all_cards)
    is_player = [i < len(player_cards) for i in range(n)]

    candidates = []   # list of (cand_type, indices, player_count)
    for r in range(3, 6):  
        for indices in combinations(range(n), r):
            candidate_cards = [all_cards[i] for i in indices]
            if is_valid_sequence(candidate_cards):
                player_count = sum(1 for i in indices if is_player[i])
                candidates.append(('sequence', indices, player_count))
            elif is_valid_group(candidate_cards):
                player_count = sum(1 for i in indices if is_player[i])
                candidates.append(('group', indices, player_count))


    model = LpProblem("RummikubSolver", LpMaximize)
    # Use integer indices as keys:
    x = {i: LpVariable(f"cand_{i}", 0, 1, LpBinary) for i, cand in enumerate(candidates)}

    # For each card i, if it is a board card, it must be used exactly once;
    # if it is a player card, it can be used at most once.
    for i in range(n):
        relevant = [x[j] for j in x if i in candidates[j][1]]
        if is_player[i]:
            model += lpSum(relevant) <= 1
        else:
            model += lpSum(relevant) == 1

    # Objective: maximize total number of used player cards
    model += lpSum(x[j] * candidates[j][2] for j in x)

    try:
        status = model.solve(PULP_CBC_CMD(msg=False, timeLimit=30))
        used_candidates = [candidates[j] for j in x if x[j].varValue and x[j].varValue > 0.5]
        solution_seqs = []
        solution_groups = []
        for cand_type, indices, _ in used_candidates:
            cand_cards = [all_cards[i] for i in indices]
            if cand_type == "sequence":
                solution_seqs.append(cand_cards)
                if verbose:
                    print(f"Chosen sequence: {[f'{c.color.name}:{c.number}' for c in cand_cards]}")
            elif cand_type == "group":
                solution_groups.append(cand_cards)
                if verbose:
                    print(f"Chosen group: {[f'{c.color.name}:{c.number}' for c in cand_cards]}")
        return solution_seqs, solution_groups
    except Exception as e:
        print(f"Error solving ILP: {e}")
        return [], []


def merge_sequences(board):
    seq_start_map = {}
    for seq in board:
        if not isinstance(seq, CardSequence):
            continue
        col = seq.get_color()
        if col not in seq_start_map:
            seq_start_map[col] = {} 
        seq_start_map[col][seq.cards[0].number] = seq
        
    for color, seqs in seq_start_map.items():
        
        found_change = True
        while found_change:
            found_change = False
            for seq in seqs.values():
                end_seq = seq.cards[-1].number+1
                if end_seq in seqs:
                    for c in seqs[end_seq].cards:
                        seq.add_card(c)
                    
                    seqs[end_seq].cards = []
                    del seqs[end_seq]
                    found_change = True
                    break
      
    board = [seq for seq in board if len(seq.cards) > 0]
    return board


def find_moves(board: list[CardCollection], player_cards: list[tuple[Color, int]], verbose=False, merge=True):
    """Find all valid moves for a player given the current board."""
    if not player_cards:
        return []
    
    board_cards = flatten_board(board)
    
    solution_seqs, solution_groups = direct_rummikub_solver(player_cards, board_cards)
    
    new_board = []
    for seq in solution_seqs:
        seq.sort(key=lambda x: x.number)
        jokers = [c for c in seq if c.color == Color.WILD]            
        
        # put the wild cards in the right place
        if len(jokers) > 0:
            nonwild = [c for c in seq if c.color != Color.WILD]
            prev = nonwild[0].number
            for card in nonwild:
                if card.number > prev+1:
                    j = jokers.pop()
                    j.number = prev+1
                prev = card.number
            for j in jokers:
                j.number = prev+1
            seq.sort(key=lambda x: x.number)
                
        new_board.append(CardSequence(seq))
    for group in solution_groups:
        new_board.append(CardGroup(group))
        
    if merge:
        new_board = merge_sequences(new_board)
    return new_board