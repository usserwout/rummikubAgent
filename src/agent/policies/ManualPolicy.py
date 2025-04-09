import os
import datetime
import time
from flask import  render_template, Flask
from flask_socketio import SocketIO, emit
import threading
import webbrowser

from src.agent.Policy import Policy
from src.rummikub.CardCollection import CardGroup
from src.rummikub.EventEmitter import event_emitter  



class ManualPolicy(Policy):
    app = Flask(__name__, 
              template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'templates'),
              static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'static'))
    socketio = SocketIO(app, cors_allowed_origins="*")
    lock = threading.Lock()
    game_state = None
    move_submitted = False
    new_board = None
    picking_card = False
    last_moves = [] 
    is_connected = False


    def __init__(self, port=5000):
        super().__init__()
        self.port = port
        self.server_thread = None
        
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'templates')
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'static')
        
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        
        @ManualPolicy.app.route('/')
        def index():
            return render_template('rummikub.html')
        
        ManualPolicy.socketio.on('connect')(handle_connect)
        ManualPolicy.socketio.on('disconnect')(self.handle_disconnect)
        ManualPolicy.socketio.on('make_move')(handle_make_move)
        ManualPolicy.socketio.on('request_game_state')(handle_request_game_state)
        ManualPolicy.socketio.on('pick_card')(handle_pick_card)
        
        event_emitter.on('player_move', self.handle_player_move)
        event_emitter.on('game_update', self.handle_game_update)
        event_emitter.on('player_turn', self.handle_player_turn)
        
        self.start_server()

    def handle_disconnect(self):
        print('Client disconnected')
        ManualPolicy.is_connected = False

    def handle_player_move(self, player_name, action, cards=None):
        """Handle player move events from the EventEmitter"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        move_info = {
            'player': player_name,
            'action': action,
            'timestamp': timestamp
        }
        
        if cards:
            move_info['cards'] = [{'color': card.color.value, 'number': card.number} for card in cards]
        
        ManualPolicy.last_moves.append(move_info)
        if len(ManualPolicy.last_moves) > 50:
            ManualPolicy.last_moves = ManualPolicy.last_moves[-50:]
            
        ManualPolicy.socketio.emit('player_move', move_info)
        
    def handle_player_turn(self, player_name):
        """Handle player turn events from the EventEmitter"""
        ManualPolicy.socketio.emit('player_turn', {'player_name': player_name})
        
    def handle_game_update(self, game, playing_as_name):
        """Handle game update events from the EventEmitter"""
        ManualPolicy.game_state = {
            'current_player': game.get_current_player().name,
            'board': [],
            'players': {},
            'round': game.round,
            'player': playing_as_name,
            'deck_count': len(game.cards)
        }
        
        for collection in game.board:
            collection_type = 'group' if isinstance(collection, CardGroup) else 'sequence'
            cards = []
            for card in collection.cards:
                cards.append({
                    'color': card.color.value,
                    'number': card.number,
                    'id': card.id
                })
            ManualPolicy.game_state['board'].append({
                'type': collection_type,
                'cards': cards
            })
        
        for player_name, cards in game.player_cards.items():
            player_cards = []
            for card in cards:
                player_cards.append({
                    'color': card.color.value,
                    'number': card.number,
                    'id': card.id
                })
            ManualPolicy.game_state['players'][player_name] = {
                'cards': player_cards,
                'card_count': len(player_cards),
                'is_current': player_name == game.get_current_player().name,
            }
        
        if ManualPolicy.game_state:
            ManualPolicy.socketio.emit('game_state', ManualPolicy.game_state)
        ManualPolicy.socketio.emit('move_history', ManualPolicy.last_moves)
        
    def handle_request_game_state(self):
        """This method is removed as it's no longer needed - we use socketio.emit directly"""
        pass
        
    def start_server(self):
        """Start the Flask server in a separate thread"""
        def run_server():
            ManualPolicy.socketio.run(ManualPolicy.app, port=self.port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
            
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"Server started at http://localhost:{self.port}")
        time.sleep(1)
        
        webbrowser.open(f"http://localhost:{self.port}")
    
    def select_move(self, game, player_name):
        """Wait for user to submit a move through the web interface"""

        self.handle_game_update(game, player_name)
        
        self.handle_player_turn(game.get_current_player().name)
        
        with ManualPolicy.lock:
            ManualPolicy.move_submitted = False
            ManualPolicy.new_board = None
            ManualPolicy.picking_card = False
        
        while not ManualPolicy.move_submitted:
            time.sleep(0.1)
        
        if ManualPolicy.picking_card:
            return "pick"
            
        return ManualPolicy.new_board


def handle_connect():
    print('Client connected')
    if ManualPolicy.game_state:
        ManualPolicy.socketio.emit('game_state', ManualPolicy.game_state)
    ManualPolicy.socketio.emit('move_history', ManualPolicy.last_moves)

def handle_make_move(data):
    with ManualPolicy.lock:
        ManualPolicy.move_submitted = True
        ManualPolicy.new_board = data.get('board', [])
        print(f"Move received: {data}")
        ManualPolicy.socketio.emit('move_received', {'status': 'success'}, broadcast=True)
        
def handle_request_game_state():
    print('Client requested game state')
    if ManualPolicy.game_state:
        ManualPolicy.socketio.emit('game_state', ManualPolicy.game_state)
    ManualPolicy.socketio.emit('move_history', ManualPolicy.last_moves)
    
def handle_pick_card():
    with ManualPolicy.lock:
        ManualPolicy.move_submitted = True
        ManualPolicy.picking_card = True
        print("Client requested to pick a card")
        ManualPolicy.socketio.emit('move_received', {'status': 'success'}, broadcast=True)
