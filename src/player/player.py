from abc import ABC, abstractmethod

class Player(ABC):

    steps_used: int
    has_found_survivor: bool  # TODO: schauen ob so besser

    def __init__(self):
        self.steps_used = 0
        self.has_found_survivor = False # TODO: gucken wie besser


    # TODO: nachschauen ob doch lieber abstract 
    def get_results(self) -> str:
        """
        Gibt die Ergebnisse der Suche zurück
        """
        if self.has_found_survivor:
            return f"Survivor wurde in {self.steps_used} Schritten gefunden."
        else:
            return f"Kein Survivor nach {self.steps_used} Schritten gefunden."


        
    @abstractmethod
    def choose_cell(self) -> int:
        pass

