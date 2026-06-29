#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details

import os
import re
import json
import importlib.util

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_MODULE_DIR)))
_PARSER_PATH = os.path.join(_PROJECT_ROOT, "noe-lang", "parser", "v2.0.0", "noe_parser.py")
_LINTER_PATH = os.path.join(_PROJECT_ROOT, "noe-lang", "lint", "v2.0.0", "noe_lint.py")
STATE_DIR = os.path.expanduser("~/.noesis/state")

_parser_module = None
_linter_module = None


def _load_mod(path):
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("_noe_mod", path)
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
