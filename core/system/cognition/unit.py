#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details

import os
import sys
import subprocess
import tempfile

AI_SYSTEM_ENABLED = False
AI_MODEL_NAME = "default"
AI_THINKING_LEVEL = 0
AI_MEMORY_INTEGRATION = True
AI_MODELS_CACHE_DIR = os.path.expanduser("~/.noesis/ai_models")
NOESIS_DIR = os.path.expanduser("~/.noesis")

AI_MODEL_CHOICES = [
    "mistralai/Mistral-7B-Instruct-v0.2",
    "google/gemma-2b-it",
    "google/flan-t5-large",
    "openchat/openchat-3.5-0106",
    "microsoft/phi-2",
    "stabilityai/stablelm-3b-4e1t",
]

AI_MODEL_LICENSES = {
    "mistralai/Mistral-7B-Instruct-v0.2": "Apache 2.0",
    "google/gemma-2b-it": "Permissive (Gemma license)",
    "google/flan-t5-large": "Apache 2.0",
    "openchat/openchat-3.5-0106": "Apache 2.0",
    "microsoft/phi-2": "MIT",
    "stabilityai/stablelm-3b-4e1t": "MIT",
}

_emotion_module = None
_consciousness_module = None


def _load_emotion():
    global _emotion_module
    if _emotion_module:
        return _emotion_module
    try:
        import importlib.util, os
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "emotion", "unit.py")
        spec = importlib.util.spec_from_file_location("emotion", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _emotion_module = mod
    except Exception:
        pass
    return _emotion_module


def _check_import(pkg):
    r = subprocess.run([sys.executable, "-c", f"import {pkg}"], capture_output=True)
    return r.returncode == 0


def init_ai_system():
    global AI_SYSTEM_ENABLED
    print("Initializing AI integration system...")
    os.makedirs(AI_MODELS_CACHE_DIR, exist_ok=True)

    if not _check_import("transformers"):
        print("Warning: Transformers package not found")
        print("To enable AI: python3 tools/fast_ai_install.py")
        AI_SYSTEM_ENABLED = False
        return False

    compat = os.path.join(NOESIS_DIR, "torch_compat.py")
    if not _check_import("torch"):
        if os.path.isfile(compat):
            r = subprocess.run([sys.executable, "-c",
                                f"import sys; sys.path.insert(0, '{NOESIS_DIR}'); import torch_compat"],
                               capture_output=True)
            if r.returncode == 0:
                print("Using PyTorch compatibility layer")
                AI_SYSTEM_ENABLED = True
            else:
                AI_SYSTEM_ENABLED = False
                return False
        else:
            AI_SYSTEM_ENABLED = False
            return False
    else:
        AI_SYSTEM_ENABLED = True
        print("AI integration system initialized successfully")

    if _consciousness_module and hasattr(_consciousness_module, "init_consciousness"):
        _consciousness_module.init_consciousness()

    return True


def ai_list_models():
    print("Available AI models from Hugging Face:")
    for m in AI_MODEL_CHOICES:
        print(f"  - {m}")


def ai_set_model(requested_model):
    global AI_MODEL_NAME
    license_info = AI_MODEL_LICENSES.get(requested_model)
    if license_info:
        print(f"Model: {requested_model}\nLicense: {license_info}")
        print("This model's license is compatible with the Noesis License.")
    else:
        print(f"Warning: Model '{requested_model}' is not in the predefined list")
        ans = input("Continue anyway? (y/N): ").strip().lower()
        if ans not in ("y", "yes"):
            return False

    ai_check_license_compatibility(requested_model)
    AI_MODEL_NAME = requested_model
    print(f"AI model set to: {AI_MODEL_NAME}")

    if AI_SYSTEM_ENABLED:
        print("Downloading model weights (this may take some time)...")
        r = subprocess.run([sys.executable, "-c",
                            f"from transformers import AutoTokenizer, AutoModelForCausalLM; "
                            f"t = AutoTokenizer.from_pretrained('{requested_model}'); "
                            f"m = AutoModelForCausalLM.from_pretrained('{requested_model}', device_map='auto')"],
                           capture_output=True)
        if r.returncode == 0:
            print("Model downloaded successfully")
        else:
            print("Warning: Could not download model. It may be downloaded on first use.")
    return True


def ai_generate(prompt):
    if not AI_SYSTEM_ENABLED:
        print("AI system is not enabled. Please install required dependencies.")
        return None

    if not prompt:
        print("Error: No prompt provided")
        return None

    print(f"Generating response using {AI_MODEL_NAME}...")

    script = f"""
import sys, os
sys.path.insert(0, '{NOESIS_DIR}')
try:
    import torch
except ImportError:
    try:
        import torch_compat
    except ImportError:
        print("ERROR: No PyTorch available")
        sys.exit(1)

from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

model_name = {repr(AI_MODEL_NAME)}
prompt = {repr(prompt)}

try:
    is_compat = getattr(sys.modules.get('torch', object()), '__version__', '') == '0.1.0-compat'
    if is_compat:
        print(f"I am the Noesis system responding to: {{prompt}}")
        sys.exit(0)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto')
    gen = pipeline('text-generation', model=model, tokenizer=tokenizer)
    result = gen(prompt, max_new_tokens=500, do_sample=True, temperature=0.7)
    print(result[0]['generated_text'])
except Exception as e:
    print(f"Error generating text: {{e}}")
    sys.exit(1)
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name

    try:
        r = subprocess.run([sys.executable, tmp], capture_output=False)
        return r.returncode == 0
    finally:
        os.unlink(tmp)


def ai_set_thinking_level(level):
    global AI_THINKING_LEVEL
    level = int(level)
    if not (0 <= level <= 5):
        print("Error: Thinking level must be between 0 and 5")
        return False
    AI_THINKING_LEVEL = level
    print(f"AI thinking level set to {level}")
    return True


def ai_toggle_memory_integration():
    global AI_MEMORY_INTEGRATION
    AI_MEMORY_INTEGRATION = not AI_MEMORY_INTEGRATION
    state = "enabled" if AI_MEMORY_INTEGRATION else "disabled"
    print(f"AI memory integration {state}")


def ai_emotional_response(input_text):
    if not AI_SYSTEM_ENABLED:
        em = _load_emotion()
        if em:
            em.emotional_response(input_text)
        return

    em = _load_emotion()
    emotion_name = em.get_current_emotion() if em else "neutral"
    intensity = em.get_emotion_intensity() if em else 0

    prompt = (f"You are the Noesis synthetic conscious system. Your current emotional state is "
              f"{emotion_name} with intensity {intensity} out of 10. Please respond to: '{input_text}'")
    ai_generate(prompt)


def ai_process_perception(input_text):
    if not AI_SYSTEM_ENABLED:
        print("AI processing not available - using basic perception")
        return False
    prompt = f"As the Noesis synthetic conscious system, analyze this perception data: {input_text}"
    return ai_generate(prompt)


def ai_introspect():
    if not AI_SYSTEM_ENABLED:
        print("AI introspection not available")
        return False

    prompts = {
        0: "focusing only on your current state.",
        1: "examining your current state and immediate goals.",
        2: "examining your current state, goals, and recent interactions.",
        3: "deeply analyzing your emotional state, goals, and interaction patterns.",
        4: "deeply analyzing your emotional state, goals, interaction patterns, and self-improvement opportunities.",
        5: "performing a full philosophical examination of your cognitive state, emotions, goals, history, and concepts of self-awareness.",
    }
    prompt = f"As the Noesis synthetic conscious system, perform an introspection {prompts.get(AI_THINKING_LEVEL, prompts[0])}"
    return ai_generate(prompt)


def ai_status():
    print("AI System Status:")
    print(f"  Enabled: {AI_SYSTEM_ENABLED}")
    print(f"  Current Model: {AI_MODEL_NAME}")
    print(f"  Thinking Level: {AI_THINKING_LEVEL}")
    print(f"  Memory Integration: {AI_MEMORY_INTEGRATION}")
    print(f"  Cache Directory: {AI_MODELS_CACHE_DIR}")
    print()
    print("Dependencies:")
    print(f"  Python: {sys.version.split()[0]}")

    for pkg, name in [("transformers", "Transformers"), ("torch", "PyTorch")]:
        r = subprocess.run([sys.executable, "-c", f"import {pkg}; print({pkg}.__version__)"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print(f"  {name}: installed ({r.stdout.strip()})")
        else:
            print(f"  {name}: not installed")


def ai_install_dependencies():
    global AI_SYSTEM_ENABLED
    py_minor = sys.version_info.minor

    if py_minor >= 13:
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "tools", "fast_ai_install_py13.py")
        if os.path.isfile(script):
            r = subprocess.run([sys.executable, script])
            if r.returncode == 0:
                AI_SYSTEM_ENABLED = True
                return True
        return False

    for script_name in ["fast_ai_install.py", "setup_torch_mac.py", "install_ai_deps.py"]:
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "tools", script_name)
        if os.path.isfile(script):
            r = subprocess.run([sys.executable, script])
            if r.returncode == 0:
                AI_SYSTEM_ENABLED = True
                return True

    return False


def ai_check_license_compatibility(model_name):
    if not _check_import("huggingface_hub"):
        print("Warning: huggingface_hub not installed. Cannot verify license automatically.")
        return False

    script = f"""
import sys
from huggingface_hub import HfApi

PERMISSIVE = {{"mit", "apache-2.0", "apache2.0", "apache", "bsd", "cc-by", "cc-by-sa",
               "cc0", "openrail", "bigscience-openrail-m", "creativeml-openrail-m",
               "bigcode-openrail-m", "llama2"}}

try:
    api = HfApi()
    info = api.model_info({repr(model_name)})
    lic = getattr(info, 'license', 'Unknown') or 'Unknown'
    compatible = any(p in lic.lower() for p in PERMISSIVE)
    print(f"Model: {repr(model_name)}")
    print(f"License: {{lic}}")
    print(f"Compatible with Noesis License: {{'Yes' if compatible else 'Needs review'}}")
    sys.exit(0 if compatible else 1)
except Exception as e:
    print(f"Error: {{e}}")
    sys.exit(1)
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script)
        tmp = f.name

    try:
        r = subprocess.run([sys.executable, tmp])
        return r.returncode == 0
    finally:
        os.unlink(tmp)
