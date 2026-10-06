#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

from array import array
import base64
import json
import math
import secrets
import struct
import time


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
}

MAGIC = b"DODL"
HEADER_SIZE = 16


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


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


def encode_model_for_storage(buffer):
    return base64.b64encode(buffer).decode("ascii")


def decode_model_from_storage(encoded):
    return base64.b64decode(encoded, validate=True)


def create_initial_state():
    timestamp = now()
    return {
        "energy": 72,
        "curiosity": 50,
        "confidence": 50,
        "stability": 80,
        "cycle": 0,
        "lastAction": None,
        "lastReward": 0,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }


def create_initial_goals():
    return [
        {"id": "survive", "priority": 100, "target": {"energyMin": 20}},
        {"id": "explore", "priority": 50, "target": {"curiosityMin": 60}},
        {"id": "learn", "priority": 40, "target": {"confidenceMin": 50}},
    ]


def create_initial_rules():
    return [
        {
            "id": "rest-low-energy",
            "condition": {"type": "less-than", "variable": "energy", "value": 20},
            "action": {"type": "rest"},
            "priority": 100,
            "enabled": True,
            "success": 0,
            "failure": 0,
        },
        {
            "id": "explore-high-curiosity",
            "condition": {"type": "greater-than", "variable": "curiosity", "value": 70},
            "action": {"type": "explore"},
            "priority": 60,
            "enabled": True,
            "success": 0,
            "failure": 0,
        },
        {
            "id": "observe-default",
            "condition": {"type": "always"},
            "action": {"type": "observe"},
            "priority": 10,
            "enabled": True,
            "success": 0,
            "failure": 0,
        },
    ]


def create_initial_behavior():
    return [
        ["READ", "energy"],
        ["LESS_THAN", 20],
        ["IF"],
        ["ACTION", "rest"],
        ["ELSE"],
        ["READ", "curiosity"],
        ["GREATER_THAN", 70],
        ["IF"],
        ["ACTION", "explore"],
        ["ELSE"],
        ["ACTION", "observe"],
        ["END"],
        ["END"],
    ]


def _float32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


class TinyNetwork:
    def __init__(self, random=None):
        self.input_size = CONFIG["INPUT_SIZE"]
        self.hidden_size = CONFIG["HIDDEN_SIZE"]
        self.output_size = CONFIG["OUTPUT_SIZE"]
        self.weights1 = array("f", [0]) * (self.input_size * self.hidden_size)
        self.bias1 = array("f", [0]) * self.hidden_size
        self.weights2 = array("f", [0]) * (self.hidden_size * self.output_size)
        self.bias2 = array("f", [0]) * self.output_size
        self.initialize(random or Random())

    def initialize(self, random):
        for index in range(len(self.weights1)):
            self.weights1[index] = random.float(-0.1, 0.1)
        for index in range(len(self.weights2)):
            self.weights2[index] = random.float(-0.1, 0.1)
        self.bias1 = array("f", [0]) * self.hidden_size
        self.bias2 = array("f", [0]) * self.output_size

    @staticmethod
    def relu(value):
        return max(0, value)

    def forward(self, input_vector):
        hidden = array("f", [0]) * self.hidden_size
        output = array("f", [0]) * self.output_size
        for hidden_index in range(self.hidden_size):
            total = self.bias1[hidden_index]
            start = hidden_index * self.input_size
            for input_index in range(self.input_size):
                total += input_vector[input_index] * self.weights1[start + input_index]
            hidden[hidden_index] = self.relu(total)
        for output_index in range(self.output_size):
            total = self.bias2[output_index]
            start = output_index * self.hidden_size
            for hidden_index in range(self.hidden_size):
                total += hidden[hidden_index] * self.weights2[start + hidden_index]
            output[output_index] = total
        return {"hidden": hidden, "output": output}

    def learn(self, input_vector, target, learning_rate):
        result = self.forward(input_vector)
        hidden = result["hidden"]
        output = result["output"]
        output_errors = array("f", [0]) * self.output_size
        for output_index in range(self.output_size):
            output_error = target[output_index] - output[output_index]
            output_errors[output_index] = output_error
            start = output_index * self.hidden_size
            for hidden_index in range(self.hidden_size):
                index = start + hidden_index
                self.weights2[index] = clamp(
                    self.weights2[index] + learning_rate * output_error * hidden[hidden_index],
                    CONFIG["MIN_WEIGHT"],
                    CONFIG["MAX_WEIGHT"],
                )
            self.bias2[output_index] += learning_rate * output_error

        for hidden_index in range(self.hidden_size):
            error = 0
            for output_index in range(self.output_size):
                error += output_errors[output_index] * self.weights2[
                    output_index * self.hidden_size + hidden_index
                ]
            if hidden[hidden_index] <= 0:
                error = 0
            start = hidden_index * self.input_size
            for input_index in range(self.input_size):
                index = start + input_index
                self.weights1[index] = clamp(
                    self.weights1[index] + learning_rate * error * input_vector[input_index],
                    CONFIG["MIN_WEIGHT"],
                    CONFIG["MAX_WEIGHT"],
                )
            self.bias1[hidden_index] += learning_rate * error


