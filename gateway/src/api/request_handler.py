#!/usr/bin/env python3
import os
import sys
import json
import re
import subprocess
import importlib.util
from http.server import BaseHTTPRequestHandler

UPLOAD_DIR = os.path.join(os.getcwd(), "temp", "uploads")
NOE_CORE_PATH = os.path.join(os.getcwd(), "..", "noe-core")

_INTENT_MODULE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "core", "soul", "intent.py"
)


def _load_intent_module():
    spec = importlib.util.spec_from_file_location("noesis_intent", _INTENT_MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def send_response(status, body):
    body_bytes = body.encode()
    print(f"HTTP/1.1 {status}")
    print("Content-Type: application/json")
    print(f"Content-Length: {len(body_bytes)}")
    print("Access-Control-Allow-Origin: *")
    print()
    print(body)


def handle_request(method, path, body="", headers=None):
    route = f"{method} {path}"

    if path == "/api/noesis" and method == "POST":
        try:
            data = json.loads(body) if body else {}
        except (json.JSONDecodeError, ValueError):
            data = {}

        action = data.get("action", "")

        if action == "getVersion":
            send_response("200 OK", json.dumps({"version": "2.2.0", "status": "online"}))

        elif action == "updateState":
            send_response("200 OK", json.dumps({"status": "saved"}))

        elif action == "think":
            input_text = data.get("input", "").strip()
            if not input_text:
                send_response("400 Bad Request", json.dumps({"error": "input is required for think action"}))
                return
            try:
                intent_mod = _load_intent_module()
                response_text = intent_mod.process_intent_api(input_text)
                send_response("200 OK", json.dumps({"response": response_text, "status": "processed"}))
            except Exception as e:
                send_response("500 Internal Server Error", json.dumps({"error": str(e)}))

        else:
            send_response("400 Bad Request", json.dumps({"error": f"Unknown action: {action}"}))

    elif route == "GET /api/noe/status":
        if os.path.isdir(NOE_CORE_PATH):
            send_response("200 OK", json.dumps({"status": "connected", "path": NOE_CORE_PATH}))
        else:
            send_response("200 OK", json.dumps({"status": "disconnected", "message": "noe-core repository not found"}))

    elif route == "POST /api/noe/process":
        import time
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ts = int(time.time())
        test_file = os.path.join(UPLOAD_DIR, f"test-{ts}.noe")
        with open(test_file, "w") as f:
            f.write("This is a test .noe file content")

        if process_noe_file(test_file):
            send_response("200 OK", json.dumps({"message": "File processed successfully", "file": test_file}))
        else:
            send_response("500 Internal Server Error", json.dumps({"error": "Failed to process file"}))

    elif route == "POST /api/noe/command":
        m = re.search(r'"command":"([^"]+)"', body)
        command = m.group(1) if m else None

        if not command:
            send_response("400 Bad Request", json.dumps({"error": "Command is required"}))
            return

        if os.path.isdir(NOE_CORE_PATH):
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=NOE_CORE_PATH)
            send_response("200 OK", json.dumps({"status": "success", "command": command, "output": result.stdout}))
        else:
            send_response("500 Internal Server Error", json.dumps({"status": "error", "message": "noe-core not found"}))

    elif method == "OPTIONS":
        send_response("200 OK", "{}")

    else:
        send_response("404 Not Found", json.dumps({"error": f"Route not found: {path}"}))


def process_noe_file(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return False
    if not file_path.endswith(".noe"):
        print("Error: Only .noe files are supported", file=sys.stderr)
        return False

    print(f"Processing .noe file: {file_path}", file=sys.stderr)
    processed_path = file_path + ".processed"
    with open(file_path) as f:
        lines = [l for l in f if not l.startswith("#")]
    with open(processed_path, "w") as f:
        f.writelines(lines)
    return True


def parse_request():
    import sys
    request_line = sys.stdin.readline().strip()
    parts = request_line.split(" ")
    if len(parts) < 2:
        send_response("400 Bad Request", '{"error":"Invalid HTTP request"}')
        return

    method, path = parts[0], parts[1]
    headers = {}
    while True:
        line = sys.stdin.readline().strip()
        if not line:
            break
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()

    content_length = int(headers.get("Content-Length", 0))
    body = sys.stdin.read(content_length) if content_length > 0 else ""

    print(f"HTTP Request: {method} {path}", file=sys.stderr)
    handle_request(method, path, body, headers)


if __name__ == "__main__":
    parse_request()
