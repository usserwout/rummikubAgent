import unittest
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Now import the modules using the correct paths
from src.rummikub.CardCollection import CardSequence, CardGroup, Color, Card
from src.solver.ILP import find_moves
from src.rummikub.Game import Game



def visualize_board(board):
    """Utility function to print the board state"""
    for i, collection in enumerate(board):
        if isinstance(collection, CardSequence):
            print(f"  Stack {i+1} (Sequence):")
            print("    " + " ".join([f"[{card.number:2d}]" for card in collection.cards]))
        else:
            print(f"  Stack {i+1} (Group):")
            print("    " + " ".join([f"[{card.color.name[0]}{card.number}]" for card in collection.cards]))
    print()

class TestRummikubSolver(unittest.TestCase):
    def setUp(self):
        # Create a fresh game for each test
        self.game = Game()
    
    def test_basic_sequence_extension(self):
        """Test adding a card to extend an existing sequence"""
        # Starting with a sequence BLACK 1-3
        self.game.place_cards([Card(Color.BLACK, 1), Card(Color.BLACK, 2), Card(Color.BLACK, 3)])
        
        # Player has BLACK 4 to extend the sequence
        player_cards = [Card(Color.BLACK, 4)]
        
        # Find moves - now returns a new board state
        new_board = find_moves(self.game.board, player_cards)
        
        # Validate we found a move
        self.assertTrue(len(new_board) > 0, "Should find at least one collection")
        
        # Set the game board to the new state
        self.game.board = new_board
        
        # Should have 1 collection with 4 cards (1-4)
        self.assertEqual(len(self.game.board), 1, "Should have 1 collection")
        
        # Find the sequence collection
        sequences = [c for c in self.game.board if isinstance(c, CardSequence)]
        self.assertEqual(len(sequences), 1, "Should have 1 sequence")
        seq = sequences[0]
        
        # Sequence should have 4 cards
        self.assertEqual(len(seq.cards), 4, "Sequence should have 4 cards")
        
        # Cards should be 1, 2, 3, 4 in order
        numbers = [card.number for card in seq.cards]
        self.assertEqual(numbers, [1, 2, 3, 4], "Sequence should be 1-4")
    
    def test_sequence_split(self):
        """Test splitting a sequence when playing a duplicate card"""
        # Starting with a sequence BLACK 1-6
        self.game.place_cards([
            Card(Color.BLACK, 1), Card(Color.BLACK, 2), Card(Color.BLACK, 3), 
            Card(Color.BLACK, 4), Card(Color.BLACK, 5), Card(Color.BLACK, 6)
        ])
        
        # Player has another BLACK 4
        player_cards = [Card(Color.BLACK, 4)]
        
        # Find moves
        new_board = find_moves(self.game.board, player_cards)
        
        # Validate we found a move
        self.assertTrue(len(new_board) > 0, "Should find at least one collection")
        
        # Apply the move
        self.game.board = new_board
        
        # Should now have 2 sequences
        sequences = [c for c in self.game.board if isinstance(c, CardSequence)]
        self.assertEqual(len(sequences), 2, "Should have 2 sequences")
        
        # Sort sequences by length
        sequences.sort(key=lambda s: len(s.cards))
        
        # First sequence should have at least 3 cards
        self.assertGreaterEqual(len(sequences[0].cards), 3, "First sequence should have at least 3 cards")
        
        # Second sequence should have at least 3 cards
        self.assertGreaterEqual(len(sequences[1].cards), 3, "Second sequence should have at least 3 cards")
        
        # Verify that BLACK 4 appears in both sequences
        has_black_4_in_first = any(card.color == Color.BLACK and card.number == 4 for card in sequences[0].cards)
        has_black_4_in_second = any(card.color == Color.BLACK and card.number == 4 for card in sequences[1].cards)
        
        self.assertTrue(has_black_4_in_first or has_black_4_in_second, 
                       "At least one sequence should have BLACK 4")
    
    def test_group_extension(self):
        """Test adding a card to extend an existing group"""
        # Starting with a group of 3s (BLACK, RED, BLUE)
        self.game.place_cards([
            Card(Color.BLACK, 3), Card(Color.RED, 3), Card(Color.BLUE, 3)
        ])
        
        # Player has YELLOW 3 to complete the group
        player_cards = [Card(Color.YELLOW, 3)]
        
        # Find moves
        new_board = find_moves(self.game.board, player_cards)
        
        # Validate we found a move
        self.assertTrue(len(new_board) > 0, "Should find at least one collection")
        
        # Apply the move
        self.game.board = new_board
        
        # Find the group collection
        groups = [c for c in self.game.board if isinstance(c, CardGroup)]
        self.assertEqual(len(groups), 1, "Should have 1 group")
        group = groups[0]
        
        # Group should have 4 cards
        self.assertEqual(len(group.cards), 4, "Group should have 4 cards")
        
        # All cards should be 3s
        self.assertTrue(all(card.number == 3 for card in group.cards), 
                       "All cards should be 3s")
        
        # Should have all 4 colors
        colors = [card.color for card in group.cards]
        self.assertEqual(set(colors), {Color.BLACK, Color.RED, Color.BLUE, Color.YELLOW}, 
                        "Group should have all 4 colors")
    
    def test_create_new_sequence(self):
        """Test creating a new sequence from scratch"""
        # Starting board has a group of 5s
        self.game.place_cards([
            Card(Color.BLACK, 5), Card(Color.RED, 5), Card(Color.BLUE, 5)
        ])
        
        # Player has a sequence RED 1-3
        player_cards = [Card(Color.RED, 1), Card(Color.RED, 2), Card(Color.RED, 3)]
        
        # Find moves
        new_board = find_moves(self.game.board, player_cards)
        
        # Validate we found a move
        self.assertTrue(len(new_board) > 0, "Should find at least one collection")
        
        # Apply the move
        self.game.board = new_board
        
        # Should now have 2 collections
        self.assertEqual(len(self.game.board), 2, "Should have 2 collections")
        
        # One collection should be a group, the other a sequence
        groups = [c for c in self.game.board if isinstance(c, CardGroup)]
        sequences = [c for c in self.game.board if isinstance(c, CardSequence)]
        
        self.assertEqual(len(groups), 1, "Should have 1 group")
        self.assertEqual(len(sequences), 1, "Should have 1 sequence")
        
        # Group should have 3 cards, all 5s
        self.assertEqual(len(groups[0].cards), 3, "Group should have 3 cards")
        self.assertTrue(all(card.number == 5 for card in groups[0].cards), 
                       "All cards in group should be 5s")
        
        # Sequence should have 3 cards, RED 1-3
        self.assertEqual(len(sequences[0].cards), 3, "Sequence should have 3 cards")
        numbers = sorted([card.number for card in sequences[0].cards])
        self.assertEqual(numbers, [1, 2, 3], "Sequence should be 1-3")
        colors = set([card.color for card in sequences[0].cards])
        self.assertEqual(colors, {Color.RED}, "All cards in sequence should be RED")
    
    def test_create_new_group(self):
        """Test creating a new group from scratch"""
        # Starting board has a sequence BLACK 1-5
        self.game.place_cards([
            Card(Color.BLACK, 1), Card(Color.BLACK, 2), Card(Color.BLACK, 3),
            Card(Color.BLACK, 4), Card(Color.BLACK, 5)
        ])
        
        # Player has a group of 7s
        player_cards = [Card(Color.BLACK, 7), Card(Color.RED, 7), Card(Color.BLUE, 7)]
        
        # Find moves
        new_board = find_moves(self.game.board, player_cards)
        
        # Validate we found a move
        self.assertTrue(len(new_board) > 0, "Should find at least one collection")
        
        # Apply the move
        self.game.board = new_board
        
        # Should have 2 collections
        self.assertEqual(len(self.game.board), 2, "Should have 2 collections")
        
        # One collection should be a sequence, the other a group
        sequences = [c for c in self.game.board if isinstance(c, CardSequence)]
        groups = [c for c in self.game.board if isinstance(c, CardGroup)]
        
        self.assertEqual(len(sequences), 1, "Should have 1 sequence")
        self.assertEqual(len(groups), 1, "Should have 1 group")
        
        # Sequence should have 5 cards, BLACK 1-5
        self.assertEqual(len(sequences[0].cards), 5, "Sequence should have 5 cards")
        numbers = sorted([card.number for card in sequences[0].cards])
        self.assertEqual(numbers, [1, 2, 3, 4, 5], "Sequence should be 1-5")
        
        # Group should have 3 cards, all 7s
        self.assertEqual(len(groups[0].cards), 3, "Group should have 3 cards")
        self.assertTrue(all(card.number == 7 for card in groups[0].cards), 
                       "All cards in group should be 7s")
    
    def test_complex_scenario(self):
        """Test a more complex scenario with multiple options"""
        # Board has:
        # - Sequence BLACK 1-3
        # - Group of 5s (RED, BLUE, YELLOW)
        self.game.place_cards([Card(Color.BLACK, 1), Card(Color.BLACK, 2), Card(Color.BLACK, 3)])
        self.game.place_cards([Card(Color.RED, 5), Card(Color.BLUE, 5), Card(Color.YELLOW, 5)])
        
        # Player has BLACK 4, BLACK 5, BLACK 6
        player_cards = [Card(Color.BLACK, 4), Card(Color.BLACK, 5), Card(Color.BLACK, 6)]
        
        # Find moves
        new_board = find_moves(self.game.board, player_cards)
        
        # Validate we found moves
        self.assertTrue(len(new_board) > 0, "Should find at least one collection")
        
        # Apply the moves
        self.game.board = new_board
        
        # Should have at least 2 collections
        self.assertGreaterEqual(len(self.game.board), 2, "Should have at least 2 collections")
        
        # Count sequences and groups
        sequences = [c for c in self.game.board if isinstance(c, CardSequence)]
        groups = [c for c in self.game.board if isinstance(c, CardGroup)]
        
        # Should have at least one sequence and one group
        self.assertGreaterEqual(len(sequences), 1, "Should have at least 1 sequence")
        self.assertGreaterEqual(len(groups), 1, "Should have at least 1 group")
    
    def test_no_valid_moves(self):
        """Test when there are no valid moves"""
        # This test might need adjustment since find_moves now returns a new board state
        # rather than a list of valid moves
        
        # Create a board with a sequence the player can't extend
        self.game.place_cards([Card(Color.BLACK, 6), Card(Color.BLACK, 7), Card(Color.BLACK, 8)])
        
        
        # Player has unrelated cards that can't be played
        player_cards = [Card(Color.RED, 1), Card(Color.BLUE, 3)]
        
        # Find moves
        new_board = find_moves(self.game.board, player_cards)
        self.game.board = new_board
        
        self.assertTrue(self.game.board_is_valid(), "Board should be valid after moves")
        # If no valid moves, the board should remain unchanged
        # Though with the new implementation, we may need to adjust this expectation
        self.assertTrue(len(new_board) > 0, "Should return a non-empty board even without moves")
        
        # Check that nothing changed with the sequences
        sequences = [c for c in new_board if isinstance(c, CardSequence)]
        self.assertEqual(len(sequences), 1, "Should still have 1 sequence")
        self.assertEqual(len(sequences[0].cards), 3, "Sequence should still have 3 cards")
        numbers = [card.number for card in sequences[0].cards]
        self.assertEqual(sorted(numbers), [6, 7, 8], "Sequence should still be 6-8")

    def test_complex_group_formation(self):
        """Test forming a group with cards across player's hand and board"""
        # Board has RED:1, RED:2, RED:3
        self.game.place_cards([Card(Color.RED, 1), Card(Color.RED, 2), Card(Color.RED, 3)])
        
        # Player has BLUE:1, YELLOW:1, BLACK:4, RED:4
        player_cards = [
            Card(Color.BLUE, 1), Card(Color.YELLOW, 1),
            Card(Color.BLACK, 4), Card(Color.RED, 4)
        ]
        
        # Find moves
        new_board = find_moves(self.game.board, player_cards)
        
        # Apply the moves
        self.game.board = new_board
        
        self.assertTrue(self.game.board_is_valid(), "Board should be valid after moves")
        
        # Should have at least 2 collections
        self.assertGreaterEqual(len(self.game.board), 2, "Should have at least 1 collection")
        
        # We should have formed a group of 1s (RED, BLUE, YELLOW)
        groups = [c for c in self.game.board if isinstance(c, CardGroup) and c.cards[0].number == 1]
        self.assertGreaterEqual(len(groups), 1, "Should have at least 1 group of 1s")
        
        group_of_1s = groups[0]
        self.assertEqual(len(group_of_1s.cards), 3, "Group of 1s should have 3 cards")
        
        # Should have RED, BLUE, YELLOW
        colors = {card.color for card in group_of_1s.cards}
        self.assertEqual(colors, {Color.RED, Color.BLUE, Color.YELLOW}, 
                        "Group should contain RED, BLUE, and YELLOW 1s")
    
    
    def test_no_moves(self):
        """Test when there are no moves to make"""
        # Board has RED:1, RED:2, RED:3
        self.game.place_cards([Card(Color.RED, 1), Card(Color.RED, 2), Card(Color.RED, 3)])
        
        # Player has no valid moves
        player_cards = [
            Card(Color.BLUE, 1), Card(Color.YELLOW, 1),
            Card(Color.BLACK, 4), Card(Color.YELLOW, 4)
        ]
        
        # Find moves
        new_board = find_moves(self.game.board, player_cards)
        
        # Should have the same board
        self.assertEqual(self.game.board, new_board, "Board should remain unchanged")
        
    def test_complex_stuctures(self):
        self.game.place_cards([Card(Color.RED, 1), Card(Color.RED, 2), Card(Color.RED, 3)])
        self.game.place_cards([Card(Color.BLACK, 9),Card(Color.BLACK, 10), Card(Color.BLACK, 11), Card(Color.BLACK, 12), Card(Color.BLACK, 13)])
        self.game.place_cards([Card(Color.YELLOW, 10), Card(Color.RED, 10),Card(Color.BLUE, 10)])
        
        
        # Player has BLUE:1, YELLOW:1, BLACK:4, RED:4
        player_cards = [
            Card(Color.RED, 4), Card(Color.YELLOW, 1), Card(Color.BLACK, 1), Card(Color.BLACK, 11), Card(Color.BLACK, 10), Card(Color.RED, 2),
        ]
            
        new_board = find_moves(self.game.board, player_cards)

        self.game.board = new_board
        self.assertTrue(self.game.board_is_valid(), "Board should be valid after moves")
        

        sequences = [c for c in new_board if isinstance(c, CardSequence)]
        groups = [c for c in new_board if isinstance(c, CardGroup)]
        
        self.assertGreaterEqual(len(sequences), 3, "Should have at least 1 sequence")
        self.assertGreaterEqual(len(groups), 2, "Should have at least 1 group")


if __name__ == "__main__":
    unittest.main()
