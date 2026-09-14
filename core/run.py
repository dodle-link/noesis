#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details
# run.py - Main entry point for the Noesis implementation

import os
import sys
import subprocess
import importlib.util

NOESIS_VERSION = "2.3.0"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_console = None
_orchestrator = None


def _load_module(rel_path, key):
    path = os.path.join(SCRIPT_DIR, *rel_path.split('/'))
    spec = importlib.util.spec_from_file_location(key, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _get_console():
    global _console
    if _console is None:
        _console = _load_module("system/control/console.py", "console")
    return _console


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        path = os.path.join(SCRIPT_DIR, "system", "control", "orchestrator.py")
        if not os.path.isfile(path):
            print(f"{_get_console().RED}Error: system/control/orchestrator.py not found{_get_console().NC}")
            sys.exit(1)
        _orchestrator = _load_module("system/control/orchestrator.py", "orchestrator")
    return _orchestrator


def print_banner():
    c = _get_console()
    print(f"{c.PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{c.NC}")
    print(f"{c.PINK}  NOESIS v{NOESIS_VERSION}            {c.NC}")
    print(f"{c.PINK}  Synthetic Sentience SYSTEM         {c.NC}")
    print(f"{c.PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{c.NC}")
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
    c = _get_console()
    minor = sys.version_info.minor
    if minor >= 13:
        ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"{c.YELLOW}WARNING: Python {ver} detected.{c.NC}")
        print(f"{c.YELLOW}This version may have compatibility issues with PyTorch.{c.NC}")
        print(f"{c.YELLOW}Using compatibility mode for AI features.{c.NC}")
        print()
        return False
    return True


def check_for_updates():
    c = _get_console()
    print(f"{c.YELLOW}Checking for updates...{c.NC}")
    if not _command_exists("git"):
        print(f"{c.RED}Error: Git is not installed. Cannot check for updates.{c.NC}")
        return False

    import tempfile, shutil
    tmp_dir = tempfile.mkdtemp()
    try:
        r = subprocess.run(
            ["git", "clone", "--quiet", "https://github.com/napol/noesis.git"],
            capture_output=True, cwd=tmp_dir
        )
        if r.returncode != 0:
            print(f"{c.RED}Error: Could not connect to the repository.{c.NC}")
            return False

        run_fish = os.path.join(tmp_dir, "noesis", "run.fish")
        latest = None
        if os.path.isfile(run_fish):
            with open(run_fish) as f:
                for line in f:
                    import re
                    m = re.search(r'NOESIS_VERSION\s*=\s*"([0-9.]+)"', line)
                    if m:
                        latest = m.group(1)
                        break
            if latest == NOESIS_VERSION:
                print(f"{c.GREEN}You are already running the latest version (v{NOESIS_VERSION}).{c.NC}")
            else:
                print(f"{c.GREEN}A new version is available: v{latest} (you have v{NOESIS_VERSION}){c.NC}")
        return True
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _command_exists(cmd):
    import shutil
    return shutil.which(cmd) is not None


def noesis_main(args):
    c = _get_console()
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
                c.log_with_timestamp("Terminal status script not found", "ERROR")
        elif cmd == "test":
            c.log_with_timestamp("Running Noesis tests...", "INFO")
            test_path = os.path.join(SCRIPT_DIR, "tools", "test.py")
            if os.path.isfile(test_path):
                r = subprocess.run([sys.executable, test_path])
                sys.exit(r.returncode)
            c.log_with_timestamp("All tests completed successfully", "SUCCESS")
        elif cmd in ("-q", "--quantum"):
            c.log_with_timestamp("Starting Noesis in quantum mode...", "INFO")
            orchestrator = _get_orchestrator()
            orchestrator.main(["--quantum"])
        elif cmd == "verbose":
            orchestrator = _get_orchestrator()
            orchestrator.VERBOSE_MODE = not orchestrator.VERBOSE_MODE
            state = "enabled" if orchestrator.VERBOSE_MODE else "disabled"
            c.log_with_timestamp(f"Verbose mode {state}", "INFO")
        else:
            c.log_with_timestamp(f"Unknown option: {cmd}", "ERROR")
            show_help()
            sys.exit(1)
    else:
        print_banner()
        orchestrator = _get_orchestrator()
        orchestrator.main([])


if __name__ == "__main__":
    noesis_main(sys.argv[1:])
