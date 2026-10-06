import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest


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

    def test_create_model_file_writes_deserializable_model(self):
        with tempfile.TemporaryDirectory(prefix="model-tests-") as directory:
            path = os.path.join(directory, "test.dodl")
            model = self.model_module.create_model_file(path)

            with open(path, "rb") as model_file:
                data = model_file.read()

        self.assertEqual(data[:4], self.model_module.MAGIC)
        loaded_model = self.model_module.deserialize_model(data)
        self.assertEqual(loaded_model["version"], model["version"])

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

        self.assertEqual(loaded_model["version"], self.model_module.CONFIG["VERSION"])


if __name__ == "__main__":
    unittest.main()