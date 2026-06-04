from player import player
from state_writer import StateWriter

class GameManager:

    
    def __init__(self, max_zuege, human_player, grover_player, state_writer, grid) :
        self.aktuelle_runde = 0
        self.max_zuege = max_zuege
        self.human_player = human_player
        self.grover_player = grover_player
        self.human_survivor_found = False #ob der human_player den survivor gefunden hat
        self.grover_survivor_found = False #ob der grover_player den survivor gefunden hat
        self.game_phase = "start" #Am Anfang startet man im start_scren
                                    # 4 Phasen: start, story, game, end 
        self.state_writer = state_writer
        self.grid = grid
        self.survivor_cell = self.grid.survivor_cell #Zelle des survivors aus dem grid extrahieren
        self.human_rounds_completed = 0
        self.grover_rounds_completed = 0
        self.gewinner = None
        self.human_ready_for_next_round = False
        self.grover_ready_for_next_round = False
        self.round_active = True
    


    def start_screen(self):
        self.game_phase = "start"


    def storyline(self):
        self.game_phase = "story"
        print('Es ist die Nacht des 3. Oktobers. Wir sind auf einem Frachtschiff.\n ' \
            'Es gab einen Schrei und ein Platschen. Jemand ist über Bord gegangen, wir müssen ihn so schnell wie möglich finden. \n ' \
            'ZENTRALE: \nDu fliegst die Drohne. Wärmebildsensor aktiv. \n Irgendwo da draußen wartet er. ' \
            '\n Das Meer ist weit und die Zeit läuft ab.')
        

    def start_game(self):
        self.game_phase = "game"


    def human_zug(self, spot):

        self.load_game_state()

        if not self.round_active:
            return False
        self.human_rounds_completed += 1

        if spot == self.survivor_cell:
            self.human_survivor_found = True
            print(f"human player hat survivor in {self.human_rounds_completed} Zügen gefunden")
            
        self.human_ready_for_next_round = True
        self.save_game_state()
        self.beide_player_fertig()
        return self.human_survivor_found


    def grover_zug(self, spot):

        self.load_game_state()

        if not self.round_active:
            return False
        self.grover_rounds_completed += 1

        if spot == self.survivor_cell:
            self.grover_survivor_found = True
            print(f"grover player hat survivor in {self.grover_rounds_completed} Zügen gefunden")
            
        self.grover_ready_for_next_round = True
        self.save_game_state()
        self.beide_player_fertig()

        return self.grover_survivor_found

    def messen(self):
        self.load_game_state()

        if self.grover_survivor_found:
            print("Grover hat survivor gefunden")
            return None

        gemessene_zelle = self.grover_player.measure()
        if gemessene_zelle == self.survivor_cell:#wenn beim messen der survivor gezogen wurde
            self.grover_survivor_found = True

        else:
            #wenn der survivor nicht aufgedeckt wurde dann wird der grover algo nochmal von neuem gestartet
            self.grover_player.initialize(self.survivor_cell, self.grid.size)

        self.grover_rounds_completed += 1
        self.grover_ready_for_next_round = True

        self.save_game_state()

        self.beide_player_fertig()

        return gemessene_zelle



    def next_round(self):

        self.aktuelle_runde += 1
        self.round_active = True
        self.human_ready_for_next_round = False
        self.grover_ready_for_next_round = False
        print(f"Runde {self.aktuelle_runde} beginnt")

        self.save_game_state()
        


    def beide_player_fertig(self):

        self.load_game_state()

        if self.human_ready_for_next_round and self.grover_ready_for_next_round:
            self.round_active = False

        self.save_game_state()

        # Human ist fertig wenn: gefunden ODER keine Züge mehr
        human_endgueltig_fertig = (
            self.human_survivor_found
            or self.human_rounds_completed >= self.max_zuege
        )
        # Grover ist fertig wenn: gefunden ODER keine Züge mehr
        grover_endgueltig_fertig = (
            self.grover_survivor_found
            or self.grover_rounds_completed >= self.max_zuege
        )

        # Gewinner vormerken
        if self.grover_survivor_found and self.gewinner is None:
            self.gewinner = 'grover'
            self.save_game_state()
        if self.human_survivor_found and self.gewinner is None:
            self.gewinner = 'human'
            self.save_game_state()
        if self.human_survivor_found and self.grover_survivor_found and self.gewinner != 'beide':
            self.gewinner = 'beide'
            self.save_game_state()

        # Spiel beenden wenn beide endgültig fertig
        if human_endgueltig_fertig and grover_endgueltig_fertig:
            self.game_end()
            return

        # Nächste Runde starten wenn beide diese Runde ihren Zug gemacht haben
        grover_done_this_round = (
            self.grover_ready_for_next_round
            or self.grover_survivor_found
            or self.grover_rounds_completed >= self.max_zuege
        )
        human_done_this_round = (
            self.human_ready_for_next_round
            or self.human_survivor_found
            or self.human_rounds_completed >= self.max_zuege
        )

        if grover_done_this_round and human_done_this_round:
            self.next_round()


    def grover_iteration_signal(self):
        """Grover hat eine Iteration abgeschlossen (Zug beendet ohne Messen), signalisiert Bereitschaft"""
        self.load_game_state()
        self.grover_rounds_completed += 1
        self.grover_ready_for_next_round = True
        self.save_game_state()
        self.beide_player_fertig()

    def save_game_state(self):
        """
        nach jedem Zug wird der aktuelle Spielzustand gespeichert
        """
        if self.state_writer:
            self.state_writer.write(self)
        

    def load_game_state(self):
        """
        Vor jedem Zug wird der aktuelle Spielstand geladen
        """
        if self.state_writer:
            self.state_writer.read(self)


    def update_game_state(self, state):
        if state:
            self.aktuelle_runde = state.get('aktuelle_runde', 0)
            self.human_survivor_found = state.get('human_survivor_found', False)
            self.grover_survivor_found = state.get('grover_survivor_found', False)
            self.human_rounds_completed = state.get('human_rounds_completed', 0)
            self.grover_rounds_completed = state.get('grover_rounds_completed', 0)
            self.game_phase = state.get('game_phase', 'start')
            self.round_active = state.get('round_active', True)
            self.human_ready_for_next_round = state.get('human_ready_for_next_round', False)
            self.grover_ready_for_next_round = state.get('grover_ready_for_next_round', False)

    def game_end(self):
        self.game_phase = "end"
        print("\n" + "=" * 40)
        print("           SPIEL BEENDET")
        print("=" * 40)
        print(f"  Grover : {self.grover_rounds_completed} Züge")
        print(f"  Human  : {self.human_rounds_completed} Züge")
        print("-" * 40)
        if self.gewinner == 'human':
            print(f"  GEWINNER: Human")
        elif self.gewinner == 'grover':
            print(f"  GEWINNER: Grover")
        elif self.gewinner == 'beide':
            print(f"  UNENTSCHIEDEN")
        print("=" * 40)
        # game_phase = 'end' muss in die JSON gespeichert werden,
        # damit das andere Terminal die Endschleife verlassen kann
        self.save_game_state()
