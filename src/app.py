
from flask import Flask, request, jsonify, send_from_directory
import os
import uuid

from game_manager import GameManager
from grid import Grid
from local_storage import LocalStorage
from state_writer import StateWriter
from player.human_player import HumanPlayer
from player.grover_player import GroverPlayer

PUBLIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'public')
app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path='')

@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'start.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(PUBLIC_DIR, filename)
GRID_SIZE = 16  
MAX_ZUEGE = 100   # Grover hat kein hartes Limit (Iterationen begrenzen ihn)
MAX_HUMAN_ZUEGE = 10  # Alle Spieler dürfen maximal 10 Züge machen
GAME_TYPE = "web"

# aktuelles Web-Spiel
current_grid = None
current_storage = None
current_human_player = None
current_grover_player = None
current_game_manager = None
current_grover_measured_round = None
current_human_revealed_cells = set()
current_grover_revealed_cells = set()
current_manual_players_joined = set()
current_game_mode = None  # 'quantum' oder 'manual'
current_game_id = None  # unique id per game session

@app.route("/start/game", methods=["POST"])
def start_game():
    """Startet ein neues Spiel und initialisiert den Spielzustand.
    
    Diese Route wird aufgerufen, wenn der Benutzer das Spiel startet. 
    Sie erstellt das Grid, die Player und den Game Manager, 
    initialisiert den Grover Player und speichert den Spielzustand.
    
    Returns:
        JSON: Eine Bestätigung, dass das Spiel gestartet wurde
    """

    global current_grid, current_storage, current_human_player
    global current_grover_player, current_game_manager
    global current_grover_measured_round
    global current_human_revealed_cells, current_grover_revealed_cells
    global current_manual_players_joined
    global current_manual_players_joined, current_game_mode

    data = request.get_json(silent=True) or {}
    force_new = data.get('force_new', False)

    current_state = get_state(current_storage) if game_is_started() else None
    game_ended = current_state is not None and current_state.get('game_phase') == 'end'

    # Ohne force_new: laufendes Quantenspiel beibehalten (z. B. Grover-Reload)
    if (
        not force_new
        and game_is_started()
        and current_game_mode == 'quantum'
        and not game_ended
    ):
        state = current_state
    else:
        state = initialize_game()
        current_manual_players_joined = set()
        current_game_mode = 'quantum'

    # Antwort an UI zurückgeben
    return jsonify({
        "ok": True,
        "message": "Spiel gestartet.",
        "game_mode": current_game_mode,
        "game_id": current_game_id,
        "state": state
    })

@app.route("/start/manual", methods=["POST"])
def start_manual_game():
    """Startet oder joined den Mensch-vs-Mensch-Modus ueber den bestehenden Klassik-Button."""
    global current_manual_players_joined, current_game_mode

    data = request.get_json(silent=True) or {}
    force_new = data.get('force_new', False)

    # Check if current game has ended
    current_state = get_state(current_storage) if game_is_started() else None
    game_ended = current_state is not None and current_state.get('game_phase') == 'end'

    # Laufendes Quantenspiel: klassischer Mitspieler tritt bei (kein Reset)
    if (
        game_is_started()
        and current_game_mode == 'quantum'
        and not game_ended
    ):
        return jsonify({
            "ok": True,
            "player": 1,
            "game_mode": "quantum",
            "game_id": current_game_id,
            "state": current_state,
        })

    # Zweiter Spieler tritt nur einer frischen Lobby bei (noch keine Züge)
    if (
        game_is_started()
        and current_game_mode == 'manual'
        and current_manual_players_joined == {1}
        and not game_ended
        and not force_new
    ):
        lobby_state = get_state(current_storage)
        lobby_is_fresh = (
            lobby_state is not None
            and lobby_state.get("human_rounds_completed", 0) == 0
            and lobby_state.get("grover_rounds_completed", 0) == 0
        )
        if lobby_is_fresh:
            current_manual_players_joined.add(2)
            return jsonify({
                "ok": True,
                "player": 2,
                "game_mode": "manual",
                "game_id": current_game_id,
                "state": lobby_state,
            })

    # Spiel wurde mittendrin verlassen und erneut gestartet -> komplett neues Spiel
    if (
        game_is_started()
        and current_game_mode == 'manual'
        and not game_ended
        and not force_new
    ):
        active_state = get_state(current_storage)
        if active_state and (
            active_state.get("human_rounds_completed", 0) > 0
            or active_state.get("grover_rounds_completed", 0) > 0
        ):
            state = initialize_game()
            current_manual_players_joined = {1}
            current_game_mode = 'manual'
            return jsonify({
                "ok": True,
                "player": 1,
                "game_mode": "manual",
                "game_id": current_game_id,
                "state": state,
            })

    # Reinitialize if: no game, game ended, both joined, or Neustart vom Menü
    needs_new_game = (
        not game_is_started()
        or game_ended
        or current_manual_players_joined == {1, 2}
        or force_new
    )

    if needs_new_game:
        state = initialize_game()
        current_manual_players_joined = {1}
        current_game_mode = 'manual'
        player_number = 1
    else:
        current_manual_players_joined.add(1)
        player_number = 1
        state = get_state(current_storage)

    return jsonify({
        "ok": True,
        "player": player_number,
        "game_mode": "manual",
        "game_id": current_game_id,
        "state": state
    })
    

