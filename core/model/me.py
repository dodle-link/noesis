#!/usr/bin/env python3
# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

from array import array
import argparse
import copy
import json
import math
import os
import secrets
import tempfile
import time

try:
    from .model_config import CONFIG, HEADER_SIZE, MAGIC
    from .model_formats import (
        decode_model_from_storage,
        deserialize_model,
        encode_model_for_storage,
        load_stored_model,
        save_stored_model,
        serialize_gguf_model,
        serialize_model,
        validate_model,
    )
    from .model_memory import MemoryStore, evaluate_memory_retrieval
    from .model_network import TinyNetwork, softmax
    from .model_providers import (
        BiocomputationProvider,
        BiocomputationProviderError,
        LLMProvider,
        LLMProviderError,
        normalize_provider_response,
    )
    from .model_rules import BehaviorEngine, RuleEngine, _js_number
    from .model_utils import Random, clamp, now, random_float, random_int, uuid_bytes
except ImportError:  # run as a script from core/model
    from model_config import CONFIG, HEADER_SIZE, MAGIC
    from model_formats import (
        decode_model_from_storage,
        deserialize_model,
        encode_model_for_storage,
        load_stored_model,
        save_stored_model,
        serialize_gguf_model,
        serialize_model,
        validate_model,
    )
    from model_memory import MemoryStore, evaluate_memory_retrieval
    from model_network import TinyNetwork, softmax
    from model_providers import (
        BiocomputationProvider,
        BiocomputationProviderError,
        LLMProvider,
        LLMProviderError,
        normalize_provider_response,
    )
    from model_rules import BehaviorEngine, RuleEngine, _js_number
    from model_utils import Random, clamp, now, random_float, random_int, uuid_bytes


PIXEL_INPUT_SIZE = 8
PIXEL_OUTPUT_SIZE = 2
ACTION_LABELS = ("rest", "explore", "learn", "observe")

# Input-vector layout for action-state-text-v1 and action-context-v2 networks.
FEATURE_TEXT_LENGTH = 4
FEATURE_IS_USER_INPUT = 5
FEATURE_MEMORY_FILL = 6
FEATURE_TEXT_HASH_START = 7
FEATURE_TEXT_HASH_END_CONTEXTUAL = 9
FEATURE_GOAL_GAP_START = 9
FEATURE_RECALLED_ACTION_START = 12

# Pixel network layout, mirrored by pixel_model.mjs.
PIXEL_FEATURES = (
    "x", "y", "velocityX", "velocityY", "pointerDx", "pointerDy", "hasPointer", "excitement",
)


def create_initial_self_model():
    return {
        "actions": {},
        "predictionCount": 0,
        "meanAbsoluteError": 0.0,
        "lastPrediction": None,
        "lastOutcome": None,
        "lastError": 0.0,
    }


def create_initial_bio_signals():
    return {"novelty": 0.0, "stress": 0.1, "recovery": 0.5, "arousal": 0.05}


def create_initial_workspace():
    return {
        "version": 2,
        "cycle": 0,
        "focus": "idle",
        "externalInput": None,
        "internalState": {},
        "presentSelf": None,
        "providerAnalysis": None,
        "goal": None,
        "intention": None,
        "prediction": None,
        "outcome": None,
        "predictionError": 0.0,
        "memories": [],
        "broadcast": {},
    }


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
        "bioSignals": create_initial_bio_signals(),
        "selfModel": create_initial_self_model(),
        "workspace": create_initial_workspace(),
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
            "safety": True,
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


def _pixel_training_example(random):
    x = random.next()
    y = random.next()
    velocity_x = random.float(-1, 1)
    velocity_y = random.float(-1, 1)
    has_pointer = 1 if random.next() < 0.8 else 0
    if has_pointer:
        pointer_x = random.next()
        pointer_y = random.next()
        pointer_dx = pointer_x - x
        pointer_dy = (pointer_y - y) * 0.7
    else:
        pointer_dx = 0
        pointer_dy = 0
    excitement = random.next()
    inputs = array(
        "f",
        [x, y, velocity_x, velocity_y, pointer_dx, pointer_dy, has_pointer, excitement],
    )

    distance = math.hypot(pointer_dx, pointer_dy)
    steering_x = -velocity_x * 0.04
    steering_y = -velocity_y * 0.04
    if has_pointer and distance < 0.3 and distance > 0:
        strength = (0.3 - distance) / 0.3 * (0.65 + excitement * 0.35)
        steering_x -= pointer_dx / distance * strength
        steering_y -= pointer_dy / distance * strength
    if x < 0.08:
        steering_x += (0.08 - x) / 0.08 * 0.8
    elif x > 0.92:
        steering_x -= (x - 0.92) / 0.08 * 0.8
    if y < 0.08:
        steering_y += (0.08 - y) / 0.08 * 0.8
    elif y > 0.92:
        steering_y -= (y - 0.92) / 0.08 * 0.8
    targets = array("f", [clamp(steering_x, -1, 1), clamp(steering_y, -1, 1)])
    return inputs, targets


def _pixel_validation_metrics(network, examples):
    squared_errors = [0.0] * network.output_size
    absolute_errors = [0.0] * network.output_size
    for inputs, targets in examples:
        outputs = network.forward(inputs)["output"]
        for index in range(network.output_size):
            error = outputs[index] - targets[index]
            squared_errors[index] += error * error
            absolute_errors[index] += abs(error)
    sample_count = len(examples)
    mse = sum(squared_errors) / (sample_count * network.output_size)
    return {
        "mse": mse,
        "mae_x": absolute_errors[0] / sample_count,
        "mae_y": absolute_errors[1] / sample_count,
    }


ACTION_LEARNING_RATE = 0.05
ACTION_LEARNING_RATE_DECAY = 0.1
ACTION_WEIGHT_DECAY = 1e-4
ACTION_GRAD_CLIP = 1.0
PIXEL_LEARNING_RATE = 0.01


def _action_policy_target(energy, curiosity, confidence):
    if energy < 20:
        return "rest"
    if curiosity > 70:
        return "explore"
    if confidence < 40:
        return "learn"
    return "observe"


def _action_policy_example(energy, curiosity, confidence, stability=80):
    inputs = array("f", [0]) * CONFIG["INPUT_SIZE"]
    inputs[0] = energy / 100
    inputs[1] = curiosity / 100
    inputs[2] = confidence / 100
    inputs[3] = stability / 100
    return inputs, _action_policy_target(energy, curiosity, confidence)


def _action_policy_validation_examples():
    return [
        _action_policy_example(energy, curiosity, confidence)
        for energy in (0, 19, 20, 50, 100)
        for curiosity in (0, 70, 71, 100)
        for confidence in (0, 39, 40, 60, 100)
    ]


def _action_policy_held_out_examples():
    return [
        _action_policy_example(energy, curiosity, confidence)
        for energy in (5, 15, 35, 65, 90)
        for curiosity in (10, 65, 75, 90)
        for confidence in (10, 35, 45, 75, 95)
    ]


def _action_policy_metrics(network, examples):
    correct = 0
    rule_baseline_correct = 0
    squared_error = 0.0
    cross_entropy = 0.0
    class_totals = {label: 0 for label in ACTION_LABELS}
    class_correct = {label: 0 for label in ACTION_LABELS}
    for inputs, target in examples:
        target_index = ACTION_LABELS.index(target)
        outputs = network.forward(inputs)["output"]
        prediction = ACTION_LABELS[max(range(len(ACTION_LABELS)), key=lambda index: outputs[index])]
        rule_prediction = _action_policy_target(
            inputs[0] * 100, inputs[1] * 100, inputs[2] * 100
        )
        if prediction == target:
            correct += 1
            class_correct[target] += 1
        if rule_prediction == target:
            rule_baseline_correct += 1
        class_totals[target] += 1
        for index, output in enumerate(outputs[: len(ACTION_LABELS)]):
            expected = 1.0 if index == target_index else 0.0
            squared_error += (output - expected) ** 2
        cross_entropy -= math.log(max(softmax(outputs[: len(ACTION_LABELS)])[target_index], 1e-12))
    sample_count = len(examples)
    return {
        "accuracy": correct / sample_count,
        "baseline_accuracy": max(class_totals.values()) / sample_count,
        "rule_baseline_accuracy": rule_baseline_correct / sample_count,
        "mse": squared_error / (sample_count * len(ACTION_LABELS)),
        "cross_entropy": cross_entropy / sample_count,
        "per_action_accuracy": {
            label: class_correct[label] / class_totals[label]
            if class_totals[label]
            else 0.0
            for label in ACTION_LABELS
        },
        "per_action_support": class_totals,
    }


