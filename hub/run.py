#!/usr/bin/env python3
import sys
import os
import subprocess


def show_menu():
    print("===== NOESIS HUB CONTROL CENTER =====")
    print("Available commands:")
    print("1. run             - Run Noesis Hub")
    print("2. install         - Install Noesis Hub")
    print("3. link_libraries  - Link with Core Libraries")
    print("4. install_dep     - Install Core Dependencies")
    print("5. add_lib         - Add External Library")
    print("6. launch_env      - Launch Noesis Environment")
    print("7. cleanup_struct  - Clean up Structure")
    print("8. cleanup_aggr    - Clean up Structure (Aggressive)")
    print("9. start_api       - Start NOE API Server")
    print("0. stop_api        - Stop NOE API Server")
    print("s. api_status      - Check NOE API Status")
    print("h. help            - Show this menu")
    print("q. quit            - Exit this menu")
    print("==================================")


def run_script(script, args=None):
    args = args or []
    for base in ["src/core", "src/tools"]:
        path = os.path.join(os.path.dirname(__file__), base, f"{script}.py")
        if os.path.exists(path):
            subprocess.run([sys.executable, path] + args)
            return
    print(f"Error: Script {script}.py not found in src/core or src/tools")


def run_api(cmd, *args):
    path = os.path.join(os.path.dirname(__file__), "src", "api", "noe_api.py")
    subprocess.run([sys.executable, path, cmd] + list(args))


COMMANDS = {
    "run": lambda args: run_script("run", args),
    "install": lambda args: run_script("install", args),
    "link_libraries": lambda args: run_script("link_libraries", args),
    "install_dep": lambda args: run_script("install_dependency", args),
    "add_lib": lambda args: run_script("add_external_lib", args),
    "launch_env": lambda args: run_script("launch_noesis_env", args),
    "cleanup_struct": lambda args: run_script("cleanup_structure", args),
    "cleanup_aggr": lambda args: run_script("cleanup_structure_aggressive", args),
    "start_api": lambda args: run_api("start"),
    "stop_api": lambda args: run_api("stop"),
    "api_status": lambda args: run_api("status"),
    "help": lambda args: show_menu(),
}

MENU_MAP = {
    "1": "run", "2": "install", "3": "link_libraries", "4": "install_dep",
    "5": "add_lib", "6": "launch_env", "7": "cleanup_struct", "8": "cleanup_aggr",
    "9": "start_api", "0": "stop_api", "s": "api_status", "h": "help",
}


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        args = sys.argv[2:]
        if cmd == "process_noe":
            if not args:
                print("Error: Missing file path\nUsage: run.py process_noe <file_path>")
                sys.exit(1)
            run_api("process", args[0])
        elif cmd == "exec_noe":
            if not args:
                print("Error: Missing command\nUsage: run.py exec_noe <command>")
                sys.exit(1)
            run_api("exec", *args)
        elif cmd in COMMANDS:
            COMMANDS[cmd](args)
        else:
            print(f"Unknown command: {cmd}")
            show_menu()
            sys.exit(1)
        return

    show_menu()
    while True:
        try:
            choice = input("Enter your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Noesis Hub Control Center.")
            break

        if choice in ("q", "quit"):
            print("Exiting Noesis Hub Control Center.")
            break
        elif choice in MENU_MAP:
            COMMANDS[MENU_MAP[choice]]([])
        else:
            print("Invalid choice. Please try again.")
        print()


if __name__ == "__main__":
    main()
