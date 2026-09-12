#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import sys
import os
import importlib.util
from datetime import datetime


def _load_intent():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base, "soul", "intent.py")
    if not os.path.exists(path):
        print(f"ERROR: soul/intent.py not found at {path}")
        return None
    spec = importlib.util.spec_from_file_location("intent", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def print_header(title):
    print()
    print("=" * 54)
    print(f"  {title}")
    print("=" * 54)
    print()


def run_ai_tests():
    intent = _load_intent()
    if not intent:
        sys.exit(1)

    print_header("AI and Consciousness Integration Tests")
    print(f"Starting tests at {datetime.now()}")

    print_header("Testing AI Initialization")
    if hasattr(intent, "init_ai_system"):
        intent.init_ai_system()
    if hasattr(intent, "ai_status"):
        intent.ai_status()

    print_header("Testing Consciousness Models")
    models = getattr(intent, "CONSCIOUSNESS_MODELS", [])
    for model in models:
        print(f"Setting model to {model}...")
        if hasattr(intent, "set_consciousness_model"):
            intent.set_consciousness_model(model)
        print()

    print_header("Testing Consciousness Levels")
    for level in range(6):
        print(f"Setting level to {level}...")
        if hasattr(intent, "set_consciousness_level"):
            intent.set_consciousness_level(level)
        print()

    print_header("Testing Self-Reflection")
    for model in models:
        print(f"Testing reflection with {model} model...")
        if hasattr(intent, "set_consciousness_model"):
            intent.set_consciousness_model(model)
        if hasattr(intent, "perform_self_reflection"):
            intent.perform_self_reflection()
        print()

    print_header("Testing Emotion-Consciousness Integration")
    emotion_states = range(6)
    for emotion in emotion_states:
        intensity = min(emotion * 2, 10)
        if hasattr(intent, "set_emotion"):
            intent.set_emotion(emotion, intensity)
        if hasattr(intent, "emotional_response"):
            intent.emotional_response("This is a test input")
        print()

    print_header("Tests Completed")
    print(f"All tests finished at {datetime.now()}")


def main():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print("Starting AI test script...")
    print(f"Script path: {__file__}")
    print(f"Current directory: {os.getcwd()}")

    if os.path.exists(os.path.join(base, "soul", "intent.py")):
        print("Found intent.py")
    else:
        print("ERROR: soul/intent.py not found")

    if os.path.exists(os.path.join(base, "system", "ai-model", "unit.py")):
        print("Found unit.py")
    else:
        print("ERROR: system/ai-model/unit.py not found")

    print("Running AI and consciousness tests...")
    run_ai_tests()


if __name__ == "__main__":
    main()
