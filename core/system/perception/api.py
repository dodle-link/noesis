#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import json
import re

API_VERSION = "2.1.2"

_memory = None
_perception = None
_emotion = None
_intent = None
_data_storage = None
_consciousness = None


def _load_modules():
    global _memory, _perception, _emotion, _intent, _data_storage, _consciousness
    import importlib.util, os
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def load(rel):
        path = os.path.join(base, rel)
        if not os.path.exists(path):
            return None
        spec = importlib.util.spec_from_file_location(rel.replace("/", ".").replace(".py", ""), path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    _memory = load("system/memory/unit.py")
    _perception = load("system/perception/unit.py")
    _emotion = load("system/emotion/unit.py")
    _intent = load("soul/intent.py")
    _data_storage = load("system/memory/short.py")
    _consciousness = load("system/cognition/consciousness.py")


def _consciousness_processor():
    if _consciousness and hasattr(_consciousness, "consciousness_process_perception"):
        return _consciousness.consciousness_process_perception
    return None


def api_init():
    _load_modules()
    print(f"Initializing Noesis API v{API_VERSION}")
    if _memory: _memory.init_memory_system()
    if _perception: _perception.init_perception()
    if _emotion: _emotion.init_emotion_system()
    if _data_storage: _data_storage.init_data_storage()
    if _consciousness and hasattr(_consciousness, "init_consciousness"):
        _consciousness.init_consciousness()
    print("API initialized successfully")


def api_process(request):
    if not request:
        print("Error: Empty request")
        return False

    print(f"Processing API request: {request}")
    parts = request.split(":")

    if not parts:
        print("Error: Invalid request format")
        return False

    action = parts[0]
    params = parts[1:]

    if action == "VERSION":
        print(f"NOESIS:API:{API_VERSION}")

    elif action == "STORE":
        if len(parts) < 3:
            print("Error: STORE requires key and value")
            return False
        key, value = parts[1], ":".join(parts[2:])
        if _data_storage:
            _data_storage.store_data(key, value)
        print(f"OK:STORED:{key}")

    elif action == "RETRIEVE":
        if len(parts) < 2:
            print("Error: RETRIEVE requires key")
            return False
        key = parts[1]
        value = _data_storage.retrieve_data(key) if _data_storage else None
        if value is not None:
            print(f"OK:VALUE:{value}")
        else:
            print(f"ERROR:KEY_NOT_FOUND:{key}")

    elif action == "PROCESS":
        if len(parts) < 2:
            print("Error: PROCESS requires input")
            return False
        if _perception:
            _perception.process_text_input(parts[1], consciousness_processor=_consciousness_processor())
        print("OK:PROCESSED")

    elif action == "EMOTION":
        if len(parts) < 2:
            print("Error: EMOTION requires emotion type")
            return False
        emotion = int(parts[1])
        intensity = int(parts[2]) if len(parts) >= 3 else 5
        if _emotion:
            _emotion.set_emotion(emotion, intensity)
        if _consciousness and hasattr(_consciousness, "consciousness_emotion_integration"):
            _consciousness.consciousness_emotion_integration(emotion, intensity)
        print(f"OK:EMOTION:{emotion}:{intensity}")

    else:
        print(f"Error: Unknown action: {action}")
        return False

    return True


def api_handle_json(json_str):
    print(f"Processing JSON request: {json_str}")
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        action = re.search(r'"action":"([^"]+)"', json_str)
        data = {"action": action.group(1)} if action else {}

    action = data.get("action")
    if not action:
        print('{"status":"error","message":"Missing action"}')
        return False

    if action == "getVersion":
        print(f'{{"status":"ok","version":"{API_VERSION}"}}')

    elif action == "process":
        inp = data.get("input", "")
        if not inp:
            print('{"status":"error","message":"Missing input parameter"}')
            return False
        if _perception:
            _perception.process_text_input(inp, consciousness_processor=_consciousness_processor())
        print(f'{{"status":"ok","result":"processed"}}')

    else:
        print(f'{{"status":"error","message":"Unknown action: {action}"}}')
        return False

    return True


def api_cleanup():
    print("Cleaning up Noesis API resources")


def api_version():
    return API_VERSION
