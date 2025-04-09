from src.agent.policies.GreedyPolicy import GreedyPolicy
from src.rummikub.CardCollection import CardCollection
from typing import List
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.rummikub.Game import Game
    from src.rummikub.CardCollection import Card

class Player:
    def __init__(self, name, policy=None):
        if not policy:
            policy = GreedyPolicy()
        self.name = name
        self.policy = policy
        
    def __repr__(self):
        return f"Player({self.name})"
    
    def next_move(self,game:'Game') -> List[CardCollection]: 
        

        if game.requires_meld(self.name):
            cards = game.get_cards(self.name)
            new_board = game.solver.get_best_move([], cards)
            #new_board = self.policy.select_move(game, self.name)
            card_sum = sum([collection.sum() for collection in new_board])
            if card_sum >= 30:
                return new_board + game.board
            return None
        

        sum_before = card_sum = sum([len(collection) for collection in game.board])
        new_board = self.policy.select_move(game, self.name)
        sum_after = sum([len(collection) for collection in new_board])
        if sum_after > sum_before:
            return new_board
         
        return None

