#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details
# Noesis Object Encoding (.noe) Linter - Version 1.0.0

import re
import sys
import argparse
import os


def is_minified(file_path):
    if file_path.endswith(".min.noe"):
        return True
    try:
        with open(file_path) as f:
            lines = f.readlines()
        return len(lines) < 5
    except Exception:
        return False


def check_balanced_braces(content, verbose):
    open_count = content.count('{')
    close_count = content.count('}')
    if open_count != close_count:
        print(f"Error: Unbalanced braces. Found {open_count} {{ and {close_count} }}")
        return False
    if verbose:
        print(f"✓ Braces are balanced ({open_count} pairs)")
    return True


def check_field_declarations(content, verbose):
    errors = 0
    field_count = len(re.findall(r'field \w+', content))

    if field_count == 0:
        print("Error: No field declarations found. Every .noe file must have at least one field.")
        errors += 1
    elif verbose:
        print(f"✓ Found {field_count} field declaration(s)")

    for lineno, line in enumerate(content.splitlines(), 1):
        if 'field' in line:
            if not re.search(r'field [A-Za-z0-9_]+ \{', line):
                print(f"Line {lineno}: Invalid field declaration: {line.strip()}")
                errors += 1

    return errors == 0


def check_define_statements(content, verbose):
    errors = 0
    define_count = len(re.findall(r'define [A-Za-z0-9_.]+:', content))

    if define_count == 0:
        print("Warning: No define statements found. Fields usually contain define statements.")
    elif verbose:
        print(f"✓ Found {define_count} define statement(s)")

    for lineno, line in enumerate(content.splitlines(), 1):
        if 'define' in line and '//' not in line:
            if not re.search(r'define [A-Za-z0-9_.]+:', line):
                print(f"Line {lineno}: Invalid define statement: {line.strip()}")
                errors += 1

    return errors == 0


def check_directives(content, verbose):
    errors = 0
    superposition_count = len(re.findall(r'@superposition', content))
    dynamic_count = len(re.findall(r'@dynamic', content))
    fixed_count = len(re.findall(r'@fixed', content))

    if verbose:
        print(f"✓ Found directives: @superposition ({superposition_count}), @dynamic ({dynamic_count}), @fixed ({fixed_count})")

    for lineno, line in enumerate(content.splitlines(), 1):
        if '//' in line:
            continue
        if '@superposition' in line:
            if not re.search(r'@superposition \{', line):
                print(f"Line {lineno}: Invalid @superposition directive: {line.strip()}")
                print('  Proper format: @superposition { key = value, ... }')
                errors += 1
        if '@dynamic' in line:
            if not re.search(r'@dynamic\("[^"]*"\)', line):
                print(f"Line {lineno}: Invalid @dynamic directive: {line.strip()}")
                print('  Proper format: @dynamic("string")')
                errors += 1
        if '@fixed' in line:
            if not re.search(r'@fixed\("[^"]*"\)', line):
                print(f"Line {lineno}: Invalid @fixed directive: {line.strip()}")
                print('  Proper format: @fixed("timestamp")')
                errors += 1

    return errors == 0


def check_quantum_circuits(content, verbose):
    errors = 0
    qc_count = len(re.findall(r'quantum_circuit \w+', content))

    if qc_count > 0 and verbose:
        print(f"✓ Found {qc_count} quantum circuit(s)")

    in_circuit = False
    has_qbits = False
    has_apply = False

    for lineno, line in enumerate(content.splitlines(), 1):
        if '//' in line:
            continue

        if 'quantum_circuit' in line:
            in_circuit = True
            has_qbits = False
            has_apply = False
            if not re.search(r'quantum_circuit [A-Za-z0-9_]+ \{', line):
                print(f"Line {lineno}: Invalid quantum_circuit declaration: {line.strip()}")
                errors += 1

        if in_circuit:
            if 'qbits:' in line:
                has_qbits = True
                if not re.search(r'qbits: \[.*\]', line):
                    print(f"Line {lineno}: Invalid qbits declaration: {line.strip()}")
                    errors += 1
            if 'apply:' in line:
                has_apply = True
            if '->' in line and '//' not in line:
                if not re.search(r'-> [A-Za-z0-9_]+', line):
                    print(f"Line {lineno}: Invalid gate application: {line.strip()}")
                    errors += 1
            if '}' in line:
                if not has_qbits or not has_apply:
                    print(f"Line {lineno}: Quantum circuit missing required sections (qbits and/or apply)")
                    errors += 1
                in_circuit = False

    return errors == 0


def check_comments(content, verbose):
    comment_count = len(re.findall(r'// ', content))
    if comment_count > 0 and verbose:
        print(f"✓ Found {comment_count} comment(s)")


def fix_noe_file(file_path, minified):
    with open(file_path) as f:
        content = f.read()

    if not minified:
        lines = content.splitlines()
        fixed_lines = []
        depth = 0

        for line in lines:
            clean = line.strip()

            if '}' in clean:
                depth = max(0, depth - 1)

            indent = '  ' * depth

            if not clean or clean.startswith('//'):
                fixed_lines.append(clean)
            else:
                fixed_lines.append(f"{indent}{clean}")

            if '{' in clean and '}' not in clean:
                depth += 1

        fixed_content = '\n'.join(fixed_lines)
    else:
        fixed_content = content.replace('\n', '').replace('\r', '')

    with open(file_path, 'w') as f:
        f.write(fixed_content)

    print(f"Fixed formatting issues in {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Noesis Object Encoding (.noe) Linter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  noe_lint.py sample.noe\n  noe_lint.py --verbose sample.noe\n  noe_lint.py --fix sample.min.noe"
    )
    parser.add_argument("file", help="The .noe file to lint")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information about each check")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix minor issues")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Error: File '{args.file}' does not exist.")
        sys.exit(1)

    if not (args.file.endswith('.noe') or args.file.endswith('.min.noe')):
        print(f"Warning: File '{args.file}' does not have .noe or .min.noe extension.")

    minified = is_minified(args.file)

    with open(args.file) as f:
        content = f.read()

    print(f"Linting {args.file}...")
    print("Detected minified .noe format" if minified else "Detected full .noe format")

    errors = 0

    if not check_balanced_braces(content, args.verbose):
        errors += 1
    if not check_field_declarations(content, args.verbose):
        errors += 1
    if not check_define_statements(content, args.verbose):
        errors += 1
    if not check_directives(content, args.verbose):
        errors += 1
    if not check_quantum_circuits(content, args.verbose):
        errors += 1

    check_comments(content, args.verbose)

    if errors == 0:
        print("✓ Lint successful: No syntax errors found.")
        if args.fix:
            fix_noe_file(args.file, minified)
        sys.exit(0)
    else:
        print(f"✗ Lint failed: {errors} syntax error(s) found.")
        if args.fix:
            print("Automatic fixing is not available for files with syntax errors.")
            print("Please fix the errors manually and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
