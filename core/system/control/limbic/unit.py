#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import re
import time

NOESIS_VERSION = "2.1.2"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
PURPLE = "\033[35m"
NC = "\033[0m"

LIMBIC_AROUSAL = 0.5
LIMBIC_VALENCE = 0.5
LIMBIC_THRESHOLD = 0.7
LIMBIC_DECAY = 0.05
LIMBIC_MAX_MEMORY = 1000

AMYGDALA_STATE = 0.0
HIPPOCAMPUS_STATE = 0.0
HYPOTHALAMUS_STATE = 0.0
THALAMUS_STATE = 0.0
CINGULATE_STATE = 0.0

_limbic_memories = []
_limbic_linked = False

THREAT_KEYWORDS = {"danger", "threat", "fear", "attack", "harmful"}
POSITIVE_KEYWORDS = {"good", "happy", "pleasure", "reward", "safe"}
NEGATIVE_KEYWORDS = {"bad", "sad", "pain", "danger", "risk"}


def init_limbic_system():
    global LIMBIC_AROUSAL, LIMBIC_VALENCE, AMYGDALA_STATE, HIPPOCAMPUS_STATE
    global HYPOTHALAMUS_STATE, THALAMUS_STATE, CINGULATE_STATE, _limbic_memories

    print(f"{BLUE}Initializing limbic system...{NC}")
    LIMBIC_AROUSAL = 0.5
    LIMBIC_VALENCE = 0.5
    AMYGDALA_STATE = HIPPOCAMPUS_STATE = HYPOTHALAMUS_STATE = 0.0
    THALAMUS_STATE = CINGULATE_STATE = 0.0
    _limbic_memories = []
    print(f"{GREEN}Limbic system initialized successfully{NC}")


def amygdala_process(stimulus, intensity=0.5, context=""):
    global AMYGDALA_STATE, LIMBIC_AROUSAL, LIMBIC_VALENCE
    print(f"Amygdala processing stimulus: {stimulus}")

    threat = any(kw in stimulus.lower() for kw in THREAT_KEYWORDS)
    if threat:
        print(f"{RED}Threat detected! Activating fear response{NC}")
        AMYGDALA_STATE = 1.0
        LIMBIC_AROUSAL = min(1.0, LIMBIC_AROUSAL + intensity * 0.5)
        LIMBIC_VALENCE = max(0.0, LIMBIC_VALENCE - intensity * 0.3)
        limbic_create_memory(stimulus, context, intensity * 0.8, "fear")
    else:
        print("No threat detected in stimulus")
        AMYGDALA_STATE = 0.0

    return threat


def hippocampus_process(experience, context="", emotional_strength=0.5):
    global HIPPOCAMPUS_STATE
    print(f"Hippocampus indexing experience with context: {context}")
    memory_strength = emotional_strength * (0.5 + LIMBIC_AROUSAL * 0.5)
    HIPPOCAMPUS_STATE = 1.0
    limbic_create_memory(experience, context, memory_strength, "episodic")
    HIPPOCAMPUS_STATE = max(0.0, HIPPOCAMPUS_STATE - 0.1)


def hypothalamus_regulate(current_state, target_state=0.5):
    global HYPOTHALAMUS_STATE
    imbalance = abs(current_state - target_state)
    if imbalance > 0.2:
        print(f"{YELLOW}Homeostatic imbalance detected: {imbalance:.3f}{NC}")
        HYPOTHALAMUS_STATE = 1.0
        drive_strength = imbalance * 5
        print(f"Generated homeostatic drive with strength: {drive_strength:.3f}")
    else:
        print("Homeostasis within normal parameters")
        HYPOTHALAMUS_STATE = 0.0


def thalamus_relay(sensory_input):
    global THALAMUS_STATE
    print("Thalamus relaying sensory information...")
    THALAMUS_STATE = 1.0

    if "pain" in sensory_input.lower():
        priority = 0.9
    elif "pleasure" in sensory_input.lower():
        priority = 0.8
    else:
        priority = 0.5

    print(f"Sensory input priority: {priority}")
    if priority > LIMBIC_THRESHOLD:
        print("Routing high priority input to amygdala...")
        amygdala_process(sensory_input, priority, "sensory")
    else:
        print("Normal priority sensory processing...")

    THALAMUS_STATE = max(0.0, THALAMUS_STATE - 0.2)


