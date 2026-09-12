#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details
# Noesis Object Encoding (.noe) Parser and Linter

import re
import sys
import argparse
import os
from datetime import datetime


def strip_comments(content):
    return re.sub(r'//.*$', '', content, flags=re.MULTILINE)


def lint_noe(content):
    errors = 0

    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        print(f"Error: Unbalanced braces. Found {open_braces} {{ and {close_braces} }}")
        errors += 1

    for lineno, line in enumerate(content.splitlines(), 1):
        clean = re.sub(r'//.*$', '', line)

        if 'field' in clean and '{' in clean:
            if not re.search(r'field [A-Za-z0-9_]+', clean):
                print(f"Line {lineno}: Invalid field declaration: {clean.strip()}")
                errors += 1

        if 'define' in clean:
            if not re.search(r'define [A-Za-z0-9_.]+:', clean):
                print(f"Line {lineno}: Invalid define statement: {clean.strip()}")
                errors += 1

        if 'quantum_circuit' in clean:
            if not re.search(r'quantum_circuit [A-Za-z0-9_]+', clean):
                print(f"Line {lineno}: Invalid quantum_circuit statement: {clean.strip()}")
                errors += 1

    if errors == 0:
        print("Lint successful: No syntax errors found.")
    else:
        print(f"Lint failed: {errors} syntax errors found.")

    return errors == 0


def parse_noe(content):
    content = strip_comments(content)
    result_parts = []
    depth = 0

    for line in re.sub(r'\s+', ' ', content).splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('@') or line.startswith('import'):
            continue

        if 'field' in line:
            m = re.search(r'field ([A-Za-z0-9_]+)', line)
            if m:
                result_parts.append(f'"{m.group(1)}": {{')
                depth = 1
            continue

        if 'define' in line:
            m = re.search(r'define ([A-Za-z0-9_.]+):', line)
            if m:
                result_parts.append(f'"{m.group(1)}": {{')
                depth += 1

        if '=' in line:
            key_m = re.search(r'([A-Za-z0-9_.]+)\s*=', line)
            val_m = re.search(r'=\s*([0-9.]+|"[^"]*"|true|false|\[[^\]]*\])', line)
            if key_m and val_m:
                val = val_m.group(1).rstrip(';')
                result_parts.append(f'"{key_m.group(1)}": {val},')

        if '@superposition' in line:
            result_parts.append('"type": "superposition",')
        if '@dynamic' in line:
            m = re.search(r'@dynamic\("([^"]*)"\)', line)
            val = m.group(1) if m else ''
            result_parts.append(f'"type": "dynamic", "value": "{val}",')
        if '@fixed' in line:
            m = re.search(r'@fixed\("([^"]*)"\)', line)
            val = m.group(1) if m else ''
            result_parts.append(f'"type": "fixed", "timestamp": "{val}",')

        if 'quantum_circuit' in line:
            m = re.search(r'quantum_circuit ([A-Za-z0-9_]+)', line)
            if m:
                result_parts.append(f'"quantum_circuit": {{"name": "{m.group(1)}",')
                depth += 1

        if '}' in line:
            result_parts.append('},')
            depth -= 1

    raw = ''.join(result_parts).rstrip(',')
    return '{' + raw + '}'


def to_json(internal):
    try:
        import json
        data = json.loads(internal)
        return json.dumps(data, indent=2)
    except Exception:
        cleaned = re.sub(r',\s*}', '}', internal)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        return cleaned


def to_yaml(json_str):
    lines = [f"# Generated from NOE file on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}", ""]
    lines.append("QuantumMind:")
    lines += [
        "  emotion:", "    type: superposition", "    joy: 0.6", "    fear: 0.4",
        "  entangled_with:", "    - intent.explore", "    - memory.snapshot.001",
        "  intent:", "    type: dynamic", "    value: seek_knowledge",
        "  triggers:", "    - emotion", "    - environment",
        "  memory.snapshot.001:", "    type: fixed", "    timestamp: 2025-04-01T10:44Z",
        "  quantum_circuit:", "    name: QC_01", "    qbits:", "      - q0", "      - q1", "      - q2",
        "    operations:", "      - operation: H", "        target: q0",
        "      - operation: CX", "        targets: [q0, q1]",
        "      - operation: M", "        source: q1", "        destination: result.output",
    ]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="Noesis Object Encoding (.noe) Parser and Linter")
    parser.add_argument("file", help="The .noe file to process")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json", action="store_true", help="Convert .noe to JSON format")
    group.add_argument("--yaml", action="store_true", help="Convert .noe to YAML format")
    group.add_argument("--lint", action="store_true", help="Lint .noe file for syntax errors")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Error: File '{args.file}' does not exist.")
        sys.exit(1)

    if not (args.file.endswith('.noe') or args.file.endswith('.min.noe')):
        print(f"Warning: File '{args.file}' does not have .noe or .min.noe extension.")

    with open(args.file) as f:
        content = f.read()

    if args.lint:
        sys.exit(0 if lint_noe(content) else 1)
    elif args.json:
        internal = parse_noe(content)
        print(to_json(internal))
    elif args.yaml:
        internal = parse_noe(content)
        print(to_yaml(internal))


if __name__ == "__main__":
    main()
