#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun.
# Licensed under the MIT License.

import os
import subprocess
import sys

PARSER = os.path.join(os.path.dirname(__file__), "..", "parser", "v2.0.0", "noe_parser.py")
LINTER = os.path.join(os.path.dirname(__file__), "..", "LINT", "v2.0.0", "noe_lint.py")
SAMPLE = os.path.join(os.path.dirname(__file__), "sample.noe")
SAMPLE_MIN = os.path.join(os.path.dirname(__file__), "sample.min.noe")


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def main():
    print("Noesis Object Encoding (.noe) Tools Examples")
    print("=============================================")
    print()

    print("Example 1: Linting a .noe file")
    print("-----------------------------")
    subprocess.run([sys.executable, LINTER, "--verbose", SAMPLE])
    print()

    print("Example 2: Validating against formal BNF grammar")
    print("--------------------------------------------")
    subprocess.run([sys.executable, PARSER, "--grammar", SAMPLE])
    print()

    print("Example 3: Converting .noe to JSON")
    print("--------------------------------")
    out = run([sys.executable, PARSER, "--json", SAMPLE])
    json_path = os.path.join(os.path.dirname(__file__), "sample.json")
    with open(json_path, "w") as f:
        f.write(out)
    print("Converted to sample.json")
    print("\n".join(out.splitlines()[:10]))
    print("...")
    print()

    print("Example 4: Converting .noe to YAML")
    print("--------------------------------")
    out = run([sys.executable, PARSER, "--yaml", SAMPLE])
    yaml_path = os.path.join(os.path.dirname(__file__), "sample.yaml")
    with open(yaml_path, "w") as f:
        f.write(out)
    print("Converted to sample.yaml")
    print("\n".join(out.splitlines()[:10]))
    print("...")
    print()

    print("Example 5: Using with minified .noe files")
    print("---------------------------------------")
    out = run([sys.executable, PARSER, "--json", SAMPLE_MIN])
    min_json_path = os.path.join(os.path.dirname(__file__), "sample.min.json")
    with open(min_json_path, "w") as f:
        f.write(out)
    print("Converted minified .noe to JSON")
    print("\n".join(out.splitlines()[:10]))
    print("...")
    print()

    print("Examples completed. You can now use these tools for your .noe files.")


if __name__ == "__main__":
    main()
