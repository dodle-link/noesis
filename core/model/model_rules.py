# Copyright (c) Napol Thanarangkaun
# Licensed under the MIT License - See LICENSE file for details

import math

try:
    from .model_config import CONFIG
    from .model_utils import clamp
except ImportError:  # run as a script from core/model
    from model_config import CONFIG
    from model_utils import clamp


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
        return sorted(applicable, key=lambda rule: (rule.get("safety", False), rule["priority"]), reverse=True)

    def select(self, state):
        applicable = self.get_applicable(state)
        return applicable[0] if applicable else None

    def reward(self, rule_id, reward):
        rule = next((item for item in self.rules if item.get("id") == rule_id), None)
        if rule and not rule.get("safety", False):
            if reward > 0:
                rule["success"] += 1
                rule["priority"] += 1
            else:
                rule["failure"] += 1
                rule["priority"] -= 1
            rule["priority"] = clamp(rule["priority"], 0, 1000)

    def evolve(self):
        for rule in self.rules:
            if rule.get("safety", False):
                continue
            total = rule["success"] + rule["failure"]
            if total >= 10 and rule["success"] / total < 0.1:
                rule["enabled"] = False
        if len(self.rules) > CONFIG["RULE_LIMIT"]:
            self.rules = sorted(self.rules, key=lambda rule: (rule.get("safety", False), rule["priority"]), reverse=True)[
                : CONFIG["RULE_LIMIT"]
            ]


class BehaviorEngine:
    def __init__(self, program=None):
        self.program = program if program is not None else []

    def run(self, state):
        action = "observe"
        value_stack = []
        conditions = []
        for index, instruction in enumerate(self.program):
            if index >= CONFIG["BEHAVIOR_LIMIT"]:
                break
            if not instruction:
                continue
            op = instruction[0]
            arg = instruction[1] if len(instruction) > 1 else None
            if op == "READ":
                value_stack.append(state.get(arg))
            elif op == "LESS_THAN":
                value = value_stack.pop() if value_stack else None
                value_stack.append(_js_number(value) < arg)
            elif op == "GREATER_THAN":
                value = value_stack.pop() if value_stack else None
                value_stack.append(_js_number(value) > arg)
            elif op == "IF":
                condition = bool(value_stack.pop()) if value_stack else False
                conditions.append({"condition": condition, "in_else": False})
            elif op == "ELSE":
                if conditions:
                    conditions[-1]["in_else"] = True
            elif op == "ACTION" and all(
                condition["condition"] != condition["in_else"]
                for condition in conditions
            ):
                action = arg
            elif op == "END":
                if conditions:
                    conditions.pop()
        return action

    def mutate(self, random):
        if len(self.program) >= CONFIG["BEHAVIOR_LIMIT"]:
            return
        actions = ["rest", "explore", "observe", "learn"]
        mutation = int(random.next() * 3)
        if mutation == 0:
            action_index = int(random.next() * len(actions))
            self.program.append(["ACTION", actions[action_index]])
        elif mutation == 1:
            action_indexes = [
                index
                for index, instruction in enumerate(self.program)
                if instruction and instruction[0] == "ACTION"
            ]
            if action_indexes:
                index = action_indexes[int(random.next() * len(action_indexes))]
                self.program.pop(index)
        else:
            comparisons = [
                instruction
                for instruction in self.program
                if instruction and instruction[0] in ("LESS_THAN", "GREATER_THAN")
            ]
            if comparisons:
                instruction = comparisons[int(random.next() * len(comparisons))]
                instruction[1] = int(random.next() * 91) + 5
