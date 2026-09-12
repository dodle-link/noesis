#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import sys
import os
import subprocess
import platform

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
NC = "\033[0m"


def check_import(pkg):
    r = subprocess.run([sys.executable, "-c", f"import {pkg}"], capture_output=True)
    return r.returncode == 0


def pip_install(*args):
    subprocess.run([sys.executable, "-m", "pip", "install"] + list(args))


def fast_install():
    print(f"{BLUE}Starting fast installation...{NC}")
    using_conda = bool(os.environ.get("CONDA_PREFIX"))
    os_type = platform.system()
    arch = platform.machine()

    if using_conda:
        subprocess.run(["conda", "install", "-y", "pip"])
    else:
        pip_install("--upgrade", "pip")

    if not check_import("transformers"):
        print("Installing Hugging Face transformers...")
        pip_install("--upgrade", "transformers")

    if not check_import("huggingface_hub"):
        print("Installing Hugging Face Hub...")
        pip_install("--upgrade", "huggingface_hub")

    if not check_import("accelerate"):
        print("Installing accelerate...")
        pip_install("--upgrade", "accelerate")

    if check_import("torch"):
        print("PyTorch is already installed.")
        return True

    if using_conda:
        print(f"{YELLOW}Installing PyTorch via conda...{NC}")
        r = subprocess.run(["conda", "install", "-y", "--no-deps", "pytorch", "-c", "pytorch"])
        if r.returncode == 0:
            subprocess.run(["conda", "install", "-y", "torchvision", "torchaudio", "-c", "pytorch"])
            return True
        if arch == "arm64":
            subprocess.run(["conda", "install", "-y", "pytorch=2.0.0", "torchvision=0.15.0", "torchaudio=2.0.0", "-c", "pytorch"])
        else:
            subprocess.run(["conda", "install", "-y", "pytorch=1.13.1", "torchvision=0.14.1", "torchaudio=0.13.1", "-c", "pytorch"])
    elif os_type == "Darwin":
        print(f"{YELLOW}Installing PyTorch for macOS ({arch})...{NC}")
        if arch == "arm64":
            pip_install("--no-cache-dir", "torch==2.1.0")
            pip_install("--no-cache-dir", "torchvision==0.16.0")
            pip_install("--no-cache-dir", "torchaudio==2.1.0")
        else:
            pip_install("--no-deps", "--no-cache-dir", "torch==1.13.1", "torchvision==0.14.1", "torchaudio==0.13.1",
                        "--index-url", "https://download.pytorch.org/whl/cpu")
    else:
        pip_install("torch", "torchvision", "torchaudio")

    ok = check_import("torch") and check_import("transformers")
    return ok


def main():
    print(f"{CYAN}")
    print("╔════════════════════════════════════════════════════╗")
    print("║       NOESIS FAST AI DEPENDENCIES INSTALLER        ║")
    print("╚════════════════════════════════════════════════════╝")
    print(f"{NC}")

    os_type = platform.system()
    arch = platform.machine()
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"{BLUE}System: {os_type} ({arch}), Python: {py_ver}{NC}")
    print()

    if sys.version_info.minor > 10:
        print(f"{YELLOW}Warning: Python {py_ver} detected. PyTorch may not have pre-built binaries.{NC}")
        if sys.version_info.minor > 12:
            print(f"{RED}Your Python {py_ver} is very new and likely incompatible with current PyTorch releases.{NC}")
            ans = input("Continue anyway? (y/N): ").strip().lower()
            if ans not in ("y", "yes"):
                print(f"{RED}Installation aborted.{NC}")
                sys.exit(1)

    using_conda = bool(os.environ.get("CONDA_PREFIX"))
    print(f"{GREEN}Active conda: {os.environ['CONDA_PREFIX']}{NC}" if using_conda else f"{YELLOW}Using system Python{NC}")

    success = fast_install()

    if success:
        print()
        print(f"{GREEN}{'='*68}{NC}")
        print(f"{GREEN}✓ Fast AI dependency installation completed successfully!{NC}")
        print(f"{GREEN}{'='*68}{NC}")

        def ver(pkg):
            r = subprocess.run([sys.executable, "-c", f"import {pkg}; print({pkg}.__version__)"],
                               capture_output=True, text=True)
            return r.stdout.strip() if r.returncode == 0 else None

        t = ver("torch")
        tr = ver("transformers")
        acc = ver("accelerate")

        print(f"\n{CYAN}Available AI features:{NC}")
        print(f"  {GREEN if t else RED}{'✓' if t else '✗'} PyTorch {t or '(not available)'}{NC}")
        print(f"  {GREEN if tr else RED}{'✓' if tr else '✗'} Transformers {tr or '(not available)'}{NC}")
        print(f"  {GREEN if acc else YELLOW}{'✓' if acc else '○'} Accelerate {acc or '(not available)'}{NC}")
        sys.exit(0)
    else:
        print()
        print(f"{RED}{'='*68}{NC}")
        print(f"{RED}✗ Fast installation failed.{NC}")
        print(f"{RED}{'='*68}{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
