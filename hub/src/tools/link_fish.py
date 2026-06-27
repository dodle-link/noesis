#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess


def ensure_fish_repo():
    external_path = os.path.join(os.getcwd(), "external")
    fish_repo_path = os.path.join(external_path, "fish-shell")

    os.makedirs(external_path, exist_ok=True)

    if not os.path.isdir(fish_repo_path):
        print("Fish shell repository not found. Initializing git submodule...")
        subprocess.run(["git", "submodule", "init"])
        subprocess.run(["git", "submodule", "update"])
    elif not os.path.exists(os.path.join(fish_repo_path, "CMakeLists.txt")):
        print("Fish shell submodule appears empty. Updating submodule...")
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"])
    else:
        print(f"Fish shell repository already exists at {fish_repo_path}")

    print(f"Fish shell repository is ready at {fish_repo_path}")


def build_fish():
    fish_repo_path = os.path.join(os.getcwd(), "external", "fish-shell")

    if not os.path.isdir(fish_repo_path):
        print("Fish shell repository not found. Run ensure_fish_repo first.")
        return False

    print("Building fish shell from the repository...")
    build_dir = os.path.join(fish_repo_path, "build")
    os.makedirs(build_dir, exist_ok=True)

    subprocess.run(["cmake", ".."], cwd=build_dir)
    cpu_count = os.cpu_count() or 1
    subprocess.run(["make", f"-j{cpu_count}"], cwd=build_dir)

    print(f"Fish shell built at {build_dir}")
    return True


def link_fish_to_noesis():
    fish_build_path = os.path.join(os.getcwd(), "external", "fish-shell", "build")
    noesis_lib_path = os.path.join(os.getcwd(), "lib", "fish")

    if not os.path.isdir(fish_build_path):
        print("Fish shell build not found. Run build_fish first.")
        return False

    os.makedirs(noesis_lib_path, exist_ok=True)
    print("Linking fish shell libraries to noesis-hub...")

    for name in ["fish", "share"]:
        src = os.path.join(fish_build_path, name)
        dst = os.path.join(noesis_lib_path, name)
        if os.path.exists(src):
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

    print(f"Fish shell linked to noesis-hub at {noesis_lib_path}")
    return True


COMMANDS = {
    "ensure": ensure_fish_repo,
    "build": build_fish,
    "link": link_fish_to_noesis,
    "all": lambda: (ensure_fish_repo(), build_fish(), link_fish_to_noesis()),
}

USAGE = ("Usage: link_fish.py [ensure|build|link|all]\n"
         "  ensure  - Ensure fish-shell repository exists\n"
         "  build   - Build the fish-shell repository\n"
         "  link    - Link fish-shell to noesis-hub\n"
         "  all     - Run all steps")


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return

    cmd = sys.argv[1]
    if cmd in COMMANDS:
        COMMANDS[cmd]()
    else:
        print(USAGE)


if __name__ == "__main__":
    main()
