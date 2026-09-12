#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

MAX_QUBITS = 16
MAX_GATES = 256

GATE_H = 1
GATE_X = 2
GATE_Y = 3
GATE_Z = 4
GATE_CNOT = 5
GATE_SWAP = 6

GATE_NAMES = ["H", "X", "Y", "Z", "CNOT", "SWAP"]
GATE_TYPES = [GATE_H, GATE_X, GATE_Y, GATE_Z, GATE_CNOT, GATE_SWAP]

_qubits_allocated = [False] * MAX_QUBITS
_gates = []
_circuit_num_qubits = 0


def q_init():
    global _qubits_allocated, _gates, _circuit_num_qubits
    _qubits_allocated = [False] * MAX_QUBITS
    _gates = []
    _circuit_num_qubits = 0
    print(f"Quantum system initialized with {MAX_QUBITS} qubits capacity")


def q_alloc():
    global _circuit_num_qubits
    for i, allocated in enumerate(_qubits_allocated):
        if not allocated:
            _qubits_allocated[i] = True
            if i + 1 > _circuit_num_qubits:
                _circuit_num_qubits = i + 1
            print(f"Allocated qubit #{i}")
            return i
    print("Error: Out of qubits", flush=True)
    return -1


def q_add_gate(name, *targets):
    if len(_gates) >= MAX_GATES:
        print("Error: Circuit at maximum gate capacity")
        return -1

    if name not in GATE_NAMES:
        print(f"Error: Unknown gate '{name}'")
        return -2

    gate = {"name": name, "targets": list(targets)}
    _gates.append(gate)
    print(f"Added {name} gate to circuit (position {len(_gates)})")
    return 0


def q_get_circuit():
    print("Circuit state:")
    print(f"  Qubits: {_circuit_num_qubits}")
    print(f"  Gates: {len(_gates)}")
    for i, gate in enumerate(_gates):
        print(f"  Gate {i+1}: {gate['name']} targets: {gate['targets']}")


def q_process_with_noesis(inp):
    print("Running in standalone mode. Noesis Core not available.")
    print(f"Input: {inp}")


def get_circuit():
    return _gates, _circuit_num_qubits
