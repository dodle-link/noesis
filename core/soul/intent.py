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

import re
import sys

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


def init_logic_system():
    print("Logic system initialized")


def init_intent_system():
    init_logic_system()
    print("Intent system initialized")


def evaluate_boolean(a, operator, b):
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


def _normalize_expression(expression):
    if expression is None:
        return ""
    if not isinstance(expression, str):
        expression = str(expression)
    return " ".join(expression.strip().split())


def parse_logical_expression(expression, announce=True):
    expression = _normalize_expression(expression)
    if not expression:
        if announce:
            print("Unknown logical expression")
        return UNKNOWN

    for pattern, label, operator in _SYMBOL_OPERATORS:
        if pattern.search(expression):
            if announce:
                print(f"{label} operation detected")
            return operator

    word_tokens = set(re.findall(r"[A-Za-z]+", expression))
    upper_tokens = {token.upper() for token in word_tokens}

    if "AND" in upper_tokens and re.search(r"(?i)(?<![A-Za-z])AND(?![A-Za-z])", expression):
        if announce:
            print("AND operation detected")
        return LOGIC_AND
    elif "OR" in upper_tokens and re.search(r"(?i)(?<![A-Za-z])OR(?![A-Za-z])", expression):
        if announce:
            print("OR operation detected")
        return LOGIC_OR
    elif "NOT" in upper_tokens and re.search(r"(?i)(?<![A-Za-z])NOT(?![A-Za-z])", expression):
        if announce:
            print("NOT operation detected")
        return LOGIC_NOT
    elif "XOR" in upper_tokens and re.search(r"(?i)(?<![A-Za-z])XOR(?![A-Za-z])", expression):
        if announce:
            print("XOR operation detected")
        return LOGIC_XOR
    elif "IMPLIES" in upper_tokens and re.search(r"(?i)(?<![A-Za-z])IMPLIES(?![A-Za-z])", expression):
        if announce:
            print("IMPLIES operation detected")
        return LOGIC_IMPLIES
    if announce:
        print("Unknown logical expression")
    return UNKNOWN


def _evaluate_logical_expression(expression, announce=True):
    expression = _normalize_expression(expression)
    operator = parse_logical_expression(expression, announce=announce)
    if operator == UNKNOWN:
        return UNKNOWN
    right_operand = None if operator == LOGIC_NOT else FALSE
    return evaluate_boolean(TRUE, operator, right_operand)


def reason_about(problem):
    for line in _reason_about_lines(problem):
        print(line)


def _reason_about_lines(problem):
    return [
        f"Reasoning about: {problem}",
        "Analyzing problem components...",
        "Checking knowledge base...",
        "Applying logical rules...",
        "Conclusion: More data needed for definitive answer",
    ]


def _pixel_context_message(context: str) -> str:
    parts = {}
    for part in context.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            parts[k.strip()] = v.strip()

    try:
        energy = float(parts.get("energy", 100))
    except ValueError:
        energy = 100
    excited = parts.get("excited", "false").lower() == "true"

    if energy <= 0:
        return "Consciousness state: null. Energy substrate exhausted. Awaiting resurrection signal."
    elif energy < 10:
        return "CRITICAL: Cognitive substrate collapsing. Survival imperative overrides all higher functions. Seeking energy."
    elif energy < 30:
        return "Low-energy state registered. Conservation mode active. Scanning environment for resource nodes."
    elif energy < 50:
        return "Sub-optimal energy detected. Reducing exploratory radius. Prioritising efficient movement patterns."
    elif excited:
        return "Elevated arousal state confirmed. Dopaminergic pathways active. Integrating external stimulus data."
    return "Nominal cognitive state. Exploratory curiosity loop engaged. Synthetic awareness: stable."


def _process_pixel_context(context: str) -> None:
    print(_pixel_context_message(context))


def _logic_api_response(expression: str) -> str:
    expression = _normalize_expression(expression)
    result = _evaluate_logical_expression(expression, announce=False)
    if result == UNKNOWN:
        return f"Unknown logical expression: {expression}"
    return f"Logic result: {'TRUE' if result == TRUE else 'FALSE'}"


def process_intent_api(text: str) -> str:
    """Programmatic entry point — no stdin interaction. Returns response as string."""
    if text is None:
        text = ""
    text = str(text).strip()
    if not text:
        return "Intent processed: "

    text_lower = text.lower()

    try:
        if text_lower.startswith("pixel:"):
            response = _pixel_context_message(text[len("pixel:"):])
        elif text_lower.startswith("reason about "):
            response = "\n".join(_reason_about_lines(text[len("reason about "):].strip()))
        elif text_lower.startswith("logic "):
            response = _logic_api_response(text[len("logic "):].strip())
        else:
            response = "\n".join(_reason_about_lines(text))
    except Exception as e:
        return f"System error: {e}"
    return response if response else f"Intent processed: {text}"


if __name__ == "__main__":
    print("intent.py is the soul module (identity, reasoning, self-narrative).")
    print("It has no runnable body of its own — start the system with run.py.")
    sys.exit(1)
