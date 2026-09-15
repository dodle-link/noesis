#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import sys
import os
import importlib.util
from datetime import datetime

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
PINK = "\033[38;2;255;95;215m"
NC = "\033[0m"
BG_RED = "\033[41;1m"
BG_YELLOW = "\033[43;1m"
BG_GREEN = "\033[42;1m"
BG_PINK = "\033[48;2;255;95;215;1m"

VERBOSE_MODE = True


def log_message(message, level="INFO"):
    now = datetime.now()
    formatted_date = now.strftime("%d %b %Y %H:%M:%S")
    days = (now - datetime(1970, 1, 1)).days

    level_colors = {
        "ERROR": (BG_RED, RED, "    ERROR    "),
        "WARNING": (BG_YELLOW, YELLOW, "    WARNING    "),
        "SUCCESS": (BG_GREEN, GREEN, "    SUCCESS    "),
        "INFO": (BG_PINK, PINK, "    INFO    "),
    }
    bg, fg, label = level_colors.get(level, level_colors["INFO"])

    print()
    print(f"{bg}{label}{NC}")
    print()
    print(f"{fg}    [Time[{formatted_date}]]    {NC}")
    print(f"{fg}    [Unix Time[{days} days, {int(now.timestamp())} seconds]]    {NC}")
    print()
    print(f"{fg}    {message}    {NC}")
    print()


def print_banner():
    print()
    print(f"{PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{PINK}  NOESIS v2.3.1 - SIMPLIFIED         {NC}")
    print(f"{PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print()


def main():
    print_banner()
    log_message("Loading modules...", "INFO")

    orchestrator_path = os.path.join(os.path.dirname(__file__), "..", "system", "control", "orchestrator.py")
    if not os.path.exists(orchestrator_path):
        log_message("Cannot find system/control/orchestrator.py", "ERROR")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("orchestrator", orchestrator_path)
    orchestrator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orchestrator)
    log_message("Found and loaded orchestrator.py", "SUCCESS")

    if hasattr(orchestrator, "initialize_systems") and callable(orchestrator.initialize_systems):
        log_message("Found initialize_systems function, running it", "INFO")
        orchestrator.initialize_systems()
    else:
        log_message("initialize_systems function not found", "ERROR")
        sys.exit(1)

    log_message("Simplified run_simplified.py completed", "SUCCESS")


if __name__ == "__main__":
    main()
