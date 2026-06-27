#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime


def _load_config():
    import importlib.util
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")
    spec = importlib.util.spec_from_file_location("config", cfg_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def process_noe_file(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return None

    if not file_path.endswith(".noe"):
        print("Error: Only .noe files are supported", file=sys.stderr)
        return None

    print(f"Processing .noe file: {file_path}", file=sys.stderr)

    cfg = _load_config()
    if not os.path.isdir(cfg.NOE_CORE_PATH):
        print(f"Error: noe-core repository not found at {cfg.NOE_CORE_PATH}", file=sys.stderr)
        return None

    parsed = parse_noe_file(file_path)
    result = process_noe_data(parsed, file_path, cfg)
    print(result)
    return result


def parse_noe_file(file_path):
    with open(file_path) as f:
        content = f.read().strip()
    if content.startswith("{"):
        return f"json:{content}"
    return f"raw:{content}"


def process_noe_data(data, original_file_path, cfg=None):
    type_part, *rest = data.split(":", 1)
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    basename = os.path.basename(original_file_path)

    result = {
        "processed": True,
        "timestamp": now,
        "originalFile": basename,
        "type": type_part,
    }
    return json.dumps(result)


def execute_noe_command(command):
    cfg = _load_config()
    if not os.path.isdir(cfg.NOE_CORE_PATH):
        print(f"Error: noe-core not found at {cfg.NOE_CORE_PATH}", file=sys.stderr)
        return None

    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cfg.NOE_CORE_PATH)
    if result.returncode != 0:
        print(f"Error executing noe-core command: {command}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return None
    return result.stdout


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: noe_processor.py <file_path>", file=sys.stderr)
        sys.exit(1)
    process_noe_file(sys.argv[1])