class MemoryStore:
    def __init__(self, memory=None):
        self.items = memory if memory is not None else []

    def add(self, memory):
        self.items.append(
            {
                "id": uuid_bytes(),
                "timestamp": now(),
                "input": memory.get("input"),
                "action": memory.get("action"),
                "result": memory.get("result"),
                "reward": memory.get("reward"),
                "importance": clamp(memory.get("importance", 50), 0, 100),
            }
        )
        self.limit()

    def limit(self):
        while len(self.items) > CONFIG["MEMORY_LIMIT"]:
            self.items.sort(key=lambda item: item["importance"])
            self.items.pop(0)

    def get_recent(self, count=10):
        return self.items[-count:]

    def clear(self):
        self.items.clear()


def _js_number(value):
    if value is None:
        return 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


class RuleEngine:
    def __init__(self, rules=None):
        self.rules = rules if rules is not None else []

    def evaluate_condition(self, condition, state):
        if not condition:
            return False
        condition_type = condition.get("type")
        variable = condition.get("variable")
        if condition_type == "always":
            return True
        if condition_type == "less-than":
            return _js_number(state.get(variable)) < condition.get("value")
        if condition_type == "greater-than":
            return _js_number(state.get(variable)) > condition.get("value")
        if condition_type == "equals":
            value = state.get(variable)
            expected = condition.get("value")
            return type(value) is type(expected) and value == expected
        return False

    def get_applicable(self, state):
        applicable = [
            rule
            for rule in self.rules
            if rule.get("enabled") and self.evaluate_condition(rule.get("condition"), state)
        ]
        return sorted(applicable, key=lambda rule: rule["priority"], reverse=True)

    def select(self, state):
        applicable = self.get_applicable(state)
        return applicable[0] if applicable else None

    def reward(self, rule_id, reward):
        rule = next((item for item in self.rules if item.get("id") == rule_id), None)
        if rule:
            if reward > 0:
                rule["success"] += 1
                rule["priority"] += 1
            else:
                rule["failure"] += 1
                rule["priority"] -= 1
            rule["priority"] = clamp(rule["priority"], 0, 1000)

    def evolve(self):
        for rule in self.rules:
            total = rule["success"] + rule["failure"]
            if total >= 10 and rule["success"] / total < 0.1:
                rule["enabled"] = False
        if len(self.rules) > CONFIG["RULE_LIMIT"]:
            self.rules = sorted(self.rules, key=lambda rule: rule["priority"], reverse=True)[
                : CONFIG["RULE_LIMIT"]
            ]


