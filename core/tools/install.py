#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details

import sys
import os
import shutil

NOESIS_VERSION = "2.1.2"
PINK = "\033[38;2;255;95;215m"
GREEN = "\033[32m"
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

INSTALL_DIR = "/usr/local/lib/noesis"
BIN_DIR = "/usr/local/bin"
EXECUTABLE = os.path.join(BIN_DIR, "noesis")


def main():
    print(f"{PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{PINK}  NOESIS v{NOESIS_VERSION} - SYSTEM INSTALLER     {NC}")
    print(f"{PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print()

    if os.geteuid() != 0:
        print(f"{RED}Error: This script needs to be run with sudo privileges.")
        print(f"Please run: sudo python3 install.py{NC}")
        sys.exit(1)

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"{YELLOW}Checking required files...{NC}")
    missing = [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(base, f))]
    if missing:
        for f in missing:
            print(f"{RED}Missing file: {f}{NC}")
        print(f"{RED}Error: Some required files are missing{NC}")
        sys.exit(1)
    print(f"{GREEN}All required files exist{NC}")

    print(f"{YELLOW}Creating installation directories...{NC}")
    os.makedirs(INSTALL_DIR, exist_ok=True)
    os.makedirs(BIN_DIR, exist_ok=True)

    print(f"{YELLOW}Copying Noesis files...{NC}")
    for name in ["LICENSE", "README.md", "run.py"]:
        src = os.path.join(base, name)
        if os.path.exists(src):
            shutil.copy2(src, INSTALL_DIR)

    docs_src = os.path.join(base, "docs")
    if os.path.isdir(docs_src):
        shutil.copytree(docs_src, os.path.join(INSTALL_DIR, "docs"), dirs_exist_ok=True)

    for rel_path in REQUIRED_FILES:
        src = os.path.join(base, rel_path)
        dst = os.path.join(INSTALL_DIR, rel_path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    print(f"{YELLOW}Creating executable...{NC}")
    with open(EXECUTABLE, "w") as f:
        f.write("#!/usr/bin/env python3\n")
        f.write("import sys, os\n")
        f.write('sys.path.insert(0, "/usr/local/lib/noesis")\n')
        f.write('os.chdir("/usr/local/lib/noesis")\n')
        f.write('import run\n')
        f.write('run.main()\n')
    os.chmod(EXECUTABLE, 0o755)

    print(f"{GREEN}Installation complete!{NC}")
    print(f"You can now run Noesis from anywhere using the {YELLOW}noesis{NC} command.")
    print(f"Try {YELLOW}noesis -v{NC} to verify the installation.")
    print()


if __name__ == "__main__":
    main()
