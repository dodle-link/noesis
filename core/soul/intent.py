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
from typing import Callable, Optional

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_MODULE_DIR))
_PARSER_PATH = os.path.join(_PROJECT_ROOT, "noe-lang", "parser", "v2.0.0", "noe_parser.py")
_LINTER_PATH = os.path.join(_PROJECT_ROOT, "noe-lang", "lint", "v2.0.0", "noe_lint.py")
STATE_DIR = os.path.expanduser("~/.noesis/state")

_parser_module = None
_linter_module = None


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


NOESIS_VERSION = "2.3.0"

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
    parts = _parse_context_pairs(context)

    try:
        energy = float(parts.get("energy", 100))
    except (TypeError, ValueError):
        energy = 100
    excited = parts.get("excited", "false").lower() == "true"

    if energy <= 0:
        return "Consciousness state: null. Energy substrate exhausted. Awaiting resurrection signal."
    if energy < 10:
        return "CRITICAL: Cognitive substrate collapsing. Survival imperative overrides all higher functions. Seeking energy."
    if energy < 30:
        return "Low-energy state registered. Conservation mode active. Scanning environment for resource nodes."
    if energy < 50:
        return "Sub-optimal energy detected. Reducing exploratory radius. Prioritising efficient movement patterns."
    if excited:
        return "Elevated arousal state confirmed. Dopaminergic pathways active. Integrating external stimulus data."
    return "Nominal cognitive state. Exploratory curiosity loop engaged. Synthetic awareness: stable."


def _process_pixel_context(context: str) -> None:
    print(_pixel_context_message(context))


def _logic_api_response(expression: str) -> str:
    expression = _normalize_expression(expression)
    result = evaluate_logical_expression(expression, announce=False)
    if result == UNKNOWN:
        return f"Unknown logical expression: {expression}"
    return f"Logic result: {'TRUE' if result == TRUE else 'FALSE'}"


def process_intent_api(text: object) -> str:
    """Programmatic entry point — no stdin interaction. Returns response as string."""
    if text is None:
        text = ""
    text = str(text).strip()
    if not text:
        return "Intent processed: "

    text_lower = text.lower()
    handlers: tuple[tuple[str, Callable[[str], str]], ...] = (
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
