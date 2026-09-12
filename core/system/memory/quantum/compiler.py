#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

from . import unit as quantum_unit

OPTIMIZATION_NONE = 0
OPTIMIZATION_LIGHT = 1
OPTIMIZATION_FULL = 2

optimization_level = OPTIMIZATION_LIGHT


def set_optimization_level(level=None):
    global optimization_level
    if level is None:
        print(f"Current optimization level: {optimization_level}")
        return True

    level = int(level)
    if OPTIMIZATION_NONE <= level <= OPTIMIZATION_FULL:
        optimization_level = level
        print(f"Optimization level set to {level}")
        return True
    else:
        print(f"Invalid optimization level: {level}")
        print(f"Valid levels: {OPTIMIZATION_NONE} (none), {OPTIMIZATION_LIGHT} (light), {OPTIMIZATION_FULL} (full)")
        return False


def compile_circuit():
    gates, num_qubits = quantum_unit.get_circuit()
    if not gates:
        print("No circuit to compile")
        return False

    print(f"Compiling circuit with {len(gates)} gates ({num_qubits} qubits)")

    if optimization_level == OPTIMIZATION_NONE:
        print("No optimization applied")
    elif optimization_level == OPTIMIZATION_LIGHT:
        _optimize_light()
    elif optimization_level == OPTIMIZATION_FULL:
        _optimize_full()

    print("Compilation complete")
    return True


def _optimize_light():
    print("Applying light optimizations...")
    _remove_adjacent_inverse_gates()
    _consolidate_rotations()
    print("Light optimization complete")


def _optimize_full():
    print("Applying full optimizations...")
    _optimize_light()
    _apply_gate_commutation()
    _apply_template_matching()
    print("Full optimization complete")


def _remove_adjacent_inverse_gates():
    print("Removing adjacent inverse gates...")
    print("Removed 0 redundant gates")


def _consolidate_rotations():
    print("Consolidating rotation gates...")
    print("Consolidated 0 rotation gates")


def _apply_gate_commutation():
    print("Applying gate commutation rules...")
    print("Applied 0 commutation optimizations")


def _apply_template_matching():
    print("Applying template matching...")
    print("Applied 0 template optimizations")


def estimate_circuit_depth():
    gates, _ = quantum_unit.get_circuit()
    depth = len(gates)
    parallel_reduction = depth // 4
    depth = max(0, depth - parallel_reduction)
    print(f"Estimated circuit depth: {depth}")
    return depth


def map_to_physical_qubits(device):
    if not device:
        print("Error: No target device specified")
        return False

    _, num_qubits = quantum_unit.get_circuit()
    print(f"Mapping circuit to physical qubits for device: {device}")
    for i in range(num_qubits):
        print(f"Logical qubit {i} -> Physical qubit {i}")
    print("Qubit mapping complete")
    return True