class BehaviorEngine:
    def __init__(self, program=None):
        self.program = program if program is not None else []

    def run(self, state):
        action = "observe"
        stack = []
        skip = False
        for index, instruction in enumerate(self.program):
            if index >= CONFIG["BEHAVIOR_LIMIT"]:
                break
            op = instruction[0]
            arg = instruction[1] if len(instruction) > 1 else None
            if op == "READ":
                stack.append(state.get(arg))
            elif op == "LESS_THAN":
                stack.append(_js_number(stack.pop()) < arg)
            elif op == "GREATER_THAN":
                stack.append(_js_number(stack.pop()) > arg)
            elif op == "IF":
                condition = bool(stack.pop())
                stack.append({"type": "if", "condition": condition, "active": condition})
                skip = not condition
            elif op == "ELSE":
                block = stack.pop() if stack else None
                if isinstance(block, dict) and block.get("type") == "if":
                    block["active"] = not block["condition"]
                    stack.append(block)
                    skip = not block["active"]
            elif op == "ACTION" and not skip:
                action = arg
            elif op == "END":
                skip = False
        return action

    def mutate(self, random):
        if len(self.program) >= CONFIG["BEHAVIOR_LIMIT"]:
            return
        actions = ["rest", "explore", "observe", "learn"]
        mutation = random_int(0, 2)
        if mutation == 0:
            self.program.append(["ACTION", actions[random_int(0, len(actions) - 1)]])
        elif mutation == 1:
            if len(self.program) > 3:
                self.program.pop(random_int(0, len(self.program) - 1))
        else:
            instruction = self.program[random_int(0, len(self.program) - 1)]
            if instruction[0] in ("LESS_THAN", "GREATER_THAN"):
                instruction[1] = random_int(5, 95)


def create_model():
    random = Random(random_int(1, 0xFFFFFFFF))
    network = TinyNetwork(random)
    timestamp = now()
    return {
        "version": CONFIG["VERSION"],
        "id": list(secrets.token_bytes(16)),
        "createdAt": timestamp,
        "updatedAt": timestamp,
        "randomSeed": random.seed,
        "network": {
            "inputSize": network.input_size,
            "hiddenSize": network.hidden_size,
            "outputSize": network.output_size,
            "weights1": network.weights1,
            "bias1": network.bias1,
            "weights2": network.weights2,
            "bias2": network.bias2,
        },
        "memory": [],
        "rules": create_initial_rules(),
        "behavior": create_initial_behavior(),
        "state": create_initial_state(),
        "goals": create_initial_goals(),
    }


def validate_model(model):
    if len(model["memory"]) > CONFIG["MEMORY_LIMIT"]:
        raise ValueError("Memory limit exceeded.")
    if len(model["rules"]) > CONFIG["RULE_LIMIT"]:
        raise ValueError("Rule limit exceeded.")
    if len(model["behavior"]) > CONFIG["BEHAVIOR_LIMIT"]:
        raise ValueError("Behavior limit exceeded.")
    return True


def _float_array_bytes(values):
    return struct.pack(f"<{len(values)}f", *values)


def serialize_model(model):
    validate_model(model)
    model["updatedAt"] = now()
    network = model["network"]
    metadata = {
        "version": model["version"],
        "id": list(model["id"]),
        "createdAt": model["createdAt"],
        "updatedAt": model["updatedAt"],
        "randomSeed": model["randomSeed"],
        "memory": model["memory"],
        "rules": model["rules"],
        "behavior": model["behavior"],
        "state": model["state"],
        "goals": model["goals"],
        "networkShape": {
            "inputSize": network["inputSize"],
            "hiddenSize": network["hiddenSize"],
            "outputSize": network["outputSize"],
        },
    }
    metadata_bytes = json.dumps(metadata, separators=(",", ":"), allow_nan=False).encode("utf-8")
    network_bytes = b"".join(
        _float_array_bytes(network[key]) for key in ("weights1", "bias1", "weights2", "bias2")
    )
    total_size = HEADER_SIZE + len(metadata_bytes) + len(network_bytes)
    if total_size > CONFIG["MAX_FILE_SIZE"]:
        raise ValueError(f"Model exceeds 1 MB: {total_size} bytes")
    header = MAGIC + struct.pack("<HHII", CONFIG["VERSION"], 0, len(metadata_bytes), len(network_bytes))
    return header + metadata_bytes + network_bytes


def create_model_file(path):
    model = create_model()
    with open(path, "wb") as model_file:
        model_file.write(serialize_model(model))
    return model