def _network_from_model(model):
    stored = model["network"]
    network = TinyNetwork(
        Random(1),
        input_size=stored["inputSize"],
        hidden_size=stored["hiddenSize"],
        output_size=stored["outputSize"],
    )
    network.weights1 = stored["weights1"]
    network.bias1 = stored["bias1"]
    network.weights2 = stored["weights2"]
    network.bias2 = stored["bias2"]
    return network


def evaluate_action_model(model):
    """Score a model on validation and separate held-out policy scenarios."""
    if not isinstance(model, dict):
        model = load_model_file(model)
    network = _network_from_model(model)
    if network.output_size < len(ACTION_LABELS):
        raise ValueError("Action models must have at least four output values.")
    metrics = _action_policy_metrics(network, _action_policy_validation_examples())
    metrics["held_out"] = _action_policy_metrics(
        network, _action_policy_held_out_examples()
    )
    metrics["policy_trained"] = bool(model["network"].get("policyTrained", False))
    return metrics


def train_action_model(
    path="noe-action-model.dodl",
    sample_count=1200,
    epochs=20,
    seed=None,
    patience=5,
    metrics_callback=None,
):
    if not isinstance(sample_count, int) or isinstance(sample_count, bool) or sample_count < 1:
        raise ValueError("sample_count must be a positive integer.")
    if not isinstance(epochs, int) or isinstance(epochs, bool) or epochs < 1:
        raise ValueError("epochs must be a positive integer.")
    if not isinstance(patience, int) or isinstance(patience, bool) or patience < 1:
        raise ValueError("patience must be a positive integer.")
    if metrics_callback is not None and not callable(metrics_callback):
        raise ValueError("metrics_callback must be callable.")

    random = Random(seed if seed is not None else random_int(1, 0xFFFFFFFF))
    model = create_model(seed=random.seed)
    network = TinyNetwork(random, output_size=len(ACTION_LABELS))
    for hidden_index in range(network.hidden_size):
        start = hidden_index * network.input_size
        for input_index in range(FEATURE_TEXT_LENGTH, network.input_size):
            network.weights1[start + input_index] = 0

    examples = [
        _action_policy_example(
            random.float(0, 100),
            random.float(0, 100),
            random.float(0, 100),
        )
        for _ in range(sample_count)
    ]
    validation_examples = _action_policy_validation_examples()
    best_score = (-1.0, float("inf"))
    best_weights = None
    stale_epochs = 0
    for epoch in range(1, epochs + 1):
        for index in range(sample_count - 1, 0, -1):
            swap_index = int(random.next() * (index + 1))
            examples[index], examples[swap_index] = examples[swap_index], examples[index]
        learning_rate = ACTION_LEARNING_RATE / (1 + ACTION_LEARNING_RATE_DECAY * (epoch - 1))
        for inputs, label in examples:
            targets = array("f", [0]) * len(ACTION_LABELS)
            targets[ACTION_LABELS.index(label)] = 1
            network.learn(
                inputs, targets, learning_rate,
                loss="cross_entropy", weight_decay=ACTION_WEIGHT_DECAY, grad_clip=ACTION_GRAD_CLIP,
            )
        metrics = _action_policy_metrics(network, validation_examples)
        if metrics_callback is not None:
            metrics_callback(epoch, metrics)
        score = (metrics["accuracy"], -metrics["cross_entropy"])
        if score > best_score:
            best_score = score
            best_weights = {
                key: array("f", getattr(network, key))
                for key in ("weights1", "bias1", "weights2", "bias2")
            }
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break

    for key, values in best_weights.items():
        setattr(network, key, values)

    model["randomSeed"] = random.seed
    model["network"] = {
        "inputSize": network.input_size,
        "hiddenSize": network.hidden_size,
        "outputSize": network.output_size,
        "weights1": network.weights1,
        "bias1": network.bias1,
        "weights2": network.weights2,
        "bias2": network.bias2,
        "policyTrained": True,
        "trainingMethod": "threshold-imitation-v2",
        "featureSchema": "action-state-text-v1",
    }
    model["updatedAt"] = now()
    gguf_path = os.path.splitext(os.fsdecode(path))[0] + ".F32.gguf"
    _write_model_artifacts(
        ((path, serialize_model(model)), (gguf_path, serialize_gguf_model(model)))
    )
    return model


def train_pixel_model(
    path="noe-pixel-model.dodl",
    sample_count=1200,
    epochs=12,
    seed=None,
    patience=4,
    metrics_callback=None,
):
    if not isinstance(sample_count, int) or sample_count < 1:
        raise ValueError("sample_count must be a positive integer.")
    if not isinstance(epochs, int) or epochs < 1:
        raise ValueError("epochs must be a positive integer.")
    if not isinstance(patience, int) or patience < 1:
        raise ValueError("patience must be a positive integer.")
    if metrics_callback is not None and not callable(metrics_callback):
        raise ValueError("metrics_callback must be callable.")

    random = Random(seed if seed is not None else random_int(1, 0xFFFFFFFF))
    model = create_model(seed=random.seed)
    network = TinyNetwork(random, input_size=PIXEL_INPUT_SIZE, output_size=PIXEL_OUTPUT_SIZE)

    validation_count = max(128, min(512, sample_count // 5))
    validation_examples = [_pixel_training_example(random) for _ in range(validation_count)]
    examples = [_pixel_training_example(random) for _ in range(sample_count)]
    best_loss = float("inf")
    best_weights = None
    stale_epochs = 0
    for epoch in range(1, epochs + 1):
        for index in range(sample_count - 1, 0, -1):
            swap_index = int(random.next() * (index + 1))
            examples[index], examples[swap_index] = examples[swap_index], examples[index]
        learning_rate = PIXEL_LEARNING_RATE / (1 + ACTION_LEARNING_RATE_DECAY * (epoch - 1))
        for inputs, targets in examples:
            network.learn(inputs, targets, learning_rate, weight_decay=ACTION_WEIGHT_DECAY)
        metrics = _pixel_validation_metrics(network, validation_examples)
        if metrics_callback is not None:
            metrics_callback(epoch, metrics)
        if metrics["mse"] < best_loss:
            best_loss = metrics["mse"]
            best_weights = {
                key: array("f", getattr(network, key))
                for key in ("weights1", "bias1", "weights2", "bias2")
            }
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break

    for key, values in best_weights.items():
        setattr(network, key, values)

    model["randomSeed"] = random.seed
    model["network"] = {
        "inputSize": network.input_size,
        "hiddenSize": network.hidden_size,
        "outputSize": network.output_size,
        "weights1": network.weights1,
        "bias1": network.bias1,
        "weights2": network.weights2,
        "bias2": network.bias2,
        "trainingMethod": "pixel-steering-v1",
        "featureSchema": "pixel-steering-v1",
    }
    model["updatedAt"] = now()
    gguf_path = os.path.splitext(os.fsdecode(path))[0] + ".F32.gguf"
    _write_model_artifacts(
        ((path, serialize_model(model)), (gguf_path, serialize_gguf_model(model)))
    )
    return model


def train_action_model_from_outcomes(
    model, episodes=None, *, path=None, epochs=3, learning_rate=0.02, seed=1
):
    """Fine-tune a trained policy with reward-weighted policy-gradient steps on recorded outcomes.

    Episodes default to the model's own memory. Actions that earned more than the mean reward
    are reinforced and those that earned less are discouraged; rules still override the policy.
    """
    if not isinstance(model, dict):
        model = load_model_file(model)
    validate_model(model)
    network_info = model["network"]
    if not network_info.get("policyTrained") or network_info["outputSize"] < len(ACTION_LABELS):
        raise ValueError("A trained action policy is required.")
    if not isinstance(epochs, int) or isinstance(epochs, bool) or epochs < 1:
        raise ValueError("epochs must be a positive integer.")
    if isinstance(learning_rate, bool) or not isinstance(learning_rate, (int, float)) or not 0 < learning_rate < math.inf:
        raise ValueError("learning_rate must be a positive finite number.")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer.")

    def finite_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

    metrics = ("energy", "curiosity", "confidence")
    usable = [
        episode for episode in (model["memory"] if episodes is None else episodes)
        if isinstance(episode, dict) and episode.get("action") in ACTION_LABELS
        and finite_number(episode.get("reward")) and isinstance(episode.get("previousState"), dict)
        and all(finite_number(episode["previousState"].get(key)) for key in metrics)
    ]
    if not usable:
        raise ValueError("No usable outcome episodes.")

    result = copy.deepcopy(model)
    # Recall features are built without memory so an episode never retrieves itself.
    feature_model = copy.deepcopy(model)
    feature_model["memory"] = []
    engine = AIEngine(feature_model)
    examples = []
    for episode in usable:
        engine.state.update({key: episode["previousState"][key] for key in metrics})
        examples.append((engine.encode_input(episode.get("input")), episode["action"], episode["reward"]))
    mean_reward = sum(reward for _, _, reward in examples) / len(examples)

    random = Random(seed)
    network = _network_from_model(result)
    for _ in range(epochs):
        for index in range(len(examples) - 1, 0, -1):
            swap_index = int(random.next() * (index + 1))
            examples[index], examples[swap_index] = examples[swap_index], examples[index]
        for inputs, action, reward in examples:
            targets = array("f", [0]) * network.output_size
            targets[ACTION_LABELS.index(action)] = 1
            network.learn(
                inputs, targets, learning_rate * (reward - mean_reward),
                loss="cross_entropy", grad_clip=ACTION_GRAD_CLIP,
            )
    result["network"]["trainingMethod"] = "outcome-policy-gradient-v1"
    result["updatedAt"] = now()
    if path is not None:
        gguf_path = os.path.splitext(os.fsdecode(path))[0] + ".F32.gguf"
        _write_model_artifacts(((path, serialize_model(result)), (gguf_path, serialize_gguf_model(result))))
    return result, {"episodes": len(examples), "mean_reward": mean_reward, "epochs": epochs}


def create_model(seed=None):
    random = Random(seed if seed is not None else random_int(1, 0xFFFFFFFF))
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
            "policyTrained": False,
            "trainingMethod": "untrained",
            "featureSchema": "action-state-text-v1",
        },
        "memory": [],
        "rules": create_initial_rules(),
        "behavior": create_initial_behavior(),
        "state": create_initial_state(),
        "goals": create_initial_goals(),
    }


