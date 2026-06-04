# Quantum Drone - Grover Algorithmus Demonstrator

Ein interaktives Spiel zur Demonstration des Grover-Quantenalgorithmus, entwickelt für die Lange Nacht der Wissenschaften im Rahmen des Projektstudiums "Quantencomputing Demonstrator".

## Spielidee

"Es ist die Nacht des 6. Juni. Wir sind auf einem Frachtschiff. Es gab einen Schrei und ein Platschen. Jemand ist uber Bord gegangen - wir mussen ihn so schnell wie moglich finden. 

ZENTRALE: Du fliegst die Drohne. Warmebildsensor aktiv. Irgendwo da draussen wartet er. Das Meer ist weit und die Zeit lauft ab. 

Ist der Grover Algorithmus schneller als die manuelle Suche?"

Eine Drohne mit Warmebildkamera sucht nach einem Uberlebenden im Wasser. Zwei Spieler treten gegeneinander an:
- Klassische Suche - Manuelles Aufdecken von Hitzespots
- Grover Suche - Quantenbeschleunigte Suche mit dem Grover-Algorithmus

## Installation

```bash
pip install -r requirements.txt
python3 src/app.py
```

Öffne dann die angezeigte Server-Adresse in zwei Browsertabs (ein Spieler pro Tab).

## Spielprinzip
- Beide Spieler versuchen, den Überlebenden so schnell wie möglich zu finden
- Wärmekamera zeigt mögliche Hitzespots (orangene Farbe)
- Der Grover-Algorithmus nutzt Superposition und Amplitude Amplification
- Nach wenigen Grover-Iterationen ist die Wahrscheinlichkeit für den richtigen Spot extrem hoch

## Projektstruktur
├── public/          # Frontend (CSS, JS, HTML)

├── src/             # Backend (Python Flask App)

├── gamestate.json   # Spielzustand

├── requirements.txt # Python Abhängigkeiten

└── .gitignore
