#!/usr/bin/env python3

import importlib.util
import os
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

    def test_logic_command_is_case_insensitive(self):
        response = self.intent.process_intent_api("logic a and b")
        self.assertEqual(response, "Logic result: FALSE")

    def test_logic_command_supports_symbolic_operators(self):
        response = self.intent.process_intent_api("logic a && b")
        self.assertEqual(response, "Logic result: FALSE")

    def test_implication_operator_is_detected_before_not(self):
        response = self.intent.process_intent_api("logic A=>B")
        self.assertEqual(response, "Logic result: FALSE")

    def test_logic_command_ignores_partial_word_matches(self):
        response = self.intent.process_intent_api("logic ORDINARY")
        self.assertEqual(response, "Unknown logical expression: ORDINARY")

    def test_logic_api_response_is_not_polluted_by_detection_logs(self):
        response = self.intent.process_intent_api("logic A AND B")
        self.assertEqual(response, "Logic result: FALSE")


if __name__ == "__main__":
    unittest.main()