@app.route("/state", methods=["GET"])
def get_game_state():
    """Gibt den aktuellen Spielzustand zurück."""
    
    # prüfen, ob ein Spiel gestartet wurde
    if not game_is_started():
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # current_game aus Storage laden
    state = get_state(current_storage)

    # Falls kein Spielzustand vorhanden, Fehler zurückgeben
    if state is None:
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)
    
    player_number = get_player_number(request.args.get("player"))

    # Human-vs-Human-Hack:
    # player=1 benutzt die human_* Felder, player=2 benutzt die grover_* Felder.
    # Im normalen Grover-Modus bleiben die grover_* Felder weiterhin der Quanten-Spieler.
    can_human_play_now = can_human_play(state)
    can_grover_play_now = can_grover_play(state)
    can_current_human_play = can_human_player_play(state, player_number)
    can_measure = can_grover_measure(state)
    probabilities = current_grover_player.get_probabilities()

    # JSON-Antwort an die UI.
    # Fuer Human-vs-Human kommen zusaetzlich player/revealed_cells/player_rounds_completed mit.
    response_data = {
        "ok": True,

        # kompletter Spielzustand
        "state": state,

        "player": player_number,
        "game_id": current_game_id,
        "game_mode": current_game_mode,
        "waiting_for_second_player": is_waiting_for_second_player(),
        "waiting_for_human_partner": is_waiting_for_human_partner(state),
        "can_human_play": can_human_play_now,
        "can_current_human_play": can_current_human_play,
        "can_grover_play": can_grover_play_now,
        "can_oracle": can_grover_play_now and not current_grover_player._oracle_applied,
        "can_amplify": can_grover_play_now and current_grover_player._oracle_applied,
        "can_measure": can_measure,

        "grid_size": current_grid.size,
        "grid_cells": state.get("grid_cells"),
        "survivor_cell": state.get("survivor_cell"),
        "max_zuege": MAX_HUMAN_ZUEGE,
        "max_steps": MAX_HUMAN_ZUEGE,
        "game_phase": state.get("game_phase"),
        "aktuelle_runde": state.get("aktuelle_runde"),
        "gewinner": state.get("gewinner"),
        "human_survivor_found": state.get("human_survivor_found"),
        "grover_survivor_found": state.get("grover_survivor_found"),
        # Aus Sicht des jeweiligen Spielers (für Banner-Logik in human.js)
        "player_found": state.get("human_survivor_found") if player_number == 1 else state.get("grover_survivor_found"),
        "opponent_found": state.get("grover_survivor_found") if player_number == 1 else state.get("human_survivor_found"),
        "human_rounds_completed": state.get("human_rounds_completed"),
        "grover_rounds_completed": state.get("grover_rounds_completed"),
        "player_rounds_completed": get_human_rounds_completed(state, player_number),
        "opponent_rounds_completed": get_human_rounds_completed(state, 2 if player_number == 1 else 1),
        "human_ready_for_next_round": state.get("human_ready_for_next_round"),
        "grover_ready_for_next_round": state.get("grover_ready_for_next_round"),
        "revealed_cells": get_revealed_cells(player_number),
        "grover_has_measured": not can_measure,
        "round_active": state.get("round_active"),
        "saved_at": state.get("saved_at"),
        "version": state.get("version"),

        "probabilities": probabilities,
        "current_iteration": current_grover_player.current_iteration,
        "max_iterations": current_grover_player.max_iterations,
        "oracle_applied": current_grover_player._oracle_applied
    }

    return jsonify(response_data)



