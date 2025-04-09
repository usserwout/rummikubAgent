import sys
from pathlib import Path
from typing import List, Optional
from src.rummikub.Player import Player
from src.rummikub.util import init_cards, visualize_board
from src.rummikub.CardCollection import CardCollection, CardSequence, CardGroup, Card
from src.solver.solver import Solver
from src.rummikub.EventEmitter import event_emitter  # Import our event emitter


class Game:
  board: List[CardCollection]

  def __init__(self, players=4, solver=Solver()):
    self.board = []
    self.current_player = 0
    self.round = 0
    self.solver = solver
    if isinstance(players, int):
      self.player_count = players
      players = [Player(f'Player {i}', self) for i in range(players)]
    else:
      self.player_count = len(players)
    self.players = []
    self.cards = init_cards()  


    self.player_cards = {player.name: [] for player in players}
    self.finished_meld = {player.name: False for player in players}

    for p in players:
      self.players.append(p)
      self.pick_n_cards(p, 14)


  def is_finished(self):
    return any([len(cards) == 0 for cards in self.player_cards.values()]) or len(self.cards) == 0
    
  
  def pick_card(self, player):
    if len(self.cards) == 0:
      raise ValueError('No more cards in the deck')
    card = self.cards.pop()
    self.player_cards[player.name].append(card)
    
    event_emitter.emit('player_move', player.name, "picked a card")
    event_emitter.emit('game_update', self, player.name)

  def pick_n_cards(self, player, n):
    cards = []
    for _ in range(n):
      if len(self.cards) > 0:
        cards.append(self.cards.pop())
    self.player_cards[player.name] += cards
    
    if self.round > 0 and len(cards) > 0:
      event_emitter.emit('player_move', player.name, f"picked {len(cards)} cards")
      event_emitter.emit('game_update', self, player.name)
        
    return cards
  
  def requires_meld(self, player_name:str):
    return not self.finished_meld[player_name]
  
  def get_cards(self, player_name:str) -> List[Card]:
    return self.player_cards[player_name]


  def next_turn(self):
    self.current_player = (self.current_player + 1) % len(self.players)
    if self.current_player == 0:
      self.round += 1
    
    next_player = self.players[self.current_player]
    
    event_emitter.emit('player_move', next_player.name, "is now playing")
    event_emitter.emit('game_update', self, next_player.name)
      
    return next_player  
    
  
  def board_is_valid(self):
    return all([stack.is_valid() for stack in self.board])
  
  def auto_place(self, cards, player:Player=None):
    new_board, new_cards = self.solver.find_best_move(self.board, cards)
    player = self.players[self.current_player] if player is None else player
    if len(new_cards) == len(cards):
      self.pick_card(player)
      self.next_turn()
      return

    self.board = new_board
    cards_played = []
    for c in cards:
      if c not in new_cards:
        cards_played.append(c)
        self.player_cards[player.name].remove(c)
        
    if cards_played:
      event_emitter.emit('player_move', player.name, "played cards automatically", cards_played)
      event_emitter.emit('game_update', self, player.name)


  
        
      
  def get_current_player(self) -> Player: 
    return self.players[self.current_player]
    

  def place(self, cards, stack:CardCollection=None, player=None):
    stack = self.place_cards(cards, stack)
    
    if player is None:
      player = self.players[self.current_player]      
      self.next_turn()
        
    for card in cards:
      self.player_cards[player.name].remove(card)
    
    event_emitter.emit('player_move', player.name, "played cards", cards)
    event_emitter.emit('game_update', self, player.name)
    
    return stack
  
  
  def place_cards(self, cards, stack:CardCollection=None):
    if not isinstance(cards, list):
      cards = [cards]
    
    if stack is None:
      # Add new stack
      if len(cards) < 3:
        raise ValueError('You must place at least 3 cards or add to an existing stack')
      if all([card.number == cards[0].number for card in cards]):
        stack = CardGroup(cards)        
      else:
        stack = CardSequence(cards)
      self.board.append(stack)
    else: 
      for card in cards:
        stack.add_card(card)
        
    return stack
  


  def play(self, verbose=False):

    player_retake = False 

    while not self.is_finished():
      player = self.get_current_player()

      new_board = player.next_move(self)

      if new_board is None:
 
        
        if player_retake:
          self.next_turn()
          player_retake = False
        else: 
          if verbose:
            print(f"{player.name} has no valid moves. Picking a card.")
          self.pick_card(player)
          player_retake = True
        continue

      self.finished_meld[player.name] = True

      player_cards = self.player_cards[player.name]

      cards_played = []
      new_player_cards = player_cards.copy()
      for card_collection in new_board:
        for card in card_collection.cards:
          if card in new_player_cards:
            cards_played.append(card)
            new_player_cards.remove(card)

      if verbose:
        print(f"{player.name} played {len(cards_played)} cards: {[f'{c.color.name}:{c.number}' for c in cards_played]}")    
      self.player_cards[player.name] = new_player_cards

      self.board = new_board
      
      if cards_played:
        event_emitter.emit('player_move', player.name, f"played {len(cards_played)} cards", cards_played)
        event_emitter.emit('game_update', self, player.name)
      
      if verbose:
        self.show()

      if len(self.player_cards[player.name]) == 0:
        winner_message = f"{player.name} has finished the game!"
        print(winner_message)
        
        event_emitter.emit('player_move', player.name, "wins the game!")
        event_emitter.emit('game_update', self, player.name)
          
        return player

      self.next_turn()
      
    return None
    
  
  def show(self):
    visualize_board(self)
    
  
if __name__ == '__main__':
  g = Game()


