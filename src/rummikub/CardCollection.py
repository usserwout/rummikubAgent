from abc import ABC, abstractmethod
from enum import Enum



class Color(Enum):
  RED = 'red'
  BLUE = 'blue'
  YELLOW = 'yellow'
  BLACK = 'black'
  WILD = 'wild'

  def __lt__(self, other):
    if not isinstance(other, Color):
      return NotImplemented
    order = ['red', 'blue', 'yellow', 'black', 'wild']
    return order.index(self.value) < order.index(other.value)
  
class Card:
  _id_counter = 0

  def __init__(self, color: Color, number: int):
    if not isinstance(color, Color):
      raise ValueError(f"Invalid color: {color}")
    self.color = color
    self.number = number
    self.id = Card._id_counter
    Card._id_counter += 1
  
  def __repr__(self):
    return f'{self.color.value}:{self.number}'
  
  def __str__(self):
    return self.__repr__()

  def __getitem__(self, index):
    if index == 0:
      return self.color
    elif index == 1:
      return self.number
    elif index == 2:
      return self.id
    else:
      raise IndexError("Card index out of range")
  
  def __hash__(self):
    return hash(self.id)
    
  

class CardCollection(ABC):
  def __init__(self, cards):
    self.cards = cards

  @abstractmethod
  def is_valid(self):
    pass

  @abstractmethod
  def add_card(self, card):
    pass
  
  def can_add_card(self, card):
    self.cards.append(card)
    answer = self.is_valid()
    self.cards.pop()
    return answer
  
  def __eq__(self, other):
    if not isinstance(other, CardCollection):
      return False
    if len(self.cards) != len(other.cards):
      return False
    
    for i,card in enumerate(self.cards):
        if card != other.cards[i]:
            return False
    return True
  
  def sum(self):
    return sum(card.number for card in self.cards)
  

  def __iter__(self):
    return iter(self.cards)  
  
  def __len__(self):
    return len(self.cards)
  
class CardSequence(CardCollection):
  def __repr__(self):
    return f'Sequence({self.cards})'
  
  def is_valid(self):
    if len(self.cards) < 3:
      return False
    
    sequence_color = self.cards[0][0]
    card_numbers = set()
    
    for card in self.cards:
      if card.color == Color.WILD:
        continue
      
      if card.color is not sequence_color:
        return False
      
      if card.number in card_numbers:
        return False
      card_numbers.add(card.number)
    
    return True
  
  def add_card(self, card):
    self.cards.append(card)
    if not self.is_valid():
      raise ValueError(f"Invalid sequence: {self.cards}")
    return True
  
  def get_color(self):
    return self.cards[0].color
  


class CardGroup(CardCollection):
  def __repr__(self):
    return f'Group({self.cards})'
  
  def is_valid(self):
    if len(self.cards) < 3:
      return False
    
    colors = set()
    group_card_number = self.cards[0][1]
    
    for card in self.cards:
      if card.color == Color.WILD:
        continue
      
      if card.color in colors:
        return False
      colors.add(card.color)
      
      if card.number is not group_card_number:
        return False
    return True
  
  def add_card(self, card):
    self.cards.append(card)
    if not self.is_valid():
      raise ValueError(f"Invalid group: {self.cards}")
    return True
  
  def can_add_card(self, card):
    self.cards.append(card)
    answer = self.is_valid()
    self.cards.pop()
    return answer

