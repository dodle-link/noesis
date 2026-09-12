#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import os
import sys
import subprocess

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
NC = "\033[0m"


def main():
    print(f"{BLUE}Installing PyTorch dependencies for macOS...{NC}")

    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        print(f"{GREEN}Active conda environment detected: {conda_prefix}{NC}")
    else:
        print(f"{YELLOW}No conda environment detected. Using system Python.{NC}")
        print("For best results, we recommend using conda:")
        print("  1. Install with: brew install miniconda")
        print("  2. Create env: conda create -n noesis python=3.9")
        print("  3. Activate: conda activate noesis")
        print()
        answer = input("Continue with system Python? (y/N): ").strip().lower()
        if answer not in ("y", "yes"):
            print(f"{RED}Aborted. Please install conda and try again.{NC}")
            sys.exit(1)

    result = subprocess.run([sys.executable, "setup-torch-mac.py"])
    if result.returncode == 0:
        print(f"{GREEN}PyTorch installation successful!{NC}")
        print("You can now use AI features in Noesis.")
    else:
        print(f"{RED}PyTorch installation failed.{NC}")
        print("Please try the manual installation process:")
        print()
        print("With conda (recommended):")
        print("  conda install -y pytorch torchvision torchaudio -c pytorch")
        print("  conda install -y pip")
        print("  pip install transformers accelerate huggingface_hub")
        print()
        print("With pip:")
        print("  pip install torch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1")
        print("  pip install transformers accelerate huggingface_hub")
        sys.exit(1)


if __name__ == "__main__":
    main()
