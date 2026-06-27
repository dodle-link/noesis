#!/usr/bin/env python3
import os
import sys
import subprocess


def link_libraries(*args):
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                               "scripts", "python")
    script = os.path.join(scripts_dir, "link_libraries.py")

    if os.path.exists(script):
        subprocess.run([sys.executable, script] + list(args))
    else:
        print(f"link_libraries script not found at {script}")
        print("Please ensure the scripts/python/link_libraries.py exists.")


if __name__ == "__main__":
    link_libraries(*sys.argv[1:])
