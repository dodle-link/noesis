#!/usr/bin/env python3
import os
import sys
import subprocess


def install_noesis():
    print("Starting Noesis Hub installation...")
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "link_fish.py")])

    fish_path = "./external/fish-shell"
    build_dir = os.path.join(fish_path, "build")

    os.makedirs(build_dir, exist_ok=True)

    print("Building fish-shell...")
    subprocess.run(["cmake", "-G", "Ninja", ".."], cwd=build_dir)
    subprocess.run(["ninja"], cwd=build_dir)

    print("Linking libraries...")
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "link_libraries.py")])

    print("Noesis Hub installation complete!")
    print("You can now run 'python3 run.py launch_env' to start the Noesis Hub environment")


if __name__ == "__main__":
    install_noesis()
