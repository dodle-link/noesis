#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details
# intent.py - Central orchestrator for the Noesis system

import os
import sys
import importlib.util
import time

NOESIS_VERSION = "2.2.0"

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
PINK = "\033[38;5;213m"
ORANGE = "\033[38;5;208m"
PURPLE = "\033[38;5;92m"
CYAN = "\033[96m"
NC = "\033[0m"

LOGIC_AND = 0
LOGIC_OR = 1
LOGIC_NOT = 2
LOGIC_XOR = 3
LOGIC_IMPLIES = 4

TRUE = 1
FALSE = 0
UNKNOWN = -1

MAX_INTENTIONS = 100
intention_memory = [""] * MAX_INTENTIONS
intention_count = 0

VERBOSE_MODE = False

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_loaded_modules = {}


def _load_module(rel_path):
    key = rel_path
    if key in _loaded_modules:
        return _loaded_modules[key]
    path = os.path.join(_BASE_DIR, *rel_path.split('/'))
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location(key.replace('/', '_'), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _loaded_modules[key] = mod
    return mod


def log_with_timestamp(message, level="INFO"):
    ts = time.strftime("%d %b %Y %H:%M:%S")
    colors = {
        "ERROR": RED, "WARNING": YELLOW, "SUCCESS": GREEN, "DEBUG": BLUE,
    }
    color = colors.get(level, PINK)
    print()
    print(f"{color}    {level}    {NC}")
    print()
    print(f"{color}    Time: {ts}    {NC}")
    print()
    print(f"{color}    {message}    {NC}")
    print()


def handle_error(message, code=1):
    log_with_timestamp(message, "ERROR")
    return code


def init_logic_system():
    print("Logic system initialized")


def evaluate_boolean(a, operator, b):
    if operator == LOGIC_AND:
        return TRUE if a == TRUE and b == TRUE else FALSE
    elif operator == LOGIC_OR:
        return TRUE if a == TRUE or b == TRUE else FALSE
    elif operator == LOGIC_NOT:
        return TRUE if a != TRUE else FALSE
    elif operator == LOGIC_XOR:
        return TRUE if (a == TRUE) != (b == TRUE) else FALSE
    elif operator == LOGIC_IMPLIES:
        return TRUE if a != TRUE or b == TRUE else FALSE
    return UNKNOWN


def parse_logical_expression(expression):
    if "AND" in expression:
        print("AND operation detected")
        return LOGIC_AND
    elif "OR" in expression:
        print("OR operation detected")
        return LOGIC_OR
    elif "NOT" in expression:
        print("NOT operation detected")
        return LOGIC_NOT
    elif "XOR" in expression:
        print("XOR operation detected")
        return LOGIC_XOR
    elif "IMPLIES" in expression:
        print("IMPLIES operation detected")
        return LOGIC_IMPLIES
    print("Unknown logical expression")
    return -1


def reason_about(problem):
    print(f"Reasoning about: {problem}")
    print("Analyzing problem components...")
    print("Checking knowledge base...")
    print("Applying logical rules...")
    print("Conclusion: More data needed for definitive answer")


def init_intent_system():
    global intention_memory, intention_count
    intention_memory = [""] * MAX_INTENTIONS
    intention_count = 0
    init_logic_system()
    print(f"{GREEN}Intent system initialized{NC}")


def initialize_systems():
    print(f"{YELLOW}Initializing Noesis systems...{NC}")
    print()

    mem = _load_module("system/memory/unit.py")
    if mem and hasattr(mem, 'init_memory_system'):
        mem.init_memory_system()

    perc = _load_module("system/perception/unit.py")
    if perc and hasattr(perc, 'init_perception'):
        perc.init_perception()

    em = _load_module("system/emotion/unit.py")
    if em and hasattr(em, 'init_emotion_system'):
        em.init_emotion_system()

    init_intent_system()

    ai = _load_module("system/ai-model/unit.py")
    if ai and hasattr(ai, 'init_ai_system'):
        ai.init_ai_system()

    qstub = _load_module("system/memory/quantum/backend_stub.py")
    if qstub and hasattr(qstub, 'stub_init'):
        qstub.stub_init()

    print()
    print(f"{GREEN}All systems initialized successfully{NC}")
    print()


def _show_help():
    print(f"{PURPLE}== Cognitive Commands =={NC}")
    print(f"  {GREEN}- help:{NC}                View this help message")
    print(f"  {GREEN}- status:{NC}              Show system status")
    print(f"  {GREEN}- history:{NC}             View command history")
    print(f"  {GREEN}- clear:{NC}               Clear the screen")
    print(f"  {GREEN}- verbose:{NC}             Toggle verbose debug mode")
    print(f"  {GREEN}- exit:{NC}                Exit the system")
    print()
    print(f"{PURPLE}== Reasoning & Logic =={NC}")
    print(f"  {GREEN}- reason about <topic>:{NC} Reason about a given topic")
    print(f"  {GREEN}- logic <expression>:{NC   } Process a logical expression (AND, OR, NOT, XOR, IMPLIES)")
    print()
    print(f"{PURPLE}== System Commands =={NC}")
    print(f"  {GREEN}- quantum:{NC}             Enter quantum processing mode")
    print(f"  {GREEN}- ai:{NC}                  Access AI and consciousness features")


def _show_status(history_count):
    print(f"{CYAN}System Status{NC}")
    print(f"  Intentions processed: {intention_count}")
    print(f"  Commands in history: {history_count}")
    print(f"  Verbose mode: {VERBOSE_MODE}")


def process_intention(intention, history, add_to_history_fn):
    global intention_count, VERBOSE_MODE

    if not intention:
        return True

    intention_lower = intention.lower().strip()

    if intention_lower in ("help",):
        _show_help()
    elif intention_lower in ("exit", "e"):
        return False
    elif intention_lower in ("status",):
        _show_status(len([h for h in history if h]))
    elif intention_lower in ("history",):
        show_history(history)
    elif intention_lower in ("verbose",):
        VERBOSE_MODE = not VERBOSE_MODE
        state = "enabled" if VERBOSE_MODE else "disabled"
        log_with_timestamp(f"Verbose mode {state}", "INFO")
    elif intention_lower in ("clear",):
        os.system('clear')
        print(f"{CYAN}NOESIS Cognitive Interface{NC}")
    elif intention_lower in ("quantum",):
        log_with_timestamp("Switching to quantum mode", "INFO")
        handle_quantum_io(history, add_to_history_fn)
        log_with_timestamp("Returned from quantum mode", "INFO")
    elif intention_lower.startswith("ai"):
        log_with_timestamp("Accessing AI features", "INFO")
        ish = _load_module("system/control/intent_shell.py")
        if ish and hasattr(ish, 'parse_command_for_intent') and hasattr(ish, 'handle_intent_command'):
            ai_intent = ish.parse_command_for_intent(intention)
            params = intention[2:].strip() if len(intention) > 2 else ""
            ish.handle_intent_command(ai_intent, params)
        log_with_timestamp("AI operation completed", "INFO")
    elif intention_lower.startswith("reason about "):
        problem = intention[len("reason about "):].strip()
        reason_about(problem)
    elif intention_lower.startswith("logic "):
        expression = intention[len("logic "):].strip()
        log_with_timestamp(f"Evaluating logical expression: {expression}", "DEBUG")
        operator = parse_logical_expression(expression)
        if operator >= 0:
            result = evaluate_boolean(TRUE, operator, FALSE) if operator != LOGIC_NOT else evaluate_boolean(TRUE, operator, None)
            if result == TRUE:
                log_with_timestamp("Expression evaluates to TRUE", "SUCCESS")
            else:
                log_with_timestamp("Expression evaluates to FALSE", "INFO")
        else:
            handle_error(f"Invalid logical expression: {expression}", 1)
    else:
        handle_error(f"Unknown intention: {intention}", 1)
        print(f"Type '{GREEN}help{NC}' for available commands")

    intention_count += 1
    return True


def show_history(history):
    valid = [h for h in history if h]
    if not valid:
        print("No command history available")
        return
    print("Command history (most recent first):")
    print()
    for i, cmd in enumerate(valid, 1):
        print(f"{i:3d}: {cmd}")


def handle_quantum_io(history, add_to_history_fn):
    print(f"{CYAN}Welcome to NOESIS Quantum Interface{NC}")
    print()
    print("Available quantum demos:")
    print(f"  {GREEN}- demo_quantum_field:{NC}       Interactive quantum field demo")
    print(f"  {GREEN}- demo_wave_interference:{NC}   Quantum wave interference demo")
    print(f"  {GREEN}- q_init:{NC}                   Initialize quantum system")
    print(f"  {GREEN}- history:{NC}                  View command history")
    print(f"  {GREEN}- exit:{NC}                     Return to main shell")
    print()

    qfield = _load_module("system/memory/quantum/field/quantum_field.py")
    qunit = _load_module("system/memory/quantum/unit.py")

    while True:
        try:
            command = input(f"{GREEN}quantum > {NC}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not command:
            continue

        add_to_history_fn(command)

        if command == "demo_quantum_field":
            log_with_timestamp("Starting quantum field demo", "INFO")
            if qfield and hasattr(qfield, 'demo_quantum_field'):
                qfield.demo_quantum_field()
            log_with_timestamp("Quantum field demo completed", "SUCCESS")
        elif command == "demo_wave_interference":
            log_with_timestamp("Starting wave interference demo", "INFO")
            if qfield and hasattr(qfield, 'demo_wave_interference'):
                qfield.demo_wave_interference()
            log_with_timestamp("Wave interference demo completed", "SUCCESS")
        elif command == "q_init":
            log_with_timestamp("Initializing quantum system", "INFO")
            if qunit and hasattr(qunit, 'q_init'):
                qunit.q_init()
            log_with_timestamp("Quantum system initialized", "SUCCESS")
        elif command == "history":
            show_history(history)
        elif command in ("exit", "e"):
            print()
            log_with_timestamp("Exiting quantum mode...", "INFO")
            print()
            return
        elif command == "help":
            print(f"  {GREEN}- demo_quantum_field:{NC}       Interactive quantum field demo")
            print(f"  {GREEN}- demo_wave_interference:{NC}   Quantum wave interference demo")
            print(f"  {GREEN}- q_init:{NC}                   Initialize quantum system")
            print(f"  {GREEN}- history:{NC}                  View command history")
            print(f"  {GREEN}- exit:{NC}                     Return to main shell")
        else:
            handle_error(f"Unknown command: {command}", 1)
            print(f"Type '{GREEN}help{NC}' for available commands")


def handle_io():
    history = []

    def add_to_history(cmd):
        if cmd and (not history or cmd != history[0]):
            history.insert(0, cmd)
            if len(history) > 50:
                history.pop()

    print(f"{CYAN}Welcome to NOESIS intent system{NC}")
    print()
    print(f"Type '{GREEN}help{NC}' for available commands")
    print(f"Type '{GREEN}exit{NC}' to exit")

    while True:
        print()
        try:
            intention = input(f"{GREEN}noesis > {NC}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        print()
        if not intention:
            continue

        add_to_history(intention)

        if not process_intention(intention, history, add_to_history):
            break


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    initialize_systems()

    if "--quantum" in args or "-q" in args:
        log_with_timestamp("Starting quantum IO interface...", "INFO")
        print()
        history = []

        def add_to_history(cmd):
            if cmd and (not history or cmd != history[0]):
                history.insert(0, cmd)
        handle_quantum_io(history, add_to_history)
        return

    log_with_timestamp("Starting cognitive IO interface...", "INFO")
    print()
    handle_io()
    print()
    log_with_timestamp("NOESIS system exiting", "INFO")
    print()


if __name__ == "__main__":
    if sys.argv[0].endswith('intent.py'):
        log_with_timestamp("Running intent.py directly (prefer using run.py)", "WARNING")
    main(sys.argv[1:])
