import random
from typing import List
from colorama import Fore, Back, Style, init
from .CardCollection import CardGroup, CardSequence, Card, Color


color_map = {
    Color.RED: Fore.RED,
    Color.BLUE: Fore.BLUE,
    Color.YELLOW: Fore.YELLOW,
    Color.BLACK: Fore.WHITE, 
    Color.WILD: Fore.MAGENTA
}

init()

def init_cards() -> List[Card]:
  
  cards = []
  for color in [Color.RED, Color.BLUE, Color.YELLOW, Color.BLACK]:
    for card_number in range(1, 14):
      for i in range(2):
        cards.append(Card(color, card_number))
        
  for card_number in range(2):
    cards.append(Card(Color.WILD, 0))
    
  random.shuffle(cards)
  return cards


def visualize_card(card:Card) -> str:
    color_str = card.color
    # Format the card
    if color_str == 'wild':
        card_str = f"{color_map[color_str]}[JOKER]{Style.RESET_ALL}"
    else:
        card_str = f"{color_map[color_str]}[{card.number:2d}]{Style.RESET_ALL}"
        
    return card_str

def visualize_board(game):
    output = []
    

    
    output.append(f"\n{Fore.CYAN}{'=' * 60}")
    output.append(f"{Fore.CYAN}{'RUMMIKUB GAME BOARD':^60}")
    output.append(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
    
    output.append(f"{Fore.CYAN}BOARD:{Style.RESET_ALL}")
    
    if not game.board:
        output.append("  No tiles on board yet.")
    else:
        for i, stack in enumerate(game.board):
            # Determine if it's a sequence or a group
            stack_type = "Group" if isinstance(stack, CardGroup) else "Sequence"
            output.append(f"  Stack {i+1} ({stack_type}):")
            
            # Display the cards in a nice format
            cards_display = []
            for card in stack.cards:
                cards_display.append(visualize_card(card))
            
            output.append("    " + " ".join(cards_display))
            
    
    # Player information
    output.append(f"\n{Fore.CYAN}PLAYERS:{Style.RESET_ALL}")
    for i, player in enumerate(game.players):
        current_marker = "→ " if i == game.current_player else "  "
        output.append(f"{current_marker}{player.name}: {len(game.player_cards[player.name])} tiles" + (" (Meld required)" if game.requires_meld(player.name) else ""))

        # print player cards
        player_cards = game.get_cards(player.name)
        output.append("    " + " ".join([visualize_card(card) for card in player_cards]))

    
    output.append(f"\n{Fore.CYAN}GAME INFO:{Style.RESET_ALL}")
    output.append(f"  Round: {game.round}")
    output.append(f"  Tiles in pool: {len(game.cards)}")
    
    print("\n".join(output))
    return "\n".join(output)

def visualize_player_hand(player):
    color_map = {
        'red': Fore.RED,
        'blue': Fore.BLUE,
        'yellow': Fore.YELLOW,
        'black': Fore.WHITE, 
        'wild': Fore.MAGENTA
    }
    
    output = []
    output.append(f"\n{Fore.GREEN}{player.name}'s Hand:{Style.RESET_ALL}")
    
    sorted_cards = sorted(player.cards, key=lambda card: (card[0].value if hasattr(card[0], 'value') else card[0], card[1]))
    
    cards_display = []
    for color, number in sorted_cards:
        if isinstance(color, str):
            color_str = color
        else:  # Handle Enum type
            color_str = color.value
        
        # Format the card
        if color_str == 'wild':
            card_str = f"{color_map[color_str]}[JOKER]{Style.RESET_ALL}"
        else:
            card_str = f"{color_map[color_str]}[{number:2d}]{Style.RESET_ALL}"
        cards_display.append(card_str)
    
    # Display cards in rows of 13 for readability
    for i in range(0, len(cards_display), 13):
        output.append("  " + " ".join(cards_display[i:i+13]))
    
    print("\n".join(output))
    return "\n".join(output)


