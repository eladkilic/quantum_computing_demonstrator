import math
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from player.player import Player


class GroverPlayer(Player):

    def __init__(self, algorithm):
        super().__init__()
        self.algorithm = algorithm
        self._circuit = None
        self._n_qubits = None
        self._target = None
        self._n_cells = None
        self.current_iteration = 0
        self.max_iterations = 0
        self._oracle_applied = False

    def initialize(self, target_cell: int, n_cells: int = 16):
        # Einmalig aufrufen, Superposition wird nur einmal gesetzt
        self._n_qubits = int(math.log2(n_cells))
        self._target = target_cell
        self._n_cells = n_cells
        self.current_iteration = 0
        self.max_iterations = round(math.pi / 4 * math.sqrt(n_cells))
        self._oracle_applied = False
        self._circuit = QuantumCircuit(self._n_qubits)
        self._circuit.h(range(self._n_qubits))

    def apply_oracle(self):
        # Flippt die Phase der Survivor-Zelle, Wahrscheinlichkeiten bleiben noch gleich
        for i in range(self._n_qubits):
            if not (self._target >> i) & 1:
                self._circuit.x(i)
        self._circuit.h(self._n_qubits - 1)
        self._circuit.mcx(list(range(self._n_qubits - 1)), self._n_qubits - 1)
        self._circuit.h(self._n_qubits - 1)
        for i in range(self._n_qubits):
            if not (self._target >> i) & 1:
                self._circuit.x(i)
        self._oracle_applied = True

    def amplify_amplitude(self):
        # Grover Diffusion: Amplituden um Durchschnitt reflektieren -> Wahrscheinlichkeit steigt
        self._circuit.h(range(self._n_qubits))
        self._circuit.x(range(self._n_qubits))
        self._circuit.h(self._n_qubits - 1)
        self._circuit.mcx(list(range(self._n_qubits - 1)), self._n_qubits - 1)
        self._circuit.h(self._n_qubits - 1)
        self._circuit.x(range(self._n_qubits))
        self._circuit.h(range(self._n_qubits))
        self._oracle_applied = False
        self.current_iteration += 1

    def get_probabilities(self) -> list:
        # Berechnet amplitude^2 ohne zu messen, Superposition bleibt erhalten
        sv = Statevector(self._circuit)
        probs = sv.probabilities()
        return [float(p) for p in probs[:self._n_cells]]

    def measure(self) -> int:
        # Misst eine Kopie des Schaltkreises, kollabiert Superposition
        meas_circuit = self._circuit.copy()
        creg = ClassicalRegister(self._n_qubits)
        meas_circuit.add_register(creg)
        meas_circuit.measure(range(self._n_qubits), range(self._n_qubits))
        simulator = AerSimulator()
        job = simulator.run(meas_circuit, shots=1)
        counts = job.result().get_counts()
        measured = max(counts, key=counts.get)
        return int(measured, 2)

    def choose_cell(self, target_cell: int, n_cells: int = 16) -> int:
        # Für Rückwärtskompatibilität (z.B. test_grover.py), läuft automatisch durch
        self.initialize(target_cell, n_cells)
        print(f"[Grover] Initialisiere Superposition über {n_cells} Zellen ({self._n_qubits} Qubits)")
        for i in range(self.max_iterations):
            print(f"[Grover] Iteration {i + 1}/{self.max_iterations}: Oracle + Amplifikation")
            self.apply_oracle()
            self.amplify_amplitude()
        result = self.measure()
        print(f"[Grover] Messung ergibt: Zelle {result + 1}")
        return result
