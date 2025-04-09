
from abc import ABC, abstractmethod


from typing import List
from src.rummikub.CardCollection import CardCollection

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.rummikub.Game import Game

class Policy(ABC):
    
    @abstractmethod
    def select_move(self, game:'Game', player_name:str) -> List[CardCollection]:
        pass


