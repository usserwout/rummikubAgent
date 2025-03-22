class Player:
    def __init__(self, name):
        self.name = name
        self.cards = []
        
    def __repr__(self):
        return f"Player({self.name}, {len(self.cards)} cards)"