def load_model_file(path):
    path = os.fspath(path)
    with open(path, "rb") as model_file:
        data = model_file.read()
    if data.startswith(MAGIC):
        return deserialize_model(data)
    if os.path.splitext(path)[1].lower() != ".onnx":
        raise ValueError("Unsupported model file format.")
    try:
        import onnx
    except ImportError as error:
        raise ValueError("Loading ONNX models requires the 'onnx' package.") from error

    onnx_model = onnx.load(path)
    nodes = list(onnx_model.graph.node)
    if len(nodes) != 3 or [node.op_type for node in nodes] != ["Gemm", "Relu", "Gemm"]:
        raise ValueError("ONNX models must contain a Gemm -> Relu -> Gemm network.")
    first_gemm, relu, second_gemm = nodes
    if (
        first_gemm.output[0] != relu.input[0]
        or relu.output[0] != second_gemm.input[0]
        or len(first_gemm.input) < 2
        or len(second_gemm.input) < 2
    ):
        raise ValueError("ONNX model layers are not connected as Gemm -> Relu -> Gemm.")

    initializers = {
        initializer.name: onnx.numpy_helper.to_array(initializer)
        for initializer in onnx_model.graph.initializer
    }

    def get_gemm_parameters(node):
        attributes = {attribute.name: attribute.i for attribute in node.attribute}
        if attributes.get("transA", 0):
            raise ValueError("ONNX Gemm layers with transA are not supported.")
        try:
            weights = initializers[node.input[1]]
            weights = weights.tolist() if hasattr(weights, "tolist") else weights
            if not weights or not isinstance(weights[0], (list, tuple)):
                raise ValueError("ONNX Gemm weights must be two-dimensional.")
            weights = [list(row) for row in weights]
            if not attributes.get("transB", 0):
                weights = [list(row) for row in zip(*weights)]
            bias = initializers[node.input[2]] if len(node.input) > 2 else None
        except KeyError as error:
            raise ValueError("ONNX Gemm weights and biases must be initializers.") from error
        if not weights or not weights[0] or any(len(row) != len(weights[0]) for row in weights):
            raise ValueError("ONNX Gemm weights must be a non-empty rectangular matrix.")
        if bias is None:
            bias = [0.0] * len(weights)
        else:
            bias = bias.tolist() if hasattr(bias, "tolist") else list(bias)
        if len(bias) != len(weights):
            raise ValueError("ONNX Gemm bias dimensions do not match its weights.")
        alpha = next((attribute.f for attribute in node.attribute if attribute.name == "alpha"), 1.0)
        beta = next((attribute.f for attribute in node.attribute if attribute.name == "beta"), 1.0)
        return (
            [[value * alpha for value in row] for row in weights],
            [value * beta for value in bias],
        )

    weights1, bias1 = get_gemm_parameters(first_gemm)
    weights2, bias2 = get_gemm_parameters(second_gemm)
    if len(weights2[0]) != len(weights1):
        raise ValueError("ONNX Gemm layer dimensions do not match.")

    model = create_model()
    model["network"] = {
        "inputSize": len(weights1[0]),
        "hiddenSize": len(weights1),
        "outputSize": len(weights2),
        "weights1": array("f", (value for row in weights1 for value in row)),
        "bias1": array("f", bias1),
        "weights2": array("f", (value for row in weights2 for value in row)),
        "bias2": array("f", bias2),
    }
    return model


