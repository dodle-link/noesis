from array import array
import base64
import json
import math
import struct

if __package__:
    from .model_config import CONFIG, HEADER_SIZE, MAGIC
else:
    from model_config import CONFIG, HEADER_SIZE, MAGIC


def encode_model_for_storage(buffer):
    return base64.b64encode(buffer).decode("ascii")


def decode_model_from_storage(encoded):
    return base64.b64decode(encoded, validate=True)


def _reject_json_constant(value):
    raise ValueError(f"Invalid JSON constant '{value}'.")


def _validate_json_value(value, path):
    if value is None or isinstance(value, (bool, str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"Model {path} values must be finite JSON values.")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"Model {path} object keys must be strings.")
            _validate_json_value(item, f"{path}.{key}")
        return
    raise ValueError(f"Model {path} contains a non-JSON value.")


def _finite_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_model(model):
    if not isinstance(model, dict):
        raise ValueError("Model must be an object.")
    if model.get("version") != CONFIG["VERSION"]:
        raise ValueError("Unsupported model version.")
    model_id = model.get("id")
    if not isinstance(model_id, (list, tuple, bytes, bytearray)) or len(model_id) != 16:
        raise ValueError("Model id must contain 16 bytes.")
    if any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 255 for value in model_id):
        raise ValueError("Model id must contain 16 bytes.")
    for key in ("createdAt", "updatedAt", "randomSeed"):
        value = model.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"Model {key} must be an integer.")

    for key, limit in (("memory", CONFIG["MEMORY_LIMIT"]), ("rules", CONFIG["RULE_LIMIT"])):
        values = model.get(key)
        if not isinstance(values, list):
            raise ValueError(f"Model {key} must be a list.")
        if len(values) > limit:
            raise ValueError(f"{key.capitalize()} limit exceeded.")
        for index, item in enumerate(values):
            if not isinstance(item, dict):
                raise ValueError(f"Model {key}[{index}] must be an object.")
            _validate_json_value(item, f"{key}[{index}]")

    behavior = model.get("behavior")
    if not isinstance(behavior, list):
        raise ValueError("Model behavior must be a list.")
    if len(behavior) > CONFIG["BEHAVIOR_LIMIT"]:
        raise ValueError("Behavior limit exceeded.")
    _validate_json_value(behavior, "behavior")

    for rule in model["rules"]:
        condition = rule.get("condition")
        action = rule.get("action")
        if (
            not isinstance(rule.get("id"), str)
            or not isinstance(condition, dict)
            or not isinstance(action, dict)
            or not isinstance(action.get("type"), str)
            or not action["type"]
            or not isinstance(rule.get("enabled"), bool)
            or not _finite_number(rule.get("priority"))
            or any(
                not isinstance(rule.get(key), int)
                or isinstance(rule.get(key), bool)
                or rule[key] < 0
                for key in ("success", "failure")
            )
        ):
            raise ValueError("Model rules contain an invalid rule.")
        condition_type = condition.get("type")
        if condition_type not in ("always", "less-than", "greater-than", "equals"):
            raise ValueError("Model rules contain an unsupported condition.")
        if condition_type != "always" and not isinstance(condition.get("variable"), str):
            raise ValueError("Model rule conditions must name a variable.")
        if condition_type in ("less-than", "greater-than") and not _finite_number(
            condition.get("value")
        ):
            raise ValueError("Model rule threshold must be a finite number.")

    behavior_ops = {"READ", "LESS_THAN", "GREATER_THAN", "IF", "ELSE", "ACTION", "END"}
    for instruction in behavior:
        if (
            not isinstance(instruction, list)
            or not instruction
            or not isinstance(instruction[0], str)
            or instruction[0] not in behavior_ops
        ):
            raise ValueError("Model behavior contains an invalid instruction.")
        op = instruction[0]
        if op in ("READ", "ACTION"):
            if len(instruction) != 2 or not isinstance(instruction[1], str):
                raise ValueError(f"Model behavior {op} requires a string operand.")
        elif op in ("LESS_THAN", "GREATER_THAN"):
            if len(instruction) != 2 or not _finite_number(instruction[1]):
                raise ValueError(f"Model behavior {op} requires a numeric operand.")
        elif len(instruction) != 1:
            raise ValueError(f"Model behavior {op} does not accept an operand.")

    goals = model.get("goals")
    if not isinstance(goals, list):
        raise ValueError("Model goals must be a list.")
    _validate_json_value(goals, "goals")
    for goal in goals:
        if (
            not isinstance(goal, dict)
            or not isinstance(goal.get("id"), str)
            or not _finite_number(goal.get("priority"))
            or not isinstance(goal.get("target"), dict)
            or any(not _finite_number(value) for value in goal["target"].values())
        ):
            raise ValueError("Model goals contain an invalid goal.")

    state = model.get("state")
    if not isinstance(state, dict):
        raise ValueError("Model state must be an object.")
    for key in ("energy", "curiosity", "confidence", "stability", "lastReward"):
        if not _finite_number(state.get(key)):
            raise ValueError(f"Model state field '{key}' must be a finite number.")
    if not isinstance(state.get("cycle"), int) or isinstance(state.get("cycle"), bool):
        raise ValueError("Model state cycle must be an integer.")
    if state.get("lastAction") is not None and not isinstance(state.get("lastAction"), str):
        raise ValueError("Model state lastAction must be a string or null.")
    if "bioSignals" in state and not isinstance(state["bioSignals"], dict):
        raise ValueError("Model state bioSignals must be an object.")
    if "selfModel" in state and not isinstance(state["selfModel"], dict):
        raise ValueError("Model state selfModel must be an object.")
    if "workspace" in state and not isinstance(state["workspace"], dict):
        raise ValueError("Model state workspace must be an object.")
    _validate_json_value(state, "state")

    network = model.get("network")
    if not isinstance(network, dict):
        raise ValueError("Model network must be an object.")
    shape = tuple(network.get(key) for key in ("inputSize", "hiddenSize", "outputSize"))
    if any(not isinstance(size, int) or isinstance(size, bool) or size <= 0 for size in shape):
        raise ValueError("Invalid network shape.")
    input_size, hidden_size, output_size = shape
    if "policyTrained" in network and not isinstance(network["policyTrained"], bool):
        raise ValueError("Model network policyTrained must be a boolean.")
    for key in ("trainingMethod", "featureSchema"):
        if key in network and (not isinstance(network[key], str) or not network[key] or len(network[key]) > 128):
            raise ValueError(f"Model network {key} must be a non-empty string of at most 128 characters.")
    expected_lengths = {
        "weights1": input_size * hidden_size,
        "bias1": hidden_size,
        "weights2": hidden_size * output_size,
        "bias2": output_size,
    }
    for key, expected_length in expected_lengths.items():
        values = network.get(key)
        if not isinstance(values, (array, list, tuple)) or len(values) != expected_length:
            raise ValueError(f"Model has invalid {key} array lengths.")
        for value in values:
            if not _finite_number(value):
                raise ValueError(f"Model {key} values must be finite numbers.")
    return True


