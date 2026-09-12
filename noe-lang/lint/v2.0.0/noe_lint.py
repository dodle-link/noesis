#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details
# Noesis Object Encoding (.noe) Linter - Version 2.0.0

import re
import sys
import argparse


def is_minified(file_path):
    if file_path.endswith(".min.noe"):
        return True
    try:
        with open(file_path) as f:
            lines = f.readlines()
        return len(lines) < 5
    except Exception:
        return False


def check_directives(content, verbose):
    version_match = re.search(r'@version\("([0-9\.]+)"\);', content)
    if version_match:
        if verbose:
            print(f"✓ Found version directive: {version_match.group(1)}")
    else:
        print('Warning: No @version directive found. Recommended format: @version("2.0.0");')

    author_match = re.search(r'@author\("([^"]*)"\);', content)
    if author_match and verbose:
        print(f"✓ Found author directive: {author_match.group(1)}")

    directive_count = len(re.findall(r'@[a-zA-Z0-9_]+\([^)]*\);', content))
    if directive_count > 0 and verbose:
        print(f"✓ Found {directive_count} directive(s) total")

    import_count = len(re.findall(r'import "[^"]+";', content))
    if import_count > 0 and verbose:
        print(f"✓ Found {import_count} import statement(s)")

    type_exprs = set(re.findall(
        r'@(superposition|dynamic|fixed|enum|timestamp|array|object|tuple|reference|string|boolean|number|int)',
        content
    ))
    if type_exprs and verbose:
        print(f"✓ Found type expressions: {', '.join(sorted(type_exprs))}")


def check_balanced_braces(content, verbose):
    open_count = content.count('{')
    close_count = content.count('}')
    if open_count != close_count:
        print(f"Error: Unbalanced braces. Found {open_count} {{ and {close_count} }}")
        return False
    if verbose:
        print(f"✓ Braces are balanced ({open_count} pairs)")
    return True


def check_balanced_parentheses(content, verbose):
    open_count = content.count('(')
    close_count = content.count(')')
    if open_count != close_count:
        print(f"Error: Unbalanced parentheses. Found {open_count} ( and {close_count} )")
        return False
    if verbose:
        print(f"✓ Parentheses are balanced ({open_count} pairs)")
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
        if 'field' in line and '//' not in line and '/*' not in line:
            if not re.search(r'field [A-Za-z0-9_]+ \{', line):
                print(f"Line {lineno}: Invalid field declaration: {line.strip()}")
                print("  Proper format: field FieldName { ... }")
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
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('/*'):
            continue
        if 'define' in line:
            if not re.search(r'define [A-Za-z0-9_.]+:', line):
                print(f"Line {lineno}: Invalid define statement: {line.strip()}")
                print("  Proper format: define identifier: @type_expression [{ ... }];")
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
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('/*'):
            continue

        if 'quantum_circuit' in line:
            in_circuit = True
            has_qbits = False
            has_apply = False
            if not re.search(r'quantum_circuit [A-Za-z0-9_]+ \{', line):
                print(f"Line {lineno}: Invalid quantum_circuit declaration: {line.strip()}")
                print("  Proper format: quantum_circuit CircuitName { ... }")
                errors += 1

        if in_circuit:
            if 'qbits:' in line:
                has_qbits = True
                if not re.search(r'qbits: \[.*\]', line):
                    print(f"Line {lineno}: Invalid qbits declaration: {line.strip()}")
                    print("  Proper format: qbits: [q0, q1, ...];")
                    errors += 1

            if 'apply:' in line:
                has_apply = True

            if '->' in line:
                if not re.search(r'-> ([A-Za-z0-9_]+|\[[^\]]+\]|\([^)]+\))', line):
                    print(f"Line {lineno}: Invalid gate application: {line.strip()}")
                    print("  Proper format: Gate -> qbit; or Gate -> (q0, q1); or Gate -> [q0, q1];")
                    errors += 1

            if '}' in line:
                if not has_qbits or not has_apply:
                    print(f"Line {lineno}: Quantum circuit missing required sections (qbits and/or apply)")
                    errors += 1
                in_circuit = False

    return errors == 0


def check_comments(content, verbose):
    single_count = len(re.findall(r'//', content))
    multi_begin = len(re.findall(r'/\*', content))
    multi_end = len(re.findall(r'\*/', content))

    if multi_begin != multi_end:
        print(f"Error: Unbalanced multi-line comments. Found {multi_begin} /* and {multi_end} */")
        return False

    if (single_count + multi_begin) > 0 and verbose:
        print(f"✓ Found {single_count} single-line and {multi_begin} multi-line comment(s)")

    return True


def check_references(content, verbose):
    ref_count = len(re.findall(r'#[A-Za-z0-9_.]+', content))
    if ref_count > 0 and verbose:
        print(f"✓ Found {ref_count} reference(s)")