def merge_models(model_a, model_b, alpha=0.5):
    if not isinstance(model_a, dict):
        model_a = load_model_file(model_a)
    if not isinstance(model_b, dict):
        model_b = load_model_file(model_b)
    validate_model(model_a)
    validate_model(model_b)
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not math.isfinite(alpha):
        raise ValueError("alpha must be a finite number between 0 and 1.")
    if not 0 <= alpha <= 1:
        raise ValueError("alpha must be between 0 and 1.")
    if model_a["version"] != model_b["version"]:
        raise ValueError("Models must have matching versions.")

    network_a = model_a["network"]
    network_b = model_b["network"]
    if (network_a.get("policyTrained") and network_b.get("policyTrained")
            and network_a.get("featureSchema", "unspecified") != network_b.get("featureSchema", "unspecified")):
        raise ValueError("Trained policies must have matching feature schemas to merge.")
    shape_keys = ("inputSize", "hiddenSize", "outputSize")
    shape_a = tuple(network_a[key] for key in shape_keys)
    shape_b = tuple(network_b[key] for key in shape_keys)

    def expected_lengths(shape):
        input_size, hidden_size, output_size = shape
        if any(not isinstance(size, int) or size <= 0 for size in shape):
            raise ValueError("Models have invalid network shapes.")
        return {
            "weights1": input_size * hidden_size,
            "bias1": hidden_size,
            "weights2": hidden_size * output_size,
            "bias2": output_size,
        }

    lengths_a = expected_lengths(shape_a)
    lengths_b = expected_lengths(shape_b)
    for key in lengths_a:
        if len(network_a[key]) != lengths_a[key] or len(network_b[key]) != lengths_b[key]:
            raise ValueError(f"Models have invalid {key} array lengths.")

    merged = copy.deepcopy(model_a)
    merged["id"] = list(secrets.token_bytes(16))
    merged["createdAt"] = now()
    merged["updatedAt"] = merged["createdAt"]
    for key, size in zip(shape_keys, shape_b):
        merged["network"][key] = size

    input_size, hidden_size, output_size = shape_b
    adapted_a = {}
    for key, rows_a, columns_a, rows_b, columns_b in (
        ("weights1", shape_a[1], shape_a[0], hidden_size, input_size),
        ("weights2", shape_a[2], shape_a[1], output_size, hidden_size),
    ):
        values = list(network_b[key])
        source = network_a[key]
        for row in range(min(rows_a, rows_b)):
            for column in range(min(columns_a, columns_b)):
                values[row * columns_b + column] = source[row * columns_a + column]
        adapted_a[key] = values

    for key, source_size, target_size in (
        ("bias1", shape_a[1], hidden_size),
        ("bias2", shape_a[2], output_size),
    ):
        values = list(network_b[key])
        values[: min(source_size, target_size)] = network_a[key][: min(source_size, target_size)]
        adapted_a[key] = values

    for key, expected_length in lengths_b.items():
        values_a = adapted_a[key]
        values_b = network_b[key]
        merged["network"][key] = array(
            "f",
            ((1 - alpha) * value_a + alpha * value_b for value_a, value_b in zip(values_a, values_b)),
        )
    merged["network"]["policyTrained"] = bool(
        network_a.get("policyTrained", False)
        and network_b.get("policyTrained", False)
    )
    merged["network"]["trainingMethod"] = "weight-merge-v1"
    merged["network"]["featureSchema"] = (
        network_a.get("featureSchema", "unspecified")
        if network_a.get("featureSchema") == network_b.get("featureSchema")
        else "unspecified"
    )

    return merged


def _write_model_artifacts(artifacts):
    staged = []
    try:
        for path, data in artifacts:
            path = os.fsdecode(os.fspath(path))
            directory = os.path.dirname(os.path.abspath(path))
            prefix = f".{os.path.basename(path)}."
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=directory, prefix=prefix, suffix=".tmp", delete=False
            ) as temporary_file:
                staged.append((temporary_file.name, path))
                temporary_file.write(data)
        for temporary_path, path in staged:
            os.replace(temporary_path, path)
    finally:
        for temporary_path, _ in staged:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def create_model_file(path, seed=None):
    model = create_model(seed)
    _write_model_artifacts(((path, serialize_model(model)),))
    return model


def create_gguf_model_file(path, model):
    _write_model_artifacts(((path, serialize_gguf_model(model)),))


