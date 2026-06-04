from survivor import Survivor
import random
import math


class Grid:
    def __init__(self, size: int = 16):
        self.size = size
        self.cells: list[float] = []
        self.survivors: list[Survivor] = []  # only 1 survivor
        self.survivor_cell = None
        self._generate_grid()

    def _generate_grid(self):
        self.survivor_cell = random.randint(0, self.size - 1) # random cell for survivor

        body_temp = 36.5 + random.uniform(-0.5, 0.5)  # body temp of survivor: 36-37

        survivor = Survivor(self.survivor_cell, body_temp)
        self.survivors.append(survivor)

        # temps for other cells
        self.cells = []
        for cell_id in range(self.size):
            if cell_id == self.survivor_cell:
                self.cells.append(round(body_temp, 1))
            else:
                random_temp = random.uniform(20.0, 34.0) # between 20 and 34 for non-survivors
                self.cells.append(round(random_temp, 1))

    def reveal(self, index: int) -> float:
        if index < 0 or index >= self.size:
            raise IndexError(f"Cell {index} out of range")

        for survivor in self.survivors:
            if survivor.cell_index == index and not survivor.is_found:
                survivor.mark_found()

        return self.cells[index]

    def get_heat(self, index: int) -> float:
        if index < 0 or index >= self.size:
            raise IndexError(f"Cell {index} out of range")

        return self.cells[index]

    def is_found_all(self) -> bool:
        return all(survivor.is_found for survivor in self.survivors)

    def get_survivor_location(self) -> int:
        """Helper method for quantum search - returns where survivor is"""
        return self.survivors[0].cell_index

    def display(self, revealed_cells: set = None):
        if revealed_cells is None:
            revealed_cells = set()

        cols = int(math.sqrt(self.size))
        print("\n" + "=" * (cols * 10))

        for i in range(self.size):
            if i in revealed_cells:
                # Show actual temperature
                temp = self.cells[i]
                if i == self.survivors[0].cell_index:
                    symbol = f"[{temp:5.1f}°🌡]"  # Survivor marker
                else:
                    symbol = f"[{temp:5.1f}° ]"
            else:
                # Hidden cell
                symbol = f"[Cell {i + 1:2d}]"

            print(f"{symbol}", end=" ")

            if (i + 1) % cols == 0:
                print()

        print("=" * (cols * 10))