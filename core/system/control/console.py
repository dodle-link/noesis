#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details
# console.py - Shared console/output helpers for the body (system) layer.
#
# Centralizes the color palette, timestamped logging, error handling and
# command-history helpers that were previously duplicated across run.py and
# soul/intent.py.

import sys
import time

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
PINK = "\033[38;5;213m"
ORANGE = "\033[38;5;208m"
PURPLE = "\033[38;5;92m"
CYAN = "\033[96m"
NC = "\033[0m"

MAX_HISTORY = 50

_LEVEL_COLORS = {
    "ERROR": RED,
    "WARNING": YELLOW,
    "SUCCESS": GREEN,
    "DEBUG": BLUE,
}


def log_with_timestamp(message, level="INFO"):
    ts = time.strftime("%d %b %Y %H:%M:%S")
    color = _LEVEL_COLORS.get(level, PINK)
    print()
    print(f"{color}    {level}    {NC}")
    print()
    print(f"{color}    Time: {ts}    {NC}")
    print()
    print(f"{color}    {message}    {NC}")
    print()


def handle_error(message, code=1):
    log_with_timestamp(message, "ERROR")
    return code


def add_to_history(history, command, limit=MAX_HISTORY):
    if command and (not history or command != history[0]):
        history.insert(0, command)
        if limit is not None and len(history) > limit:
            history.pop()


def show_history(history):
    valid = [h for h in history if h]
    if not valid:
        print("No command history available")
        return
    print("Command history (most recent first):")
    print()
    for i, cmd in enumerate(valid, 1):
        print(f"{i:3d}: {cmd}")


def clear_screen():
    print("\033[2J\033[H", end="")
    sys.stdout.flush()
