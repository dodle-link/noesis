#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import os
import re
import time
import random

TRUE = 1
FALSE = 0


def print_timestamp(message):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {message}")


def is_numeric(val):
    return bool(re.match(r'^[0-9]+(\.[0-9]+)?$', str(val)))


def file_exists(path):
    return os.path.isfile(path)


def dir_exists(path):
    return os.path.isdir(path)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def append_file(path, content):
    with open(path, "a") as f:
        f.write(content + "\n")


def get_timestamp():
    return int(time.time())


def format_number(number, precision=2):
    return f"{number:.{precision}f}"


def generate_id(prefix="noesis", length=8):
    rand_part = random.randint(100000000, 999999999)
    ts = int(time.time())
    return f"{prefix}_{rand_part}_{ts}"
