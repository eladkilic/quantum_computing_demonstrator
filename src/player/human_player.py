from player.player import Player

class HumanPlayer(Player):

    def __init__(self, input_mode: str):
        super().__init__()
        # ob maus oder touch? überhaupt wichtig? 
        self.input_method = input_mode
        self.selected_cell = None
        self.selected_cell_list = []


    def choose_cell(self, cell_index: int) -> int:
        """
        Speichert die vom Benutzer ausgewählte Zelle und gibt die aktuell ausgewählte Zelle zurück

        Returns:
            int: Die ID der ausgewählten Zelle
        """
        if cell_index is None:
            raise ValueError("Keine Zelle ausgewählt.")

        self.selected_cell = cell_index
        self.selected_cell_list.append(cell_index)

        return self.selected_cell
    

    def get_selected_cell_list(self) -> list:
        """
        Gibt alle bisher ausgewählten Zellen zurück
        
        Returns:
            list: Die IDs der ausgewählten Zellen
        """
        return self.selected_cell_list

