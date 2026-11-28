# Evaluation

Examples use Python 3 and run from `core/model`. See the [model README](../model/README.md) for a quick start.

## Evaluate action scenarios

Use `evaluate_action_scenarios` to compare prediction-informed decisions (`prediction`), the policy without prediction-based selection (`policy`), and the threshold baseline (`rule_baseline`) on multi-step tasks. All run through the same engine, including rule and goal overrides. Supply representative task inputs, starting state values, optional `goals`, and measurable final-state objectives. For example, this is a synthetic illustration, not evidence of real-world performance:

```python
from me import evaluate_action_scenarios, load_model_file

model = load_model_file("noe-action-model.dodl")
scenarios = [{
    "initial_state": {"energy": 80, "curiosity": 50, "confidence": 50},
    "inputs": [{"type": "user_input", "value": "first"},
               {"type": "user_input", "value": "second"}],
    "expected_actions": ["learn", "learn"],
    "objectives": {"confidence": {"min": 55}, "energy": {"min": 20}},
}]
results = evaluate_action_scenarios(model, scenarios)
print(results["prediction"]["success_rate"], results["policy"]["success_rate"],
    results["rule_baseline"]["success_rate"])
print(results["policy"]["action_accuracy"], results["policy"]["decision_source_counts"])
```

Objectives support `min` and `max` bounds on final `energy`, `curiosity`, `confidence`, and `stability`. Results include success rates, mean total reward, mean prediction error, and each scenario's actions, decision sources, minimum energy, final state, and success. `decision_source_counts` and `override_rate` show how often a rule, goal, or prediction selected an action instead of the policy. For independently labeled decisions, add `expected_actions` to a scenario: one action name or `None` per input. `action_accuracy` is the fraction of labeled actions matched, or `None` when no labels were supplied. Labels should be chosen independently of the model and its training data.

Add `trajectory_objectives` with the same bounds to check the initial state and every post-step state. `trajectory_success` and `trajectory_success_rate` report these bounds separately from final-state success; the rate covers only scenarios with trajectory objectives and is `None` when none are supplied. For example, `"trajectory_objectives": {"energy": {"min": 20}}` detects a temporary energy drop even if the final energy recovers. The default rest rule triggers only below 20 and does not guarantee this bound.

The evaluator copies the model for each run. Its state objectives, rewards, and action labels measure this simulation only; they do not measure actual user outcomes. Build held-out scenarios from intended use cases, with independently defined success criteria and task or source groups. The engine's four actions do not themselves perform external tasks, so an end-to-end usefulness benchmark also needs evaluation of the surrounding application and its real outcomes.

## Evaluate application outcomes

Record independently assessed outcomes from representative tasks in the surrounding application. Compare methods on equivalent tasks using the same success criteria and an evaluation design that avoids order and selection bias. `task_id` must identify the same task across methods; each method/task pair may appear once.

```python
from me import evaluate_task_outcomes

results = evaluate_task_outcomes([
    {"task_id": "task-1", "method": "policy", "success": True},
    {"task_id": "task-1", "method": "rule_baseline", "success": False},
])
print(results["methods"], results["vs_rule_baseline"])
```

The report includes each method's task count and success rate, plus the paired task count and success-rate difference against `rule_baseline`. Unpaired tasks contribute to their method's overall rate but not the paired comparison. These summaries do not establish statistical significance or eliminate bias; collect enough independently labeled results before deciding whether to deploy a trained policy.

Records can also include measured non-negative `latency_seconds` and `cost_usd`. Each method reports the mean and count for available measurements. Comparisons report mean differences and counts only for task pairs with measurements for both methods. Costs must be supplied by the caller; the engine does not estimate provider pricing.

## Evaluate memory retrieval

Use representative queries and independently labeled relevant episode IDs to measure retrieval before changing its ranking or adding semantic search:

```python
from me import MemoryStore, evaluate_memory_retrieval

memory = MemoryStore()
memory.add({"input": {"value": "billing question"}, "action": "observe"})
results = evaluate_memory_retrieval(memory, [{
    "input": {"value": "billing question"},
    "relevant_ids": [memory.items[0]["id"]],
}], count=3)
print(results["recall"], results["mrr"])
```

The report gives mean recall at `count` and mean reciprocal rank. The example only illustrates the API; use held-out queries including paraphrases and irrelevant overlaps to assess retrieval quality.

Use an empty `relevant_ids` list for a query that should match no episodes. `false_positive_rate` is the fraction of those queries that return any match. Recall and MRR cover only queries with relevant IDs and are `None` when there are none; the false-positive rate is `None` when there are no no-match queries.