def _float_array_bytes(values):
    return struct.pack(f"<{len(values)}f", *values)


def serialize_model(model):
    validate_model(model)
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
        "policyTrained": bool(network.get("policyTrained", False)),
        "trainingMethod": network.get("trainingMethod", "unspecified"),
        "featureSchema": network.get("featureSchema", "unspecified"),
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


def _gguf_string(value):
    encoded = value.encode("utf-8")
    return struct.pack("<Q", len(encoded)) + encoded


def serialize_gguf_model(model):
    validate_model(model)
    network = model["network"]
    tensors = (
        ("network.weights1", (network["inputSize"], network["hiddenSize"]), network["weights1"]),
        ("network.bias1", (network["hiddenSize"],), network["bias1"]),
        ("network.weights2", (network["hiddenSize"], network["outputSize"]), network["weights2"]),
        ("network.bias2", (network["outputSize"],), network["bias2"]),
    )
    metadata = (
        ("general.architecture", 8, "noesis"),
        ("general.name", 8, "Noesis Tiny Network"),
        ("general.alignment", 4, 32),
        ("noesis.input_size", 4, network["inputSize"]),
        ("noesis.hidden_size", 4, network["hiddenSize"]),
        ("noesis.output_size", 4, network["outputSize"]),
        ("noesis.workspace_version", 4, 2),
        ("noesis.workspace_format", 8, "cycle_snapshot"),
        ("noesis.policy_trained", 4, int(network.get("policyTrained", False))),
        ("noesis.training_method", 8, network.get("trainingMethod", "unspecified")),
        ("noesis.feature_schema", 8, network.get("featureSchema", "unspecified")),
        ("noesis.tensor_layout", 8, "output-major-f32"),
    )
    metadata_bytes = bytearray()
    for key, value_type, value in metadata:
        metadata_bytes.extend(_gguf_string(key))
        metadata_bytes.extend(struct.pack("<I", value_type))
        metadata_bytes.extend(_gguf_string(value) if value_type == 8 else struct.pack("<I", value))

    tensor_data = bytearray()
    tensor_descriptors = bytearray()
    for name, dimensions, values in tensors:
        tensor_data.extend(b"\0" * ((-len(tensor_data)) % 32))
        offset = len(tensor_data)
        tensor_data.extend(_float_array_bytes(values))
        tensor_descriptors.extend(_gguf_string(name))
        tensor_descriptors.extend(struct.pack("<I", len(dimensions)))
        tensor_descriptors.extend(struct.pack(f"<{len(dimensions)}Q", *dimensions))
        tensor_descriptors.extend(struct.pack("<IQ", 0, offset))

    header = b"GGUF" + struct.pack("<IQQ", 3, len(tensors), len(metadata))
    content = header + metadata_bytes + tensor_descriptors
    content += b"\0" * ((-len(content)) % 32)
    return content + tensor_data