class AIEngine:
    def __init__(self, model=None, provider=None, *, event_callback=None):
        if event_callback is not None and not callable(event_callback):
            raise ValueError("event_callback must be callable.")
        self.model = model if model is not None else create_model()
        validate_model(self.model)
        self.provider = provider
        self.event_callback = event_callback
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
        self.policy_trained = bool(stored_network.get("policyTrained", False))
        self.memory = MemoryStore(self.model["memory"])
        self.rules = RuleEngine(self.model["rules"])
        self.behavior = BehaviorEngine(self.model["behavior"])
        self.state = self.model["state"]
        bio_signals = self.state.setdefault("bioSignals", create_initial_bio_signals())
        for key, value in create_initial_bio_signals().items():
            bio_signals.setdefault(key, value)
        self_model = self.state.setdefault("selfModel", create_initial_self_model())
        for key, value in create_initial_self_model().items():
            self_model.setdefault(key, value)
        self.workspace = self.state.setdefault("workspace", create_initial_workspace())
        self.goals = self.model["goals"]

    def _emit_event(self, event):
        if self.event_callback is not None:
            try:
                self.event_callback(event)
            except Exception:
                pass

    def encode_input(self, input_value, workspace=None):
        vector = array("f", [0]) * self.network.input_size
        contextual = self.model["network"].get("featureSchema") == "action-context-v2"
        if contextual and workspace is None:
            workspace = self.open_workspace(self.observe(input_value), persist=False)
        state_features = (
            self.state["energy"] / 100,
            self.state["curiosity"] / 100,
            self.state["confidence"] / 100,
            self.state["stability"] / 100,
        )
        for index, value in enumerate(state_features[: len(vector)]):
            vector[index] = value
        if isinstance(input_value, dict):
            value = input_value.get("value")
            if isinstance(value, str) and len(vector) > FEATURE_TEXT_LENGTH:
                vector[FEATURE_TEXT_LENGTH] = min(len(value) / 100, 1)
                feature_start = FEATURE_TEXT_HASH_START
                feature_end = FEATURE_TEXT_HASH_END_CONTEXTUAL if contextual else len(vector)
                feature_count = feature_end - feature_start
                if feature_count > 0:
                    for token in value.lower().split():
                        token_hash = 2166136261
                        for byte in token.encode("utf-8"):
                            token_hash = ((token_hash ^ byte) * 16777619) & 0xFFFFFFFF
                        bucket = token_hash % feature_count
                        sign = 1 if token_hash & 0x80000000 else -1
                        vector[feature_start + bucket] += sign
                    feature_values = vector[feature_start:feature_end]
                    magnitude = max((abs(value) for value in feature_values), default=0)
                    if magnitude > 1:
                        for index in range(feature_start, feature_end):
                            vector[index] /= magnitude
            if input_value.get("type") == "user_input" and len(vector) > FEATURE_IS_USER_INPUT:
                vector[FEATURE_IS_USER_INPUT] = 1
        if len(vector) > FEATURE_MEMORY_FILL:
            vector[FEATURE_MEMORY_FILL] = min(len(self.memory.items) / CONFIG["MEMORY_LIMIT"], 1)
        if contextual:
            goal = next((goal for goal in self.goals if goal.get("id") == workspace.get("goal")), None)
            if goal:
                for index, key in enumerate(("energy", "curiosity", "confidence"), FEATURE_GOAL_GAP_START):
                    target = goal.get("target", {}).get(key + "Min", goal.get("target", {}).get(key, self.state[key]))
                    vector[index] = clamp((target - self.state[key]) / 100, 0, 1)
            for match in workspace.get("memories", []):
                action = match["episode"].get("action")
                if action in ACTION_LABELS:
                    index = FEATURE_RECALLED_ACTION_START + ACTION_LABELS.index(action)
                    vector[index] = max(vector[index], match["relevance"])
        return vector

    def observe(self, input_value):
        return {"input": copy.deepcopy(input_value), "timestamp": now(), "state": copy.deepcopy(self.state)}

    def interpret(self, perception, input_vector=None):
        if input_vector is None:
            input_vector = self.encode_input(perception["input"])
        return self.network.forward(input_vector)

    def sense_bio_signals(self, input_value):
        signals = self.state["bioSignals"]
        input_type = input_value.get("type") if isinstance(input_value, dict) else None
        signals["novelty"] = clamp(
            signals["novelty"] * 0.8 + (0.3 if input_type == "user_input" else 0.05),
            0,
            1,
        )
        signals["stress"] = clamp(
            signals["stress"] * 0.9 + (0.15 if self.state["energy"] < 20 else 0),
            0,
            1,
        )
        signals["recovery"] = clamp(
            signals["recovery"] * 0.9 + (0.1 if self.state["energy"] >= 50 else 0),
            0,
            1,
        )
        signals["arousal"] = clamp(
            signals["novelty"] * 0.6 + signals["stress"] * 0.4, 0, 1
        )

    def apply_action_to_bio_signals(self, action):
        signals = self.state["bioSignals"]
        if action["type"] == "rest":
            changes = {"stress": -0.15, "recovery": 0.2, "novelty": -0.1}
        elif action["type"] == "explore":
            changes = {"stress": 0.1, "recovery": -0.1, "novelty": 0.15}
        elif action["type"] == "learn":
            changes = {"stress": 0.03, "recovery": -0.05, "novelty": -0.05}
        else:
            changes = {"stress": 0, "recovery": 0, "novelty": -0.02}
        for key, change in changes.items():
            signals[key] = clamp(signals[key] + change, 0, 1)
        signals["arousal"] = clamp(
            signals["novelty"] * 0.6 + signals["stress"] * 0.4, 0, 1
        )

    def open_workspace(self, perception, persist=True):
        input_value = perception["input"]
        focus = input_value.get("type", "input") if isinstance(input_value, dict) else "input"
        salient_goal = None
        highest_score = 0
        for goal in self.goals:
            target = goal.get("target", {})
            deficit = max(
                (
                    value - self.state.get(key[:-3] if key.endswith("Min") else key, value)
                    for key, value in target.items()
                    if isinstance(value, (int, float))
                ),
                default=0,
            )
            score = goal.get("priority", 0) * clamp(deficit / 100, 0, 1)
            if score > highest_score:
                highest_score = score
                salient_goal = goal.get("id")
        workspace = {
            "version": 2,
            "cycle": self.state["cycle"] + 1,
            "focus": focus,
            "externalInput": copy.deepcopy(input_value),
            "internalState": {
                key: self.state[key]
                for key in ("energy", "curiosity", "confidence", "stability")
            },
            "providerAnalysis": None,
            "goal": salient_goal,
            "intention": None,
            "prediction": None,
            "outcome": None,
            "predictionError": 0.0,
            "memories": self.memory.recall(input_value),
            "broadcast": {},
        }
        if persist:
            self.workspace = workspace
            self.state["workspace"] = workspace
        return workspace

    def decide(self, perception, workspace=None):
        def selected(action_type, rule_id, source):
            if workspace is not None:
                workspace["decisionSource"] = source
            return {"type": action_type, "ruleId": rule_id}

        rule = self.rules.select(self.state)
        if rule and rule.get("safety", False):
            return selected(rule["action"]["type"], rule["id"], "safety_rule")
        default_action = rule is None or rule["action"]["type"] == "observe"
        signals = self.state["bioSignals"]
        if workspace and default_action and signals["stress"] < 0.75 and signals["recovery"] > 0.1:
            predicted_action = self.select_predicted_action(workspace)
            if predicted_action is not None:
                return selected(predicted_action, None, "prediction")
            if workspace.get("goal") == "learn":
                return selected("learn", None, "goal")
            if workspace.get("goal") == "explore" and signals["novelty"] >= 0.7:
                return selected("explore", None, "goal")
        if rule and rule["action"]["type"] != "observe":
            return selected(rule["action"]["type"], rule["id"], "rule")
        if self.policy_trained and self.network.output_size >= len(ACTION_LABELS):
            return selected(self._policy_action(perception), None, "policy")
        if rule:
            return selected(rule["action"]["type"], rule["id"], "rule")
        return selected(self.behavior.run(self.state), None, "behavior")

    def select_predicted_action(self, workspace=None):
        best_action = None
        best_score = 0.0
        if workspace is not None:
            workspace["candidates"] = []
        for action_type in ACTION_LABELS:
            action_model = self.state["selfModel"]["actions"].get(action_type, {})
            count = action_model.get("count", 0)
            if count <= 0:
                continue
            prediction = self.predict_action({"type": action_type}, workspace)
            if prediction["energy"] < 20:
                continue
            score = 0.0
            for goal in self.goals:
                for key, target in goal.get("target", {}).items():
                    state_key = key[:-3] if key.endswith("Min") else key
                    if state_key not in prediction:
                        continue
                    before = max(0, target - self.state[state_key])
                    after = max(0, target - prediction[state_key])
                    score += goal.get("priority", 0) * (before - after)
            score *= count / (count + 1)
            if workspace is not None:
                workspace["candidates"].append({
                    "action": action_type, "prediction": prediction,
                    "observations": count, "uncertainty": 1 / (count + 1),
                    "goalScore": score,
                })
            if score > best_score:
                best_action = action_type
                best_score = score
        return best_action

    def _policy_action(self, perception):
        outputs = self.network.forward(self.encode_input(perception["input"], self.workspace))["output"]
        return ACTION_LABELS[max(range(len(ACTION_LABELS)), key=lambda index: outputs[index])]

    def predict_action(self, action, workspace=None):
        action_model = self.state["selfModel"]["actions"].get(action["type"], {})
        mean_delta = action_model.get("meanDelta", {})
        metrics = ("energy", "curiosity", "confidence")
        episodes = []
        for match in (workspace or {}).get("memories", []):
            episode = match["episode"]
            previous = episode.get("previousState")
            outcome = episode.get("outcome")
            if episode.get("action") != action["type"] or not isinstance(previous, dict) or not isinstance(outcome, dict):
                continue
            if all(
                isinstance(values.get(key), (int, float))
                and not isinstance(values[key], bool)
                and math.isfinite(values[key])
                for values in (previous, outcome) for key in metrics
            ):
                episodes.append(episode)
        if episodes:
            mean_delta = {
                key: sum(episode["outcome"][key] - episode["previousState"][key]
                         for episode in episodes) / len(episodes)
                for key in metrics
            }
        return {
            key: clamp(self.state[key] + mean_delta.get(key, 0), 0, 100)
            for key in metrics
        }

    def update_self_model(self, action, previous_state, prediction):
        metrics = ("energy", "curiosity", "confidence")
        observed = {key: self.state[key] for key in metrics}
        error = sum(abs(prediction[key] - observed[key]) for key in metrics) / len(metrics)
        self_model = self.state["selfModel"]
        action_model = self_model["actions"].setdefault(
            action["type"], {"count": 0, "meanDelta": {key: 0.0 for key in metrics}}
        )
        action_model["count"] += 1
        for key in metrics:
            delta = observed[key] - previous_state[key]
            mean_delta = action_model["meanDelta"]
            mean_delta[key] += (delta - mean_delta[key]) / action_model["count"]

        self_model["predictionCount"] += 1
        count = self_model["predictionCount"]
        self_model["meanAbsoluteError"] += (error - self_model["meanAbsoluteError"]) / count
        self_model["lastPrediction"] = {"action": action["type"], "state": prediction}
        self_model["lastOutcome"] = {"action": action["type"], "state": observed}
        self_model["lastError"] = error
        return {"predicted": prediction, "observed": observed, "absoluteError": error}

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

    def learn(self, evaluation, input_vector=None):
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
                "previousState": {
                    key: evaluation["perception"]["state"][key]
                    for key in ("energy", "curiosity", "confidence")
                },
                "prediction": self.workspace["prediction"],
                "outcome": self.workspace["outcome"],
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

    def step(self, input_value, provider_analysis=None, workspace=None):
        perception = self.observe(input_value)
        self.sense_bio_signals(input_value)
        if workspace is None:
            workspace = self.open_workspace(perception)
        else:
            workspace = copy.deepcopy(workspace)
            self.workspace = workspace
            self.state["workspace"] = workspace
        input_vector = self.encode_input(perception["input"], workspace)
        interpretation = self.interpret(perception, input_vector)
        workspace["providerAnalysis"] = copy.deepcopy(provider_analysis)
        workspace["internalState"]["bioSignals"] = copy.deepcopy(self.state["bioSignals"])
        workspace["presentSelf"] = {
            "here": {"input": copy.deepcopy(perception["input"])},
            "now": {"timestamp": perception["timestamp"], "cycle": self.state["cycle"] + 1},
            "self": {
                **{key: perception["state"][key] for key in ("energy", "curiosity", "confidence", "stability", "lastAction")},
                "bioSignals": copy.deepcopy(self.state["bioSignals"]),
            },
        }
        action = self.decide(perception, workspace)
        prediction = self.predict_action(action, workspace)
        workspace["intention"] = action["type"]
        workspace["prediction"] = prediction
        result = self.execute(action)
        self.apply_action_to_bio_signals(action)
        evaluation = self.evaluate(perception, action, result)
        self.update_state(evaluation)
        prediction_result = self.update_self_model(action, perception["state"], prediction)
        workspace["outcome"] = prediction_result["observed"]
        workspace["predictionError"] = prediction_result["absoluteError"]
        workspace["broadcast"] = {
            "externalInput": workspace["externalInput"],
            "internalState": workspace["internalState"],
            "presentSelf": workspace["presentSelf"],
            "providerAnalysis": workspace["providerAnalysis"],
            "goal": workspace["goal"],
            "intention": workspace["intention"],
            "decisionSource": workspace.get("decisionSource"),
            "prediction": workspace["prediction"],
            "outcome": workspace["outcome"],
            "predictionError": workspace["predictionError"],
            "memories": workspace["memories"],
            "candidates": workspace.get("candidates", []),
            "bioSignals": copy.deepcopy(self.state["bioSignals"]),
        }
        self.learn(evaluation, input_vector)
        self.sync_model()
        self._emit_event({
            "event": "decision",
            "source": workspace.get("decisionSource") if workspace.get("decisionSource") in ("safety_rule", "rule", "goal", "prediction", "policy", "behavior") else "unknown",
            "action": action["type"] if action["type"] in ACTION_LABELS else "other",
            "success": bool(result.get("success")),
        })
        return copy.deepcopy({
            "perception": perception,
            "interpretation": interpretation,
            "action": action,
            "prediction": prediction_result,
            "workspace": dict(workspace),
            "result": result,
            "evaluation": evaluation,
            "state": self.state,
        })

    def respond(self, input_value, provider=None, *, context_filter=None):
        """Generate a provider reply, then run one local engine step."""
        active_provider = provider or self.provider or LLMProvider()
        workspace = self.open_workspace(self.observe(input_value), persist=False)
        provider_context = {
            "user_input": copy.deepcopy(input_value),
            "state": {key: self.state[key] for key in ("energy", "curiosity", "confidence", "stability")},
            "memories": [],
        }
        if context_filter is not None:
            full_state = copy.deepcopy(self.state)
            full_state["workspace"] = copy.deepcopy(workspace)
            provider_context = context_filter({
                "user_input": copy.deepcopy(input_value),
                "state": full_state,
                "memories": [copy.deepcopy(match["episode"]) for match in workspace["memories"]],
            })
            if not isinstance(provider_context, dict) or set(provider_context) != {"user_input", "state", "memories"}:
                raise ValueError("context_filter must return user_input, state, and memories.")
        started = time.monotonic()
        try:
            if hasattr(active_provider, "generate_with_analysis"):
                provider_response = active_provider.generate_with_analysis(**provider_context)
            else:
                provider_response = active_provider.generate(**provider_context)
            normalized = normalize_provider_response(provider_response)
        except Exception:
            self._emit_event({"event": "provider", "outcome": "error", "duration_seconds": time.monotonic() - started})
            raise
        self._emit_event({"event": "provider", "outcome": "success", "duration_seconds": time.monotonic() - started})
        result = self.step(input_value, provider_analysis=normalized["analysis"], workspace=workspace)
        result["reply"] = normalized["reply"]
        return result

    def compute_biological(
        self, task, provider=None, *, approval_id, idempotency_key=None
    ):
        """Submit an explicit task to a biological-computation service."""
        if not isinstance(approval_id, str) or not approval_id.strip():
            raise ValueError("A valid human approval ID is required.")
        active_provider = provider or BiocomputationProvider()
        return active_provider.compute(
            task,
            approval_id=approval_id,
            idempotency_key=idempotency_key,
        )

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


