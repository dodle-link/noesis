#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details

import os
import sys
import subprocess

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
PINK = "\033[38;2;255;95;215m"
NC = "\033[0m"

NOESIS_DIR = os.path.expanduser("~/.noesis")
TEMP_DIR = os.path.join(NOESIS_DIR, "temp")
AI_TASK_SCRIPT = os.path.join(TEMP_DIR, "ai_task.py")

AI_TASK_CODE = '''import sys
import warnings
sys.path.insert(0, "{noesis_dir}")

try:
    import torch
    print(f"Using PyTorch: {{torch.__version__}}")
except ImportError:
    try:
        import torch_compat
        print("Using PyTorch compatibility layer")
    except ImportError:
        print("ERROR: No PyTorch or compatibility layer available")
        sys.exit(1)

try:
    import transformers
    print(f"Using Transformers: {{transformers.__version__}}")
except ImportError:
    print("ERROR: Transformers not available")
    sys.exit(1)

def handle_task(task_name, task_input):
    print(f"Processing task: {{task_name}}")
    if task_name == "echo":
        return f"Echo: {{task_input}}"
    if task_name == "sentiment":
        return f"Simulated sentiment analysis for: '{{task_input}}' - POSITIVE"
    if task_name == "summarize":
        return f"Simulated summary: '{{task_input[:30]}}...'"
    return f"Unknown task: {{task_name}}"

result = handle_task("{task}", "{inp}")
print(result)
'''


def check_python_env():
    print(f"{GREEN}Python 3 found{NC}")
    r = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
    print(r.stdout.strip())
    return True


def check_pytorch():
    r = subprocess.run([sys.executable, "-c", "import torch; print(f'PyTorch {torch.__version__} found')"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(r.stdout.strip())
        return True

    compat = os.path.join(NOESIS_DIR, "torch_compat.py")
    if os.path.exists(compat):
        r2 = subprocess.run([sys.executable, "-c",
                             f"import sys; sys.path.insert(0, '{NOESIS_DIR}'); import torch_compat; print('PyTorch compatibility layer works')"],
                            capture_output=True, text=True)
        if r2.returncode == 0:
            print(r2.stdout.strip())
            return True
    return False


def run_ai_task(task, inp=""):
    os.makedirs(TEMP_DIR, exist_ok=True)
    code = AI_TASK_CODE.format(noesis_dir=NOESIS_DIR, task=task, inp=inp)
    with open(AI_TASK_SCRIPT, "w") as f:
        f.write(code)
    result = subprocess.run([sys.executable, AI_TASK_SCRIPT])
    return result.returncode == 0


def main():
    print(f"{PINK}NOESIS AI Service Wrapper for Python 3.13+{NC}")
    print()

    if not check_python_env():
        print(f"{RED}Failed: Python environment check{NC}")
        sys.exit(1)

    if not check_pytorch():
        print(f"{YELLOW}Warning: PyTorch not available, attempting to install compatibility layer{NC}")
        subprocess.run([sys.executable, "tools/fast_ai_install_py13.py"])
        if not check_pytorch():
            print(f"{RED}Failed: PyTorch or compatibility layer not available{NC}")
            sys.exit(1)

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <task> [input]")
        print("Available tasks: echo, sentiment, summarize")
        sys.exit(1)

    task = sys.argv[1]
    inp = sys.argv[2] if len(sys.argv) > 2 else ""

    success = run_ai_task(task, inp)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
