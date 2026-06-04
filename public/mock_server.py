"""
Mock-Server zum Testen der Grover-UI ohne echtes app.py
Starten: python3 mock_server.py
Dann: http://localhost:5000/grover.html
"""
from flask import Flask, jsonify, send_from_directory
import math
import threading

app = Flask(__name__, static_folder='.', static_url_path='')

# Simulierter Spielzustand
state = {
    'iteration': 0,
    'max_iterations': 3,
    'oracle_done': False,
    'target': 2,  # Survivor in Zelle 3 (index 2)
    'aktuelle_runde': 1,
    'waiting_for_human': False,
}

N = 16
TARGET = state['target']

# Wahrscheinlichkeiten nach k Iterationen berechnen
def grover_probs(k):
    n_qubits = int(math.log2(N))
    theta = math.asin(1 / math.sqrt(N))
    angle = (2 * k + 1) * theta
    p_target = math.sin(angle) ** 2
    p_other = (1 - p_target) / (N - 1)
    probs = [p_other] * N
    probs[TARGET] = p_target
    return probs

# Temperaturen (einmalig generiert)
import random
TEMPS = [round(20 + random.uniform(0, 14), 1) for _ in range(N)]
TEMPS[TARGET] = 36.7


@app.route('/')
def index():
    return send_from_directory('.', 'grover.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/state')
def get_state():
    return jsonify({
        'probabilities': grover_probs(state['iteration']),
        'grid_cells': TEMPS,
        'current_iteration': state['iteration'],
        'max_iterations': state['max_iterations'],
        'aktuelle_runde': state['aktuelle_runde'],
        'grover_ready_for_next_round': state['waiting_for_human'],
        'grover_survivor_found': False,
        'game_phase': 'game',
    })

@app.route('/grover/oracle', methods=['POST'])
def oracle():
    state['oracle_done'] = True
    return jsonify({
        'probabilities': grover_probs(state['iteration']),
        'grid_cells': TEMPS,
    })

@app.route('/grover/amplify', methods=['POST'])
def amplify():
    state['iteration'] = min(state['iteration'] + 1, state['max_iterations'])
    state['oracle_done'] = False
    probs = grover_probs(state['iteration'])
    return jsonify({
        'probabilities': probs,
        'grid_cells': TEMPS,
        'current_iteration': state['iteration'],
    })

@app.route('/grover/end_turn', methods=['POST'])
def end_turn():
    state['waiting_for_human'] = True

    # Simuliert Human-Zug nach 2 Sekunden
    def human_done():
        import time
        time.sleep(2)
        state['oracle_done'] = False
        state['aktuelle_runde'] += 1
        state['waiting_for_human'] = False

    threading.Thread(target=human_done, daemon=True).start()
    return jsonify({'status': 'ok'})

@app.route('/grover/measure', methods=['POST'])
def measure():
    import random as rnd
    probs = grover_probs(state['iteration'])
    r = rnd.random()
    cumulative = 0
    cell_index = 0
    for i, p in enumerate(probs):
        cumulative += p
        if r <= cumulative:
            cell_index = i
            break
    found = cell_index == TARGET
    # Zustand zurücksetzen
    state['iteration'] = 0
    state['oracle_done'] = False
    return jsonify({
        'cell_index': cell_index,
        'found': found,
        'temp': TEMPS[cell_index],
    })


if __name__ == '__main__':
    print("Mock-Server läuft auf http://localhost:8080/grover.html")
    app.run(debug=True, port=8080)
