#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

GATE_MAP = {
    "H": "h",
    "X": "x",
    "Y": "y",
    "Z": "z",
    "CNOT": "cx",
    "SWAP": "swap",
}


def export_qasm(gates, num_qubits, output_file="circuit.qasm"):
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{num_qubits}];",
        f"creg c[{num_qubits}];",
    ]

    for gate in gates:
        name = gate.get("name", "")
        targets = gate.get("targets", [])
        qasm_name = GATE_MAP.get(name)

        if qasm_name is None:
            lines.append(f"# Unsupported gate: {name}")
        elif name in ("CNOT", "SWAP") and len(targets) >= 2:
            lines.append(f"{qasm_name} q[{targets[0]}], q[{targets[1]}];")
        elif targets:
            lines.append(f"{qasm_name} q[{targets[0]}];")

    lines.append("measure q -> c;")

    content = "\n".join(lines) + "\n"
    with open(output_file, "w") as f:
        f.write(content)

    print(f"Circuit exported to {output_file}")
    return content


def generate_qasm_string(gates, num_qubits):
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{num_qubits}];",
        f"creg c[{num_qubits}];",
    ]

    for gate in gates:
        name = gate.get("name", "")
        targets = gate.get("targets", [])
        qasm_name = GATE_MAP.get(name)

        if qasm_name is None:
            lines.append(f"# Unsupported gate: {name}")
        elif name in ("CNOT", "SWAP") and len(targets) >= 2:
            lines.append(f"{qasm_name} q[{targets[0]}], q[{targets[1]}];")
        elif targets:
            lines.append(f"{qasm_name} q[{targets[0]}];")

    lines.append("measure q -> c;")
    return "\n".join(lines)


def validate_qasm(qasm_file):
    if not qasm_file:
        print("Error: No QASM file specified")
        return False

    if not __import__("os").path.isfile(qasm_file):
        print(f"Error: QASM file {qasm_file} does not exist")
        return False

    with open(qasm_file) as f:
        content = f.read()

    if "OPENQASM 2.0;" not in content:
        print("Error: Missing OPENQASM 2.0 header")
        return False

    if 'include "qelib1.inc";' not in content:
        print("Error: Missing qelib1.inc include")
        return False

    if "qreg" not in content:
        print("Error: No quantum register defined")
        return False

    print("QASM syntax validation passed")
    return True
