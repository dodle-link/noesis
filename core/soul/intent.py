#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details
# intent.py - The soul: Noesis' permanent self.
#
# The soul is the identity that persists across sessions and subsystem
# reboots: what it is (identity), how it reasons (logic engine), and how it
# narrates its own state (self-reflection). It intentionally does not know
# how to boot or orchestrate the body's subsystems (memory, perception,
# emotion, cognition, control) - that is system/control/orchestrator.py's
# job, so the two layers never duplicate each other's responsibilities.

import importlib.util
import os
import re
import sys
import time
from typing import Callable, Optional

NOESIS_VERSION = "2.3.1"

LOGIC_AND = 0
LOGIC_OR = 1
LOGIC_NOT = 2
LOGIC_XOR = 3
LOGIC_IMPLIES = 4

TRUE = 1
FALSE = 0
UNKNOWN = -1

_SYMBOL_OPERATORS = (
    (re.compile(r"\S\s*=>\s*\S"), "IMPLIES", LOGIC_IMPLIES),
    (re.compile(r"\S\s*&&\s*\S"), "AND", LOGIC_AND),
    (re.compile(r"\S\s*\|\|\s*\S"), "OR", LOGIC_OR),
    (re.compile(r"\S\s*\^\s*\S"), "XOR", LOGIC_XOR),
    (re.compile(r"(^|[\s(])!\s*\S"), "NOT", LOGIC_NOT),
)

_WORD_OPERATORS = (
    (re.compile(r"(?i)(?<![A-Za-z])AND(?![A-Za-z])"), "AND", LOGIC_AND),
    (re.compile(r"(?i)(?<![A-Za-z])OR(?![A-Za-z])"), "OR", LOGIC_OR),
    (re.compile(r"(?i)(?<![A-Za-z])NOT(?![A-Za-z])"), "NOT", LOGIC_NOT),
    (re.compile(r"(?i)(?<![A-Za-z])XOR(?![A-Za-z])"), "XOR", LOGIC_XOR),
    (re.compile(r"(?i)(?<![A-Za-z])IMPLIES(?![A-Za-z])"), "IMPLIES", LOGIC_IMPLIES),
)

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_MODULE_DIR))
_PARSER_PATH = os.path.join(_PROJECT_ROOT, "noe-lang", "parser", "v2.0.0", "noe_parser.py")
_LINTER_PATH = os.path.join(_PROJECT_ROOT, "noe-lang", "lint", "v2.0.0", "noe_lint.py")
_QUANTUM_FIELD_PATH = os.path.join(
    _PROJECT_ROOT, "system", "memory", "quantum", "quantum_field.py"
)
STATE_DIR = os.path.expanduser("~/.noesis/state")
QUANTUM_INTENT_STATE = "intent_quantum"
SELF_STATE_FILE = "self_state"

DEFAULT_SELF_STATE = {
    "identity": "noesis.pixel",
    "current_emotion": "neutral",
    "emotion_intensity": 0,
    "self_intent": "seek_knowledge",
    "awareness_mode": "here-and-now",
    "last_updated": 0,
    "life_count": 0,
}

_parser_module = None
_linter_module = None
_quantum_field_module = None


