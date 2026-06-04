import time
import math
import os
from game_manager import GameManager
from player.human_player import HumanPlayer
from player.player import Player
from player.grover_player import GroverPlayer
from state_writer import StateWriter
from local_storage import LocalStorage
from grid import Grid


def display_probabilities(grid: Grid, probs: list, revealed_cells: set = None):
    if revealed_cells is None:
        revealed_cells = set()
    cols = int(math.sqrt(grid.size))
    print("\n" + "=" * (cols * 10))
    for i in range(grid.size):
        pct = probs[i] * 100
        marker = "✓" if i in revealed_cells else " "
        symbol = f"[{pct:5.1f}%{marker}]"
        print(f"{symbol}", end=" ")
        if (i + 1) % cols == 0:
            print()
    print("=" * (cols * 10))


def main():

    # diese Main Methode zuerst starten

    print("----------Grover Suche -----------")

    if os.path.exists("gamestate.json"):
        os.remove("gamestate.json")

    grid = Grid(16)

    storage = LocalStorage("gamestate.json")
    state_writer = StateWriter(storage)

    initial_state = {
        'aktuelle_runde': 0,
        'max_zuege': 5,
        'human_survivor_found': False,
        'grover_survivor_found': False,
        'game_phase': 'start',
        'survivor_cell': grid.survivor_cell,
        'grid_cells': grid.cells,
        'human_rounds_completed': 0,
        'grover_rounds_completed': 0,
        'gewinner': 'keiner',
        'human_ready_for_next_round': False,
        'grover_ready_for_next_round': False,
        'round_active': True,
        'last_update': time.time()
    }
    storage.setItem('current_game', initial_state)

    human_player = HumanPlayer('console')
    grover_player = GroverPlayer('console')

    game_manager = GameManager(max_zuege=5, human_player=human_player,
        grover_player=grover_player, state_writer=state_writer, grid=grid)

    game_manager.start_screen()
    game_manager.storyline()

    while True:
        state = storage.getItem('current_game')
        if state:
            print("Spiel startet. Du benutzt die Grover-Suche")
            break
        time.sleep(1)

    game_manager.start_game()

    # Schaltkreis einmalig initialisieren, Superposition wird nur einmal gesetzt
    grover_player = game_manager.grover_player
    grover_player.initialize(grid.get_survivor_location(), grid.size)

    play_grover(grid, storage, game_manager, grover_player)



def measure_and_scan(grid: Grid, game_manager, grover_player: GroverPlayer, revealed_cells: set, attempts: int):
    print("\n[Grover] Messung...")
    cell_index = grover_player.measure()
    print(f"[Grover] Messung ergibt: Zelle {cell_index + 1}")

    if cell_index in revealed_cells:
        unrevealed = [i for i in range(grid.size) if i not in revealed_cells]
        if not unrevealed:
            return False
        cell_index = unrevealed[0]
        print(f"[Grover] Zelle bereits bekannt, weiche auf Zelle {cell_index + 1} aus")

    attempts += 1
    temp = game_manager.grid.get_heat(cell_index)
    revealed_cells.add(cell_index)
    grover_found = game_manager.grover_zug(cell_index)

    if grover_found:
        print(f"\n[Grover] Survivor gefunden! Zelle {cell_index + 1}: {temp:.1f}°C")
        print(f"Anzahl Versuche: {attempts}")
        grid.display(revealed_cells)
    else:
        print(f"Zelle {cell_index + 1}: {temp:.1f}°C — kein Survivor")
        grover_player.initialize(grid.get_survivor_location(), grid.size)
        print("[Grover] Schaltkreis zurückgesetzt für neue Iterationsrunde")

    return grover_found