def cingulate_resolve(option_a, option_b, context=""):
    global CINGULATE_STATE
    print(f"{PURPLE}Cingulate cortex resolving conflict...{NC}")
    CINGULATE_STATE = 1.0

    import random
    val_a = limbic_evaluate_option(option_a)
    val_b = limbic_evaluate_option(option_b)

    val_a *= 1.0 + LIMBIC_VALENCE - 0.5
    val_b *= 1.0 + LIMBIC_VALENCE - 0.5

    random_factor = 0.9 + random.randint(1, 20) / 100
    val_a *= random_factor

    CINGULATE_STATE = 0.7
    if val_a > val_b:
        print(f"Resolution: Selected Option A ({val_a:.3f} > {val_b:.3f})")
        return 1
    else:
        print(f"Resolution: Selected Option B ({val_b:.3f} > {val_a:.3f})")
        return 2


def limbic_evaluate_option(option):
    valence = 0.5
    text = option.lower()
    for kw in POSITIVE_KEYWORDS:
        if kw in text:
            valence += 0.1
    for kw in NEGATIVE_KEYWORDS:
        if kw in text:
            valence -= 0.1
    return max(0.0, min(1.0, valence))


def limbic_create_memory(experience, context="", strength=0.5, emotion_type="neutral"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "experience": experience,
        "context": context,
        "strength": float(strength),
        "emotion_type": emotion_type,
        "timestamp": timestamp,
    }

    if len(_limbic_memories) < LIMBIC_MAX_MEMORY:
        _limbic_memories.append(entry)
        idx = len(_limbic_memories) - 1
    else:
        weakest = min(range(len(_limbic_memories)), key=lambda i: _limbic_memories[i]["strength"])
        _limbic_memories[weakest] = entry
        idx = weakest

    print(f"Created limbic memory #{idx} with strength {strength}")
    return idx


def limbic_retrieve_memories(query, emotion_type=None, min_strength=0.0):
    print(f"Retrieving limbic memories matching: {query}")
    found = 0
    for i, mem in enumerate(_limbic_memories):
        if mem["strength"] < min_strength:
            continue
        if emotion_type and mem["emotion_type"] != emotion_type:
            continue
        if query.lower() in mem["experience"].lower() or query.lower() in mem["context"].lower():
            print(f"Memory #{i} ({mem['emotion_type']}, strength {mem['strength']:.2f}):")
            print(f"  Experience: {mem['experience']}")
            print(f"  Context: {mem['context']}")
            print(f"  Created: {mem['timestamp']}")
            found += 1
    print(f"Found {found} matching memories")
    return found


def limbic_process_experience(experience, context="", intensity=0.5):
    global LIMBIC_AROUSAL
    print(f"{BLUE}Processing limbic experience: {experience}{NC}")
    thalamus_relay(experience)
    amygdala_process(experience, intensity, context)
    hippocampus_process(experience, context, intensity)
    LIMBIC_AROUSAL = min(1.0, max(0.0, LIMBIC_AROUSAL + (intensity - 0.5) * 0.2))
    print(f"Current Limbic State:\n  Arousal: {LIMBIC_AROUSAL:.3f}\n  Valence: {LIMBIC_VALENCE:.3f}")


def limbic_process_decay():
    global LIMBIC_AROUSAL, LIMBIC_VALENCE, AMYGDALA_STATE, HIPPOCAMPUS_STATE
    global HYPOTHALAMUS_STATE, THALAMUS_STATE, CINGULATE_STATE

    if LIMBIC_AROUSAL > 0.5:
        LIMBIC_AROUSAL = max(0.5, LIMBIC_AROUSAL - LIMBIC_DECAY)
    elif LIMBIC_AROUSAL < 0.5:
        LIMBIC_AROUSAL = min(0.5, LIMBIC_AROUSAL + LIMBIC_DECAY)

    if LIMBIC_VALENCE > 0.5:
        LIMBIC_VALENCE = max(0.5, LIMBIC_VALENCE - LIMBIC_DECAY)
    elif LIMBIC_VALENCE < 0.5:
        LIMBIC_VALENCE = min(0.5, LIMBIC_VALENCE + LIMBIC_DECAY)

    for name in ("AMYGDALA_STATE", "HIPPOCAMPUS_STATE", "HYPOTHALAMUS_STATE",
                 "THALAMUS_STATE", "CINGULATE_STATE"):
        val = globals()[name]
        globals()[name] = max(0.0, val - LIMBIC_DECAY)


def limbic_update_cycle():
    limbic_process_decay()
    hypothalamus_regulate(LIMBIC_AROUSAL, 0.5)


print("Limbic system module loaded")
