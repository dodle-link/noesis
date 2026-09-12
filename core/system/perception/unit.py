#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import os
import platform
import random

F_OK = 0


def detect_environment():
    os_name = platform.system()
    host = platform.node()
    print("Environment detection:")
    print(f"Operating system: {os_name}")
    print(f"Hostname: {host}")

    if os.path.isdir("/dev/input"):
        print("Input devices available")
    if os.path.isdir("/sys/class/thermal"):
        print("Thermal sensors available")


def process_visual_input():
    print("Processing visual input (simulated)")
    objects = ["desk", "keyboard", "monitor", "person"]
    detected = random.choice(objects)
    print(f"Detected: {detected}")
    return detected


def process_audio_input():
    print("Processing audio input (simulated)")
    level = random.randint(10, 90)
    print(f"Ambient sound level: {level} dB")
    if level > 70:
        print("Warning: High noise levels detected")
    return level


def read_input():
    print()
    return input("input > ")


def process_text_input(text, ai_processor=None, consciousness_processor=None):
    if not text:
        return False

    if ai_processor and callable(ai_processor):
        result = ai_processor(text)
        if consciousness_processor and callable(consciousness_processor):
            consciousness_processor(result)
        return True

    if "hello" in text.lower():
        print("Greeting detected")
    elif "help" in text.lower():
        print("Help request detected")
    elif "status" in text.lower():
        print("Status query detected")
    else:
        print("General input detected")

    if consciousness_processor and callable(consciousness_processor):
        consciousness_processor(text)

    return True


def init_perception():
    print("Initializing perception systems...")
    detect_environment()
    print("Perception systems online")