def deserialize_model(buffer):
    buffer = bytes(buffer)
    if len(buffer) < HEADER_SIZE or len(buffer) > CONFIG["MAX_FILE_SIZE"] or buffer[:4] != MAGIC:
        raise ValueError("Invalid DODL model file.")
    version, _, metadata_size, network_size = struct.unpack_from("<HHII", buffer, 4)
    if version != CONFIG["VERSION"]:
        raise ValueError("Unsupported model version.")
    if HEADER_SIZE + metadata_size + network_size != len(buffer):
        raise ValueError("Corrupt model size.")
    metadata_start = HEADER_SIZE
    try:
        metadata = json.loads(
            buffer[metadata_start : metadata_start + metadata_size].decode("utf-8"),
            parse_constant=_reject_json_constant,
        )
        if not isinstance(metadata, dict) or metadata.get("version") != version:
            raise ValueError("Invalid model metadata.")
        shape = metadata["networkShape"]
        input_size = shape["inputSize"]
        hidden_size = shape["hiddenSize"]
        output_size = shape["outputSize"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid DODL model metadata.") from error
    if any(
        not isinstance(size, int) or isinstance(size, bool) or size <= 0
        for size in (input_size, hidden_size, output_size)
    ):
        raise ValueError("Invalid network shape.")
    lengths = (
        input_size * hidden_size,
        hidden_size,
        hidden_size * output_size,
        output_size,
    )
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
            "policyTrained": metadata.get("policyTrained", False),
            "trainingMethod": metadata.get("trainingMethod", "unspecified"),
            "featureSchema": metadata.get("featureSchema", "unspecified"),
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