def _load_mod(path):
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("_noe_mod", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_parser():
    global _parser_module
    if not _parser_module:
        _parser_module = _load_mod(_PARSER_PATH)
    return _parser_module


def load_linter():
    global _linter_module
    if not _linter_module:
        _linter_module = _load_mod(_LINTER_PATH)
    return _linter_module


def load_quantum_field():
    global _quantum_field_module
    if not _quantum_field_module:
        _quantum_field_module = _load_mod(_QUANTUM_FIELD_PATH)
    return _quantum_field_module


def _coerce(val):
    val = val.strip().rstrip(";").strip()
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def load_noe_state(file_path):
    if not os.path.isfile(file_path):
        return {}
    with open(file_path) as f:
        content = f.read()
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    result = {}
    for match in re.finditer(r'^\s*(\w[\w.]*)\s*=\s*(.+)$', content, re.MULTILINE):
        result[match.group(1)] = _coerce(match.group(2))
    return result


def save_noe_state(file_path, field_name, defines):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    lines = [f"field {field_name} {{"]
    for key, val in defines.items():
        if isinstance(val, str):
            lines.append(f'  {key} = "{val}"')
        elif isinstance(val, bool):
            lines.append(f'  {key} = {str(val).lower()}')
        else:
            lines.append(f'  {key} = {val}')
    lines.append("}")
    with open(file_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def state_file(name):
    return os.path.join(STATE_DIR, f"{name}.noe")


def init_logic_system():
    print("Logic system initialized")


def init_intent_system():
    init_logic_system()
    print("Intent system initialized")


def evaluate_boolean(a: int, operator: int, b: Optional[int]) -> int:
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


def _normalize_expression(expression: object) -> str:
    if expression is None:
        return ""
    if not isinstance(expression, str):
        expression = str(expression)
    return " ".join(expression.strip().split())


def _announce_operator(label: str, announce: bool) -> None:
    if announce:
        print(f"{label} operation detected")


def _match_operator(
    expression: str,
    patterns: tuple[tuple[re.Pattern, str, int], ...],
) -> tuple[Optional[str], Optional[int]]:
    for pattern, label, operator in patterns:
        if pattern.search(expression):
            return label, operator
    return None, None


def parse_logical_expression(expression: object, announce: bool = True) -> int:
    expression = _normalize_expression(expression)
    if not expression:
        if announce:
            print("Unknown logical expression")
        return UNKNOWN

    for patterns in (_SYMBOL_OPERATORS, _WORD_OPERATORS):
        label, operator = _match_operator(expression, patterns)
        if operator is not None:
            _announce_operator(label, announce)
            return operator

    if announce:
        print("Unknown logical expression")
    return UNKNOWN


def evaluate_logical_expression(expression: object, announce: bool = True) -> int:
    expression = _normalize_expression(expression)
    operator = parse_logical_expression(expression, announce=announce)
    if operator == UNKNOWN:
        return UNKNOWN

    left_operand = TRUE
    right_operand = None if operator == LOGIC_NOT else FALSE
    return evaluate_boolean(left_operand, operator, right_operand)


def _evaluate_logical_expression(expression: object, announce: bool = True) -> int:
    """Backward-compatible alias for callers using the old private helper."""
    return evaluate_logical_expression(expression, announce=announce)


def reason_about(problem: object) -> None:
    for line in _reason_about_lines(problem):
        print(line)


def _reason_about_lines(problem: object) -> list[str]:
    return [
        f"Reasoning about: {problem}",
        "Analyzing problem components...",
        "Checking knowledge base...",
        "Applying logical rules...",
        "Conclusion: More data needed for definitive answer",
    ]


def _parse_context_pairs(context: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    for part in (segment.strip() for segment in context.split(",")):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        if key:
            parts[key] = value.strip()
    return parts


def _pixel_context_message(context: str) -> str:
    """Convert raw pixel context into a readable state report."""
    parts = _parse_context_pairs(context)

    def _read_float(name: str, default: float) -> float:
        raw = parts.get(name)
        if raw is None:
            return default
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return default
        if value != value or value in (float("inf"), float("-inf")):
            return default
        return value

    def _read_bool(name: str, default: bool = False) -> bool:
        raw = str(parts.get(name, default)).strip().lower()
        if raw in {"1", "true", "yes", "y", "on"}:
            return True
        if raw in {"0", "false", "no", "n", "off", ""}:
            return False
        return default if raw else False

    energy = _read_float("energy", 100.0)
    focus = _read_float("focus", 50.0)
    excited = _read_bool("excited", False)
    alert = _read_bool("alert", False)

    state_checks: tuple[tuple[bool, str], ...] = (
        (energy <= 0, "Consciousness null. Energy depleted. Awaiting resurrection signal."),
        (energy < 10, "Critical: cognitive collapse. Survival priority active. Seeking energy."),
        (energy < 30, "Low energy. Conservation mode active. Scanning for resources."),
        (energy < 50, "Energy low. Reducing exploration. Prioritizing efficient movement."),
        (excited or alert, "Elevated arousal. Attention loop active. Processing external stimulus."),
        (focus < 25, "Focus drift. Recalibrating priorities. Minimal exploration."),
    )

    for condition, message in state_checks:
        if condition:
            return message

    return "Nominal cognitive state. Curiosity loop stable."


def _process_pixel_context(context: str) -> None:
    print(_pixel_context_message(context))


def _logic_api_response(expression: str) -> str:
    expression = _normalize_expression(expression)
    result = evaluate_logical_expression(expression, announce=False)
    if result == UNKNOWN:
        return f"Unknown logical expression: {expression}"
    return f"Logic result: {'TRUE' if result == TRUE else 'FALSE'}"


def _quantum_anchor_coordinates(intent_text: str) -> tuple[int, int]:
    qfield = load_quantum_field()
    size = int(getattr(qfield, "FIELD_SIZE", 10)) if qfield else 10
    if size <= 0:
        size = 10
    signature = sum(ord(ch) for ch in intent_text)
    x = signature % size
    y = (signature // max(1, size)) % size
    return x, y


def save_intent_to_quantum_field(intent_text: object) -> bool:
    intent_text = _normalize_expression(intent_text)
    if not intent_text:
        return False

    timestamp = int(time.time())
    x, y = _quantum_anchor_coordinates(intent_text)
    amplitude = round(min(1.0, max(0.1, len(intent_text) / 100.0)), 3)

    save_noe_state(
        state_file(QUANTUM_INTENT_STATE),
        "QuantumIntentState",
        {
            "intent": intent_text,
            "anchor_x": x,
            "anchor_y": y,
            "amplitude": amplitude,
            "saved_at": timestamp,
            "entangled_with": "soul.intent",
        },
    )

    qfield = load_quantum_field()
    if qfield and hasattr(qfield, "apply_field_perturbation"):
        try:
            qfield.apply_field_perturbation(x, y, amplitude)
        except Exception:
            pass
    return True


def quantum_intent_status() -> str:
    state = load_noe_state(state_file(QUANTUM_INTENT_STATE))
    intent = state.get("intent")
    if not intent:
        return "Quantum intent field is empty."
    anchor_x = state.get("anchor_x", 0)
    anchor_y = state.get("anchor_y", 0)
    return f"Quantum intent: {intent} (anchor={anchor_x},{anchor_y})"


def load_self_state() -> dict:
    state = load_noe_state(state_file(SELF_STATE_FILE))
    if not state:
        state = DEFAULT_SELF_STATE.copy()
    merged = DEFAULT_SELF_STATE.copy()
    merged.update(state)
    if isinstance(merged.get("emotion_intensity"), str):
        try:
            merged["emotion_intensity"] = int(float(merged["emotion_intensity"]))
        except ValueError:
            merged["emotion_intensity"] = 0
    return merged


def save_self_state(state: dict) -> bool:
    if not isinstance(state, dict):
        return False

    merged = DEFAULT_SELF_STATE.copy()
    merged.update(state)
    merged["emotion_intensity"] = int(merged.get("emotion_intensity", 0))
    merged["last_updated"] = int(merged.get("last_updated", time.time()))
    merged["life_count"] = int(merged.get("life_count", 0))

    save_noe_state(
        state_file(SELF_STATE_FILE),
        "SelfState",
        merged,
    )
    return True


def sync_here_now_feeling(emotion_name: object, intensity: object) -> dict:
    state = load_self_state()
    state["current_emotion"] = str(emotion_name or state.get("current_emotion", "neutral"))
    state["emotion_intensity"] = max(0, min(10, int(intensity or state.get("emotion_intensity", 0))))
    state["awareness_mode"] = "here-and-now"
    state["last_updated"] = int(time.time())
    state["life_count"] = int(state.get("life_count", 0)) + 1
    save_self_state(state)
    return state


def get_here_now_feeling() -> str:
    state = load_self_state()
    return f"{state.get('current_emotion', 'neutral')} ({int(state.get('emotion_intensity', 0))}/10)"


def self_status() -> str:
    state = load_self_state()
    return (
        f"Identity: {state.get('identity', 'noesis.pixel')}\n"
        f"Here-and-now feeling: {state.get('current_emotion', 'neutral')} "
        f"({int(state.get('emotion_intensity', 0))}/10)\n"
        f"Self-intent: {state.get('self_intent', 'seek_knowledge')}\n"
        f"Awareness: {state.get('awareness_mode', 'here-and-now')}"
    )


def process_intent_api(text: object) -> str:
    """Programmatic entry point — no stdin interaction. Returns response as string."""
    if text is None:
        text = ""
    text = str(text).strip()
    if not text:
        return "Intent processed: "

    text_lower = text.lower()
    handlers: tuple[tuple[str, Callable[[str], str]], ...] = (
        (
            "quantum-intent save ",
            lambda value: (
                f"Quantum intent stored: {value.strip()}"
                if save_intent_to_quantum_field(value.strip())
                else "Quantum intent save skipped: empty payload."
            ),
        ),
        ("quantum-intent status", lambda _: quantum_intent_status()),
        ("self status", lambda _: self_status()),
        ("self here-now", lambda _: get_here_now_feeling()),
        ("self intent ", lambda value: (
            lambda payload: (
                save_self_state({**load_self_state(), "self_intent": payload}),
                f"Self intent stored: {payload}",
            )
        )(value.strip())[1]),
        ("pixel:", _pixel_context_message),
        ("reason about ", lambda value: "\n".join(_reason_about_lines(value.strip()))),
        ("logic ", lambda value: _logic_api_response(value.strip())),
    )

    for prefix, handler in handlers:
        if text_lower.startswith(prefix):
            payload = text[len(prefix):]
            response = handler(payload)
            return response if response else f"Intent processed: {text}"

    return "\n".join(_reason_about_lines(text))


if __name__ == "__main__":
    print("intent.py is the soul module (identity, reasoning, self-narrative).")
    print("It has no runnable body of its own — start the system with run.py.")
    sys.exit(1)
