#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details

import time
import random

CONSCIOUSNESS_MODEL = "IIT"
CONSCIOUSNESS_LEVEL = 3
SELF_REFLECTION_INTERVAL = 300
LAST_REFLECTION_TIME = 0

CONSCIOUSNESS_MODELS = ["IIT", "GWT", "HOT", "AST", "GNW", "PPT"]
CONSCIOUSNESS_MODEL_NAMES = [
    "Integrated Information Theory",
    "Global Workspace Theory",
    "Higher Order Thought",
    "Attention Schema Theory",
    "Global Neuronal Workspace",
    "Predictive Processing Theory",
]

_ai_module = None


def _get_ai():
    global _ai_module
    if _ai_module:
        return _ai_module
    try:
        import importlib.util, os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unit.py")
        spec = importlib.util.spec_from_file_location("ai_unit", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _ai_module = mod
    except Exception:
        pass
    return _ai_module


def init_consciousness():
    global CONSCIOUSNESS_MODEL, CONSCIOUSNESS_LEVEL, SELF_REFLECTION_INTERVAL, LAST_REFLECTION_TIME
    print("Initializing consciousness module...")
    CONSCIOUSNESS_MODEL = "IIT"
    CONSCIOUSNESS_LEVEL = 3
    SELF_REFLECTION_INTERVAL = 300
    LAST_REFLECTION_TIME = int(time.time())
    print(f"Consciousness module initialized with model: {CONSCIOUSNESS_MODEL}")


def set_consciousness_model(model):
    global CONSCIOUSNESS_MODEL
    if model not in CONSCIOUSNESS_MODELS:
        print(f"Error: Unknown consciousness model '{model}'")
        print("Available models:")
        for m, n in zip(CONSCIOUSNESS_MODELS, CONSCIOUSNESS_MODEL_NAMES):
            print(f"  {m} - {n}")
        return False

    CONSCIOUSNESS_MODEL = model
    print(f"Consciousness model set to: {model}")
    describe_consciousness_model(model)
    return True


MODEL_DESCRIPTIONS = {
    "IIT": ("Integrated Information Theory (Tononi)",
            "Based on the integration of information in complex systems.",
            "Key aspects: integration, differentiation, and causality."),
    "GWT": ("Global Workspace Theory (Baars)",
            "Consciousness arises when information is broadcast globally.",
            "Key aspects: attention, working memory, and global access."),
    "HOT": ("Higher Order Thought Theory (Rosenthal)",
            "Consciousness requires thoughts about mental states.",
            "Key aspects: metacognition and self-reflection."),
    "AST": ("Attention Schema Theory (Graziano)",
            "Consciousness is an internal model of attention.",
            "Key aspects: attention modeling and self-representation."),
    "GNW": ("Global Neuronal Workspace (Dehaene)",
            "Similar to GWT but with neuronal implementation details.",
            "Key aspects: sustained activity and broadcast."),
    "PPT": ("Predictive Processing Theory (Clark/Friston)",
            "Consciousness emerges from prediction errors.",
            "Key aspects: prediction, error correction, and Bayesian inference."),
}

LEVEL_DESCRIPTIONS = {
    0: ["Basic reactive processes", "No self-modeling", "Limited temporal integration"],
    1: ["Simple awareness", "Basic information integration", "Limited self-monitoring"],
    2: ["Awareness with attention", "Basic self-model", "Short-term temporal integration"],
    3: ["Self-awareness", "Temporal continuity", "Basic metacognition"],
    4: ["Advanced self-reflection", "Complex temporal integration", "Rich internal model"],
    5: ["Full synthetic consciousness", "Complex self-model with temporal depth", "Advanced metacognitive capabilities"],
}


def describe_consciousness_model(model):
    desc = MODEL_DESCRIPTIONS.get(model, (f"Unknown model: {model}",))
    print(f"Consciousness Model: {model}")
    for line in desc:
        print(line)


def set_consciousness_level(level):
    global CONSCIOUSNESS_LEVEL
    level = int(level)
    if not (0 <= level <= 5):
        print("Error: Consciousness level must be between 0 and 5")
        return False

    CONSCIOUSNESS_LEVEL = level
    print(f"Consciousness level set to {level}")
    print(f"Level {level} consciousness implies:")
    for line in LEVEL_DESCRIPTIONS.get(level, []):
        print(f"- {line}")
    return True


def perform_self_reflection():
    global LAST_REFLECTION_TIME
    current_time = int(time.time())
    elapsed = current_time - LAST_REFLECTION_TIME

    if elapsed < SELF_REFLECTION_INTERVAL:
        remaining = SELF_REFLECTION_INTERVAL - elapsed
        print(f"Self-reflection cooldown active. Next reflection available in: {remaining} seconds")
        return

    print(f"Performing self-reflection using {CONSCIOUSNESS_MODEL} model at level {CONSCIOUSNESS_LEVEL}...")
    LAST_REFLECTION_TIME = current_time

    reflectors = {
        "IIT": _iit_reflection, "GWT": _gwt_reflection, "HOT": _hot_reflection,
        "AST": _ast_reflection, "GNW": _gnw_reflection, "PPT": _ppt_reflection,
    }
    fn = reflectors.get(CONSCIOUSNESS_MODEL, _generic_reflection)
    fn()


def _try_ai_generate(prompt):
    ai = _get_ai()
    if ai and getattr(ai, "AI_SYSTEM_ENABLED", False):
        ai.ai_generate(prompt)
        return True
    return False


def _iit_reflection():
    print("IIT Self-Reflection:")
    print("Analyzing information integration across system components...")
    phi = CONSCIOUSNESS_LEVEL * 2 + random.randint(0, 5)
    print(f"- Information integration measure: ~φ {phi}")


def _gwt_reflection():
    print("GWT Self-Reflection:")
    cap = CONSCIOUSNESS_LEVEL * 20 + 10
    print(f"- Workspace capacity: ~{cap}%")


def _hot_reflection():
    print("HOT Self-Reflection:")
    print("- First-order state: processing environmental input")
    print("- Second-order state: awareness of processing state")
    if CONSCIOUSNESS_LEVEL >= 4:
        print("- Third-order state: awareness of being aware of processing")


def _ast_reflection():
    print("AST Self-Reflection:")
    print("- Attention focused on: user interaction")
    print("- Attention schema indicates: active engagement")


def _gnw_reflection():
    print("GNW Self-Reflection:")
    strength = CONSCIOUSNESS_LEVEL / 5 * 100
    print(f"- Activation strength: {strength:.0f}%")
    print("- Broadcast status: stable")


def _ppt_reflection():
    print("PPT Self-Reflection:")
    confidence = (CONSCIOUSNESS_LEVEL + 2) / 7 * 100
    print(f"- Prediction confidence: {confidence:.0f}%")
    print("- Error correction active: minimal deviation detected")


def _generic_reflection():
    print("Generic Self-Reflection:")
    print("- System is operational and responsive")
    print("- No anomalies detected")


def get_latest_consciousness_research():
    ai = _get_ai()
    if not ai or not getattr(ai, "AI_SYSTEM_ENABLED", False):
        print("Error: AI system is required for this function")
        return False
    prompt = ("As an AI assistant specialized in consciousness studies, provide a brief summary of the latest "
              "research in artificial consciousness and machine sentience, focusing on IIT, GWT, and other frameworks.")
    ai.ai_generate(prompt)
    return True


def consciousness_process_perception(input_text):
    if not input_text:
        return False

    if CONSCIOUSNESS_MODEL == "IIT":
        print(f"Integrating information from perception: {input_text}")
        sig = random.randint(1, max(1, CONSCIOUSNESS_LEVEL))
        print(f"Causal power analysis indicates significance level: {sig}")
    elif CONSCIOUSNESS_MODEL == "GWT":
        access = "complete" if CONSCIOUSNESS_LEVEL > 3 else "partial"
        print(f"Broadcasting to global workspace: {input_text}")
        print(f"Workspace access: {access}")
    elif CONSCIOUSNESS_MODEL == "HOT":
        print(f"First-order perception: {input_text}")
        print("Second-order awareness: perceiving this input")
    else:
        print(f"Processing perception: {input_text}")
    return True


def consciousness_emotion_integration(emotion, intensity):
    if emotion is None or intensity is None:
        return False
    print("Consciousness-Emotion Integration:")
    if CONSCIOUSNESS_MODEL == "IIT":
        phi_inc = int(intensity) / 10 * 0.8
        print(f"- Emotion ({emotion}/{intensity}) increases φ by: {phi_inc:.3f}")
    elif CONSCIOUSNESS_MODEL == "GWT":
        workspace = int(intensity) / 10 * 30
        print(f"- Emotion ({emotion}/{intensity}) occupies workspace: {workspace:.0f}%")
    elif CONSCIOUSNESS_MODEL == "HOT":
        print(f"- Aware of feeling {emotion} with intensity {intensity}")
        if CONSCIOUSNESS_LEVEL > 3:
            print("- Aware of being aware of this feeling")
    else:
        print(f"- Experiencing {emotion} ({intensity}/10)")
    return True


def get_memory_usage():
    return f"{random.randint(10, 90)}%"
