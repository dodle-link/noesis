#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import time
import os
import sys

FIELD_SIZE = 10
FIELD_DIMENSIONS = 2
FIELD_POINTS = FIELD_SIZE ** FIELD_DIMENSIONS

_field_values = [0.0] * FIELD_POINTS
_field_momentum = [0.0] * FIELD_POINTS
_field_energy = [0.0] * FIELD_POINTS

ANSI_CHARS = [" ", ".", "-", "+", "*", "#"]


def init_quantum_field():
    global _field_values, _field_momentum, _field_energy
    _field_values = [0.0] * FIELD_POINTS
    _field_momentum = [0.0] * FIELD_POINTS
    _field_energy = [0.0] * FIELD_POINTS
    print(f"Initializing quantum field simulation ({FIELD_DIMENSIONS} dimensions, {FIELD_SIZE} points per dimension)")
    print(f"Quantum field initialized with {FIELD_POINTS} points")


def apply_field_perturbation(x, y, amplitude):
    x, y = int(x), int(y)
    if not (0 <= x < FIELD_SIZE and 0 <= y < FIELD_SIZE):
        print("Error: Coordinates out of bounds")
        return False
    idx = y * FIELD_SIZE + x
    _field_values[idx] = float(amplitude)
    print(f"Applied perturbation of amplitude {amplitude} at point ({x}, {y})")
    return True


def evolve_field(time_steps=1):
    dt = 0.1
    print(f"Evolving quantum field for {time_steps} time steps")

    for _ in range(int(time_steps)):
        print(".", end="", flush=True)
        new_momentum = _field_momentum[:]

        for y in range(FIELD_SIZE):
            for x in range(FIELD_SIZE):
                idx = y * FIELD_SIZE + x
                y_up = ((y - 1) % FIELD_SIZE) * FIELD_SIZE + x
                y_down = ((y + 1) % FIELD_SIZE) * FIELD_SIZE + x
                x_left = y * FIELD_SIZE + (x - 1) % FIELD_SIZE
                x_right = y * FIELD_SIZE + (x + 1) % FIELD_SIZE

                lap = (_field_values[y_up] + _field_values[y_down] +
                       _field_values[x_left] + _field_values[x_right] -
                       4 * _field_values[idx])
                new_momentum[idx] = _field_momentum[idx] + lap * dt

        for i in range(FIELD_POINTS):
            _field_momentum[i] = new_momentum[i]
            _field_values[i] += _field_momentum[i] * dt
            kinetic = 0.5 * _field_momentum[i] ** 2
            potential = 0.5 * _field_values[i] ** 2
            _field_energy[i] = kinetic + potential

    print("\nField evolution complete")


def calculate_total_energy():
    total = sum(_field_energy)
    print(f"Total field energy: {total:.4f}")
    return total


def visualize_field():
    print("Quantum field visualization:")
    ANSI_RESET = "\033[0m"
    colors = ["\033[37m", "\033[36m", "\033[34m", "\033[32m", "\033[33m", "\033[31m"]
    chars = [" ", ".", "-", "+", "*", "#"]
    thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]

    for y in range(FIELD_SIZE):
        line = ""
        for x in range(FIELD_SIZE):
            val = abs(_field_values[y * FIELD_SIZE + x])
            level = sum(1 for t in thresholds if val >= t)
            line += colors[level] + chars[level]
        print(line + ANSI_RESET)


def demo_quantum_field():
    print("Starting quantum field interactive demo...")
    init_quantum_field()
    center = FIELD_SIZE // 2
    apply_field_perturbation(center, center, 1.0)
    print("Initial field state:")
    visualize_field()

    for step in range(1, 21):
        os.system("clear")
        print(f"Quantum Field Evolution - Step {step}/20")
        evolve_field(1)
        visualize_field()
        calculate_total_energy()
        time.sleep(0.2)

    print("\nDemo complete! Final field state:")
    visualize_field()


def demo_wave_interference():
    print("Starting quantum wave interference demo...")
    init_quantum_field()
    quarter = FIELD_SIZE // 4
    three_quarter = 3 * FIELD_SIZE // 4
    center = FIELD_SIZE // 2
    apply_field_perturbation(quarter, center, 1.0)
    apply_field_perturbation(three_quarter, center, 1.0)

    print("Initial field state (two wave sources):")
    visualize_field()

    for step in range(1, 31):
        os.system("clear")
        print(f"Quantum Wave Interference - Step {step}/30")
        evolve_field(1)
        visualize_field()
        calculate_total_energy()
        time.sleep(0.2)

    print("\nDemo complete! Final interference pattern:")
    visualize_field()