def play_grover(grid: Grid, storage, game_manager, grover_player: GroverPlayer):
    revealed_cells = set()
    attempts = 0
    local_round = 0
    current_view = 'p' # warscheinlichkeit anzeigen
    waiting_printed = False

    while not (game_manager.human_survivor_found or game_manager.grover_survivor_found):
        state = storage.getItem('current_game')

        if not state:
            time.sleep(1)
            continue

        grover_ready = state.get('grover_ready_for_next_round', False)
        round_active = state.get('round_active', True)
        current_round = state.get('aktuelle_runde', 1)

        # Grover hat diese Runde schon gespielt, warten auf Human
        if grover_ready:
            if not round_active:
                if current_round != local_round:
                    local_round = current_round
                    waiting_printed = False
                    time.sleep(1)
            else:
                if not waiting_printed:
                    print("[Grover] Warte auf Human-Spieler...")
                    waiting_printed = True
                time.sleep(1)
            continue

        waiting_printed = False

        # Eine Iteration pro Runde 
        print(f"\n=== Grover — Iteration {grover_player.current_iteration + 1}/{grover_player.max_iterations} ===")
        print("'o' = Oracle | 'p' = Wahrscheinlichkeiten | 't' = Temperaturen | 'c' = Zellen")

        # Schritt 1: Oracle ('o')
        while True:
            if current_view == 'p':
                display_probabilities(grid, grover_player.get_probabilities(), revealed_cells)
            elif current_view == 't':
                print(f"DEBUG: Survivor at cell {grid.get_survivor_location() + 1}")
                grid.display(set(range(grid.size)))
            else:  # 'c'
                grid.display(revealed_cells)
            key = input("'o' für Oracle: ").strip().lower()
            if key == 'o':
                grover_player.apply_oracle()
                print("Oracle angewendet - Phase umgekehrt.")
                print("-> Wahrscheinlichkeiten noch unverändert! (Phase ≠ Wahrscheinlichkeit)")
                break
            elif key == 't':
                current_view = 't'
            elif key == 'p':
                current_view = 'p'
            elif key == 'c':
                current_view = 'c'

        # Schritt 2: Amplitude Amplification ('a') oder Messen ('m')
        while True:
            if current_view == 'p':
                display_probabilities(grid, grover_player.get_probabilities(), revealed_cells)
            elif current_view == 't':
                grid.display(set(range(grid.size)))
            else:  # 'c'
                grid.display(revealed_cells)
            is_last = grover_player.current_iteration + 1 == grover_player.max_iterations
            prompt = "'a' Amplitude | 'm' Messen: " if is_last else "'a' Amplitude | 'm' Jetzt messen: "
            key = input(prompt).strip().lower()
            if key == 'a':
                grover_player.amplify_amplitude()
                probs = grover_player.get_probabilities()
                top = probs.index(max(probs))
                print(f"Amplitude amplified! Höchste Wahrscheinlichkeit: Zelle {top + 1} ({max(probs)*100:.1f}%)")
                display_probabilities(grid, probs, revealed_cells)
                break
            elif key == 'm':
                grover_player.amplify_amplitude()
                measure_and_scan(grid, game_manager, grover_player, revealed_cells, attempts)
                return
            elif key == 't':
                current_view = 't'
            elif key == 'p':
                current_view = 'p'
            elif key == 'c':
                current_view = 'c'

        # Nach Amplification: Messen oder Human dran
        if grover_player.current_iteration == grover_player.max_iterations:
            found = measure_and_scan(grid, game_manager, grover_player, revealed_cells, attempts)
            if found is not None:
                return
        else:
            game_manager.grover_iteration_signal()
            print(f"[Grover] Iteration {grover_player.current_iteration}/{grover_player.max_iterations} abgeschlossen - Human ist dran")

    #  Version A: Warten bis Human-Spieler auch fertig ist
    if game_manager.game_phase != 'end':
        print("[Grover] Warte auf Ende des anderen Spielers...")
        while game_manager.game_phase != 'end':
            time.sleep(1)
            game_manager.load_game_state()
    # Finales Ergebnis auch auf Grover-Terminal anzeigen
    game_manager.load_game_state()
    game_manager.game_end()

if __name__ == "__main__":
    main()
