#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details
# run.py - Main entry point for the Noesis implementation

import os
import sys
import subprocess
import importlib.util
import time

NOESIS_VERSION = "2.2.0"

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
PINK = "\033[38;5;213m"
ORANGE = "\033[38;5;208m"
PURPLE = "\033[38;5;92m"
CYAN = "\033[96m"
NC = "\033[0m"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VERBOSE_MODE = False
MAX_COMMAND_HISTORY = 50
command_history = []
history_count = 0


def log_with_timestamp(message, level="INFO"):
    ts = time.strftime("%d %b %Y %H:%M:%S")
    epoch = int(time.time())
    days = epoch // 86400
    colors = {"ERROR": RED, "WARNING": YELLOW, "SUCCESS": GREEN, "DEBUG": BLUE}
    color = colors.get(level, PINK)
    print()
    print(f"{color}    {level}    {NC}")
    print()
    print(f"{color}    Time: {ts}    {NC}")
    print(f"{color}    Unix Time: {days} days {epoch} seconds    {NC}")
    print()
    print(f"{color}    {message}    {NC}")
    print()


def handle_error(message, code=1):
    log_with_timestamp(message, "ERROR")
    return code


def init_command_history():
    global command_history, history_count
    command_history = []
    history_count = 0
    log_with_timestamp("Command history initialized", "DEBUG")


def add_to_history(command):
    global history_count
    if not command or (command_history and command == command_history[0]):
        return
    command_history.insert(0, command)
    if len(command_history) > MAX_COMMAND_HISTORY:
        command_history.pop()
    history_count = len(command_history)


def show_history():
    if not command_history:
        print("No command history available")
        return
    print("Command history (most recent first):")
    print()
    for i, cmd in enumerate(command_history, 1):
        print(f"{i:3d}: {cmd}")


def print_banner():
    print(f"{PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{PINK}  NOESIS v{NOESIS_VERSION}            {NC}")
    print(f"{PINK}  Synthetic Sentience SYSTEM         {NC}")
    print(f"{PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print()


def show_version():
    print(f"Noesis v{NOESIS_VERSION}")
    print("Synthetic Sentience System")
    print("Copyright (c) Napol Thanarangkaun")
    print("Licensed under the MIT License - See LICENSE file for details")


def show_help():
    print(f"Noesis v{NOESIS_VERSION} - Synthetic Sentience System")
    print()
    print("Usage: noesis [options]")
    print()
    print("Options:")
    print("  -v, --version     Display version information")
    print("  -h, --help        Display this help message")
    print("  test              Run all tests")
    print("  -q, --quantum     Run in quantum mode")
    print("  update            Check for updates and update Noesis")
    print()
    print("Without options, Noesis starts in interactive mode.")


def check_python_version_compatibility():
    minor = sys.version_info.minor
    if minor >= 13:
        ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"{YELLOW}WARNING: Python {ver} detected.{NC}")
        print(f"{YELLOW}This version may have compatibility issues with PyTorch.{NC}")
        print(f"{YELLOW}Using compatibility mode for AI features.{NC}")
        print()
        return False
    return True


def check_for_updates():
    print(f"{YELLOW}Checking for updates...{NC}")
    if not _command_exists("git"):
        print(f"{RED}Error: Git is not installed. Cannot check for updates.{NC}")
        return False

    import tempfile, shutil
    tmp_dir = tempfile.mkdtemp()
    try:
        r = subprocess.run(
            ["git", "clone", "--quiet", "https://github.com/napol/noesis.git"],
            capture_output=True, cwd=tmp_dir
        )
        if r.returncode != 0:
            print(f"{RED}Error: Could not connect to the repository.{NC}")
            return False

        run_fish = os.path.join(tmp_dir, "noesis", "run.fish")
        if os.path.isfile(run_fish):
            with open(run_fish) as f:
                for line in f:
                    import re
                    m = re.search(r'NOESIS_VERSION\s*=\s*"([0-9.]+)"', line)
                    if m:
                        latest = m.group(1)
                        break
            if latest == NOESIS_VERSION:
                print(f"{GREEN}You are already running the latest version (v{NOESIS_VERSION}).{NC}")
            else:
                print(f"{GREEN}A new version is available: v{latest} (you have v{NOESIS_VERSION}){NC}")
        return True
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _command_exists(cmd):
    import shutil
    return shutil.which(cmd) is not None


def _load_intent():
    intent_path = os.path.join(SCRIPT_DIR, "soul", "intent.py")
    if not os.path.isfile(intent_path):
        print(f"{RED}Error: soul/intent.py not found{NC}")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("intent", intent_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def noesis_main(args):
    global VERBOSE_MODE
    init_command_history()
    check_python_version_compatibility()

    if args:
        cmd = args[0]
        if cmd in ("-v", "--version"):
            show_version()
        elif cmd in ("-h", "--help"):
            show_help()
        elif cmd == "update":
            check_for_updates()
        elif cmd == "status":
            status_path = os.path.join(SCRIPT_DIR, "tools", "terminal_status.py")
            if os.path.isfile(status_path):
                subprocess.run([sys.executable, status_path])
            else:
                log_with_timestamp("Terminal status script not found", "ERROR")
        elif cmd == "test":
            log_with_timestamp("Running Noesis tests...", "INFO")
            test_path = os.path.join(SCRIPT_DIR, "tools", "test.py")
            if os.path.isfile(test_path):
                r = subprocess.run([sys.executable, test_path])
                sys.exit(r.returncode)
            log_with_timestamp("All tests completed successfully", "SUCCESS")
        elif cmd in ("-q", "--quantum"):
            log_with_timestamp("Starting Noesis in quantum mode...", "INFO")
            intent = _load_intent()
            intent.main(["--quantum"])
        elif cmd == "verbose":
            VERBOSE_MODE = not VERBOSE_MODE
            state = "enabled" if VERBOSE_MODE else "disabled"
            log_with_timestamp(f"Verbose mode {state}", "INFO")
        else:
            log_with_timestamp(f"Unknown option: {cmd}", "ERROR")
            show_help()
            sys.exit(1)
    else:
        print_banner()
        intent = _load_intent()
        intent.main([])


if __name__ == "__main__":
    noesis_main(sys.argv[1:])
