#!/usr/bin/env python3

import importlib.util
import os
import shutil
import tempfile
import unittest


def _load_intent_module():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "soul", "intent.py")
    spec = importlib.util.spec_from_file_location("intent", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load intent module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IntentApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intent = _load_intent_module()
        cls._tmp_state_dir = tempfile.mkdtemp(prefix="intent-tests-")
        cls.intent.STATE_DIR = cls._tmp_state_dir

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp_state_dir, ignore_errors=True)

    def test_logic_command_is_case_insensitive(self):
        response = self.intent.process_intent_api("logic a and b")
        self.assertEqual(response, "Logic result: FALSE")

    def test_logic_command_supports_symbolic_operators(self):
        response = self.intent.process_intent_api("logic a && b")
        self.assertEqual(response, "Logic result: FALSE")

    def test_implication_operator_is_detected_before_not(self):
        response = self.intent.process_intent_api("logic A=>B")
        self.assertEqual(response, "Logic result: FALSE")

    def test_not_operator_requires_actual_operator_position(self):
        response = self.intent.process_intent_api("logic A!")
        self.assertEqual(response, "Unknown logical expression: A!")

    def test_logic_command_ignores_partial_word_matches(self):
        response = self.intent.process_intent_api("logic ORDINARY")
        self.assertEqual(response, "Unknown logical expression: ORDINARY")

    def test_logic_not_word_form_is_case_insensitive(self):
        response = self.intent.process_intent_api("logic not a")
        self.assertEqual(response, "Logic result: FALSE")

    def test_logic_api_response_is_not_polluted_by_detection_logs(self):
        response = self.intent.process_intent_api("logic A AND B")
        self.assertEqual(response, "Logic result: FALSE")

    def test_logic_none_input_is_handled_gracefully(self):
        response = self.intent.process_intent_api(None)
        self.assertEqual(response, "Intent processed: ")

    def test_quantum_intent_save_persists_soul_intent_state(self):
        response = self.intent.process_intent_api("quantum-intent save seek_knowledge")
        self.assertEqual(response, "Quantum intent stored: seek_knowledge")
        state = self.intent.load_noe_state(
            self.intent.state_file(self.intent.QUANTUM_INTENT_STATE)
        )
        self.assertEqual(state.get("intent"), "seek_knowledge")
        self.assertEqual(state.get("entangled_with"), "soul.intent")

    def test_quantum_intent_status_returns_last_saved_intent(self):
        self.intent.process_intent_api("quantum-intent save explore_memory")
        response = self.intent.process_intent_api("quantum-intent status")
        self.assertIn("Quantum intent: explore_memory", response)


if __name__ == "__main__":
    unittest.main()
