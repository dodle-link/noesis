#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details

import subprocess
import platform
import sys
import os

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
NC = "\033[0m"


def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True).strip()
    except subprocess.CalledProcessError as e:
        return e.output.strip()


def main():
    print()
    print(f"{BLUE}╔════════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║     NOESIS TERMINAL STATUS DIAGNOSTICS         ║{NC}")
    print(f"{BLUE}╚════════════════════════════════════════════════╝{NC}")
    print()

    os_type = platform.system()
    arch = platform.machine()
    print(f"{YELLOW}System: {os_type} ({arch}){NC}")

    if sys.executable:
        py_version = f"Python {sys.version.split()[0]}"
        print(f"{YELLOW}{py_version}{NC}")
        if sys.version_info.minor >= 13:
            print(f"{RED}WARNING: Python 3.13+ detected - may have compatibility issues with PyTorch{NC}")
            print("Consider using the Python 3.13+ specific AI tools:")
            print("  python3 tools/fast_ai_install_py13.py")
    else:
        print(f"{RED}WARNING: Python 3 not found.{NC}")

    print()
    print(f"{BLUE}Checking for hanging Python processes...{NC}")
    python_procs = run("ps aux | grep python | grep -v grep")
    if python_procs:
        print(f"{YELLOW}Found running Python processes:{NC}")
        print(python_procs)
        print()
        print("To kill all Python processes:")
        print(f"{RED}pkill -9 python{NC}")
    else:
        print(f"{GREEN}No hanging Python processes detected.{NC}")

    print()
    print(f"{BLUE}Checking for high CPU usage processes...{NC}")
    print(f"{YELLOW}Top CPU consuming processes:{NC}")
    print(run("ps aux | sort -nrk 3,3 | head -5"))

    print()
    print(f"{BLUE}Checking disk space...{NC}")
    print(run("df -h | grep -E '^Filesystem|/$'"))

    print()
    print(f"{BLUE}Checking memory usage...{NC}")
    if platform.system() == "Darwin":
        print(run("vm_stat | grep Pages"))
    else:
        print(run("free -h"))

    print()
    print(f"{BLUE}Checking for Noesis-specific processes...{NC}")
    noesis_procs = run("ps aux | grep -E 'noesis|quantum' | grep -v grep")
    if noesis_procs:
        print(f"{YELLOW}Found Noesis processes:{NC}")
        print(noesis_procs)
    else:
        print(f"{GREEN}No specific Noesis processes detected.{NC}")

    print()
    print(f"{BLUE}╔════════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║     RECOMMENDATIONS TO FIX TERMINAL ISSUES     ║{NC}")
    print(f"{BLUE}╚════════════════════════════════════════════════╝{NC}")
    print()
    print("1. If using Python 3.13+, run the compatible AI installer:")
    print(f"   {GREEN}python3 tools/fast_ai_install_py13.py{NC}")
    print()
    print("2. If terminal is hanging, try these commands:")
    print(f"   {GREEN}pkill -9 python{NC}")
    print()
    print("3. Use the simplified run script to test:")
    print(f"   {GREEN}python3 tools/run_simplified.py{NC}")
    print()
    print("4. Clear Python package cache if needed:")
    print(f"   {GREEN}python3 -m pip cache purge{NC}")
    print()
    print(f"{GREEN}Diagnostics complete.{NC}")


if __name__ == "__main__":
    main()
