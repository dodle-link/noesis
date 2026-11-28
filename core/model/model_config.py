CONFIG = {
    "VERSION": 2,
    "MAX_FILE_SIZE": 1024 * 1024,
    "TARGET_FILE_SIZE": 950 * 1024,
    "INPUT_SIZE": 16,
    "HIDDEN_SIZE": 32,
    "OUTPUT_SIZE": 8,
    "MEMORY_LIMIT": 200,
    "RULE_LIMIT": 64,
    "BEHAVIOR_LIMIT": 128,
    "LEARNING_RATE": 0.02,
    "MIN_WEIGHT": -5,
    "MAX_WEIGHT": 5,
    "STATE_MIN": 0,
    "STATE_MAX": 100,
    # Networks with at least this many first-layer weights use NumPy when it is installed.
    "NUMPY_MIN_WEIGHTS": 4096,
}

MAGIC = b"DODL"
HEADER_SIZE = 16