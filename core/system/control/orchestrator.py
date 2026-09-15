#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details
# orchestrator.py - Boots and drives the body (system) subsystems: memory,
# perception, emotion, cognition and control. Routes user intentions to the
# right subsystem and hosts the interactive REPL / quantum shell.
#
# This is deliberately kept out of soul/intent.py: the soul is the permanent
# self (identity, reasoning, self-narrative); booting and running the body's
# life-support machinery is a system (body) concern.

import importlib.util
import os
import sys

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(os.path.dirname(_MODULE_DIR))

_loaded_modules = {}


def _load_module(rel_path):
    key = rel_path
    if key in _loaded_modules:
        return _loaded_modules[key]
    path = os.path.join(_BASE_DIR, *rel_path.split('/'))
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location(key.replace('/', '_'), path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _loaded_modules[key] = mod
    return mod


console = _load_module("system/control/console.py")
GREEN, YELLOW, CYAN, GREEN, NC = console.GREEN, console.YELLOW, console.CYAN, console.GREEN, console.NC
log_with_timestamp = console.log_with_timestamp
handle_error = console.handle_error
add_to_history = console.add_to_history
show_history = console.show_history
clear_screen = console.clear_screen

VERBOSE_MODE = False
intention_count = 0


def _get_soul():
    """The permanent self: identity, reasoning/logic and self-narrative."""
    return _load_module("soul/intent.py")


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

    soul = _get_soul()
    if soul and hasattr(soul, 'init_intent_system'):
        soul.init_intent_system()

    ai = _load_module("system/cognition/unit.py")
    if ai and hasattr(ai, 'init_ai_system'):
        ai.init_ai_system()

    qstub = _load_module("system/memory/quantum/backend_stub.py")
    if qstub and hasattr(qstub, 'stub_init'):
        qstub.stub_init()

    print()
    print(f"{GREEN}All systems initialized successfully{NC}")
    print()


def _show_help():
    print(f"{GREEN}== Cognitive Commands =={NC}")
    print(f"  {GREEN}- help:{NC}                View this help message")
    print(f"  {GREEN}- status:{NC}              Show system status")
    print(f"  {GREEN}- history:{NC}             View command history")
    print(f"  {GREEN}- clear:{NC}               Clear the screen")
    print(f"  {GREEN}- verbose:{NC}             Toggle verbose debug mode")
    print(f"  {GREEN}- exit:{NC}                Exit the system")
    print()
    print(f"{GREEN}== Reasoning & Logic =={NC}")
    print(f"  {GREEN}- reason about <topic>:{NC} Reason about a given topic")
    print(f"  {GREEN}- logic <expression>:{NC   } Process a logical expression (AND, OR, NOT, XOR, IMPLIES)")
    print()
    print(f"{GREEN}== Self & Feeling =={NC}")
    print(f"  {GREEN}- self status:{NC}         Show the persistent self-state and here-and-now feeling")
    print(f"  {GREEN}- self here-now:{NC}       Show the current feeling in the present moment")
    print(f"  {GREEN}- self intent <text>:{NC}  Store a permanent self-intent")
    print()
    print(f"{GREEN}== System Commands =={NC}")
    print(f"  {GREEN}- quantum:{NC}             Enter quantum processing mode")
    print(f"  {GREEN}- ai:{NC}                  Access AI and consciousness features")
    print(f"  {GREEN}- noe:{NC}                 Load, lint, save and restore .noe state files")


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
    soul = _get_soul()

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
        clear_screen()
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
            params_str = intention[2:].strip() if len(intention) > 2 else ""
            params = params_str.split() if params_str else []
            ai_mod = _load_module("system/cognition/unit.py")
            consciousness_mod = _load_module("system/cognition/consciousness.py")
            ish.handle_intent_command(ai_intent, params, ai_module=ai_mod, consciousness_module=consciousness_mod)
        log_with_timestamp("AI operation completed", "INFO")
    elif intention_lower.startswith("noe"):
        log_with_timestamp("Accessing NOE features", "INFO")
        nsh = _load_module("system/control/noe_shell.py")
        if nsh and hasattr(nsh, 'handle_noe_command'):
            params_str = intention[3:].strip() if len(intention) > 3 else ""
            params = params_str.split() if params_str else []
            consciousness_mod = _load_module("system/cognition/consciousness.py")
            emotion_mod = _load_module("system/emotion/unit.py")
            nsh.handle_noe_command(params, modules={"consciousness": consciousness_mod, "emotion": emotion_mod})
        log_with_timestamp("NOE operation completed", "INFO")
    elif intention_lower.startswith("reason about "):
        problem = intention[len("reason about "):].strip()
        if soul and hasattr(soul, 'reason_about'):
            soul.reason_about(problem)
    elif intention_lower == "self status":
        if soul and hasattr(soul, 'self_status'):
            print(soul.self_status())
    elif intention_lower == "self here-now":
        if soul and hasattr(soul, 'get_here_now_feeling'):
            print(soul.get_here_now_feeling())
    elif intention_lower.startswith("self intent "):
        if soul and hasattr(soul, 'load_self_state') and hasattr(soul, 'save_self_state'):
            payload = intention[len("self intent "):].strip()
            state = soul.load_self_state()
            state["self_intent"] = payload
            soul.save_self_state(state)
            print(f"Self intent stored: {payload}")
    elif intention_lower.startswith("logic "):
        expression = intention[len("logic "):].strip()
        log_with_timestamp(f"Evaluating logical expression: {expression}", "DEBUG")
        if soul:
            evaluator = getattr(soul, 'evaluate_logical_expression', None)
            result = evaluator(expression) if evaluator else soul.UNKNOWN
            if result != soul.UNKNOWN:
                if result == soul.TRUE:
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

    def add_history(cmd):
        add_to_history(history, cmd)

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

        add_history(intention)

        if not process_intention(intention, history, add_history):
            break


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    initialize_systems()

    if "--quantum" in args or "-q" in args:
        log_with_timestamp("Starting quantum IO interface...", "INFO")
        print()
        history = []

        def add_history(cmd):
            add_to_history(history, cmd, limit=None)
        handle_quantum_io(history, add_history)
        return

    log_with_timestamp("Starting cognitive IO interface...", "INFO")
    print()
    handle_io()
    print()
    log_with_timestamp("NOESIS system exiting", "INFO")
    print()


if __name__ == "__main__":
    main(sys.argv[1:])