def validate_grammar(file_path, verbose):
    print(f"Validating {file_path} against formal grammar...")
    with open(file_path) as f:
        contents = f.read()

    valid = True

    if re.search(r'field\s+[A-Za-z][A-Za-z0-9_]*\s*\{', contents):
        if verbose:
            print("✓ Valid field blocks found")
    else:
        print("Error: No valid field blocks found. Field blocks should follow the pattern defined in grammar.bnf")
        valid = False

    if re.search(r'@[a-zA-Z][a-zA-Z0-9_]*(\([^)]*\))?\s*;', contents) and verbose:
        print("✓ Valid directives found")

    if re.search(r'import\s+"[^"]+"\s*(as\s+[A-Za-z][A-Za-z0-9_]*)?\s*;', contents) and verbose:
        print("✓ Valid import statements found")

    if re.search(r'define\s+[A-Za-z][A-Za-z0-9_.]*\s*:', contents):
        if verbose:
            print("✓ Valid define statements found")
    else:
        print("Error: No valid define statements found. Define statements should follow the pattern defined in grammar.bnf")
        valid = False

    if re.search(r'@(superposition|dynamic|fixed|enum|timestamp|array|object|tuple|reference|string|boolean|number|int)', contents):
        if verbose:
            print("✓ Valid type expressions found")
    else:
        print("Warning: No standard type expressions found")

    if valid:
        print("✓ File appears to be valid according to grammar rules")
    else:
        print("✗ File contains grammar errors")

    return valid


def check_data_literals(content, verbose):
    if verbose:
        arrays = len(re.findall(r'\[[^\]]*\]', content))
        if arrays:
            print(f"✓ Found {arrays} array literal(s)")
        objects = len(re.findall(r'\{[^{}]*\}', content))
        if objects:
            print(f"✓ Found {objects} object literal(s)")
        tuples = len(re.findall(r'\([^()]*\)', content))
        if tuples:
            print(f"✓ Found {tuples} tuple literal(s)")
        scientific = len(re.findall(r'[0-9]+\.[0-9]*[eE][+-]?[0-9]+', content))
        if scientific:
            print(f"✓ Found {scientific} scientific notation value(s)")
        hex_vals = len(re.findall(r'0x[0-9a-fA-F]+', content))
        if hex_vals:
            print(f"✓ Found {hex_vals} hexadecimal value(s)")
        binary = len(re.findall(r'0b[01]+', content))
        if binary:
            print(f"✓ Found {binary} binary value(s)")
        bools = len(re.findall(r'= (true|false)', content))
        if bools:
            print(f"✓ Found {bools} boolean value(s)")
        nulls = len(re.findall(r'= null', content))
        if nulls:
            print(f"✓ Found {nulls} null value(s)")


def fix_noe_file(file_path, minified):
    with open(file_path) as f:
        content = f.read()

    if not minified:
        lines = content.splitlines()
        fixed_lines = []
        depth = 0
        in_multiline = False

        for line in lines:
            clean = line.strip()

            if '/*' in clean and '*/' not in clean:
                in_multiline = True
                fixed_lines.append(clean)
                continue

            if in_multiline:
                if '*/' in clean:
                    in_multiline = False
                fixed_lines.append(clean)
                continue

            if not clean or clean.startswith('//') or (clean.startswith('/*') and clean.endswith('*/')):
                fixed_lines.append(clean)
                continue

            if '}' in clean and '{' not in clean:
                depth = max(0, depth - 1)

            indent = '  ' * depth
            fixed_lines.append(f"{indent}{clean}")

            if '{' in clean and '}' not in clean:
                depth += 1

        fixed_content = '\n'.join(fixed_lines)
    else:
        fixed_content = re.sub(r'\s+', '', content)

    with open(file_path, 'w') as f:
        f.write(fixed_content)

    print(f"Fixed formatting issues in {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Noesis Object Encoding (.noe) Linter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  noe_lint.py sample.noe\n  noe_lint.py --verbose sample.noe\n  noe_lint.py --fix sample.min.noe\n  noe_lint.py --grammar sample.noe"
    )
    parser.add_argument("file", help="The .noe file to lint")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information about each check")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix minor issues")
    parser.add_argument("--grammar", action="store_true", help="Validate against formal grammar.bnf")
    parser.add_argument("--version", "-v", action="version", version="Noesis Object Encoding (.noe) Linter - Version 2.0.0")
    args = parser.parse_args()

    import os
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

    check_directives(content, args.verbose)

    if not check_balanced_braces(content, args.verbose):
        errors += 1
    if not check_balanced_parentheses(content, args.verbose):
        errors += 1
    if not check_comments(content, args.verbose):
        errors += 1
    if not check_field_declarations(content, args.verbose):
        errors += 1
    if not check_define_statements(content, args.verbose):
        errors += 1
    if not check_quantum_circuits(content, args.verbose):
        errors += 1

    check_references(content, args.verbose)
    check_data_literals(content, args.verbose)

    if args.grammar:
        if not validate_grammar(args.file, args.verbose):
            errors += 1

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
