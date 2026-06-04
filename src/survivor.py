

class Survivor:

    def __init__(self, cell_index: int, heat_signature: float):
        self.cell_index = cell_index
        self.heat_signature = heat_signature
        self.is_found = False

    def mark_found(self):
        self.is_found = True

    def __repr__(self):
        return (f"Survivor in cell={self.cell_index}, "
                f"heat={self.heat_signature:.1f}°C, found={self.is_found})")
