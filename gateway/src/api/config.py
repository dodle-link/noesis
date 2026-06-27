#!/usr/bin/env python3
import os

API_PORT = int(os.environ.get("API_PORT", 3000))
API_HOST = os.environ.get("API_HOST", "localhost")

NOE_CORE_PATH = os.environ.get("NOE_CORE_PATH", os.path.join(os.getcwd(), "..", "noe-core"))

NOE_COMMANDS_STATUS = "status"
NOE_COMMANDS_PROCESS = "process"
NOE_COMMANDS_EXECUTE = "execute"

MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))

ALLOWED_FILE_TYPES = [".noe"]

LOG_LEVEL = os.environ.get("LOG_LEVEL", "info")
LOG_FILE = os.environ.get("LOG_FILE", os.path.join(os.getcwd(), "api.log"))
