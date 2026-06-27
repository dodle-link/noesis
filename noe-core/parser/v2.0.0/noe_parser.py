#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under Noesis License - See LICENSE file for details
# Noesis Object Encoding (.noe) Parser and Linter - Version 1.0.0

import re
import sys
import argparse
import os
import json


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


def validate_grammar(file_path, verbose=False):
    print(f"Validating {file_path} against formal grammar...")

    with open(file_path) as f:
        contents = f.read()

    valid = True

    if re.search(r'field\s+[A-Za-z][A-Za-z0-9_]*\s*\{', contents):
        if verbose:
            print("✓ Valid field blocks found")
    else:
        print("Error: No valid field blocks found. Field blocks should follow pattern: field Name { ... }")
        valid = False

    open_count = contents.count('{')
    close_count = contents.count('}')
    if open_count != close_count:
        print(f"Error: Unbalanced braces. Found {open_count} opening and {close_count} closing braces.")
        valid = False

    if re.search(r'define\s+[A-Za-z][A-Za-z0-9_.]*\s*:', contents):
        print("✓ Valid define statements found")
    else:
        print("Error: No valid define statements found. Define statements should follow pattern: define name: ...")
        valid = False

    if re.search(r'@(superposition|dynamic|fixed)', contents):
        print("✓ Valid type expressions found")
    else:
        print("Warning: No standard type expressions (@superposition, @dynamic, @fixed) found")

    if valid:
        print("✓ File appears to be valid according to grammar rules")
    else:
        print("✗ File contains grammar errors")

    return valid


def _parse_value(line):
    line = line.rstrip(';').strip()
    if re.search(r'=\s*\{', line):
        m = re.search(r'=\s*(\{[^}]*\})', line)
        return m.group(1) if m else 'null'
    if re.search(r'=\s*\(', line):
        m = re.search(r'=\s*(\([^)]*\))', line)
        if m:
            return m.group(1).replace('(', '[').replace(')', ']')
        return 'null'
    if re.search(r'=\s*\[', line):
        m = re.search(r'=\s*(\[[^\]]*\])', line)
        return m.group(1) if m else 'null'
    if re.search(r'=\s*(true|false)\b', line):
        m = re.search(r'=\s*(true|false)', line)
        return m.group(1) if m else 'null'
    if re.search(r'=\s*null\b', line):
        return 'null'
    if re.search(r'=\s*"', line):
        m = re.search(r'=\s*"([^"]*)"', line)
        return f'"{m.group(1)}"' if m else 'null'
    if re.search(r"=\s*'", line):
        m = re.search(r"=\s*'([^']*)'", line)
        return f'"{m.group(1)}"' if m else 'null'
    if re.search(r'=\s*0x', line):
        m = re.search(r'=\s*0x([0-9a-fA-F]+)', line)
        return str(int(m.group(1), 16)) if m else 'null'
    if re.search(r'=\s*0b', line):
        m = re.search(r'=\s*0b([01]+)', line)
        return str(int(m.group(1), 2)) if m else 'null'
    if re.search(r'=\s*[0-9]+\.[0-9]*[eE]', line):
        m = re.search(r'=\s*([0-9.]+[eE][+-]?[0-9]+)', line)
        return m.group(1) if m else 'null'
    m = re.search(r'=\s*([0-9.]+)', line)
    if m:
        return m.group(1)
    return 'null'


