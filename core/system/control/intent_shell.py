#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import subprocess
import sys
import os


def init_intent_shell():
    print("Intent shell initialized")


def process_shell_command(*args):
    if not args:
        return 1
    cmd = " ".join(str(a) for a in args)
    print(f"Processing shell command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout + result.stderr
    print("Command output:")
    print(output)
    return result.returncode


def parse_command_for_intent(command):
    command = command.lower()
    if "load" in command:
        return "LOAD_INTENT"
    elif "save" in command:
        return "SAVE_INTENT"
    elif "execute" in command:
        return "EXECUTE_INTENT"
    elif "analyze" in command:
        return "ANALYZE_INTENT"
    elif "ai" in command:
        return "AI_COMMAND"
    return "UNKNOWN_INTENT"


def handle_intent_command(intent, params=None, ai_module=None):
    params = params or []
    handlers = {
        "LOAD_INTENT": lambda: print(f"Loading intent from: {params}"),
        "SAVE_INTENT": lambda: print(f"Saving intent to: {params}"),
        "EXECUTE_INTENT": lambda: print(f"Executing intent: {params}"),
        "ANALYZE_INTENT": lambda: print(f"Analyzing intent: {params}"),
        "AI_COMMAND": lambda: handle_ai_command(params, ai_module=ai_module),
    }
    handler = handlers.get(intent)
    if handler:
        handler()
        return True
    print(f"Unknown intent command: {intent}")
    return False


def handle_ai_command(args, ai_module=None):
    if not args or args[0] in ("", "ai"):
        print("AI system commands:")
        print("  ai status              - Display AI system status")
        print("  ai install             - Install AI dependencies")
        print("  ai install-py13        - Install AI dependencies for Python 3.13+")
        print("  ai list-models         - List available AI models")
        print("  ai set-model MODEL     - Set active AI model")
        print("  ai thinking LEVEL      - Set AI thinking level (0-5)")
        print("  ai memory TOGGLE       - Toggle AI memory integration (on/off)")
        print("  ai generate PROMPT     - Generate text using the active model")
        print("  ai introspect          - Perform AI introspection")
        print()
        print("Consciousness commands:")
        print("  ai consciousness status           - Show consciousness status")
        print("  ai consciousness model MODEL      - Set consciousness model")
        print("  ai consciousness level LEVEL      - Set consciousness level (0-5)")
        print("  ai consciousness reflect          - Perform self-reflection")
        return

    cmd = args[0] if args else ""
    rest = args[1:] if len(args) > 1 else []

    if ai_module is None:
        print(f"AI command: {cmd} (no AI module loaded)")
        return

    dispatch = {
        "status": lambda: ai_module.ai_status() if hasattr(ai_module, "ai_status") else None,
        "install": lambda: ai_module.ai_install_dependencies() if hasattr(ai_module, "ai_install_dependencies") else None,
        "install-py13": lambda: subprocess.run([sys.executable, "tools/fast_ai_install_py13.py"]),
        "list-models": lambda: ai_module.ai_list_models() if hasattr(ai_module, "ai_list_models") else None,
        "set-model": lambda: ai_module.ai_set_model(rest[0]) if rest and hasattr(ai_module, "ai_set_model") else None,
        "thinking": lambda: ai_module.ai_set_thinking_level(int(rest[0])) if rest and hasattr(ai_module, "ai_set_thinking_level") else None,
        "memory": lambda: ai_module.ai_toggle_memory_integration() if hasattr(ai_module, "ai_toggle_memory_integration") else None,
        "generate": lambda: ai_module.ai_generate(" ".join(rest)) if rest and hasattr(ai_module, "ai_generate") else None,
        "introspect": lambda: ai_module.ai_introspect() if hasattr(ai_module, "ai_introspect") else None,
        "consciousness": lambda: handle_consciousness_command(rest, ai_module),
    }

    fn = dispatch.get(cmd)
    if fn:
        fn()
    else:
        print(f"Unknown AI command: {cmd}")


def handle_consciousness_command(args, ai_module=None):
    if not args:
        print("Usage: ai consciousness [status|model|level|reflect|research|models]")
        return

    cmd = args[0]
    rest = args[1:] if len(args) > 1 else []

    if ai_module is None:
        print(f"Consciousness command: {cmd} (no AI module loaded)")
        return

    if cmd == "status":
        model = getattr(ai_module, "CONSCIOUSNESS_MODEL", "unknown")
        level = getattr(ai_module, "CONSCIOUSNESS_LEVEL", 0)
        print(f"Consciousness Status:\n  Model: {model}\n  Level: {level}/5")
    elif cmd == "model" and rest:
        if hasattr(ai_module, "set_consciousness_model"):
            ai_module.set_consciousness_model(rest[0])
    elif cmd == "level" and rest:
        if hasattr(ai_module, "set_consciousness_level"):
            ai_module.set_consciousness_level(int(rest[0]))
    elif cmd == "reflect":
        if hasattr(ai_module, "perform_self_reflection"):
            ai_module.perform_self_reflection()
    elif cmd == "research":
        if hasattr(ai_module, "get_latest_consciousness_research"):
            ai_module.get_latest_consciousness_research()
    elif cmd == "models":
        models = getattr(ai_module, "CONSCIOUSNESS_MODELS", [])
        names = getattr(ai_module, "CONSCIOUSNESS_MODEL_NAMES", [])
        print("Available Consciousness Models:")
        for m, n in zip(models, names):
            print(f"  {m} - {n}")
    else:
        print(f"Unknown consciousness command: {cmd}")
