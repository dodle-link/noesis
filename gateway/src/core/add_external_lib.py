#!/usr/bin/env python3
import os
import sys
import subprocess


def add_external_lib(lib_name, git_url=None):
    if not lib_name:
        print("Usage: add_external_lib.py <library_name> [git_url]")
        return False

    external_path = os.path.join(os.getcwd(), "external")

    if not os.path.isdir(external_path):
        print("Creating external directory...")
        os.makedirs(external_path)

    lib_path = os.path.join(external_path, lib_name)
    if not os.path.isdir(lib_path):
        print(f"Cloning {lib_name} repository...")
        subprocess.run(["git", "clone", git_url, lib_name], cwd=external_path)
        print(f"{lib_name} repository cloned successfully")
    else:
        print(f"{lib_name} repository already exists at {lib_path}")
        print(f"To update: cd {lib_path} && git pull")

    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: add_external_lib.py <library_name> [git_url]")
        sys.exit(1)
    success = add_external_lib(args[0], args[1] if len(args) > 1 else None)
    sys.exit(0 if success else 1)