@app.route("/human/move", methods=["POST"])
def human_move():
    """Verarbeitet den Zug des menschlichen Spielers."""

    global current_grid, current_storage, current_game_manager
    global current_human_revealed_cells, current_grover_revealed_cells
    
    # aus HTTP_Req die ausgewählte Zelle extrahieren 
    data = request.get_json()

    if data is None:
        return error_response("Ungültige Anfrage. Es wurden keine JSON-Daten gesendet.", 400)
    
    cell = data.get("cell_index")
    player_number = get_player_number(data.get("player"))

    if cell is None:
        return error_response("Ungültige Anfrage. 'cell_index' fehlt.", 400)
    try:
        cell = int(cell) # in int konvertieren, da es als String ankommen könnte
    except ValueError:
        return error_response("'cell_index' muss eine ganze Zahl sein.", 400)

    # prüfen, ob ein Spiel gestartet wurde
    if not game_is_started():
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # aktuellen Spielzustand laden 
    state = get_state(current_storage)

    if state is None:
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # prüfen, ob Zelle gültig
    if not cell_is_valid(cell, current_grid):
        return error_response("Ungültige Zelle.", 400)
   
    # Human-vs-Human-Hack:
    # player=1 macht einen normalen Human-Zug.
    # player=2 benutzt current_game_manager.grover_zug(), obwohl hier ein Mensch klickt.
    if not can_human_player_play(state, player_number):
        return error_response("Dieser Spieler ist gerade nicht am Zug oder hat keine Züge mehr.", 409)

    # Temperatur dieser Zelle holen für UI
    temperature = current_grid.get_heat(cell)

    if player_number == 1:
        current_human_revealed_cells.add(cell)
        found_survivor = current_game_manager.human_zug(cell)
    else:
        current_grover_revealed_cells.add(cell)
        found_survivor = current_game_manager.grover_zug(cell)
    
    # Spielzustand speichern 
    new_state = get_state(current_storage) 

    return jsonify({
        "ok": True,
        "cell_index": cell,
        "player": player_number,
        "temperature": temperature,
        "found_survivor": found_survivor,
        "revealed_cells": get_revealed_cells(player_number),
        "state": new_state
     })



# Grover Player
@app.route("/grover/oracle", methods=["POST"])
def grover_oracle():
    """Verarbeitet die Anfrage für die Grover-Oracle-Funktion."""
    
    # prüfen, ob ein Spiel gestartet wurde
    if not game_is_started():
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # aktuellen Spielzustand laden
    state = get_state(current_storage)

    if state is None:
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # prüfen, ob Grover an Reihe ist
    if not can_grover_play(state):
        return error_response("Human ist zuerst am Zug oder Grover hat diese Runde bereits abgeschlossen.", 409)

    if current_grover_player._oracle_applied:
        return error_response("Oracle wurde bereits angewendet. Führe zuerst Amplify aus.", 409)

    # apply oracle Funktion von Grover Player
    current_grover_player.apply_oracle()

    # neue Wahrscheinlichkeiten holen
    probabilities = current_grover_player.get_probabilities()

    # Spielzustand speichern und an UI zurückgeben 
    current_game_manager.save_game_state()
    new_state = get_state(current_storage)

    return jsonify({
        "ok": True,
        "message": "Oracle wurde angewendet.",
        "current_iteration": current_grover_player.current_iteration,
        "max_iterations": current_grover_player.max_iterations,
        "oracle_applied": current_grover_player._oracle_applied,
        "probabilities": probabilities,
        "state": new_state
    })

