#!/usr/bin/env python3
import subprocess
import shutil
import sys


def install_dependency():
    print("Installing dependencies for Noesis Hub...")
    packages = ["cmake", "ninja", "gcc", "pkg-config", "gettext", "pcre2", "ncurses"]

    if shutil.which("brew"):
        print("Using Homebrew package manager...")
        subprocess.run(["brew", "update"])
        for pkg in packages:
            print(f"Installing {pkg}...")
            subprocess.run(["brew", "install", pkg])
    elif shutil.which("apt-get"):
        print("Using apt package manager...")
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "-y",
                        "build-essential", "cmake", "ninja-build",
                        "libncurses5-dev", "libpcre2-dev", "gettext"])
    elif shutil.which("dnf"):
        print("Using dnf package manager...")
        subprocess.run(["sudo", "dnf", "install", "-y",
                        "gcc", "gcc-c++", "cmake", "ninja-build",
                        "ncurses-devel", "pcre2-devel", "gettext-devel"])
    elif shutil.which("pacman"):
        print("Using pacman package manager...")
        subprocess.run(["sudo", "pacman", "-Syu", "--noconfirm",
                        "gcc", "cmake", "ninja", "ncurses", "pcre2", "gettext"])
    else:
        print("No supported package manager found. Please install manually:")
        for pkg in ["cmake", "ninja or make", "gcc and g++", "libncurses", "libpcre2", "gettext"]:
            print(f"- {pkg}")
        return False

    print("Core dependencies installation complete!")
    print("You may now run 'python3 run.py install' to build the project")
    return True


if __name__ == "__main__":
    success = install_dependency()
    sys.exit(0 if success else 1)
