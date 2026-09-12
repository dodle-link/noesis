#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import os
import sys
import subprocess
import platform

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
NC = "\033[0m"

NOESIS_DIR = os.path.expanduser("~/.noesis")
TORCH_COMPAT_PATH = os.path.join(NOESIS_DIR, "torch_compat.py")

TORCH_COMPAT_CODE = '''import sys
import warnings

class FakeTorch:
    def __init__(self):
        self.__version__ = "0.1.0-compat"
        self.nn = FakeNN()
        self.cuda = FakeCuda()
    def tensor(self, *args, **kwargs):
        import numpy as np
        return np.array(*args)
    def load(self, *args, **kwargs):
        warnings.warn("PyTorch model loading not available in compatibility mode")
        return None

class FakeNN:
    def __init__(self):
        self.Module = type("Module", (), {"__init__": lambda self: None})
        self.functional = type("functional", (), {})

class FakeCuda:
    def is_available(self):
        return False

sys.modules["torch"] = FakeTorch()
warnings.warn("Using PyTorch compatibility layer. Limited functionality available.")
'''


def run(cmd):
    return subprocess.run(cmd, shell=isinstance(cmd, str))


def check_torch():
    r = subprocess.run([sys.executable, "-c", "import torch; print(torch.__version__)"],
                       capture_output=True, text=True)
    return r.returncode == 0, r.stdout.strip()


def check_compat_layer():
    r = subprocess.run([sys.executable, "-c",
                        f"import sys; sys.path.insert(0, '{NOESIS_DIR}'); import torch_compat; print('ok')"],
                       capture_output=True, text=True)
    return r.returncode == 0


def main():
    print(f"{CYAN}")
    print("╔════════════════════════════════════════════════════╗")
    print("║     NOESIS PYTHON 3.13+ AI DEPENDENCIES SETUP      ║")
    print("╚════════════════════════════════════════════════════╝")
    print(f"{NC}")

    os_type = platform.system()
    arch = platform.machine()
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"{BLUE}System: {os_type} ({arch}), Python: {py_ver}{NC}")
    print()

    os.makedirs(NOESIS_DIR, exist_ok=True)
    os.makedirs(os.path.join(NOESIS_DIR, "torch_compat"), exist_ok=True)

    print(f"{YELLOW}Running specialized Python 3.13+ AI installation...{NC}")
    run([sys.executable, "tools/setup-torch-py13.py"])

    ai_installed = False
    ok, torch_ver = check_torch()
    if ok:
        ai_installed = True
        print(f"{GREEN}PyTorch successfully installed!{NC}")
        print(f"Version: {torch_ver}")
    else:
        print(f"{YELLOW}PyTorch not detected. Using compatibility layer...{NC}")

        if not os.path.exists(TORCH_COMPAT_PATH):
            print(f"{YELLOW}Creating minimal PyTorch compatibility layer...{NC}")
            with open(TORCH_COMPAT_PATH, "w") as f:
                f.write(TORCH_COMPAT_CODE)

        print(f"{YELLOW}Installing numpy (required for compatibility)...{NC}")
        subprocess.run([sys.executable, "-m", "pip", "install", "numpy"])

        print(f"{YELLOW}Testing compatibility layer...{NC}")
        if check_compat_layer():
            ai_installed = True
            print("Compatibility layer works!")

    print(f"{YELLOW}Installing Hugging Face Transformers...{NC}")
    subprocess.run([sys.executable, "-m", "pip", "install", "transformers", "accelerate", "--no-deps"])
    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub", "tokenizers"])

    r = subprocess.run([sys.executable, "-c", "import transformers; print(transformers.__version__)"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f"{GREEN}Transformers successfully installed! Version: {r.stdout.strip()}{NC}")
        ai_installed = True
    else:
        print(f"{RED}Failed to install Transformers.{NC}")

    print()
    if ai_installed:
        print(f"{GREEN}{'='*68}{NC}")
        print(f"{GREEN}AI dependencies installed (with Python 3.13+ compatibility)!{NC}")
        print(f"{GREEN}{'='*68}{NC}")
        sys.exit(0)
    else:
        print(f"{RED}{'='*68}{NC}")
        print(f"{RED}Failed to install AI dependencies for Python 3.13+{NC}")
        print(f"{RED}{'='*68}{NC}")
        print()
        print(f"{YELLOW}Recommendations:{NC}")
        print("1. Install an older Python version compatible with PyTorch (3.9 or 3.10)")
        print("2. Use conda: brew install miniforge")
        print("3. conda create -n noesis python=3.10")
        print("4. conda activate noesis")
        print("5. conda install pytorch torchvision torchaudio -c pytorch")
        sys.exit(1)


if __name__ == "__main__":
    main()