@app.route("/grover/amplify", methods=["POST"])
def grover_amplify():
    """Verarbeitet die Anfrage für die Grover-Amplifikationsfunktion."""

    # prüfen, ob ein Spiel gestartet wurde
    if not game_is_started():
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # aktuellen Spielzustand laden 
    state = get_state(current_storage)

    if state is None:
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # prüfen, ob Grover an Reihe ist
    if not can_grover_play(state):
        return error_response("Human ist zuerst am Zug oder Grover hat diese Runde bereits abgeschlossen.", 409)

    # prüfen ob Oracle schon angewendet wurde (Amplify darf nur nach Oracle angewendet werden)
    if not current_grover_player._oracle_applied:
        return error_response("Führe zuerst Oracle aus.", 409)

    # amplify Funktion von Grover Player aufrufen (overshoot erlaubt — kein hartes Limit)
    current_grover_player.amplify_amplitude()

    # neue Wahrscheinlichkeiten holen
    probabilities = current_grover_player.get_probabilities()

    # Antwort an UI zurückgeben und Spielzustand speichern
    new_state = get_state(current_storage)

    return jsonify({
        "ok": True,
        "message": "Amplifikation wurde angewendet.",
        "current_iteration": current_grover_player.current_iteration,
        "max_iterations": current_grover_player.max_iterations,
        "oracle_applied": current_grover_player._oracle_applied,
        "probabilities": probabilities,
        "state": new_state
    })

# TODO: soll messen erst nach max interation möglich sein oder wenn auf button geklickt wird?
# messen ist hier immer möglich unabhänging vn interation orakel...
@app.route("/grover/measure", methods=["POST"])
def grover_measure():
    """Verarbeitet die Anfrage für die Grover-Messfunktion."""
    global current_grover_measured_round

    # prüfen, ob ein Spiel gestartet wurde
    if not game_is_started():
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # aktuellen Spielzustand laden
    state = get_state(current_storage)

    if state is None:
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # prüfen, ob Grover an Reihe ist
    if not can_grover_measure(state):
        return error_response("Grover hat diese Runde bereits gemessen oder gewonnen.", 409)

    # Grover messen fkt und zelle holen
    cell = current_grover_player.measure()

    # prüfen, ob Zelle gültig
    if not cell_is_valid(cell, current_grid):
        return error_response("Grover hat eine ungültige Zelle gemessen.", 500)

    # Temperatur dieser Zelle holen für UI
    temperature = current_grid.get_heat(cell)

    # Grover Zug im GameManager 
    measured_round = state.get("aktuelle_runde")
    found_survivor = current_game_manager.grover_zug(cell)
    current_grover_measured_round = measured_round


    # prüfen, ob Überlebender gefunden wurde?

    # Falls nicht gefunden Algo neu starten 
    if not found_survivor:
        current_grover_player.initialize(
            current_grid.get_survivor_location(),
            current_grid.size
        )

    # Spielzustand speichern und an UI zurückgeben
    new_state = get_state(current_storage)

    return jsonify({
        "ok": True,
        "cell_index": cell,
        "temperature": temperature,
        "found_survivor": found_survivor,
        "probabilities": current_grover_player.get_probabilities(),
        "current_iteration": current_grover_player.current_iteration,
        "max_iterations": current_grover_player.max_iterations,
        "oracle_applied": current_grover_player._oracle_applied,
        "can_measure": can_grover_measure(new_state),
        "state": new_state
    })


