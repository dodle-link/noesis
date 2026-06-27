#!/usr/bin/env python3
import os
import sys
import json
import socket
import subprocess
import threading
import time

API_PORT = 3000
UPLOAD_DIR = os.path.join(os.getcwd(), "temp", "uploads")
NOE_CORE_PATH = os.path.join(os.getcwd(), "..", "noe-core")

_api_pid = None
_server_thread = None
_server_running = False


def setup_api():
    print(f"Setting up NOE API server on port {API_PORT}")
    return True


def _handle_connection(conn, addr):
    import importlib.util
    handler_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "request_handler.py")

    try:
        data = conn.recv(4096).decode("utf-8", errors="replace")
        if not data:
            return

        lines = data.split("\r\n")
        if not lines:
            return

        parts = lines[0].split(" ")
        method = parts[0] if parts else "GET"
        path = parts[1] if len(parts) > 1 else "/"

        headers = {}
        body = ""
        i = 1
        while i < len(lines) and lines[i]:
            if ":" in lines[i]:
                k, v = lines[i].split(":", 1)
                headers[k.strip()] = v.strip()
            i += 1

        content_length = int(headers.get("Content-Length", 0))
        if content_length and i + 1 < len(lines):
            body = "\r\n".join(lines[i+1:])[:content_length]

        spec = importlib.util.spec_from_file_location("request_handler", handler_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        import io
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        mod.handle_request(method, path, body, headers)
        sys.stdout = old_stdout
        response = buffer.getvalue()

        conn.sendall(response.encode())
    except Exception as e:
        conn.sendall(f"HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n{{\"error\":\"{e}\"}}".encode())
    finally:
        conn.close()


def _server_loop():
    global _server_running
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", API_PORT))
    srv.listen(5)
    srv.settimeout(1.0)
    print(f"NOE API server listening on port {API_PORT}")

    while _server_running:
        try:
            conn, addr = srv.accept()
            t = threading.Thread(target=_handle_connection, args=(conn, addr), daemon=True)
            t.start()
        except socket.timeout:
            continue
        except Exception:
            break
    srv.close()


def start_api_server():
    global _server_thread, _server_running
    print(f"Starting NOE API server on port {API_PORT}")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    _server_running = True
    _server_thread = threading.Thread(target=_server_loop, daemon=True)
    _server_thread.start()
    print(f"API server started. Ready to receive requests on port {API_PORT}")


def stop_api_server():
    global _server_running, _server_thread
    if _server_running:
        print("Stopping API server")
        _server_running = False
        if _server_thread:
            _server_thread.join(timeout=3)


def process_noe_file(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}")
        return None

    if not file_path.endswith(".noe"):
        print("Error: Only .noe files are supported")
        return None

    print(f"Processing .noe file: {file_path}")

    if os.path.isdir(NOE_CORE_PATH):
        processed_path = file_path + ".processed"
        with open(file_path) as f:
            lines = [l for l in f if not l.startswith("#")]
        with open(processed_path, "w") as f:
            f.writelines(lines)

        result = json.dumps({
            "status": "success",
            "file": file_path,
            "processed_file": processed_path,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }, indent=2)
        print(result)
        return result
    else:
        print(f"Error: noe-core repository not found at {NOE_CORE_PATH}")
        return None


def check_noe_core_status():
    if os.path.isdir(NOE_CORE_PATH):
        result = json.dumps({"status": "connected", "path": NOE_CORE_PATH}, indent=2)
    else:
        result = json.dumps({"status": "disconnected", "message": f"noe-core not found at: {NOE_CORE_PATH}"}, indent=2)
    print(result)
    return result


def execute_noe_command(command):
    print(f"Executing command: {command}")
    if not os.path.isdir(NOE_CORE_PATH):
        result = json.dumps({"status": "error", "message": f"noe-core not found at {NOE_CORE_PATH}"}, indent=2)
        print(result)
        return result

    r = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=NOE_CORE_PATH)
    result = json.dumps({"status": "success", "command": command, "output": r.stdout}, indent=2)
    print(result)
    return result


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "start":
        setup_api()
        start_api_server()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_api_server()
    elif cmd == "stop":
        stop_api_server()
    elif cmd == "status":
        check_noe_core_status()
    elif cmd == "process":
        if len(sys.argv) < 3:
            print("Error: Missing file path\nUsage: noe_api.py process <file_path>")
            sys.exit(1)
        process_noe_file(sys.argv[2])
    elif cmd == "exec":
        if len(sys.argv) < 3:
            print("Error: Missing command\nUsage: noe_api.py exec <command>")
            sys.exit(1)
        execute_noe_command(" ".join(sys.argv[2:]))
    else:
        print("NOE API - Python Implementation")
        print("\nUsage: noe_api.py <command>\n")
        print("Commands:")
        print("  start          Start the API server")
        print("  stop           Stop the API server")
        print("  status         Check noe-core connection status")
        print("  process <file> Process a .noe file")
        print("  exec <cmd>     Execute a command in the noe-core repository")


if __name__ == "__main__":
    main()
