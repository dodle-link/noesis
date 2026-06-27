#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details

import sys
import os
import subprocess
import platform

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
NC = "\033[0m"


def log(msg, level=""):
    colors = {"INFO": BLUE, "SUCCESS": GREEN, "WARNING": YELLOW, "ERROR": RED}
    c = colors.get(level, "")
    print(f"{c}{msg}{NC}")


def install_ai_dependencies():
    log("Starting AI dependency installation...", "INFO")

    if not sys.executable:
        log("Error: Python 3 is required but not installed", "ERROR")
        return False

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    log(f"Found Python version {py_ver}", "INFO")

    if sys.version_info.minor > 10:
        log(f"Warning: Python {py_ver} detected - PyTorch may not have pre-built binaries", "WARNING")
        log("Recommended: use conda with Python 3.9 or 3.10", "INFO")
        answer = input("Would you like to continue anyway? (y/N): ").strip().lower()
        if answer not in ("y", "yes"):
            log("Installation aborted.", "ERROR")
            return False

    r = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True)
    if r.returncode != 0:
        log("Error: pip is required but not installed", "ERROR")
        return False

    os_type = platform.system()
    arch = platform.machine()
    log(f"Detected OS: {os_type}, Architecture: {arch}", "INFO")

    log("Installing Hugging Face libraries...", "INFO")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.run([sys.executable, "-m", "pip", "install", "transformers", "accelerate", "huggingface_hub"])

    if os_type == "Darwin":
        log(f"Installing PyTorch for macOS ({arch})...", "INFO")
        if arch == "arm64":
            log("Using Apple Silicon (M1/M2/M3) specific installation", "INFO")
            attempts = [
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", "torch", "torchvision", "torchaudio",
                 "--index-url", "https://download.pytorch.org/whl/cpu"],
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", "torch==2.0.0", "torchvision==0.15.0", "torchaudio==2.0.0"],
            ]
        else:
            attempts = [
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", "torch", "torchvision", "torchaudio",
                 "--index-url", "https://download.pytorch.org/whl/cpu"],
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", "torch==1.13.1", "torchvision==0.14.1", "torchaudio==0.13.1",
                 "--index-url", "https://download.pytorch.org/whl/cpu"],
            ]

        for attempt in attempts:
            subprocess.run(attempt)
            r = subprocess.run([sys.executable, "-c", "import torch"], capture_output=True)
            if r.returncode == 0:
                break
    else:
        subprocess.run([sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio"])

    checks = {
        "transformers": "Transformers",
        "torch": "PyTorch",
        "huggingface_hub": "Hugging Face Hub",
    }

    log("Verifying all dependencies:", "INFO")
    all_ok = True
    for pkg, name in checks.items():
        r = subprocess.run([sys.executable, "-c", f"import {pkg}"], capture_output=True)
        if r.returncode == 0:
            log(f"✓ {name} installed", "SUCCESS")
        else:
            log(f"✗ {name} NOT installed", "ERROR")
            all_ok = False

    if all_ok:
        log("All required dependencies successfully installed!", "SUCCESS")
    else:
        log("Some dependencies failed to install.", "ERROR")
    return all_ok


if __name__ == "__main__":
    success = install_ai_dependencies()
    sys.exit(0 if success else 1)
