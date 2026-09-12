#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details
# YAML Markup Language (.yml) Parser and Converter

import sys
import argparse
import os
import re


def lint_yml(content):
    errors = 0
    for lineno, line in enumerate(content.splitlines(), 1):
        if not line.strip() or line.strip().startswith('#'):
            continue

        indent = len(line) - len(line.lstrip(' '))
        if indent % 2 != 0:
            print(f"Line {lineno}: Invalid indentation, must be multiple of 2 spaces: {line}")
            errors += 1

        if ':' in line and ': ' not in line and not line.rstrip().endswith(':'):
            print(f"Line {lineno}: Invalid colon usage, must have space after: {line}")
            errors += 1

        if '[' in line and ']' not in line:
            print(f"Line {lineno}: Possible unclosed array: {line}")
            errors += 1

        if '\t' in line:
            print(f"Line {lineno}: Tab characters are not allowed in YAML: {line}")
            errors += 1

    return errors


def yml_to_json(content):
    try:
        import yaml
        import json
        data = yaml.safe_load(content)
        print(json.dumps(data, indent=2))
        return True
    except ImportError:
        print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error converting YAML to JSON: {e}", file=sys.stderr)
        return False


def _get_type(value):
    if isinstance(value, bool):
        return 'boolean'
    elif isinstance(value, (int, float)):
        return 'number'
    elif isinstance(value, str):
        return 'string'
    return 'unknown'


def _serialize_value(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        escaped = value.replace('"', '\\"').replace('\n', '\\n')
        return f'"{escaped}"'
    return str(value)


def _serialize_list(items):
    elements = []
    for item in items:
        if isinstance(item, (dict, list)):
            elements.append(_serialize_complex(item))
        else:
            elements.append(_serialize_value(item))
    return f"[{', '.join(elements)}]"


def _serialize_complex(value):
    if isinstance(value, dict):
        parts = [f"{k}: {_serialize_value(v)}" for k, v in value.items()]
        return "{" + ', '.join(parts) + "}"
    elif isinstance(value, list):
        return _serialize_list(value)
    return _serialize_value(value)


def _yaml_to_noe(data, prefix=''):
    lines = []
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}{key}" if prefix else key
            if isinstance(value, dict):
                lines.append(_yaml_to_noe(value, f"{full_key}."))
            elif isinstance(value, list):
                lines.append(f"field {full_key} {{ type: array, value: {_serialize_list(value)} }}")
            else:
                lines.append(f"field {full_key} {{ type: {_get_type(value)}, value: {_serialize_value(value)} }}")
    return '\n'.join(lines)


def yml_to_noe(content):
    try:
        import yaml
        data = yaml.safe_load(content)
        print(_yaml_to_noe(data))
        return True
    except ImportError:
        print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error converting YAML to NOE: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="YAML Markup Language (.yml) Parser and Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  yml_parser.py --json sample.yml > output.json\n  yml_parser.py --noe sample.yml > output.noe\n  yml_parser.py --lint sample.yml"
    )
    parser.add_argument("file", help="The .yml file to process")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json", action="store_true", help="Convert .yml to JSON format")
    group.add_argument("--noe", action="store_true", help="Convert .yml to NOE format")
    group.add_argument("--lint", action="store_true", help="Lint .yml file for syntax errors")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Error: File '{args.file}' does not exist.")
        sys.exit(1)

    if not (args.file.endswith('.yml') or args.file.endswith('.yaml')):
        print(f"Warning: File '{args.file}' does not have .yml or .yaml extension.")

    with open(args.file) as f:
        content = f.read()

    if args.lint:
        print(f"Linting YAML file: {args.file}")
        error_count = lint_yml(content)
        if error_count == 0:
            print("No syntax errors found.")
            sys.exit(0)
        else:
            print(f"Found {error_count} error(s) in the YAML file.")
            sys.exit(error_count)
    elif args.json:
        print(f"Converting YAML to JSON: {args.file}", file=sys.stderr)
        sys.exit(0 if yml_to_json(content) else 1)
    elif args.noe:
        print(f"Converting YAML to NOE: {args.file}", file=sys.stderr)
        sys.exit(0 if yml_to_noe(content) else 1)


if __name__ == "__main__":
    main()
