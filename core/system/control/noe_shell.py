#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import os
import sys
import importlib.util

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_CORE_DIR = os.path.dirname(os.path.dirname(_MODULE_DIR))
_STATE_IO_PATH = os.path.join(os.path.dirname(_MODULE_DIR), "noe", "state_io.py")

_state_io = None


def _get_state_io():
    global _state_io
    if _state_io:
        return _state_io
    if not os.path.isfile(_STATE_IO_PATH):
        return None
    spec = importlib.util.spec_from_file_location("state_io", _STATE_IO_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _state_io = mod
    return mod


def handle_noe_command(params, modules=None):
    if not params:
        _print_help()
        return

    cmd = params[0]
    args = params[1:]
    modules = modules or {}

    dispatch = {
        "load": lambda: _cmd_load(args),
        "lint": lambda: _cmd_lint(args),
        "status": lambda: _cmd_status(),
        "save": lambda: _cmd_save(modules),
        "restore": lambda: _cmd_restore(modules),
    }

    fn = dispatch.get(cmd)
    if fn:
        fn()
    else:
        print(f"Unknown noe command: {cmd}")
        _print_help()


def _print_help():
    print("NOE system commands:")
    print("  noe load <file>   - Parse a .noe file and display JSON output")
    print("  noe lint <file>   - Lint/validate a .noe file")
    print("  noe status        - Show persisted state files")
    print("  noe save          - Save agent state to .noe files")
    print("  noe restore       - Restore agent state from .noe files")


def _cmd_load(args):
    if not args:
        print("Usage: noe load <file>")
        return
    path = " ".join(args)
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}")
        return
    sio = _get_state_io()
    if not sio:
        print("Error: state_io module not available")
        return
    parser = sio.load_parser()
    if not parser:
        print(f"Error: noe parser not found")
        return
    with open(path) as f:
        content = f.read()
    raw = parser.parse_noe(content)
    print(parser.to_json(raw))


def _cmd_lint(args):
    if not args:
        print("Usage: noe lint <file>")
        return
    path = " ".join(args)
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}")
        return
    sio = _get_state_io()
    if not sio:
        print("Error: state_io module not available")
        return
    linter = sio.load_linter()
    if not linter:
        print("Error: noe linter not found")
        return
    linter.validate_grammar(path, verbose=True)


def _cmd_status():
    sio = _get_state_io()
    if not sio:
        print("Error: state_io module not available")
        return
    state_dir = sio.STATE_DIR
    if not os.path.isdir(state_dir):
        print(f"No state directory found at {state_dir}")
        print("Run 'noe save' to create initial state files.")
        return
    files = [f for f in os.listdir(state_dir) if f.endswith(".noe")]
    if not files:
        print(f"State directory exists but contains no .noe files: {state_dir}")
        return
    print(f"NOE state files in {state_dir}:")
    for fname in sorted(files):
        fpath = os.path.join(state_dir, fname)
        state = sio.load_noe_state(fpath)
        print(f"  {fname}:")
        for k, v in state.items():
            print(f"    {k} = {v!r}")


def _cmd_save(modules):
    sio = _get_state_io()
    if not sio:
        print("Error: state_io module not available")
        return

    consciousness = modules.get("consciousness")
    if consciousness:
        sio.save_noe_state(
            sio.state_file("consciousness"),
            "ConsciousnessState",
            {
                "model": getattr(consciousness, "CONSCIOUSNESS_MODEL", "IIT"),
                "level": getattr(consciousness, "CONSCIOUSNESS_LEVEL", 3),
                "reflection_interval": getattr(consciousness, "SELF_REFLECTION_INTERVAL", 300),
            }
        )
        print(f"Saved consciousness state to {sio.state_file('consciousness')}")

    emotion = modules.get("emotion")
    if emotion:
        sio.save_noe_state(
            sio.state_file("emotion"),
            "EmotionState",
            {
                "emotion": getattr(emotion, "current_emotion", 0),
                "intensity": getattr(emotion, "emotion_intensity", 0),
            }
        )
        print(f"Saved emotion state to {sio.state_file('emotion')}")

    if not consciousness and not emotion:
        print("No modules available to save")


def _cmd_restore(modules):
    sio = _get_state_io()
    if not sio:
        print("Error: state_io module not available")
        return

    consciousness = modules.get("consciousness")
    if consciousness:
        state = sio.load_noe_state(sio.state_file("consciousness"))
        if state:
            if "model" in state and hasattr(consciousness, "set_consciousness_model"):
                consciousness.set_consciousness_model(state["model"])
            if "level" in state and hasattr(consciousness, "set_consciousness_level"):
                consciousness.set_consciousness_level(state["level"])
            print("Restored consciousness state from .noe")
        else:
            print("No consciousness state file found")

    emotion = modules.get("emotion")
    if emotion:
        state = sio.load_noe_state(sio.state_file("emotion"))
        if state:
            if "emotion" in state and hasattr(emotion, "set_emotion"):
                emotion.set_emotion(int(state["emotion"]), int(state.get("intensity", 5)))
            print("Restored emotion state from .noe")
        else:
            print("No emotion state file found")
