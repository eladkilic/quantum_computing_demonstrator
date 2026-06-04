from player.grover_player import GroverPlayer
from player.human_player import HumanPlayer
from grid import Grid


def main():

    print("Drone")
    print("\nWelches Modus wollen Sie?")
    print("1. Manuelle Suche")
    print("2. Quantumsuche")

    rolle_choice = input("Wähle (1 oder 2): ")

    grid = Grid(16)
    print(f"Search area has {grid.size} heat signals.")
    revealed_cells = set()
    attempts = 0

    if rolle_choice == "1":
        player = HumanPlayer("console")
        print(f"Sie sind im 1. Modus: {player.__class__.__name__}")
        play_manual(grid)

    elif rolle_choice == "2":  # quantum
        player = GroverPlayer("console")
        print(f"Sie sind im 2. Modus: {player.__class__.__name__}")
        # play_quantum(grid)

    else:
        print("Ungültige Eingabe")



    again = input("\nPlay again? \n1. Yes \n2. No ")
    if again == "1":
        main()

def play_manual(grid: Grid):
    revealed_cells = set()
    attempts = 0

    while not grid.is_found_all():
        print(f"DEBUG: Survivor at cell {grid.get_survivor_location() + 1}")
        grid.display(revealed_cells)
        print(f"attempts: {attempts}")
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
            temp = grid.reveal(cell_index)
            revealed_cells.add(cell_index)

            if grid.is_found_all():
                print("Found survivor!")
                print(f"\nCell {cell_index + 1}: {temp:.1f}°C")
                print(f"Total attempts needed: {attempts}")

                grid.display(revealed_cells)
                print("Mission Completed! You found the survivor!")
                break

            else: # revealed non-survivor
                print(f"\nCell {cell_index + 1}: {temp:.1f}°C")
                print("No survivor detected at this location")

        except ValueError:
            print("Invalid input! Please enter a number.")
        except IndexError:
            print(f"Cell number out of range! Please enter 1-{grid.size}")

if __name__ == "__main__":
    main()

