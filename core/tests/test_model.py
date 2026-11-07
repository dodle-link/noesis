import importlib.util
import io
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


def _load_model_module():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "model", "me.py")
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
            self.model_module.train_pixel_model(
                path, sample_count=8, epochs=1, seed=123
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
        self.assertEqual(gguf_data, self.model_module.serialize_gguf_model(restored))

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
        self.assertEqual(metadata_count, 8)
        self.assertIn(b"noesis.workspace_version", gguf_data)
        self.assertIn(b"noesis.workspace_format", gguf_data)
        self.assertIn(b"cycle_snapshot", gguf_data)
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

    def test_engine_learns_and_persists_action_outcome_self_model(self):
        engine = self.model_module.AIEngine()

        first = engine.step({"type": "user_input", "value": "hello"})
        second = engine.step({"type": "user_input", "value": "again"})

        self.assertEqual(first["prediction"]["absoluteError"], 1 / 3)
        self.assertEqual(second["prediction"]["absoluteError"], 0)
        self.assertEqual(engine.get_state()["selfModel"]["predictionCount"], 2)
        self.assertEqual(engine.get_state()["selfModel"]["actions"]["observe"]["count"], 2)

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
        self.assertEqual(workspace["outcome"]["energy"], 20)
        self.assertEqual(
            workspace["predictionError"], result["prediction"]["absoluteError"]
        )

        restored = self.model_module.AIEngine.import_model(engine.export_model())
        self.assertEqual(restored.get_state()["workspace"], workspace)


if __name__ == "__main__":
    unittest.main()