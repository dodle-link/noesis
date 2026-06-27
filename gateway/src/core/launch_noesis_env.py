#!/usr/bin/env python3
import os
import sys
import subprocess


def launch_noesis_env():
    fish_path = "./external/fish-shell"
    build_dir = os.path.join(fish_path, "build")

    if not os.path.isdir(build_dir):
        print("Fish build directory not found. Please run 'python3 run.py install' first.")
        return False

    print("Launching Noesis environment...")
    print("Setting up environment variables...")

    env = os.environ.copy()
    env["NOESIS_ROOT"] = os.getcwd()
    env["FISH_PATH"] = fish_path
    env["FISH_BUILD_PATH"] = build_dir

    print("Starting Noesis Hub shell environment...")
    fish_bin = os.path.join(build_dir, "fish")
    subprocess.run([fish_bin], env=env)
    return True


if __name__ == "__main__":
    success = launch_noesis_env()
    sys.exit(0 if success else 1)
