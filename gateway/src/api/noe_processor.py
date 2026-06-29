#!/usr/bin/env python3
import os
import sys
import json
import importlib.util
from datetime import datetime

_GATEWAY_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PROJECT_ROOT = os.path.dirname(_GATEWAY_DIR)
_PARSER_PATH = os.path.join(_PROJECT_ROOT, "noe-lang", "parser", "v2.0.0", "noe_parser.py")

_parser = None


def _load_parser():
    global _parser
    if _parser:
        return _parser
    if not os.path.isfile(_PARSER_PATH):
        return None
    spec = importlib.util.spec_from_file_location("noe_parser", _PARSER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _parser = mod
    return mod


def process_noe_file(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return None

    if not file_path.endswith(".noe"):
        print("Error: Only .noe files are supported", file=sys.stderr)
        return None

    print(f"Processing .noe file: {file_path}", file=sys.stderr)
    parsed = parse_noe_file(file_path)
    result = process_noe_data(parsed, file_path)
    print(result)
    return result


def parse_noe_file(file_path):
    parser = _load_parser()
    with open(file_path) as f:
        content = f.read()
    if parser:
        raw = parser.parse_noe(content)
        try:
            return json.loads(parser.to_json(raw))
        except Exception:
            pass
    if content.strip().startswith("{"):
        return json.loads(content)
    return {"_raw": content}


def process_noe_data(data, original_file_path, cfg=None):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    basename = os.path.basename(original_file_path)
    result = {
        "processed": True,
        "timestamp": now,
        "originalFile": basename,
        "data": data,
    }
    return json.dumps(result, indent=2)


def execute_noe_command(command):
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {command}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return None
    return result.stdout


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: noe_processor.py <file_path>", file=sys.stderr)
        sys.exit(1)
    process_noe_file(sys.argv[1])

