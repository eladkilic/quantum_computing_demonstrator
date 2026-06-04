import os
import time
from game_manager import GameManager
from player.human_player import HumanPlayer
from player.grover_player import GroverPlayer
from state_writer import StateWriter
from local_storage import LocalStorage
from grid import Grid


def main():

    print("----------Manuelle Suche -----------")
    #erst main_grover starten, dann diese
    print("Warten auf anderen Spieler...")

    while not os.path.exists('gamestate.json'):
        time.sleep(1)

    storage = LocalStorage("gamestate.json")
    state_writer = StateWriter(storage)

    saved_state = storage.getItem('current_game')

    if saved_state:
        grid = Grid(16)
        survivor_cell = saved_state.get('survivor_cell', 0)
        grid.survivor_cell = survivor_cell
        grid.survivors[0].cell_index = survivor_cell
        if 'grid_cells' in saved_state:
            grid.cells = saved_state['grid_cells']
    else:
        grid = Grid(16)

    human_player = HumanPlayer('console')
    grover_player = GroverPlayer('console')

    game_manager = GameManager(max_zuege=5, human_player=human_player, 
        grover_player=grover_player, state_writer=state_writer, grid=grid)
    
    #start screen
    game_manager.start_screen()
    #story-line 
    game_manager.storyline()

    while True:
        state = storage.getItem('current_game')
        if state:
            print("Spiel startet. Du benutzt die manuelle Suche")
            break
        time.sleep(1)

    #Spiel starten
    game_manager.start_game()
    play_manual(grid, storage, game_manager)



def play_manual(grid: Grid, storage, game_manager):
    revealed_cells = set()
    attempts = 0
    local_round = 0
    waiting_printed = False

    # Initialzustand aus JSON laden damit stale Werte aus alten Spielen nicht feuern
    init_state = storage.getItem('current_game')
    if init_state:
        game_manager.grover_survivor_found = init_state.get('grover_survivor_found', False)
        game_manager.human_survivor_found = init_state.get('human_survivor_found', False)

    while not game_manager.human_survivor_found:
        state = storage.getItem('current_game')

        if not state:
            time.sleep(1)
            continue

        human_ready = state.get('human_ready_for_next_round', False)
        round_active = state.get('round_active', True)
        current_round = state.get('aktuelle_runde', 1)

        # Grover hat bereits gewonnen, human spielt trotzdem weiter (Version A)
        if state.get('grover_survivor_found', False) and not game_manager.grover_survivor_found:
            game_manager.grover_survivor_found = True
            print("Grover hat den Survivor bereits gefunden! Kannst du ihn auch noch finden?")

        # Warten bis Grover seine Iteration gemacht hat (Grover ist immer zuerst dran)
        grover_done = state.get('grover_ready_for_next_round', False) or state.get('grover_survivor_found', False)
        if not grover_done and not human_ready:
            if not waiting_printed:
                print("[Human] Warte auf Grovers Iteration...")
                waiting_printed = True
            time.sleep(1)
            continue

        if human_ready:
            if not round_active:
                if current_round != local_round:
                    local_round = current_round
                    waiting_printed = False
                    time.sleep(1)
            else:
                if not waiting_printed:
                    print("[Human] Warte bis Grover fertig ist...")
                    waiting_printed = True
                time.sleep(1)
            continue

        waiting_printed = False

        if current_round != local_round:
            local_round = current_round

        print(f"DEBUG: Survivor at cell {grid.get_survivor_location() + 1}")
        grid.display(revealed_cells)

        try:

            choice = input("Enter cell number to scan: ")
            cell_index = int(choice) - 1

            if cell_index < 0 or cell_index > grid.size:
                print("Invalid cell number")
                continue
            if cell_index in revealed_cells:
                print("Cell already revealed")
                continue

            attempts += 1
            temp = game_manager.grid.get_heat(cell_index)
            revealed_cells.add(cell_index)

            human_found_survivor = game_manager.human_zug(cell_index) #human Zug machen, es wird zurückgegeben ob in der Zelle der survivor war

            if human_found_survivor:
                print("Found survivor!")
                print(f"\nCell {cell_index + 1}: {temp:.1f}°C")
                print(f"Total attempts needed: {attempts}")

                grid.display(revealed_cells)
                print("Mission Completed! You found the survivor!")
                break
            else: # revealed non-survivor
                print(f"\nCell {cell_index + 1}: {temp:.1f}°C")
                print("No survivor detected at this location")
                grid.display(revealed_cells)
        except ValueError:
            print("Invalid input! Please enter a number.")
        except IndexError:
            print(f"Cell number out of range! Please enter 1-{grid.size}")

    #  Version A: Warten bis Grover-Spieler auch fertig ist
    if game_manager.game_phase != 'end':
        print("Warte auf anderen Spielende...")
        while game_manager.game_phase != 'end':
            time.sleep(1)
            game_manager.load_game_state()


if __name__ == "__main__":
    main()