def deserialize_model(buffer):
    buffer = bytes(buffer)
    if len(buffer) < HEADER_SIZE or buffer[:4] != MAGIC:
        raise ValueError("Invalid DODL model file.")
    version, _, metadata_size, network_size = struct.unpack_from("<HHII", buffer, 4)
    if version != CONFIG["VERSION"]:
        raise ValueError("Unsupported model version.")
    if HEADER_SIZE + metadata_size + network_size != len(buffer):
        raise ValueError("Corrupt model size.")
    metadata_start = HEADER_SIZE
    metadata = json.loads(buffer[metadata_start : metadata_start + metadata_size].decode("utf-8"))
    shape = metadata["networkShape"]
    input_size = shape["inputSize"]
    hidden_size = shape["hiddenSize"]
    output_size = shape["outputSize"]
    lengths = (
        input_size * hidden_size,
        hidden_size,
        hidden_size * output_size,
        output_size,
    )
    if any(not isinstance(size, int) or size < 0 for size in (input_size, hidden_size, output_size)):
        raise ValueError("Invalid network shape.")
    if network_size != sum(lengths) * 4:
        raise ValueError("Corrupt model size.")
    offset = metadata_start + metadata_size
    arrays = []
    for length in lengths:
        values = array("f")
        values.frombytes(buffer[offset : offset + length * 4])
        if struct.pack("=I", 1) != struct.pack("<I", 1):
            values.byteswap()
        arrays.append(values)
        offset += length * 4
    model = {
        "version": metadata["version"],
        "id": bytearray(metadata["id"]),
        "createdAt": metadata["createdAt"],
        "updatedAt": metadata["updatedAt"],
        "randomSeed": metadata["randomSeed"],
        "network": {
            "inputSize": input_size,
            "hiddenSize": hidden_size,
            "outputSize": output_size,
            "weights1": arrays[0],
            "bias1": arrays[1],
            "weights2": arrays[2],
            "bias2": arrays[3],
        },
        "memory": metadata["memory"],
        "rules": metadata["rules"],
        "behavior": metadata["behavior"],
        "state": metadata["state"],
        "goals": metadata["goals"],
    }
    validate_model(model)
    return model


def load_stored_model(storage, key):
    stored_model = storage.getItem(key) if hasattr(storage, "getItem") else storage.get(key)
    if not stored_model:
        return None
    return deserialize_model(decode_model_from_storage(stored_model))


def save_stored_model(storage, key, model):
    encoded = encode_model_for_storage(serialize_model(model))
    if hasattr(storage, "setItem"):
        storage.setItem(key, encoded)
    else:
        storage[key] = encoded


