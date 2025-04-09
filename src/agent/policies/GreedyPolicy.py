from src.agent.Policy import Policy


class GreedyPolicy(Policy):


    def select_move(self, game, player_name):
        cards = game.get_cards(player_name)
        return game.solver.get_best_move(game.board, cards)  
        