@app.route("/grover/end_turn", methods=["POST"])
def grover_end_turn():
    """Beendet den aktuellen Grover-Zug und gibt den Human-Spieler frei."""

    # prüfen, ob ein Spiel gestartet wurde
    if not game_is_started():
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # aktuellen Spielzustand laden
    state = get_state(current_storage)

    if state is None:
        return error_response("Kein Spielstand gefunden. Starte zuerst ein Spiel.", 404)

    # prüfen, ob Grover an Reihe ist
    if not can_grover_play(state):
        return error_response("Human ist zuerst am Zug oder Grover hat diese Runde bereits beendet.", 409)

    # Grover-Zug beenden und Human freigeben
    current_game_manager.grover_iteration_signal()

    # neuen Spielzustand laden
    new_state = get_state(current_storage)

    # Antwort an UI zurückgeben
    return jsonify({
        "ok": True,
        "message": "Grover-Zug beendet.",
        "can_human_play": can_human_play(new_state),
        "can_measure": can_grover_measure(new_state),
        "state": new_state
    })




@app.route("/reset", methods=["POST"])
def reset_game():
    """Setzt das Spiel zurück und löscht den aktuellen Spielzustand."""
    
    global current_grid, current_storage, current_human_player
    global current_grover_player, current_game_manager
    global current_grover_measured_round
    global current_human_revealed_cells, current_grover_revealed_cells
    global current_manual_players_joined, current_game_mode, current_game_id

    # prüfen, ob ein Spiel gestartet wurde und storage gibt
    if current_storage is not None:
        current_storage.delete_all()

    # globale Spielobj zurücksetzen
    current_grid = None
    current_storage = None
    current_human_player = None
    current_grover_player = None
    current_game_manager = None
    current_grover_measured_round = None
    current_human_revealed_cells = set()
    current_grover_revealed_cells = set()
    current_manual_players_joined = set()
    current_game_mode = None
    current_game_id = None

    # JSON-Antwort zurückgeben
    return jsonify({
        "ok": True,
        "message": "Spiel wurde zurückgesetzt."
    })


# hilfsfunktionen
def initialize_game() -> dict | None:
    """Initialisiert ein neues Spiel und gibt den gespeicherten State zurueck."""
    global current_grid, current_storage, current_human_player
    global current_grover_player, current_game_manager
    global current_grover_measured_round
    global current_human_revealed_cells, current_grover_revealed_cells, current_game_id

    # Grid initialisieren
    current_grid = Grid(GRID_SIZE)
    current_storage = get_storage()
    current_storage.delete_all()
    state_writer = StateWriter(current_storage)

    # Player erstellen
    current_human_player = HumanPlayer(GAME_TYPE)
    current_grover_player = GroverPlayer(GAME_TYPE)
    current_grover_measured_round = None
    current_human_revealed_cells = set()
    current_grover_revealed_cells = set()
    current_game_id = str(uuid.uuid4())[:8]

    # Game Manager erstellen
    current_game_manager = GameManager(
        max_zuege=MAX_HUMAN_ZUEGE,
        human_player=current_human_player,
        grover_player=current_grover_player,
        state_writer=state_writer,
        grid=current_grid)
    
    # Spielphase starten
    current_game_manager.start_screen()
    current_game_manager.storyline()
    current_game_manager.start_game()

    # Grover Player initialisieren
    current_grover_player.initialize(
        current_grid.get_survivor_location(),
        current_grid.size
    )

    # Spielzustand speichern und laden
    current_game_manager.save_game_state()
    return get_state(current_storage)

def get_storage() -> LocalStorage:
    """Erstellt den Zugriff auf die Spielstand-Datei."""
    return LocalStorage("gamestate.json")

def get_state(storage: LocalStorage) -> dict | None:
    """Lädt den aktuellen Spielzustand."""
    return storage.getItem("current_game")

def game_is_started() -> bool:
    """Prüft, ob ein Web-Spiel gestartet wurde."""
    return (
        current_grid is not None
        and current_storage is not None
        and current_human_player is not None
        and current_grover_player is not None
        and current_game_manager is not None
    )

