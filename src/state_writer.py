import json
import os
from datetime import datetime

class StateWriter:
    
    #todo: anpassen an den game_manager

    def __init__(self, storage, filename="gamestate.json") :
        self.storage = storage
        self.current_game_state = None
        self.save_history = [] #zum speichern der ganzen game history



    def write(self, game_manager):
        """
        den Spielzustand in den storage schreiben
        """
        #den aktuellen zustand extrahieren vom game_manager
        state = {
            'aktuelle_runde': game_manager.aktuelle_runde,
            'max_zuege': game_manager.max_zuege,
            'human_survivor_found': game_manager.human_survivor_found,
            'grover_survivor_found': game_manager.grover_survivor_found,
            'game_phase': game_manager.game_phase,
            'survivor_cell': game_manager.survivor_cell,
            'grid_cells': list(game_manager.grid.cells),
            'human_rounds_completed': game_manager.human_rounds_completed,
            'grover_rounds_completed': game_manager.grover_rounds_completed,
            'gewinner': game_manager.gewinner,
            'human_ready_for_next_round': game_manager.human_ready_for_next_round,
            'grover_ready_for_next_round': game_manager.grover_ready_for_next_round,
            'round_active': game_manager.round_active
        }
        state['saved_at'] = datetime.now().isoformat()
        state['version'] = '1.0'

        #im storage speichern
        self.storage.setItem('current_game', state) #setItem mit 'current_game' als key und state als value

        self.save_history.append({
            'time': state['saved_at'],
            'state': state.copy()
        })
        #Spielstand setzen
        self.current_game_state = state
        


    def read(self, game_manager):
        """
        den Spielzustand aus dem storage lesen und in game_manager laden
        """
        try:
            #Spielzustand aus storage laden
            state = self.storage.getItem('current_game')

            if state is None:
                print('kein Spielstand gefunden')
                return False
            
            #Spielzustand in den game_manager laden
            self.restore_game_state(game_manager, state)
            return True

        except Exception as e:
            print(f"Fehler beim laden {e}")
            return False
        
        

    def restore_game_state(self, game_manager, state):
        game_manager.aktuelle_runde = state.get('aktuelle_runde', 0)
        game_manager.max_zuege = state.get('max_zuege', 0)
        
        game_manager.human_survivor_found = state.get('human_survivor_found', False)
        game_manager.grover_survivor_found = state.get('grover_survivor_found', False)
        game_manager.game_phase = state.get('game_phase', 'start')
        #game_manager.state_writer = state.get('state_writer', 0)
        
        game_manager.human_rounds_completed = state.get('human_rounds_completed', 0)
        game_manager.grover_rounds_completed = state.get('grover_rounds_completed', 0)
        game_manager.gewinner = state.get('gewinner', 'keiner')
        game_manager.human_ready_for_next_round = state.get('human_ready_for_next_round', False)
        game_manager.grover_ready_for_next_round = state.get('grover_ready_for_next_round', False)
        game_manager.round_active = state.get('round_active', True)

        #game_manager.num_cells = state.get('num_cells', 0)

        if hasattr(game_manager, 'survivor_cell'):
            game_manager.survivor_cell = state.get('survivor_cell', 0)


    def delete(self):
        self.storage.delete_all()