class AIEngine:
    def __init__(self, model=None):
        self.model = model if model is not None else create_model()
        self.random = Random(self.model["randomSeed"])
        stored_network = self.model["network"]
        self.network = TinyNetwork(self.random)
        self.network.input_size = stored_network["inputSize"]
        self.network.hidden_size = stored_network["hiddenSize"]
        self.network.output_size = stored_network["outputSize"]
        self.network.weights1 = stored_network["weights1"]
        self.network.bias1 = stored_network["bias1"]
        self.network.weights2 = stored_network["weights2"]
        self.network.bias2 = stored_network["bias2"]
        self.memory = MemoryStore(self.model["memory"])
        self.rules = RuleEngine(self.model["rules"])
        self.behavior = BehaviorEngine(self.model["behavior"])
        self.state = self.model["state"]
        self.goals = self.model["goals"]

    def encode_input(self, input_value):
        vector = array("f", [0]) * CONFIG["INPUT_SIZE"]
        vector[0] = self.state["energy"] / 100
        vector[1] = self.state["curiosity"] / 100
        vector[2] = self.state["confidence"] / 100
        vector[3] = self.state["stability"] / 100
        if isinstance(input_value, dict):
            value = input_value.get("value")
            if isinstance(value, str):
                vector[4] = min(len(value) / 100, 1)
            if input_value.get("type") == "user_input":
                vector[5] = 1
        vector[6] = min(len(self.memory.items) / CONFIG["MEMORY_LIMIT"], 1)
        return vector

    def observe(self, input_value):
        return {"input": input_value, "timestamp": now(), "state": dict(self.state)}

    def interpret(self, perception):
        return self.network.forward(self.encode_input(perception["input"]))

    def decide(self, perception):
        rule = self.rules.select(self.state)
        if rule:
            return {"type": rule["action"]["type"], "ruleId": rule["id"]}
        return {"type": self.behavior.run(self.state), "ruleId": None}

    def execute(self, action):
        action_type = action["type"]
        if action_type == "rest":
            self.state["energy"] = clamp(self.state["energy"] + 10, CONFIG["STATE_MIN"], CONFIG["STATE_MAX"])
            self.state["curiosity"] = clamp(self.state["curiosity"] - 2, 0, 100)
        elif action_type == "explore":
            self.state["energy"] = clamp(self.state["energy"] - 8, CONFIG["STATE_MIN"], CONFIG["STATE_MAX"])
            self.state["curiosity"] = clamp(self.state["curiosity"] - 10, 0, 100)
        elif action_type == "learn":
            self.state["energy"] = clamp(self.state["energy"] - 3, CONFIG["STATE_MIN"], CONFIG["STATE_MAX"])
            self.state["confidence"] = clamp(self.state["confidence"] + 5, 0, 100)
        else:
            self.state["energy"] = clamp(self.state["energy"] - 1, CONFIG["STATE_MIN"], CONFIG["STATE_MAX"])
        self.state["curiosity"] = clamp(self.state["curiosity"], 0, 100)
        return {"action": action_type, "success": True, "timestamp": now()}

    def evaluate(self, perception, action, result):
        reward = 0
        if self.state["energy"] >= 20:
            reward += 1
        if action["type"] == "rest" and self.state["energy"] > 50:
            reward -= 0.2
        if action["type"] == "explore":
            reward += 0.5
        return {"reward": reward, "perception": perception, "action": action, "result": result}

    def learn(self, evaluation):
        input_vector = self.encode_input(evaluation["perception"]["input"])
        target = array("f", [evaluation["reward"]]) * CONFIG["OUTPUT_SIZE"]
        self.network.learn(input_vector, target, CONFIG["LEARNING_RATE"])
        action = evaluation["action"]
        if action["ruleId"]:
            self.rules.reward(action["ruleId"], evaluation["reward"])
        self.memory.add(
            {
                "input": evaluation["perception"]["input"],
                "action": action["type"],
                "result": evaluation["result"],
                "reward": evaluation["reward"],
                "importance": abs(evaluation["reward"]) * 50 + 50,
            }
        )
        if self.random.next() < 0.05:
            self.behavior.mutate(self.random)
        self.rules.evolve()

    def update_state(self, evaluation):
        self.state["lastAction"] = evaluation["action"]["type"]
        self.state["lastReward"] = evaluation["reward"]
        self.state["cycle"] += 1
        self.state["updatedAt"] = now()
        self.state["curiosity"] += 1 if evaluation["reward"] > 0 else -1
        self.state["curiosity"] = clamp(self.state["curiosity"], 0, 100)

    def step(self, input_value):
        perception = self.observe(input_value)
        interpretation = self.interpret(perception)
        action = self.decide(perception)
        result = self.execute(action)
        evaluation = self.evaluate(perception, action, result)
        self.learn(evaluation)
        self.update_state(evaluation)
        self.sync_model()
        return {
            "perception": perception,
            "interpretation": interpretation,
            "action": action,
            "result": result,
            "evaluation": evaluation,
            "state": self.state,
        }

    def sync_model(self):
        self.model["updatedAt"] = now()
        self.model["randomSeed"] = self.random.seed
        network = self.model["network"]
        network["weights1"] = self.network.weights1
        network["bias1"] = self.network.bias1
        network["weights2"] = self.network.weights2
        network["bias2"] = self.network.bias2
        self.model["memory"] = self.memory.items
        self.model["rules"] = self.rules.rules
        self.model["behavior"] = self.behavior.program
        self.model["state"] = self.state

    def export_model(self):
        self.sync_model()
        return serialize_model(self.model)

    @classmethod
    def import_model(cls, buffer):
        return cls(deserialize_model(buffer))

    def get_state(self):
        return self.state

    def get_memory(self):
        return self.memory.items

    def get_rules(self):
        return self.rules.rules

    def get_behavior(self):
        return self.behavior.program


if __name__ == "__main__":
    output_path = "noe-model.dodl"
    create_model_file(output_path)
    print(f"Model file created: {output_path}")