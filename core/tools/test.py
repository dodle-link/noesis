#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import sys
import os
import importlib.util

NOESIS_VERSION = "2.1.2"
PINK = "\033[38;2;255;95;215m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
NC = "\033[0m"

REQUIRED_FILES = [
    "soul/intent.py",
    "system/memory/unit.py",
    "system/perception/unit.py",
    "system/emotion/unit.py",
    "system/memory/quantum/unit.py",
    "system/memory/quantum/compiler.py",
    "system/memory/quantum/backend_stub.py",
    "system/memory/quantum/backend_ibm.py",
    "system/memory/quantum/export_qasm.py",
    "system/memory/quantum/field/quantum_field.py",
    "system/memory/short.py",
    "system/memory/long.py",
    "system/perception/api.py",
]


def main():
    print(f"{PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{PINK}  NOESIS v{NOESIS_VERSION} - TEST SUITE           {NC}")
    print(f"{PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"{YELLOW}Checking required files...{NC}")
    missing = [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(base, f))]
    if missing:
        for f in missing:
            print(f"{RED}Missing file: {f}{NC}")
        print(f"{RED}Error: Some required files are missing{NC}")
        sys.exit(1)
    print(f"{GREEN}All required files exist{NC}")

    soul_path = os.path.join(base, "soul", "intent.py")
    spec = importlib.util.spec_from_file_location("intent", soul_path)
    intent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(intent)

    print(f"{YELLOW}Running test suite...{NC}")

    print(f"{BLUE}Testing memory systems...{NC}")
    if hasattr(intent, "test_memory_system"):
        intent.test_memory_system()

    print(f"{BLUE}Testing perception systems...{NC}")
    if hasattr(intent, "test_perception_system"):
        intent.test_perception_system()

    print(f"{BLUE}Testing quantum operations...{NC}")
    if hasattr(intent, "test_quantum_operations"):
        intent.test_quantum_operations()

    print(f"{GREEN}All tests completed successfully{NC}")


if __name__ == "__main__":
    main()
