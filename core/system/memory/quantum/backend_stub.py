#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import random
import math

_circuit_num_qubits = 0
_circuit_num_gates = 0
_gates = []


def _get_quantum_unit():
    try:
        import importlib.util, os
        path = os.path.join(os.path.dirname(__file__), "unit.py")
        spec = importlib.util.spec_from_file_location("quantum_unit", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def stub_init():
    print("Initializing stub quantum backend")
    q = _get_quantum_unit()
    if q and hasattr(q, "q_init"):
        q.q_init()


def stub_run_circuit(circuit_num_qubits, circuit_num_gates, gates):
    if circuit_num_gates == 0:
        print("No circuit to run")
        return False

    print(f"Running circuit with {circuit_num_gates} gates on stub simulator")
    print("Circuit execution:")
    print(f"Initializing {circuit_num_qubits} qubits to |0>")

    for gate in gates:
        print(f"Applying {gate.get('name', 'unknown')} gate to qubits: {gate.get('targets', [])}")

    print("Measurement results:")
    total_shots = 100
    state_count = 2 ** circuit_num_qubits

    if circuit_num_qubits <= 4:
        for i in range(state_count):
            binary_state = format(i, f"0{circuit_num_qubits}b")
            count = random.randint(0, total_shots)
            total_shots -= count
            if count > 0:
                print(f"  |{binary_state}>: {count} shots")
    else:
        for _ in range(5):
            state = "".join(str(random.randint(0, 1)) for _ in range(circuit_num_qubits))
            count = random.randint(1, max(1, total_shots // 5))
            total_shots -= count
            print(f"  |{state}>: {count} shots")

    return True


def stub_get_state(circuit_num_qubits):
    print("Simulated quantum state:")
    if circuit_num_qubits <= 3:
        state_count = 2 ** circuit_num_qubits
        for i in range(state_count):
            binary_state = format(i, f"0{circuit_num_qubits}b")
            amp_real = round(random.random(), 4)
            amp_imag = round(random.random(), 4)
            print(f"  |{binary_state}>: {amp_real} + {amp_imag}i")
    else:
        dim = 2 ** circuit_num_qubits
        print(f"  State vector too large to display ({circuit_num_qubits} qubits)")
        print(f"  State space has 2^{circuit_num_qubits} = {dim} dimensions")


def stub_reset():
    print("Resetting stub quantum simulator")
    stub_init()
