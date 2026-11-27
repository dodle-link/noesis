import importlib.util
import io
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


def _load_model_module():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_directory = os.path.join(base, "model")
    path = os.path.join(model_directory, "me.py")
    if model_directory not in sys.path:
        sys.path.insert(0, model_directory)
    spec = importlib.util.spec_from_file_location("model", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load model module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModelFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_module = _load_model_module()

    def test_storage_helpers_round_trip_and_reject_invalid_base64(self):
        encoded = self.model_module.encode_model_for_storage(b"model data")
        self.assertEqual(self.model_module.decode_model_from_storage(encoded), b"model data")
        with self.assertRaises(ValueError):
            self.model_module.decode_model_from_storage("not base64!")

    def test_memory_recall_normalizes_case_and_punctuation(self):
        memory = self.model_module.MemoryStore()
        memory.add({"input": {"value": "Hello, WORLD!"}, "action": "observe"})
        matches = memory.recall({"value": "hello world"})
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["relevance"], 1.0)

    def test_safety_rules_precede_and_are_not_adapted(self):
        model = self.model_module.create_model()
        safety = model["rules"][0]
        competing = model["rules"][1]
        competing["condition"] = {"type": "always"}
        competing["priority"] = 1000
        engine = self.model_module.AIEngine(model)
        engine.state["energy"] = 10
        self.assertEqual(engine.step(None)["action"]["type"], "rest")
        for _ in range(20):
            engine.rules.reward(safety["id"], -1)
        engine.rules.evolve()
        self.assertEqual((safety["priority"], safety["success"], safety["failure"]), (100, 0, 0))
        self.assertTrue(safety["enabled"])
        safety["enabled"] = False
        with self.assertRaisesRegex(ValueError, "invalid rule"):
            self.model_module.validate_model(model)

    def test_gguf_tensor_layout_reproduces_network_output(self):
        model = self.model_module.create_model()
        data = self.model_module.serialize_gguf_model(model)
        _, tensor_count, metadata_count = struct.unpack_from("<IQQ", data, 4)
        offset = 24
        for _ in range(metadata_count):
            length = struct.unpack_from("<Q", data, offset)[0]
            offset += 8 + length
            value_type = struct.unpack_from("<I", data, offset)[0]
            offset += 4
            if value_type == 8:
                length = struct.unpack_from("<Q", data, offset)[0]
                offset += 8 + length
            else:
                self.assertEqual(value_type, 4)
                offset += 4
        descriptors = {}
        for _ in range(tensor_count):
            length = struct.unpack_from("<Q", data, offset)[0]
            offset += 8
            name = data[offset:offset + length].decode("utf-8")
            offset += length
            rank = struct.unpack_from("<I", data, offset)[0]
            offset += 4
            dimensions = struct.unpack_from(f"<{rank}Q", data, offset)
            offset += rank * 8
            tensor_type, tensor_offset = struct.unpack_from("<IQ", data, offset)
            offset += 12
            self.assertEqual(tensor_type, 0)
            descriptors[name] = (dimensions, tensor_offset)
        data_start = offset + (-offset % 32)
        restored = self.model_module.copy.deepcopy(model)
        for key in ("weights1", "bias1", "weights2", "bias2"):
            dimensions, tensor_offset = descriptors[f"network.{key}"]
            count = math.prod(dimensions)
            values = struct.unpack_from(f"<{count}f", data, data_start + tensor_offset)
            restored["network"][key] = self.model_module.array("f", values)
        inputs = self.model_module.array("f", [0.25] * model["network"]["inputSize"])
        original_output = self.model_module._network_from_model(model).forward(inputs)["output"]
        restored_output = self.model_module._network_from_model(restored).forward(inputs)["output"]
        self.assertEqual(original_output, restored_output)

    def _biocomputation_provider(self, endpoint="https://bio.example.test/compute", **kwargs):
        kwargs.setdefault("operation_schemas", {"example": {"type": "object"}})
        return self.model_module.BiocomputationProvider(endpoint, **kwargs)

    def test_tiny_network_backprop_uses_pre_update_output_weights(self):
        network = self.model_module.TinyNetwork(self.model_module.Random(1))
        network.input_size = 1
        network.hidden_size = 1
        network.output_size = 1
        network.weights1 = self.model_module.array("f", [1])
        network.bias1 = self.model_module.array("f", [0])
        network.weights2 = self.model_module.array("f", [2])
        network.bias2 = self.model_module.array("f", [0])

        network.learn(
            self.model_module.array("f", [1]),
            self.model_module.array("f", [0]),
            0.1,
        )

        self.assertAlmostEqual(network.weights2[0], 1.8)
        self.assertAlmostEqual(network.weights1[0], 0.6)

    def test_ai_engine_does_not_update_untrained_network(self):
        engine = self.model_module.AIEngine()
        input_value = {"type": "user_input", "value": "hello"}
        with patch.object(engine.network, "learn") as learn:
            engine.step(input_value)
        learn.assert_not_called()

    def test_step_returns_independent_pre_and_post_action_snapshots(self):
        engine = self.model_module.AIEngine()
        input_value = {"type": "user_input", "value": "hello"}
        first = engine.step(input_value)
        saved = self.model_module.copy.deepcopy(first)
        input_value["value"] = "changed"
        engine.step({"type": "user_input", "value": "again"})
        self.assertEqual(first, saved)
        self.assertEqual(first["perception"]["state"]["cycle"], 0)
        self.assertEqual(first["state"]["cycle"], 1)
        first["state"]["energy"] = 0
        self.assertNotEqual(engine.state["energy"], 0)

    def test_encode_input_includes_repeatable_text_features(self):
        engine = self.model_module.AIEngine()
        first = {"type": "user_input", "value": "cats are kind"}
        second = {"type": "user_input", "value": "dogs are kind"}

        first_vector = list(engine.encode_input(first))
        second_vector = list(engine.encode_input(second))

        self.assertNotEqual(first_vector, second_vector)
        self.assertEqual(first_vector, list(engine.encode_input(first)))
        self.assertTrue(all(-1 <= value <= 1 for value in first_vector[7:]))

    def test_contextual_features_include_active_goal_and_recalled_actions(self):
        model = self.model_module.create_model()
        model["network"]["featureSchema"] = "action-context-v2"
        engine = self.model_module.AIEngine(model)
        engine.state["confidence"] = 30
        engine.memory.add({"input": {"value": "Study, this!"}, "action": "learn"})
        vector = engine.encode_input({"type": "user_input", "value": "study this"})
        self.assertAlmostEqual(vector[11], 0.2)
        self.assertEqual(vector[14], 1.0)
        self.assertEqual(vector[12], 0.0)

    def test_contextual_step_uses_supplied_workspace_for_interpretation_and_policy(self):
        model = self.model_module.create_model()
        model["network"]["featureSchema"] = "action-context-v2"
        model["network"]["policyTrained"] = True
        engine = self.model_module.AIEngine(model)
        workspace = engine.open_workspace(engine.observe(None), persist=False)
        workspace["memories"] = [{"episode": {"action": "learn"}, "relevance": 1.0}]
        with patch.object(engine.network, "forward", wraps=engine.network.forward) as forward:
            result = engine.step(None, workspace=workspace)
        self.assertEqual(result["workspace"]["decisionSource"], "policy")
        self.assertEqual(forward.call_args_list[0].args[0][14], 1.0)
        self.assertEqual(forward.call_args_list[1].args[0][14], 1.0)

    def test_merge_rejects_different_trained_feature_schemas(self):
        first = self.model_module.create_model()
        second = self.model_module.create_model()
        first["network"]["policyTrained"] = True
        second["network"]["policyTrained"] = True
        second["network"]["featureSchema"] = "action-context-v2"
        with self.assertRaisesRegex(ValueError, "matching feature schemas"):
            self.model_module.merge_models(first, second)

    def test_action_model_training_is_repeatable_and_beats_observe_baseline(self):
        with tempfile.TemporaryDirectory(prefix="action-model-tests-") as directory:
            metrics_a = []
            model_a = self.model_module.train_action_model(
                os.path.join(directory, "first.dodl"),
                sample_count=400,
                epochs=10,
                seed=17,
                patience=5,
                metrics_callback=lambda epoch, result: metrics_a.append(result),
            )
            metrics_b = []
            model_b = self.model_module.train_action_model(
                os.path.join(directory, "second.dodl"),
                sample_count=400,
                epochs=10,
                seed=17,
                patience=5,
                metrics_callback=lambda epoch, result: metrics_b.append(result),
            )

        for key in ("weights1", "bias1", "weights2", "bias2"):
            self.assertEqual(list(model_a["network"][key]), list(model_b["network"][key]))
        for hidden_index in range(model_a["network"]["hiddenSize"]):
            start = hidden_index * model_a["network"]["inputSize"]
            self.assertTrue(
                all(
                    model_a["network"]["weights1"][start + input_index] == 0
                    for input_index in range(4, model_a["network"]["inputSize"])
                )
            )
        self.assertEqual(metrics_a, metrics_b)
        validation = {
            (tuple(inputs), label)
            for inputs, label in self.model_module._action_policy_validation_examples()
        }
        held_out_examples = self.model_module._action_policy_held_out_examples()
        held_out = {(tuple(inputs), label) for inputs, label in held_out_examples}
        self.assertFalse(validation & held_out)
        restored = self.model_module.deserialize_model(
            self.model_module.serialize_model(model_a)
        )
        self.assertTrue(restored["network"]["policyTrained"])
        metrics = self.model_module.evaluate_action_model(restored)
        self.assertTrue(metrics["policy_trained"])
        self.assertGreater(metrics["accuracy"], metrics["baseline_accuracy"])
        self.assertEqual(metrics["rule_baseline_accuracy"], 1.0)
        self.assertEqual(metrics["held_out"]["rule_baseline_accuracy"], 1.0)
        self.assertEqual(metrics["held_out"]["per_action_support"], {
            "rest": 40,
            "explore": 30,
            "learn": 12,
            "observe": 18,
        })
        self.assertEqual(set(metrics["held_out"]["per_action_accuracy"]), set(self.model_module.ACTION_LABELS))

    def test_training_does_not_replace_artifacts_if_serialization_fails(self):
        with tempfile.TemporaryDirectory(prefix="model-atomic-write-tests-") as directory:
            path = os.path.join(directory, "pixel.dodl")
            gguf_path = os.path.join(directory, "pixel.F32.gguf")
            with open(path, "wb") as model_file:
                model_file.write(b"previous dodl")
            with open(gguf_path, "wb") as model_file:
                model_file.write(b"previous gguf")

            with patch.object(
                self.model_module,
                "serialize_gguf_model",
                side_effect=ValueError("invalid gguf model"),
            ):
                with self.assertRaisesRegex(ValueError, "invalid gguf model"):
                    self.model_module.train_pixel_model(
                        path, sample_count=8, epochs=1, seed=123
                    )

            with open(path, "rb") as model_file:
                self.assertEqual(model_file.read(), b"previous dodl")
            with open(gguf_path, "rb") as model_file:
                self.assertEqual(model_file.read(), b"previous gguf")

    def test_demonstration_training_and_held_out_scenarios(self):
        def episode(energy, text):
            return {
                "initial_state": {"energy": energy, "confidence": 50},
                "inputs": [{"type": "user_input", "value": text}, None],
                "actions": ["learn", "learn"],
                "objectives": {"confidence": {"min": 60}, "energy": {"min": 20}},
            }

        training = [episode(80, "training")]
        validation = [episode(75, "validation")]
        test = episode(70, "held out")
        test.pop("actions")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "demonstrations.dodl")
            model, report = self.model_module.train_action_model_from_episodes(
                path, training, validation, test_scenarios=[test], epochs=3, seed=7
            )
            restored = self.model_module.load_model_file(path)
            with open(os.path.join(directory, "demonstrations.F32.gguf"), "rb") as model_file:
                gguf = model_file.read()
            self.assertEqual(restored["network"]["trainingMethod"], "demonstrations-v1")
            self.assertEqual(restored["network"]["featureSchema"], "action-context-v2")
            self.assertIn(b"demonstrations-v1", gguf)
            self.assertIn(b"action-context-v2", gguf)
            self.assertTrue(model["network"]["policyTrained"])
            self.assertEqual(set(report["test_scenarios"]), {"prediction", "policy", "rule_baseline"})
            self.assertIn("mean_prediction_error", report["test_scenarios"]["prediction"])
            with self.assertRaisesRegex(ValueError, "distinct"):
                self.model_module.train_action_model_from_episodes(path, training, training)
            with self.assertRaisesRegex(ValueError, "Test scenarios must be distinct"):
                self.model_module.train_action_model_from_episodes(path, training, validation, test_scenarios=[training[0]])
            invalid = episode(80, "invalid")
            invalid["objectives"]["confidence"]["min"] = 90
            with self.assertRaisesRegex(ValueError, "does not satisfy"):
                self.model_module.train_action_model_from_episodes(path, [invalid], validation)
            invalid = episode(10, "override")
            with self.assertRaisesRegex(ValueError, "conflicts with a rule"):
                self.model_module.train_action_model_from_episodes(path, [invalid], validation)

    def test_trained_policy_selects_action_but_explicit_rules_still_override(self):
        model = self.model_module.create_model()
        network = model["network"]
        network["outputSize"] = 4
        network["weights2"] = self.model_module.array("f", [0]) * (
            network["hiddenSize"] * network["outputSize"]
        )
        network["bias2"] = self.model_module.array("f", [0, 0, 2, 0])
        network["policyTrained"] = True
        engine = self.model_module.AIEngine(model)
        engine.state["energy"] = 80
        engine.state["curiosity"] = 60
        engine.state["confidence"] = 50

        learned = engine.step({"type": "user_input", "value": "choose"})
        engine.state["energy"] = 10
        overridden = engine.step({"type": "user_input", "value": "rest"})

        self.assertEqual(learned["action"]["type"], "learn")
        self.assertEqual(overridden["action"]["type"], "rest")

    def test_scenario_evaluation_compares_multi_step_outcomes_and_overrides(self):
        model = self.model_module.create_model()
        network = model["network"]
        network["outputSize"] = 4
        network["weights2"] = self.model_module.array("f", [0]) * (network["hiddenSize"] * 4)
        network["bias2"] = self.model_module.array("f", [0, 0, 2, 0])
        network["policyTrained"] = True
        original = self.model_module.serialize_model(model)
        scenarios = [
            {
                "initial_state": {"energy": 80, "curiosity": 50, "confidence": 50},
                "inputs": [{"type": "user_input", "value": "first"}, {"type": "user_input", "value": "second"}],
                "objectives": {"confidence": {"min": 60}},
            },
            {
                "initial_state": {"energy": 80, "curiosity": 60, "confidence": 45},
                "inputs": [None, None],
                "objectives": {"confidence": {"min": 50}},
            },
            {
                "initial_state": {"energy": 10, "curiosity": 50, "confidence": 50},
                "inputs": [None, None],
                "objectives": {"energy": {"min": 15}},
            },
        ]

        results = self.model_module.evaluate_action_scenarios(model, scenarios)
        policy = results["policy"]["scenarios"]
        baseline = results["rule_baseline"]["scenarios"]
        self.assertEqual(policy[0]["actions"], ["learn", "learn"])
        self.assertEqual(baseline[0]["actions"], ["observe", "observe"])
        self.assertTrue(policy[0]["success"])
        self.assertFalse(baseline[0]["success"])
        self.assertEqual(policy[1]["actions"][0], "learn")
        self.assertEqual(baseline[1]["actions"][0], "learn")
        self.assertEqual(policy[2]["actions"][0], "rest")
        self.assertEqual(baseline[2]["actions"][0], "rest")
        self.assertEqual(policy[2]["minimum_energy"], 10)
        self.assertEqual(policy[2]["decision_sources"][0], "safety_rule")
        self.assertGreater(results["policy"]["override_rate"], 0)
        self.assertGreater(results["policy"]["decision_source_counts"]["policy"], 0)
        self.assertEqual(self.model_module.serialize_model(model), original)

    def test_scenario_expected_actions_are_scored_independently(self):
        model = self.model_module.create_model()
        model["network"]["policyTrained"] = True
        scenario = {"initial_state": {"energy": 10}, "inputs": [None, None],
                    "objectives": {"energy": {"min": 10}}, "expected_actions": ["rest", None]}
        results = self.model_module.evaluate_action_scenarios(model, [scenario])
        self.assertEqual(results["policy"]["action_accuracy"], 1.0)
        self.assertEqual(results["policy"]["scenarios"][0]["labeled_actions"], 1)
        scenario["expected_actions"] = ["rest"]
        with self.assertRaisesRegex(ValueError, "expected_actions"):
            self.model_module.evaluate_action_scenarios(model, [scenario])

    def test_demonstration_groups_cannot_overlap(self):
        episode = {"group": "source-a", "initial_state": {"energy": 80},
                   "inputs": [None], "actions": ["learn"],
                   "objectives": {"energy": {"min": 20}}}
        validation = self.model_module.copy.deepcopy(episode)
        validation["initial_state"]["energy"] = 75
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "model.dodl")
            with self.assertRaisesRegex(ValueError, "groups must be distinct"):
                self.model_module.train_action_model_from_episodes(path, [episode], [validation])
            validation["group"] = "source-b"
            test = {"group": "source-a", "inputs": [None], "objectives": {"energy": {"min": 0}}}
            with self.assertRaisesRegex(ValueError, "groups must be distinct"):
                self.model_module.train_action_model_from_episodes(path, [episode], [validation], test_scenarios=[test])

    def test_scenario_evaluation_rejects_invalid_scenarios(self):
        model = self.model_module.create_model()
        model["network"]["policyTrained"] = True
        for scenario in (
            {"inputs": [], "objectives": {"energy": {"min": 20}}},
            {"inputs": [None], "objectives": {"energy": {"min": 80, "max": 20}}},
            {"initial_state": {"energy": float("nan")}, "inputs": [None], "objectives": {"energy": {"min": 20}}},
            {"inputs": [None], "objectives": {"unknown": {"min": 20}}},
        ):
            with self.subTest(scenario=scenario), self.assertRaises(ValueError):
                self.model_module.evaluate_action_scenarios(model, [scenario])

    def test_memory_limit_evicts_low_importance_without_reordering_recent_items(self):
        memory = self.model_module.MemoryStore()
        with patch.dict(self.model_module.CONFIG, {"MEMORY_LIMIT": 3}):
            for action, importance in (
                ("old-low", 1),
                ("old-high", 100),
                ("middle", 50),
                ("latest", 10),
            ):
                memory.add({"action": action, "importance": importance})

        self.assertEqual(
            [item["action"] for item in memory.get_recent(10)],
            ["old-high", "middle", "latest"],
        )
        self.assertEqual(
            [item["action"] for item in memory.get_recent(2)], ["middle", "latest"]
        )

    def test_behavior_engine_respects_outer_branch_around_nested_if(self):
        program = [
            ["READ", "energy"],
            ["LESS_THAN", 20],
            ["IF"],
            ["READ", "curiosity"],
            ["GREATER_THAN", 70],
            ["IF"],
            ["ACTION", "explore"],
            ["ELSE"],
            ["ACTION", "rest"],
            ["END"],
            ["ELSE"],
            ["ACTION", "observe"],
            ["END"],
        ]

        action = self.model_module.BehaviorEngine(program).run(
            {"energy": 50, "curiosity": 80}
        )

        self.assertEqual(action, "observe")

    def test_serialize_model_rejects_invalid_network_array_lengths(self):
        model = self.model_module.create_model()
        model["network"]["weights1"].pop()

        with self.assertRaisesRegex(ValueError, "weights1 array length"):
            self.model_module.serialize_model(model)

    def test_validate_model_rejects_malformed_runtime_metadata(self):
        invalid_models = []

        invalid_state = self.model_module.create_model()
        invalid_state["state"]["energy"] = "high"
        invalid_models.append((invalid_state, "state field 'energy'"))

        invalid_rule = self.model_module.create_model()
        invalid_rule["rules"][0]["enabled"] = 1
        invalid_models.append((invalid_rule, "invalid rule"))

        invalid_behavior = self.model_module.create_model()
        invalid_behavior["behavior"][0] = [[]]
        invalid_models.append((invalid_behavior, "invalid instruction"))

        invalid_goal = self.model_module.create_model()
        invalid_goal["goals"][0]["target"]["energyMin"] = float("nan")
        invalid_models.append((invalid_goal, "finite JSON values"))

        for model, message in invalid_models:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                self.model_module.validate_model(model)

    def test_ai_engine_rejects_invalid_model_before_using_it(self):
        model = self.model_module.create_model()
        model["state"].pop("energy")

        with self.assertRaisesRegex(ValueError, "state field 'energy'"):
            self.model_module.AIEngine(model)

    def test_serialize_model_does_not_mutate_model(self):
        model = self.model_module.create_model()
        original_updated_at = model["updatedAt"]

        data = self.model_module.serialize_model(model)

        self.assertEqual(model["updatedAt"], original_updated_at)
        self.assertEqual(
            self.model_module.deserialize_model(data)["updatedAt"], original_updated_at
        )

    def test_deserialize_model_rejects_nonpositive_network_dimensions(self):
        data = self.model_module.serialize_model(self.model_module.create_model())
        version, _, metadata_size, network_size = struct.unpack_from("<HHII", data, 4)
        metadata = json.loads(data[16 : 16 + metadata_size])
        metadata["networkShape"]["inputSize"] = 0
        metadata_bytes = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
        malformed_data = (
            self.model_module.MAGIC
            + struct.pack("<HHII", version, 0, len(metadata_bytes), network_size)
            + metadata_bytes
            + data[16 + metadata_size :]
        )

        with self.assertRaisesRegex(ValueError, "Invalid network shape"):
            self.model_module.deserialize_model(malformed_data)

    def test_deserialize_model_rejects_nonstandard_json_constants(self):
        data = self.model_module.serialize_model(self.model_module.create_model())
        version, _, metadata_size, network_size = struct.unpack_from("<HHII", data, 4)
        metadata = json.loads(data[16 : 16 + metadata_size])
        metadata["state"]["energy"] = float("nan")
        metadata_bytes = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
        malformed_data = (
            self.model_module.MAGIC
            + struct.pack("<HHII", version, 0, len(metadata_bytes), network_size)
            + metadata_bytes
            + data[16 + metadata_size :]
        )

        with self.assertRaisesRegex(ValueError, "Invalid DODL model metadata"):
            self.model_module.deserialize_model(malformed_data)

    def test_create_model_file_writes_deserializable_model(self):
        with tempfile.TemporaryDirectory(prefix="model-tests-") as directory:
            path = os.path.join(directory, "test.dodl")
            model = self.model_module.create_model_file(path)

            with open(path, "rb") as model_file:
                data = model_file.read()

        self.assertEqual(data[:4], self.model_module.MAGIC)
        loaded_model = self.model_module.deserialize_model(data)
        self.assertEqual(loaded_model["version"], model["version"])

    def test_train_pixel_model_writes_browser_compatible_network(self):
        with tempfile.TemporaryDirectory(prefix="pixel-model-tests-") as directory:
            path = os.path.join(directory, "pixel.dodl")
            metrics = []
            self.model_module.train_pixel_model(
                path,
                sample_count=8,
                epochs=1,
                seed=123,
                metrics_callback=lambda epoch, result: metrics.append((epoch, result)),
            )
            with open(path, "rb") as model_file:
                model_data = model_file.read()
            with open(os.path.splitext(path)[0] + ".F32.gguf", "rb") as gguf_file:
                gguf_data = gguf_file.read()

        restored = self.model_module.deserialize_model(model_data)

        network = restored["network"]
        self.assertEqual(
            (network["inputSize"], network["hiddenSize"], network["outputSize"]),
            (8, 32, 2),
        )
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0][0], 1)
        self.assertTrue(all(math.isfinite(value) for value in metrics[0][1].values()))
        self.assertEqual(gguf_data, self.model_module.serialize_gguf_model(restored))

    def test_browser_pixel_inference_matches_python(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is required for browser inference compatibility.")

        with tempfile.TemporaryDirectory(prefix="pixel-inference-tests-") as directory:
            path = os.path.join(directory, "pixel.dodl")
            model = self.model_module.train_pixel_model(
                path, sample_count=8, epochs=1, seed=123
            )
            inputs = self.model_module.array(
                "f", [0.2, 0.7, -0.3, 0.4, 0.1, -0.2, 1, 0.6]
            )
            network = self.model_module._network_from_model(model)
            expected = list(network.forward(inputs)["output"])
            module_path = os.path.join(
                os.path.dirname(self.model_module.__file__), "pixel_model.mjs"
            )
            script = """
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
const [modulePath, modelPath] = process.argv.slice(1);
const { parsePixelModel, runPixelModel } = await import(pathToFileURL(modulePath));
const bytes = await readFile(modelPath);
const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
const model = parsePixelModel(buffer);
const output = runPixelModel(model, [0.2, 0.7, -0.3, 0.4, 0.1, -0.2, 1, 0.6]);
console.log(JSON.stringify(Array.from(output)));
"""
            result = subprocess.run(
                [node, "--input-type=module", "-e", script, module_path, path],
                check=True,
                capture_output=True,
                text=True,
            )

        actual = json.loads(result.stdout)
        for actual_value, expected_value in zip(actual, expected):
            self.assertAlmostEqual(actual_value, expected_value, places=5)

    def test_merge_models_interpolates_weights_without_mutating_inputs(self):
        model_a = self.model_module.create_model()
        model_b = self.model_module.create_model()
        network_keys = ("weights1", "bias1", "weights2", "bias2")
        for key in network_keys:
            model_a["network"][key] = self.model_module.array(
                "f", [2] * len(model_a["network"][key])
            )
            model_b["network"][key] = self.model_module.array(
                "f", [6] * len(model_b["network"][key])
            )

        merged = self.model_module.merge_models(model_a, model_b, alpha=0.25)

        for key in network_keys:
            self.assertEqual(set(merged["network"][key]), {3.0})
            self.assertEqual(set(model_a["network"][key]), {2.0})
            self.assertEqual(set(model_b["network"][key]), {6.0})
        self.assertNotEqual(merged["id"], model_a["id"])
        restored = self.model_module.deserialize_model(
            self.model_module.serialize_model(merged)
        )
        self.assertEqual(set(restored["network"]["weights1"]), {3.0})

    def test_merge_models_rejects_incompatible_shapes_and_alpha(self):
        model_a = self.model_module.create_model()
        model_b = self.model_module.create_model()
        model_b["network"]["hiddenSize"] += 1

        with self.assertRaisesRegex(ValueError, "weights1 array lengths"):
            self.model_module.merge_models(model_a, model_b)
        with self.assertRaisesRegex(ValueError, "alpha"):
            self.model_module.merge_models(model_a, model_a, alpha=1.1)

    def test_merge_models_loads_onnx_and_adopts_its_architecture(self):
        def gemm(inputs, output):
            return SimpleNamespace(
                op_type="Gemm",
                input=inputs,
                output=[output],
                attribute=[SimpleNamespace(name="transB", i=1, f=1.0)],
            )

        nodes = [
            gemm(["input", "weights1", "bias1"], "hidden"),
            SimpleNamespace(op_type="Relu", input=["hidden"], output=["activated"]),
            gemm(["activated", "weights2", "bias2"], "output"),
        ]
        initializers = [
            SimpleNamespace(name="weights1", value=[[1, 2, 3], [4, 5, 6]]),
            SimpleNamespace(name="bias1", value=[7, 8]),
            SimpleNamespace(name="weights2", value=[[9, 10], [11, 12]]),
            SimpleNamespace(name="bias2", value=[13, 14]),
        ]
        onnx_module = SimpleNamespace(
            load=lambda path: SimpleNamespace(
                graph=SimpleNamespace(node=nodes, initializer=initializers)
            ),
            numpy_helper=SimpleNamespace(to_array=lambda initializer: initializer.value),
        )
        model_a = self.model_module.create_model()
        for key in ("weights1", "bias1", "weights2", "bias2"):
            model_a["network"][key] = self.model_module.array(
                "f", [2] * len(model_a["network"][key])
            )

        with tempfile.TemporaryDirectory(prefix="onnx-model-tests-") as directory:
            path = os.path.join(directory, "other-model.onnx")
            with open(path, "wb") as model_file:
                model_file.write(b"onnx")
            with patch.dict(sys.modules, {"onnx": onnx_module}):
                merged = self.model_module.merge_models(model_a, path, alpha=0.5)

        network = merged["network"]
        self.assertEqual(
            (network["inputSize"], network["hiddenSize"], network["outputSize"]),
            (3, 2, 2),
        )
        self.assertEqual(list(network["weights1"]), [1.5, 2, 2.5, 3, 3.5, 4])
        self.assertEqual(list(network["weights2"]), [5.5, 6, 6.5, 7])
        engine = self.model_module.AIEngine(merged)
        self.assertEqual(len(engine.encode_input({"type": "user_input", "value": "test"})), 3)
        engine.step({"type": "user_input", "value": "test"})

    def test_running_script_creates_default_model_file(self):
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "model",
            "me.py",
        )
        with tempfile.TemporaryDirectory(prefix="model-cli-tests-") as directory:
            subprocess.run(
                [sys.executable, script_path],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )
            model_path = os.path.join(directory, "noe-model.dodl")
            with open(model_path, "rb") as model_file:
                loaded_model = self.model_module.deserialize_model(model_file.read())
            gguf_path = os.path.join(directory, "noe-model.F32.gguf")
            with open(gguf_path, "rb") as model_file:
                gguf_data = model_file.read()

        self.assertEqual(loaded_model["version"], self.model_module.CONFIG["VERSION"])
        self.assertEqual(gguf_data[:4], b"GGUF")
        version, tensor_count, metadata_count = struct.unpack_from("<IQQ", gguf_data, 4)
        self.assertEqual(version, 3)
        self.assertEqual(tensor_count, 4)
        self.assertEqual(metadata_count, 12)
        self.assertIn(b"noesis.workspace_version", gguf_data)
        self.assertIn(b"noesis.workspace_format", gguf_data)
        self.assertIn(b"cycle_snapshot", gguf_data)
        self.assertIn(b"noesis.training_method", gguf_data)
        self.assertIn(b"noesis.feature_schema", gguf_data)
        self.assertIn(b"output-major-f32", gguf_data)
        metadata_offset = 24
        first_key_size = struct.unpack_from("<Q", gguf_data, metadata_offset)[0]
        metadata_offset += 8
        first_key = gguf_data[metadata_offset : metadata_offset + first_key_size]
        self.assertEqual(first_key, b"general.architecture")
        descriptor_offset = 24
        for _ in range(metadata_count):
            key_size = struct.unpack_from("<Q", gguf_data, descriptor_offset)[0]
            descriptor_offset += 8 + key_size
            value_type = struct.unpack_from("<I", gguf_data, descriptor_offset)[0]
            descriptor_offset += 4
            if value_type == 8:
                value_size = struct.unpack_from("<Q", gguf_data, descriptor_offset)[0]
                descriptor_offset += 8 + value_size
            else:
                descriptor_offset += 4
        tensor_name_size = struct.unpack_from("<Q", gguf_data, descriptor_offset)[0]
        descriptor_offset += 8
        tensor_name = gguf_data[descriptor_offset : descriptor_offset + tensor_name_size]
        self.assertEqual(tensor_name, b"network.weights1")
        for tensor_name in ("network.weights1", "network.bias1", "network.weights2", "network.bias2"):
            self.assertIn(tensor_name.encode("utf-8"), gguf_data)

    def test_openai_provider_extracts_generated_reply(self):
        response = io.BytesIO(
            json.dumps({"choices": [{"message": {"content": "Hello from GPT"}}]}).encode()
        )
        provider = self.model_module.LLMProvider("openai", api_key="test-key")

        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            reply = provider.generate("hello", {"energy": 72}, [])

        self.assertEqual(reply, "Hello from GPT")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(json.loads(request.data)["messages"][1]["role"], "user")

    def test_provider_limits_context_to_five_recent_memories(self):
        response = io.BytesIO(
            json.dumps({"choices": [{"message": {"content": "Hello"}}]}).encode()
        )
        provider = self.model_module.LLMProvider("openai-compatible")
        memories = [{"index": index} for index in range(8)]

        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            provider.generate("hello", {}, memories)

        request_payload = json.loads(urlopen.call_args.args[0].data)
        context = json.loads(request_payload["messages"][1]["content"])
        self.assertEqual(context["recent_memory"], memories[-5:])

    def test_llm_provider_rejects_invalid_timeouts(self):
        for timeout in (0, -1, float("inf"), float("nan"), True, "30"):
            with self.subTest(timeout=timeout):
                with self.assertRaisesRegex(ValueError, "positive finite"):
                    self.model_module.LLMProvider(
                        "openai-compatible", timeout=timeout
                    )

    def test_llm_provider_bounds_and_validates_http_payloads(self):
        provider = self.model_module.LLMProvider(
            "openai-compatible", base_url="http://localhost:11434/v1"
        )
        provider.MAX_PAYLOAD_SIZE = 1024

        with patch("urllib.request.urlopen") as urlopen:
            with self.assertRaisesRegex(
                self.model_module.LLMProviderError, "request payload exceeds"
            ):
                provider.generate("x" * 2048, {}, [])
            urlopen.assert_not_called()

        oversized_response = io.BytesIO(b"{" + b" " * 1024)
        with patch("urllib.request.urlopen", return_value=oversized_response):
            with self.assertRaisesRegex(
                self.model_module.LLMProviderError, "response exceeds"
            ):
                provider.generate("hello", {}, [])

        invalid_content_type = io.BytesIO(b"{}")
        invalid_content_type.headers = {"Content-Type": "text/plain"}
        with patch("urllib.request.urlopen", return_value=invalid_content_type):
            with self.assertRaisesRegex(
                self.model_module.LLMProviderError, "JSON content type"
            ):
                provider.generate("hello", {}, [])

        with patch("urllib.request.urlopen", return_value=io.BytesIO(b"{")):
            with self.assertRaisesRegex(
                self.model_module.LLMProviderError, "invalid JSON"
            ):
                provider.generate("hello", {}, [])

    def test_biocomputation_provider_posts_versioned_task_and_returns_result(self):
        response_body = {
            "protocol": "noesis-biocompute/v1",
            "result": {"value": 1},
            "provider": "lab-adapter",
            "run_id": "run-123",
        }
        response = io.BytesIO(json.dumps(response_body).encode())
        provider = self._biocomputation_provider(
            "https://bio.example.test/compute", api_key="test-key"
        )

        with patch("urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.return_value = response
            result = provider.compute(
                {"operation": "example", "inputs": {"x": 1}},
                approval_id="approval-123",
            )

        request = build_opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://bio.example.test/compute")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(
            json.loads(request.data),
            {
                "protocol": "noesis-biocompute/v1",
                "task": {"operation": "example", "inputs": {"x": 1}},
                "approval_id": "approval-123",
            },
        )
        self.assertEqual(result, response_body)

    def test_biocomputation_provider_requires_secure_remote_endpoint(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            self.model_module.BiocomputationProvider("http://bio.example.test/compute")
        self.assertEqual(
            self.model_module.BiocomputationProvider(
                "http://localhost:9000/compute"
            ).endpoint,
            "http://localhost:9000/compute",
        )

    def test_biocomputation_provider_rejects_mismatched_response_protocol(self):
        response = io.BytesIO(
            json.dumps({"protocol": "other/v1", "result": True}).encode()
        )
        provider = self._biocomputation_provider(
            "https://bio.example.test/compute"
        )

        with patch("urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.return_value = response
            with self.assertRaisesRegex(
                self.model_module.BiocomputationProviderError, "noesis-biocompute/v1"
            ):
                provider.compute({"operation": "example"}, approval_id="approval-123")

    def test_biocomputation_provider_validates_task_shape(self):
        provider = self._biocomputation_provider(
            "https://bio.example.test/compute"
        )

        for task, message in (
            ({"operation": " "}, "non-empty operation"),
            ({"operation": "example", "inputs": []}, "inputs must be a JSON object"),
        ):
            with self.subTest(task=task), self.assertRaisesRegex(ValueError, message):
                provider.compute(task, approval_id="approval-123")

    def test_biocomputation_provider_validates_response_metadata(self):
        response = io.BytesIO(
            json.dumps(
                {
                    "protocol": "noesis-biocompute/v1",
                    "result": True,
                    "run_id": 123,
                }
            ).encode()
        )
        provider = self._biocomputation_provider(
            "https://bio.example.test/compute"
        )

        with patch("urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.return_value = response
            with self.assertRaisesRegex(
                self.model_module.BiocomputationProviderError,
                "run_id.*must be a string",
            ):
                provider.compute({"operation": "example"}, approval_id="approval-123")

    def test_biocomputation_provider_rejects_malformed_or_credentialed_endpoints(self):
        for endpoint in (
            "https://bio.example.test:invalid/compute",
            "https://user:secret@bio.example.test/compute",
            "https://bio.example.test/compute#fragment",
            "https://bio.example.test/compute#",
            "https://bad host/compute",
            "https://[::1/compute",
        ):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                self.model_module.BiocomputationProvider(endpoint)

    def test_biocomputation_provider_requires_positive_finite_timeout(self):
        for timeout in (0, -1, float("inf"), float("nan"), True, "30", 10**10000):
            with self.subTest(timeout_type=type(timeout).__name__), self.assertRaisesRegex(
                ValueError, "timeout must be a positive finite number"
            ):
                self.model_module.BiocomputationProvider(
                    "https://bio.example.test/compute", timeout=timeout
                )

    def test_biocomputation_provider_follows_only_same_origin_redirects(self):
        provider_module = sys.modules["model_providers"]
        handler = provider_module._SameOriginRedirectHandler(
            "https://bio.example.test/compute"
        )
        request = provider_module.urllib.request.Request(
            "https://bio.example.test/compute"
        )
        redirect_args = (request, io.BytesIO(), 307, "Temporary Redirect", {})

        same_origin = handler.redirect_request(
            *redirect_args, "https://bio.example.test/v2/compute"
        )
        other_host = handler.redirect_request(
            *redirect_args, "https://other.example.test/compute"
        )
        downgrade = handler.redirect_request(
            *redirect_args, "http://bio.example.test/compute"
        )

        self.assertIsNotNone(same_origin)
        self.assertIsNone(other_host)
        self.assertIsNone(downgrade)

    def test_biocomputation_provider_rejects_non_json_content_type(self):
        response = io.BytesIO(
            json.dumps(
                {"protocol": "noesis-biocompute/v1", "result": True}
            ).encode()
        )
        response.headers = {"Content-Type": "text/plain"}
        provider = self._biocomputation_provider(
            "https://bio.example.test/compute"
        )

        with patch("urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.return_value = response
            with self.assertRaisesRegex(
                self.model_module.BiocomputationProviderError, "JSON content type"
            ):
                provider.compute({"operation": "example"}, approval_id="approval-123")

    def test_biocomputation_provider_rejects_nonstandard_json_constants(self):
        response = io.BytesIO(
            b'{"protocol":"noesis-biocompute/v1","result":NaN}'
        )
        provider = self._biocomputation_provider(
            "https://bio.example.test/compute"
        )

        with patch("urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.return_value = response
            with self.assertRaisesRegex(
                self.model_module.BiocomputationProviderError, "invalid JSON"
            ):
                provider.compute({"operation": "example"}, approval_id="approval-123")

    def test_biocomputation_provider_sanitizes_transport_errors_without_retrying(self):
        provider = self._biocomputation_provider(
            "https://bio.example.test/private-path?token=secret"
        )

        with patch("urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.side_effect = OSError(
                "failed for https://bio.example.test/private-path?token=secret"
            )
            with self.assertRaisesRegex(
                self.model_module.BiocomputationProviderError,
                r"request failed \(OSError\)",
            ) as error:
                provider.compute({"operation": "example"}, approval_id="approval-123")

        self.assertNotIn("secret", str(error.exception))
        build_opener.return_value.open.assert_called_once()

    def test_biocomputation_provider_rejects_non_finite_task_values(self):
        provider = self._biocomputation_provider(
            "https://bio.example.test/compute"
        )

        with self.assertRaisesRegex(ValueError, "finite JSON values"):
            provider.compute(
                {"operation": "example", "inputs": {"value": float("nan")}},
                approval_id="approval-123",
            )

    def test_biocomputation_provider_enforces_payload_size_limits(self):
        provider = self._biocomputation_provider(
            "https://bio.example.test/compute"
        )
        oversized_task = {
            "operation": "example",
            "inputs": {"value": "x" * provider.MAX_PAYLOAD_SIZE},
        }

        with self.assertRaisesRegex(ValueError, "1 MiB payload limit"):
            provider.compute(oversized_task, approval_id="approval-123")

        response = io.BytesIO(b"x" * (provider.MAX_PAYLOAD_SIZE + 1))
        with patch("urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.return_value = response
            with self.assertRaisesRegex(
                self.model_module.BiocomputationProviderError,
                "response exceeds the 1 MiB limit",
            ):
                provider.compute({"operation": "example"}, approval_id="approval-123")

    def test_biocomputation_provider_handles_timeouts_without_retrying(self):
        provider = self._biocomputation_provider(
            "https://bio.example.test/compute"
        )

        with patch("urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.side_effect = TimeoutError("timed out")
            with self.assertRaisesRegex(
                self.model_module.BiocomputationProviderError,
                r"request failed \(TimeoutError\)",
            ):
                provider.compute({"operation": "example"}, approval_id="approval-123")

        build_opener.return_value.open.assert_called_once()

    def test_engine_submits_biocomputation_task_without_mutating_model(self):
        class FakeProvider:
            def compute(self, task, *, approval_id, idempotency_key=None):
                self.task = task
                self.approval_id = approval_id
                return {"protocol": "fake", "result": 7}

        provider = FakeProvider()
        engine = self.model_module.AIEngine()
        initial_cycle = engine.get_state()["cycle"]
        task = {"operation": "example", "inputs": {"x": 3}}

        result = engine.compute_biological(
            task, provider, approval_id="approval-123"
        )

        self.assertEqual(provider.task, task)
        self.assertEqual(provider.approval_id, "approval-123")
        self.assertEqual(result["result"], 7)
        self.assertEqual(engine.get_state()["cycle"], initial_cycle)

    def test_biocomputation_provider_enforces_operation_input_schema(self):
        provider = self._biocomputation_provider(
            operation_schemas={
                "example": {
                    "type": "object",
                    "properties": {"count": {"type": "integer", "minimum": 1}},
                    "required": ["count"],
                    "additionalProperties": False,
                }
            }
        )

        for task in (
            {"operation": "unknown", "inputs": {"count": 1}},
            {"operation": "example", "inputs": {}},
            {"operation": "example", "inputs": {"count": True}},
            {"operation": "example", "inputs": {"count": 1, "extra": 2}},
        ):
            with self.subTest(task=task), self.assertRaises(ValueError):
                provider.compute(task, approval_id="approval-123")

    def test_biocomputation_provider_requires_approval_and_async_idempotency(self):
        provider = self._biocomputation_provider(
            jobs_endpoint="https://bio.example.test/jobs"
        )

        with self.assertRaisesRegex(ValueError, "approval ID"):
            provider.compute({"operation": "example"}, approval_id=" ")
        with self.assertRaisesRegex(ValueError, "idempotency key"):
            provider.submit_task(
                {"operation": "example"},
                approval_id="approval-123",
                idempotency_key="",
            )

    def test_biocomputation_provider_submits_reads_and_cancels_async_jobs(self):
        responses = [
            {"job": {"id": "job-123", "status": "queued"}},
            {"job": {"id": "job-123", "status": "running"}},
            {"job": {"id": "job-123", "status": "cancelled"}},
        ]
        response_streams = [
            io.BytesIO(
                json.dumps({"protocol": "noesis-biocompute/v1", **body}).encode()
            )
            for body in responses
        ]
        provider = self._biocomputation_provider(
            jobs_endpoint="https://bio.example.test/jobs"
        )

        with patch("urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.side_effect = response_streams
            submitted = provider.submit_task(
                {"operation": "example"},
                approval_id="approval-123",
                idempotency_key="request-123",
            )
            job = provider.get_job("job/123")
            cancelled = provider.cancel_job(
                "job-123",
                approval_id="approval-123",
                idempotency_key="cancel-123",
            )

        requests = [call.args[0] for call in build_opener.return_value.open.call_args_list]
        self.assertEqual(submitted["job"]["status"], "queued")
        self.assertEqual(job["job"]["status"], "running")
        self.assertEqual(cancelled["job"]["status"], "cancelled")
        self.assertEqual(requests[0].get_header("Idempotency-key"), "request-123")
        self.assertEqual(requests[1].full_url, "https://bio.example.test/jobs/job%2F123")
        self.assertEqual(requests[1].get_method(), "GET")
        self.assertEqual(requests[2].full_url, "https://bio.example.test/jobs/job-123/cancel")
        self.assertEqual(requests[2].get_method(), "POST")
        self.assertEqual(requests[2].get_header("Idempotency-key"), "cancel-123")

    def test_gemini_provider_extracts_generated_reply(self):
        response = io.BytesIO(
            json.dumps(
                {"candidates": [{"content": {"parts": [{"text": "Hello from Gemini"}]}}]}
            ).encode()
        )
        provider = self.model_module.LLMProvider("gemini", api_key="test-key")

        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            reply = provider.generate("hello", {"energy": 72}, [])

        self.assertEqual(reply, "Hello from Gemini")
        request = urlopen.call_args.args[0]
        self.assertIn(":generateContent", request.full_url)
        self.assertEqual(json.loads(request.data)["contents"][0]["role"], "user")

    def test_openai_compatible_provider_supports_local_endpoint_without_key(self):
        response = io.BytesIO(
            json.dumps({"choices": [{"message": {"content": "Hello locally"}}]}).encode()
        )
        provider = self.model_module.LLMProvider(
            "openai-compatible",
            model="qwen2.5",
            base_url="http://localhost:11434/v1/",
        )

        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            reply = provider.generate("hello", {"energy": 72}, [])

        self.assertEqual(reply, "Hello locally")
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "http://localhost:11434/v1/chat/completions",
        )
        self.assertNotIn("Authorization", request.headers)

    def test_provider_can_return_structured_analysis(self):
        generated = {
            "reply": "Hello from a local model",
            "analysis": {
                "observations": ["The user greeted the assistant."],
                "hypothesis": "A greeting is appropriate.",
                "confidence": 0.8,
            },
        }
        response = io.BytesIO(
            json.dumps(
                {"choices": [{"message": {"content": json.dumps(generated)}}]}
            ).encode()
        )
        provider = self.model_module.LLMProvider(
            "openai-compatible", base_url="http://localhost:11434/v1"
        )

        with patch("urllib.request.urlopen", return_value=response):
            result = provider.generate_with_analysis("hello", {}, [])

        self.assertEqual(result, generated)

    def test_engine_respond_generates_reply_and_runs_local_step(self):
        class FakeProvider:
            def generate(self, user_input, state, memories):
                self.context = (user_input, state, memories)
                return "Hello from provider"

        provider = FakeProvider()
        engine = self.model_module.AIEngine(provider=provider)

        result = engine.respond({"type": "user_input", "value": "hello"})

        self.assertEqual(result["reply"], "Hello from provider")
        self.assertEqual(engine.get_state()["cycle"], 1)
        self.assertEqual(provider.context[0]["value"], "hello")

    def test_engine_broadcasts_provider_analysis_without_using_it_as_action(self):
        analysis = {
            "observations": ["The user greeted the assistant."],
            "hypothesis": "A greeting is appropriate.",
            "confidence": 0.8,
        }

        class FakeProvider:
            def generate_with_analysis(self, user_input, state, memories):
                return {"reply": "Hello", "analysis": analysis}

        engine = self.model_module.AIEngine(provider=FakeProvider())
        result = engine.respond({"type": "user_input", "value": "hello"})

        self.assertEqual(result["reply"], "Hello")
        self.assertEqual(result["action"]["type"], "observe")
        self.assertEqual(result["workspace"]["providerAnalysis"], analysis)
        self.assertEqual(result["workspace"]["broadcast"]["providerAnalysis"], analysis)

    def test_engine_learns_and_persists_action_outcome_self_model(self):
        engine = self.model_module.AIEngine()

        first = engine.step({"type": "user_input", "value": "hello"})
        second = engine.step({"type": "user_input", "value": "again"})

        self.assertEqual(first["prediction"]["absoluteError"], 2 / 3)
        self.assertEqual(second["prediction"]["absoluteError"], 0)
        self.assertEqual(engine.get_state()["selfModel"]["predictionCount"], 2)
        self.assertEqual(engine.get_state()["selfModel"]["actions"]["observe"]["count"], 2)
        self.assertEqual(first["workspace"]["outcome"]["curiosity"], first["state"]["curiosity"])

        restored = self.model_module.AIEngine.import_model(engine.export_model())
        self.assertEqual(
            restored.get_state()["selfModel"], engine.get_state()["selfModel"]
        )

    def test_engine_initializes_self_model_for_older_state(self):
        model = self.model_module.create_model()
        del model["state"]["selfModel"]
        del model["state"]["workspace"]

        engine = self.model_module.AIEngine(model)

        self.assertEqual(engine.get_state()["selfModel"]["predictionCount"], 0)
        self.assertEqual(engine.get_state()["selfModel"]["actions"], {})
        self.assertEqual(engine.get_state()["workspace"]["focus"], "idle")
        self.assertEqual(engine.get_state()["bioSignals"]["recovery"], 0.5)

        model["state"]["selfModel"] = {"actions": {}}
        engine = self.model_module.AIEngine(model)
        engine.step(None)
        self.assertEqual(engine.get_state()["selfModel"]["predictionCount"], 1)

    def test_engine_broadcasts_cycle_to_persistent_workspace(self):
        model = self.model_module.create_model()
        model["state"]["energy"] = 10
        engine = self.model_module.AIEngine(model)

        result = engine.step({"type": "user_input", "value": "hello"})

        workspace = result["workspace"]
        self.assertEqual(workspace["cycle"], 1)
        self.assertEqual(workspace["focus"], "user_input")
        self.assertEqual(workspace["goal"], "survive")
        self.assertEqual(workspace["intention"], "rest")
        self.assertEqual(workspace["externalInput"], {"type": "user_input", "value": "hello"})
        self.assertEqual(workspace["internalState"]["energy"], 10)
        self.assertIn("bioSignals", workspace["internalState"])
        self.assertEqual(workspace["outcome"]["energy"], 20)
        self.assertEqual(
            workspace["predictionError"], result["prediction"]["absoluteError"]
        )
        self.assertEqual(workspace["broadcast"]["goal"], "survive")
        self.assertEqual(workspace["broadcast"]["intention"], "rest")
        self.assertEqual(workspace["broadcast"]["bioSignals"], engine.get_state()["bioSignals"])

        restored = self.model_module.AIEngine.import_model(engine.export_model())
        self.assertEqual(restored.get_state()["workspace"], workspace)

    def test_workspace_goal_guides_learning_when_rules_only_observe(self):
        model = self.model_module.create_model()
        model["state"]["confidence"] = 20
        model["goals"] = [
            {"id": "learn", "priority": 40, "target": {"confidenceMin": 50}}
        ]
        engine = self.model_module.AIEngine(model)

        result = engine.step({"type": "user_input", "value": "learn"})

        self.assertEqual(result["workspace"]["goal"], "learn")
        self.assertEqual(result["action"]["type"], "learn")
        self.assertEqual(result["workspace"]["broadcast"]["outcome"]["confidence"], 25)

    def test_goal_selection_uses_learned_action_outcomes(self):
        model = self.model_module.create_model()
        model["state"]["confidence"] = 20
        model["goals"] = [{"id": "learn", "priority": 40, "target": {"confidenceMin": 50}}]
        model["state"]["selfModel"]["actions"] = {
            "observe": {"count": 4, "meanDelta": {"energy": -1, "curiosity": 0, "confidence": 8}},
            "learn": {"count": 4, "meanDelta": {"energy": -3, "curiosity": 0, "confidence": 0}},
        }
        engine = self.model_module.AIEngine(model)

        result = engine.step({"type": "user_input", "value": "learn"})

        self.assertEqual(result["action"]["type"], "observe")
        self.assertEqual(result["workspace"]["prediction"]["confidence"], 28)
        self.assertEqual(result["workspace"]["candidates"][0]["action"], "learn")
        self.assertEqual(result["workspace"]["broadcast"]["candidates"], result["workspace"]["candidates"])

    def test_workspace_retrieves_episodes_for_predictions_and_provider(self):
        class FakeProvider:
            def generate(self, user_input, state, memories):
                self.state = state
                self.memories = memories
                return "ok"

        provider = FakeProvider()
        engine = self.model_module.AIEngine(provider=provider)
        engine.step({"type": "user_input", "value": "shared topic"})
        result = engine.respond({"type": "user_input", "value": "shared topic"})

        matches = result["workspace"]["memories"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["relevance"], 1)
        self.assertEqual(matches[0]["uncertainty"], 0)
        self.assertEqual(provider.memories[0], matches[0]["episode"])
        self.assertEqual(provider.state["workspace"]["memories"], matches)
        self.assertEqual(result["workspace"]["broadcast"]["memories"], matches)
        self.assertEqual(result["prediction"]["absoluteError"], 0)
        restored = self.model_module.AIEngine.import_model(engine.export_model())
        self.assertEqual(restored.get_state()["workspace"], result["workspace"])

    def test_recalled_episode_changes_prediction_informed_choice(self):
        model = self.model_module.create_model()
        model["state"]["confidence"] = 20
        model["goals"] = [{"id": "learn", "priority": 40, "target": {"confidenceMin": 50}}]
        model["state"]["selfModel"]["actions"] = {
            "observe": {"count": 4, "meanDelta": {"energy": -1, "curiosity": 0, "confidence": 2}},
            "learn": {"count": 4, "meanDelta": {"energy": -3, "curiosity": 0, "confidence": 8}},
        }
        engine = self.model_module.AIEngine(model)
        engine.memory.add({"input": {"type": "user_input", "value": "special topic"},
                           "action": "observe", "previousState": {"energy": 72, "curiosity": 50, "confidence": 20},
                           "outcome": {"energy": 71, "curiosity": 50, "confidence": 32}})
        workspace = engine.open_workspace(engine.observe({"type": "user_input", "value": "special topic"}))
        self.assertEqual(engine.select_predicted_action(), "learn")
        self.assertEqual(engine.select_predicted_action(workspace), "observe")

    def test_bio_signals_gate_goal_actions_and_remain_bounded(self):
        model = self.model_module.create_model()
        model["state"]["curiosity"] = 0
        model["state"]["bioSignals"]["novelty"] = 0.5
        model["goals"] = [
            {"id": "explore", "priority": 50, "target": {"curiosityMin": 60}}
        ]
        engine = self.model_module.AIEngine(model)

        result = engine.step({"type": "user_input", "value": "new input"})

        self.assertEqual(result["workspace"]["goal"], "explore")
        self.assertEqual(result["action"]["type"], "explore")
        for _ in range(20):
            engine.step({"type": "user_input", "value": "more input"})

        signals = engine.get_state()["bioSignals"]
        self.assertTrue(all(0 <= value <= 1 for value in signals.values()))
        restored = self.model_module.AIEngine.import_model(engine.export_model())
        self.assertEqual(restored.get_state()["bioSignals"], signals)

    def test_high_stress_suppresses_workspace_guided_exploration(self):
        model = self.model_module.create_model()
        model["state"]["curiosity"] = 0
        model["state"]["bioSignals"]["stress"] = 0.95
        model["goals"] = [
            {"id": "explore", "priority": 50, "target": {"curiosityMin": 60}}
        ]
        engine = self.model_module.AIEngine(model)

        result = engine.step({"type": "user_input", "value": "new input"})

        self.assertEqual(result["workspace"]["goal"], "explore")
        self.assertEqual(result["action"]["type"], "observe")


if __name__ == "__main__":
    unittest.main()