def parse_noe(content):
    content = strip_comments(content)

    metadata = {}
    imports = []

    v_m = re.search(r'@version\("([0-9.]+)"\);', content)
    if v_m:
        metadata['_version'] = v_m.group(1)
    a_m = re.search(r'@author\("([^"]*)"\);', content)
    if a_m:
        metadata['_author'] = a_m.group(1)
    d_m = re.search(r'@date\("([^"]*)"\);', content)
    if d_m:
        metadata['_date'] = d_m.group(1)

    result_parts = [f'"_metadata": {json.dumps(metadata)}, "_imports": {json.dumps(imports)}, ']
    depth = 0

    for line in re.sub(r'\s+', ' ', content).splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('@') or line.startswith('import'):
            continue

        if 'field' in line and re.search(r'field [A-Za-z0-9_]+', line):
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

        if '{' in line and 'field' not in line and 'define' not in line and 'quantum_circuit' not in line:
            m = re.search(r'([A-Za-z0-9_.]+)\s*\{', line)
            if m:
                result_parts.append(f'"{m.group(1)}": {{')
                depth += 1

        if '=' in line:
            key_m = re.search(r'([A-Za-z0-9_.]+)\s*=', line)
            if key_m:
                val = _parse_value(line)
                if '#' in val:
                    ref_m = re.search(r'#([A-Za-z0-9_.]+)', val)
                    if ref_m:
                        val = f'{{"_ref": "{ref_m.group(1)}"}}'
                result_parts.append(f'"{key_m.group(1)}": {val},')

        type_m = re.search(r'@([a-zA-Z0-9_]+)', line)
        if type_m:
            result_parts.append(f'"_type": "{type_m.group(1)}",')
            params_m = re.search(r'@[a-zA-Z0-9_]+\(([^)]*)\)', line)
            if params_m:
                result_parts.append(f'"_params": "{params_m.group(1)}",')

        if 'quantum_circuit' in line:
            m = re.search(r'quantum_circuit ([A-Za-z0-9_]+)', line)
            if m:
                result_parts.append(f'"quantum_circuit": {{"name": "{m.group(1)}",')
                depth += 1

        if 'qbits:' in line:
            m = re.search(r'qbits:\s*(\[[^\]]*\])', line)
            if m:
                result_parts.append(f'"qbits": {m.group(1)},')

        if 'apply:' in line:
            result_parts.append('"apply": [')

        if '->' in line:
            gate_m = re.search(r'([A-Za-z0-9_]+)\s*->', line)
            target_m = re.search(r'->\s*([^\s;]*)', line)
            if gate_m and target_m:
                result_parts.append(f'{{"gate": "{gate_m.group(1)}", "target": "{target_m.group(1)}"}},')

        if '}' in line:
            result_parts.append('},')
            depth -= 1

    raw = ''.join(result_parts).rstrip(',')
    return '{' + raw + '}'


def to_json(internal):
    try:
        data = json.loads(internal)
        return json.dumps(data, indent=2)
    except Exception:
        cleaned = re.sub(r',\s*}', '}', internal)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        return cleaned


def _json_to_yaml(obj, indent=0):
    lines = []
    pad = '  ' * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.extend(_json_to_yaml(v, indent + 1))
            else:
                val = json.dumps(v) if isinstance(v, str) else v
                lines.append(f"{pad}{k}: {val}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    prefix = f"{pad}- " if first else f"{pad}  "
                    first = False
                    if isinstance(v, (dict, list)):
                        lines.append(f"{prefix}{k}:")
                        lines.extend(_json_to_yaml(v, indent + 1))
                    else:
                        lines.append(f"{prefix}{k}: {v}")
            else:
                lines.append(f"{pad}- {item}")
    return lines


def to_yaml(internal):
    try:
        data = json.loads(internal)
        return '\n'.join(_json_to_yaml(data))
    except Exception:
        return internal


def main():
    parser = argparse.ArgumentParser(description="Noesis Object Encoding (.noe) Parser and Linter")
    parser.add_argument("file", nargs='?', help="The .noe file to process")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--json", action="store_true", help="Convert .noe to JSON format")
    group.add_argument("--yaml", action="store_true", help="Convert .noe to YAML format")
    group.add_argument("--lint", action="store_true", help="Lint .noe file for syntax errors")
    group.add_argument("--grammar", "-g", action="store_true", help="Validate file against formal BNF grammar")
    parser.add_argument("--version", "-v", action="version", version="Noesis Object Encoding (.noe) Parser - Version 1.0.0")
    args = parser.parse_args()

    if not args.file:
        print("Error: No input file specified")
        parser.print_help()
        sys.exit(1)

    if not os.path.isfile(args.file):
        print(f"Error: File '{args.file}' does not exist.")
        sys.exit(1)

    if not (args.file.endswith('.noe') or args.file.endswith('.min.noe')):
        print(f"Warning: File '{args.file}' does not have .noe or .min.noe extension.")

    if args.grammar:
        sys.exit(0 if validate_grammar(args.file) else 1)

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
    else:
        print("Error: No action specified. Use --json, --yaml, --lint, or --grammar")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
