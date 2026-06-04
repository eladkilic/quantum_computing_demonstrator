import json
import os

class LocalStorage:

    def __init__(self, filename="gamestate.json") :
        self.filename = filename
        self.dict = self.load()


    
    def load(self):
        
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def save(self):
        with open(self.filename, 'w', encoding="utf-8") as f:
            json.dump(self.dict, f, indent=2, ensure_ascii=False)


    def setItem(self, key, value):
        """
        speichert value im dict under dem entsprechenden key
        """
        self.dict[key] = value
        self.save()


    def getItem(self, key, default=None):
        """
        Gibt ein item zurück das dem key entspricht.
        Lädt immer frisch von Disk damit beide Terminals
        gegenseitige Änderungen sehen.
        """
        self.dict = self.load()
        return self.dict.get(key, default)


    def delete_all(self):
        self.dict = {}
        self.save()


    def get_all(self):
        return self.dict.copy()