def evaluate_task_outcomes(records):
    """Summarize independently measured application outcomes by method and task."""
    if not isinstance(records, list) or not records:
        raise ValueError("records must be a non-empty list.")
    methods = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each outcome must be an object.")
        task_id, method, success = (record.get(key) for key in ("task_id", "method", "success"))
        if not isinstance(task_id, str) or not task_id.strip() or not isinstance(method, str) or not method.strip() or not isinstance(success, bool):
            raise ValueError("Each outcome needs a task_id, method, and boolean success.")
        tasks = methods.setdefault(method, {})
        if task_id in tasks:
            raise ValueError("Each method and task_id pair must be unique.")
        measurements = {}
        for key in ("latency_seconds", "cost_usd"):
            if key in record:
                value = record[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError(f"{key} must be a non-negative finite number.")
                measurements[key] = value
        tasks[task_id] = {"success": success, **measurements}
    summaries = {
        method: {"tasks": len(tasks), "success_rate": sum(task["success"] for task in tasks.values()) / len(tasks)}
        for method, tasks in methods.items()
    }
    for method, tasks in methods.items():
        for key in ("latency_seconds", "cost_usd"):
            values = [task[key] for task in tasks.values() if key in task]
            if values:
                summaries[method][f"mean_{key}"] = sum(values) / len(values)
                summaries[method][f"{key}_count"] = len(values)
    comparisons = {}
    if "rule_baseline" in methods:
        baseline = methods["rule_baseline"]
        for method, tasks in methods.items():
            if method == "rule_baseline":
                continue
            shared = tasks.keys() & baseline.keys()
            comparisons[method] = {
                "paired_tasks": len(shared),
                "success_rate_difference": (sum(int(tasks[task]["success"]) - int(baseline[task]["success"]) for task in shared) / len(shared)) if shared else None,
            }
            for key in ("latency_seconds", "cost_usd"):
                measured = [task for task in shared if key in tasks[task] and key in baseline[task]]
                if measured:
                    comparisons[method][f"paired_{key}_count"] = len(measured)
                    comparisons[method][f"mean_{key}_difference"] = sum(tasks[task][key] - baseline[task][key] for task in measured) / len(measured)
    return {"methods": summaries, "vs_rule_baseline": comparisons}


def evaluate_action_scenarios(model, scenarios):
    """Compare prediction-informed, policy-only, and threshold-baseline behavior."""
    if not isinstance(model, dict):
        model = load_model_file(model)
    validate_model(model)
    if not model["network"].get("policyTrained") or model["network"]["outputSize"] < len(ACTION_LABELS):
        raise ValueError("A trained action policy is required.")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenarios must be a non-empty list.")

    class PolicyEngine(AIEngine):
        def select_predicted_action(self, workspace=None):
            return None

    class BaselineEngine(PolicyEngine):
        def _policy_action(self, perception):
            return _action_policy_target(
                self.state["energy"], self.state["curiosity"], self.state["confidence"]
            )

    state_keys = ("energy", "curiosity", "confidence", "stability")
    runs = {"prediction": [], "policy": [], "rule_baseline": []}
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("Each scenario must be an object.")
        initial = scenario.get("initial_state", {})
        inputs = scenario.get("inputs")
        objectives = scenario.get("objectives")
        trajectory_objectives = scenario.get("trajectory_objectives")
        expected_actions = scenario.get("expected_actions")
        if not isinstance(initial, dict) or any(key not in state_keys for key in initial):
            raise ValueError("initial_state must contain only supported state values.")
        if not isinstance(inputs, list) or not inputs:
            raise ValueError("Each scenario must contain a non-empty inputs list.")
        if expected_actions is not None and (
            not isinstance(expected_actions, list) or len(expected_actions) != len(inputs)
            or any(action is not None and action not in ACTION_LABELS for action in expected_actions)
        ):
            raise ValueError("expected_actions must contain an action or null for each input.")
        if not isinstance(objectives, dict) or not objectives:
            raise ValueError("Each scenario must contain objectives.")
        for key, value in initial.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
                raise ValueError(f"Invalid initial state value for {key}.")
        if trajectory_objectives is not None and (not isinstance(trajectory_objectives, dict) or not trajectory_objectives):
            raise ValueError("trajectory_objectives must be a non-empty object.")
        for objective_set in (objectives, trajectory_objectives or {}):
            for key, bounds in objective_set.items():
                if key not in state_keys or not isinstance(bounds, dict) or not bounds or any(bound not in ("min", "max") for bound in bounds):
                    raise ValueError("Objectives must specify min or max for supported state values.")
                for value in bounds.values():
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
                        raise ValueError("Objective bounds must be finite values between 0 and 100.")
                if "min" in bounds and "max" in bounds and bounds["min"] > bounds["max"]:
                    raise ValueError("Objective min cannot exceed max.")

        def satisfies(state, bounds_by_key):
            return all(
                ("min" not in bounds or state[key] >= bounds["min"])
                and ("max" not in bounds or state[key] <= bounds["max"])
                for key, bounds in bounds_by_key.items()
            )

        scenario_model = copy.deepcopy(model)
        if "goals" in scenario:
            scenario_model["goals"] = copy.deepcopy(scenario["goals"])
            validate_model(scenario_model)
        for label, engine_type in (("prediction", AIEngine), ("policy", PolicyEngine), ("rule_baseline", BaselineEngine)):
            engine = engine_type(copy.deepcopy(scenario_model))
            engine.state.update(initial)
            actions = []
            sources = []
            total_reward = 0.0
            prediction_error = 0.0
            minimum_energy = engine.state["energy"]
            trajectory_success = satisfies(engine.state, trajectory_objectives) if trajectory_objectives is not None else None
            for input_value in inputs:
                result = engine.step(copy.deepcopy(input_value))
                actions.append(result["action"]["type"])
                sources.append(result["workspace"].get("decisionSource", "unknown"))
                total_reward += result["evaluation"]["reward"]
                prediction_error += result["prediction"]["absoluteError"]
                minimum_energy = min(minimum_energy, result["state"]["energy"])
                if trajectory_objectives is not None:
                    trajectory_success = trajectory_success and satisfies(engine.state, trajectory_objectives)
            final_state = {key: engine.state[key] for key in state_keys}
            succeeded = satisfies(final_state, objectives)
            runs[label].append({
                "actions": actions,
                "decision_sources": sources,
                "labeled_actions": sum(action is not None for action in expected_actions) if expected_actions is not None else 0,
                "correct_actions": sum(expected is not None and actual == expected for actual, expected in zip(actions, expected_actions)) if expected_actions is not None else 0,
                "total_reward": total_reward,
                "mean_prediction_error": prediction_error / len(inputs),
                "minimum_energy": minimum_energy,
                "final_state": final_state,
                "success": succeeded,
                "trajectory_success": trajectory_success,
            })
    return {
        label: {
            "success_rate": sum(run["success"] for run in results) / len(results),
            "trajectory_success_rate": (sum(run["trajectory_success"] for run in results if run["trajectory_success"] is not None) / sum(run["trajectory_success"] is not None for run in results)) if any(run["trajectory_success"] is not None for run in results) else None,
            "mean_total_reward": sum(run["total_reward"] for run in results) / len(results),
            "mean_prediction_error": sum(run["mean_prediction_error"] for run in results) / len(results),
            "decision_source_counts": {
                source: sum(run["decision_sources"].count(source) for run in results)
                for source in ("safety_rule", "rule", "goal", "prediction", "policy", "behavior", "unknown")
            },
            "override_rate": sum(source in ("safety_rule", "rule", "goal", "prediction") for run in results for source in run["decision_sources"]) / sum(len(run["decision_sources"]) for run in results),
            "action_accuracy": (sum(run["correct_actions"] for run in results) / sum(run["labeled_actions"] for run in results)) if any(run["labeled_actions"] for run in results) else None,
            "scenarios": results,
        }
        for label, results in runs.items()
    }


def train_action_model_from_episodes(path, training_episodes, validation_episodes, *, test_scenarios=None, epochs=20, seed=1):
    """Train on successful caller-provided demonstrations, validated on separate episodes."""
    if not isinstance(epochs, int) or isinstance(epochs, bool) or epochs < 1:
        raise ValueError("epochs must be a positive integer.")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer.")
    if any(not isinstance(episodes, list) or not episodes for episodes in (training_episodes, validation_episodes)):
        raise ValueError("Training and validation episodes must be non-empty lists.")
    if any(not isinstance(episode, dict) for episode in training_episodes + validation_episodes):
        raise ValueError("Each episode must be an object.")
    if test_scenarios is not None and (not isinstance(test_scenarios, list) or not test_scenarios or any(not isinstance(item, dict) for item in test_scenarios)):
        raise ValueError("test_scenarios must be a non-empty list of objects.")
    splits = [training_episodes, validation_episodes] + ([test_scenarios] if test_scenarios is not None else [])
    if any("group" in episode for split in splits for episode in split):
        if any(not isinstance(episode.get("group"), str) or not episode["group"].strip() for split in splits for episode in split):
            raise ValueError("Every episode and test scenario must have a non-empty group when grouping is used.")
        groups = [set(episode["group"] for episode in split) for split in splits]
        if any(groups[first] & groups[second] for first in range(len(groups)) for second in range(first + 1, len(groups))):
            raise ValueError("Training, validation, and test groups must be distinct.")
    try:
        training_ids = {json.dumps(episode, sort_keys=True, allow_nan=False) for episode in training_episodes}
        validation_ids = {json.dumps(episode, sort_keys=True, allow_nan=False) for episode in validation_episodes}
    except (TypeError, ValueError) as error:
        raise ValueError("Episodes must contain finite JSON values.") from error
    if training_ids & validation_ids:
        raise ValueError("Training and validation episodes must be distinct.")
    def scenario_id(episode):
        return json.dumps(
            {key: episode.get(key, {} if key in ("initial_state", "goals") else None)
             for key in ("initial_state", "inputs", "objectives", "goals")},
            sort_keys=True, allow_nan=False,
        )

    if {scenario_id(episode) for episode in training_episodes} & {scenario_id(episode) for episode in validation_episodes}:
        raise ValueError("Training and validation scenarios must be distinct.")
    if test_scenarios is not None:
        if not isinstance(test_scenarios, list) or not test_scenarios or any(not isinstance(item, dict) for item in test_scenarios):
            raise ValueError("test_scenarios must be a non-empty list of objects.")
        try:
            used = {scenario_id(episode) for episode in training_episodes + validation_episodes}
            if any(scenario_id(scenario) in used for scenario in test_scenarios):
                raise ValueError("Test scenarios must be distinct from training and validation episodes.")
        except (TypeError, AttributeError) as error:
            raise ValueError("Scenarios must contain finite JSON values.") from error

    class DemonstrationEngine(AIEngine):
        def decide(self, perception, workspace=None):
            rule = self.rules.select(self.state)
            if rule and (rule.get("safety", False) or rule["action"]["type"] != "observe"):
                if rule["action"]["type"] != self.demonstrated_action:
                    raise ValueError("A demonstrated action conflicts with a rule override.")
                return {"type": self.demonstrated_action, "ruleId": rule["id"]}
            return {"type": self.demonstrated_action, "ruleId": None}

    template = create_model()
    template["network"]["policyTrained"] = True
    template["network"]["featureSchema"] = "action-context-v2"

    def collect(episodes):
        examples = []
        for episode in episodes:
            if not isinstance(episode, dict):
                raise ValueError("Each episode must be an object.")
            inputs = episode.get("inputs")
            actions = episode.get("actions")
            if not isinstance(inputs, list) or not isinstance(actions, list) or len(inputs) != len(actions) or not inputs:
                raise ValueError("Episode inputs and actions must be non-empty lists of equal length.")
            if any(action not in ACTION_LABELS for action in actions):
                raise ValueError("Episode contains an unsupported action.")
            scenario = {key: episode[key] for key in ("initial_state", "inputs", "objectives", "trajectory_objectives", "goals") if key in episode}
            evaluate_action_scenarios(template, [scenario])
            model = copy.deepcopy(template)
            if "goals" in episode:
                model["goals"] = copy.deepcopy(episode["goals"])
            engine = DemonstrationEngine(model)
            engine.state.update(episode.get("initial_state", {}))
            def validate_trajectory():
                for key, bounds in (episode.get("trajectory_objectives") or {}).items():
                    if ("min" in bounds and engine.state[key] < bounds["min"]) or ("max" in bounds and engine.state[key] > bounds["max"]):
                        raise ValueError("Demonstration does not satisfy its trajectory objectives.")

            validate_trajectory()
            for input_value, action in zip(inputs, actions):
                examples.append((engine.encode_input(input_value), action))
                engine.demonstrated_action = action
                engine.step(copy.deepcopy(input_value))
                validate_trajectory()
            for key, bounds in episode["objectives"].items():
                if ("min" in bounds and engine.state[key] < bounds["min"]) or ("max" in bounds and engine.state[key] > bounds["max"]):
                    raise ValueError("Demonstration does not satisfy its final-state objectives.")
        return examples

    examples = collect(training_episodes)
    validation = collect(validation_episodes)
    random = Random(seed)
    network = TinyNetwork(random)
    best_weights = None
    best_score = (-1.0, float("-inf"))
    for epoch in range(epochs):
        for index in range(len(examples) - 1, 0, -1):
            swap_index = int(random.next() * (index + 1))
            examples[index], examples[swap_index] = examples[swap_index], examples[index]
        learning_rate = ACTION_LEARNING_RATE / (1 + ACTION_LEARNING_RATE_DECAY * epoch)
        for inputs, action in examples:
            targets = array("f", [0]) * network.output_size
            targets[ACTION_LABELS.index(action)] = 1
            network.learn(
                inputs, targets, learning_rate,
                loss="cross_entropy", weight_decay=ACTION_WEIGHT_DECAY, grad_clip=ACTION_GRAD_CLIP,
            )
        metrics = _action_policy_metrics(network, validation)
        score = (metrics["accuracy"], -metrics["cross_entropy"])
        if score > best_score:
            best_score = score
            best_weights = {key: array("f", getattr(network, key)) for key in ("weights1", "bias1", "weights2", "bias2")}
    model = create_model()
    model["randomSeed"] = random.seed
    model["network"].update(best_weights)
    model["network"]["policyTrained"] = True
    model["network"]["trainingMethod"] = "demonstrations-v1"
    model["network"]["featureSchema"] = "action-context-v2"
    gguf_path = os.path.splitext(os.fsdecode(path))[0] + ".F32.gguf"
    report = {"validation": _action_policy_metrics(_network_from_model(model), validation)}
    if test_scenarios is not None:
        report["test_scenarios"] = evaluate_action_scenarios(model, test_scenarios)
        results = report["test_scenarios"]
        report["test_comparison"] = {
            label: {
                "scenarios": len(results[label]["scenarios"]),
                "success_rate_difference": results[label]["success_rate"] - results["rule_baseline"]["success_rate"],
                "override_rate": results[label]["override_rate"],
            }
            for label in ("prediction", "policy")
        }
    _write_model_artifacts(((path, serialize_model(model)), (gguf_path, serialize_gguf_model(model))))
    return model, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or train a Noesis model.")
    training_modes = parser.add_mutually_exclusive_group()
    training_modes.add_argument(
        "--train-pixel",
        action="store_true",
        help="Train a pixel steering model and write noe-pixel-model.dodl.",
    )
    training_modes.add_argument(
        "--train-actions",
        action="store_true",
        help="Train an action-selection model and write noe-action-model.dodl.",
    )
    training_modes.add_argument("--train-demonstrations", metavar="JSON", help="Train from demonstration splits in a JSON file.")
    training_modes.add_argument(
        "--train-outcomes", action="store_true",
        help="Fine-tune the trained policy in --model from its recorded outcomes and write --output.",
    )
    training_modes.add_argument("--evaluate-scenarios", metavar="JSON", help="Evaluate scenario objects from a JSON file.")
    training_modes.add_argument("--evaluate-outcomes", metavar="JSON", help="Evaluate application outcome records from a JSON file.")
    training_modes.add_argument("--evaluate-memory", metavar="JSON", help="Evaluate retrieval queries from a JSON file.")
    parser.add_argument("--samples", type=int, default=1200)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output")
    parser.add_argument("--model", default="noe-model.dodl", help="Model file for scenario or memory evaluation.")
    arguments = parser.parse_args()

    output_path = "noe-model.dodl"
    if arguments.train_demonstrations:
        with open(arguments.train_demonstrations, encoding="utf-8") as source:
            dataset = json.load(source)
        if not isinstance(dataset, dict) or set(dataset) - {"training", "validation", "test_scenarios"} or not {"training", "validation"} <= set(dataset):
            parser.error("demonstrations JSON requires training and validation lists and optional test_scenarios")
        output_path = arguments.output or "noe-demonstration-model.dodl"
        _, report = train_action_model_from_episodes(
            output_path, dataset["training"], dataset["validation"],
            test_scenarios=dataset.get("test_scenarios"), epochs=arguments.epochs,
            seed=arguments.seed if arguments.seed is not None else 1,
        )
        print(json.dumps(report, indent=2, allow_nan=False))
    elif arguments.evaluate_scenarios or arguments.evaluate_outcomes or arguments.evaluate_memory:
        dataset_path = arguments.evaluate_scenarios or arguments.evaluate_outcomes or arguments.evaluate_memory
        with open(dataset_path, encoding="utf-8") as source:
            dataset = json.load(source)
        if arguments.evaluate_scenarios:
            report = evaluate_action_scenarios(arguments.model, dataset)
        elif arguments.evaluate_outcomes:
            report = evaluate_task_outcomes(dataset)
        else:
            report = evaluate_memory_retrieval(MemoryStore(load_model_file(arguments.model)["memory"]), dataset)
        print(json.dumps(report, indent=2, allow_nan=False))
    elif arguments.train_outcomes:
        output_path = arguments.output or "noe-outcome-model.dodl"
        _, report = train_action_model_from_outcomes(
            arguments.model, path=output_path,
            seed=arguments.seed if arguments.seed is not None else 1,
        )
        print(json.dumps(report, indent=2, allow_nan=False))
        print(f"Outcome-tuned model written: {output_path}")
    elif arguments.train_actions:
        output_path = arguments.output or "noe-action-model.dodl"

        def report_action_metrics(epoch, metrics):
            action_accuracy = " ".join(
                f"{label}={accuracy:.3f}"
                for label, accuracy in metrics["per_action_accuracy"].items()
            )
            print(
                f"epoch {epoch}: validation_accuracy={metrics['accuracy']:.3f} "
                f"baseline_accuracy={metrics['baseline_accuracy']:.3f} "
                f"validation_mse={metrics['mse']:.6f} "
                f"per_action_accuracy[{action_accuracy}]"
            )

        model = train_action_model(
            output_path,
            sample_count=arguments.samples,
            epochs=arguments.epochs,
            seed=arguments.seed,
            patience=arguments.patience,
            metrics_callback=report_action_metrics,
        )
        held_out_metrics = evaluate_action_model(model)["held_out"]
        held_out_accuracy = " ".join(
            f"{label}={accuracy:.3f}"
            for label, accuracy in held_out_metrics["per_action_accuracy"].items()
        )
        print(
            f"held_out_accuracy={held_out_metrics['accuracy']:.3f} "
            f"per_action_accuracy[{held_out_accuracy}]"
        )
        print(f"Action model trained: {output_path}")
        gguf_output_path = os.path.splitext(output_path)[0] + ".F32.gguf"
        print(f"GGUF model file created: {gguf_output_path}")
    elif arguments.train_pixel:
        output_path = arguments.output or "noe-pixel-model.dodl"

        def report_metrics(epoch, metrics):
            print(
                f"epoch {epoch}: validation_mse={metrics['mse']:.6f} "
                f"x_mae={metrics['mae_x']:.6f} y_mae={metrics['mae_y']:.6f}"
            )

        train_pixel_model(
            output_path,
            sample_count=arguments.samples,
            epochs=arguments.epochs,
            seed=arguments.seed,
            patience=arguments.patience,
            metrics_callback=report_metrics,
        )
        gguf_output_path = os.path.splitext(output_path)[0] + ".F32.gguf"
        print(f"Pixel control model trained: {output_path}")
        print(f"GGUF model file created: {gguf_output_path}")
    else:
        model = create_model_file(output_path, arguments.seed)
        print(f"Model file created: {output_path}")
        gguf_output_path = "noe-model.F32.gguf"
        create_gguf_model_file(gguf_output_path, model)
        print(f"GGUF model file created: {gguf_output_path}")