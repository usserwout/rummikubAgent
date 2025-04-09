from src.rummikub.CardCollection import CardCollection, Card
from typing import List
from src.solver.ILP import find_moves

class Solver:
  
  def moves(self,board: List[CardCollection], player_cards: List[Card]) -> List[List[Card]]:
    new_board = find_moves(board, player_cards, merge=False)
    moves = []
    
    for card_collection in new_board:
      seq_moves = [card for card in card_collection.cards if card in player_cards]
      if len(seq_moves) > 0:
        moves.append(seq_moves)
    return moves
  
  def find_best_move(self,board: List[CardCollection], player_cards: List[Card]) -> tuple[List[CardCollection], List[Card]]:    
    new_board = find_moves(board, player_cards)
    
    new_player_cards = player_cards.copy()
    for card_collection in new_board:
      for card in card_collection:
        if card in new_player_cards:
          new_player_cards.remove(card)    
    return new_board, new_player_cards
  
  def get_best_move(self, board: List[CardCollection], player_cards: List[Card]) -> List[CardCollection]:    
    new_board = find_moves(board, player_cards)
    
    return new_board
    
  
  