def cell_is_valid(cell_index: int, grid: Grid) -> bool:
    """Prüft, ob eine Zelle im gültigen Grid-Bereich liegt."""
    return 0 <= cell_index < grid.size

def get_player_number(player) -> int:
    """Liest den Human-vs-Human-Spieler aus Request-Daten, default ist Spieler 1."""
    try:
        player_number = int(player)
    except (TypeError, ValueError):
        player_number = 1
    return 2 if player_number == 2 else 1

def can_human_player_play(state: dict, player_number: int) -> bool:
    """Human-vs-Human: Spieler 2 benutzt intern den grover_* Slot."""
    if player_number == 2:
        return can_grover_play(state)
    return can_human_play(state)

def get_human_rounds_completed(state: dict, player_number: int) -> int:
    """Human-vs-Human: liefert die eigenen Züge der jeweiligen Ansicht."""
    if player_number == 2:
        return state.get("grover_rounds_completed", 0)
    return state.get("human_rounds_completed", 0)

def get_revealed_cells(player_number: int) -> list[int]:
    """Human-vs-Human: jeder Spieler sieht nur die selbst aufgedeckten Zellen."""
    if player_number == 2:
        return sorted(current_grover_revealed_cells)
    return sorted(current_human_revealed_cells)

def is_waiting_for_second_player() -> bool:
    """True wenn der erste Spieler beigetreten ist, aber der zweite noch nicht."""
    return (
        current_game_mode == 'manual'
        and current_manual_players_joined == {1}
    )

def is_waiting_for_human_partner(state: dict) -> bool:
    """Quantenmodus: Grover wartet, bis der klassische Spieler den ersten Zug macht."""
    return (
        current_game_mode == 'quantum'
        and state.get("game_phase") == "game"
        and state.get("human_rounds_completed", 0) == 0
        and not state.get("human_survivor_found", False)
    )

def can_human_play(state):
    # Human darf spielen wenn: Spiel läuft, noch nicht ready für nächste Runde, noch Züge übrig, noch nicht gefunden
    return (
        state.get("game_phase") == "game"
        and not state.get("human_ready_for_next_round", False)
        and state.get("human_rounds_completed", 0) < state.get("max_zuege", MAX_HUMAN_ZUEGE)
        and not state.get("human_survivor_found", False)
    )

def can_grover_play(state):
    # Grover darf spielen wenn: Human diese Runde fertig ist (gezogen hat ODER gefunden ODER keine Züge mehr)
    # UND Grover noch nicht fertig diese Runde ist und noch Züge übrig hat
    human_done_this_round = (
        state.get("human_ready_for_next_round", False)
        or state.get("human_survivor_found", False)
        or state.get("human_rounds_completed", 0) >= state.get("max_zuege", MAX_HUMAN_ZUEGE)
    )
    return (
        state.get("game_phase") == "game"
        and human_done_this_round
        and not grover_is_done(state)
        and state.get("grover_rounds_completed", 0) < state.get("max_zuege", MAX_HUMAN_ZUEGE)
        and not state.get("grover_survivor_found", False)
    )


def grover_is_done(state: dict) -> bool:
    """Prüft, ob Grover diese Runde fertig ist."""
    return state.get("grover_ready_for_next_round", False)

def can_grover_measure(state: dict) -> bool:
    """Prüft, ob Grover in dieser Runde noch messen darf."""
    return (
        can_grover_play(state)
        and current_grover_measured_round != state.get("aktuelle_runde")
    )

def human_is_done(state: dict) -> bool:
    """Prüft, ob Human diese Runde fertig ist."""
    return state.get("human_ready_for_next_round", False)

def error_response(message: str, status_code: int):
    """Gibt eine einheitliche Fehlerantwort zurück."""
    return jsonify({
        "ok": False,
        "error": message
    }), status_code

if __name__ == '__main__':
    app.run(debug=True, port=8080)
