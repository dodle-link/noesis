# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import secrets
import time


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


# secrets-based helpers are not reproducible; use Random(seed) for anything that must be repeatable.
def random_float(minimum, maximum):
    return minimum + secrets.randbelow(1 << 53) / (1 << 53) * (maximum - minimum)


def random_int(minimum, maximum):
    return secrets.randbelow(maximum - minimum + 1) + minimum


def uuid_bytes():
    return secrets.token_bytes(16).hex()


def now():
    return int(time.time() * 1000)


class Random:
    def __init__(self, seed=None):
        if seed is None:
            seed = now()
        self.seed = int(seed) & 0xFFFFFFFF or 1

    def next(self):
        value = self.seed
        value ^= (value << 13) & 0xFFFFFFFF
        value ^= value >> 17
        value ^= (value << 5) & 0xFFFFFFFF
        self.seed = value & 0xFFFFFFFF
        return self.seed / 0x100000000

    def float(self, minimum, maximum):
        return minimum + self.next() * (maximum - minimum)
