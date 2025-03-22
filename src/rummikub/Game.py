# Check if this module is run directly, and fix imports accordingly
if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Add the project root to the Python path
    project_root = Path(__file__).resolve().parents[2]  # Go up 2 levels (src/rummikub → project root)
    sys.path.insert(0, str(project_root))
    
    # Use absolute imports when run directly
    from src.rummikub.Player import Player
    from src.rummikub.util import init_cards, visualize_board
    from src.rummikub.CardCollection import CardCollection, CardSequence, CardGroup, Color
else:
    # Use relative imports when imported as a module
    from .Player import Player
    from .util import init_cards, visualize_board
    from .CardCollection import CardCollection, CardSequence, CardGroup, Color

class Game:
  def __init__(self, players=4):
    
    self.players = []
    self.cards = init_cards()  
    for i in range(players):
      p = Player(f'Player {i}')
      self.players.append(p)
      self.pick_n_cards(p, 14)

    self.board = []
    self.current_player = 0
    self.round = 0




  def finished(self):
    return any([len(player.cards) == 0 for player in self.players])
    
  
  def pick_card(self, player):
    card = self.cards.pop()
    player.cards.append(card)

  def pick_n_cards(self, player, n):
    cards = []
    for _ in range(n):
      cards.append(self.cards.pop())
    player.cards += cards
    return cards


  def next(self):
    self.current_player = (self.current_player + 1) % len(self.players)
    if self.current_player == 0:
      self.round += 1
    return self.players[self.current_player]    
    
  
  def board_is_valid(self):
    return all([stack.is_valid() for stack in self.board])
  

  def place(self, cards,  stack:CardCollection=None, player=None):
    stack = self.place_cards(cards, stack)
    
    if player is None:
      player = self.players[self.current_player]      
      self.next()
        
    for card in cards:
      player.cards.remove(card)    
    
    return stack
  
  
  def place_cards(self, cards, stack:CardCollection=None):
    if not isinstance(cards, list):
      cards = [cards]
    
    if stack is None:
      # Add new stack
      if len(cards) < 3:
        raise ValueError('You must place at least 3 cards or add to an existing stack')
      if all([card[1] == cards[0][1] for card in cards]):
        stack = CardGroup(cards)        
      else:
        stack = CardSequence(cards)
      self.board.append(stack)
    else: 
      for card in cards:
        stack.add_card(card)
        
    return stack
  
  def show(self):
    visualize_board(self)
    
  
if __name__ == '__main__':
  g = Game()
  card_stack = g.place_cards([(Color.RED, 1), (Color.RED, 2), (Color.RED, 3)])
  g.place_cards([(Color.RED, 4), (Color.RED, 5), (Color.RED, 6)], card_stack)
  
  card_stack2 = g.place_cards([(Color.BLACK, 11), (Color.BLUE, 11), (Color.RED, 11)])
  g.place_cards((Color.YELLOW, 11), card_stack2)
  
  visualize_board(g)
