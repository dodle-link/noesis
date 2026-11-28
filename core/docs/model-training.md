# Training

Examples use Python 3 and run from `core/model`. See the [model README](../model/README.md) for a quick start.

## Action policy

From this directory, train the Python model's action policy:

```bash
python3 me.py --train-actions --seed 123
```

The command replaces `noe-action-model.dodl` and `noe-action-model.F32.gguf`. It trains on generated examples and selects a checkpoint using 100 fixed validation scenarios.

It prints overall and per-action accuracy on a separate 100-scenario held-out set. To see per-action support, inspect `evaluate_action_model(model)["held_out"]["per_action_support"]`.

Use `--samples`, `--epochs`, and `--patience` to adjust training, `--output` to choose a DODL path, and `--seed` to make a run repeatable. The GGUF file uses the same path and base name. Load the trained DODL file to use its policy; rules or eligible goals can still take priority.

Evaluation reports both a majority-class baseline and `rule_baseline_accuracy`. The generated labels are defined by the same threshold policy used by the rule baseline, so a perfect rule-baseline score is expected; compare against real task scenarios before preferring the neural policy. This command imitates the rules and cannot outperform them; use demonstrations or recorded outcomes (below) to learn anything the rules do not already encode.

Training uses softmax cross-entropy, a learning rate that decays by epoch, light weight decay, and element-wise gradient clipping. Validation checkpoints are chosen by accuracy, then cross-entropy; reports include both `mse` (raw outputs against one-hot labels) and `cross_entropy`. `TinyNetwork.learn` still defaults to squared error, so existing callers are unchanged.

Networks with at least `CONFIG["NUMPY_MIN_WEIGHTS"]` first-layer weights use NumPy when it is installed; the default 16x32 network always uses the pure-Python path, so results for default models do not depend on NumPy. Results can differ slightly in the last decimal places between the two paths.

## Train from recorded outcomes

`train_action_model_from_outcomes` fine-tunes a trained policy using the rewards stored in memory (or in episodes you pass in). It applies a reward-weighted policy-gradient step: actions that earned more than the mean reward are reinforced, and those that earned less are discouraged. It returns a new model and leaves the input unchanged.

```python
from me import load_model_file, train_action_model_from_outcomes

model = load_model_file("noe-action-model.dodl")
tuned, report = train_action_model_from_outcomes(model, path="noe-outcome-model.dodl", seed=1)
print(report["episodes"], report["mean_reward"])
```

The same step is available as `python3 me.py --train-outcomes --model noe-action-model.dodl --output noe-outcome-model.dodl`. Rewards come from the local simulation's `evaluate()`, so this tunes behavior for that simulation only; validate it on held-out scenarios before use. Episodes need `action`, a finite `reward`, and `previousState` with `energy`, `curiosity`, and `confidence`.

## Train from task demonstrations

`train_action_model_from_episodes` trains on caller-supplied multi-step demonstrations instead of threshold labels. Each episode supplies `initial_state`, `inputs`, `actions`, and final-state `objectives`; `goals` is optional. The trainer replays each demonstration, rejects rule conflicts and failed objectives, selects weights using separate validation demonstrations, and can evaluate a separate test set after selection. For example:

```python
from me import train_action_model_from_episodes

def episode(energy, text, group):
    return {
        "group": group,
        "initial_state": {"energy": energy, "confidence": 50},
        "inputs": [{"type": "user_input", "value": text}, None],
        "actions": ["learn", "learn"],
        "objectives": {"confidence": {"min": 60}, "energy": {"min": 20}},
    }

training = [episode(80, "training task", "training-source")]
validation = [episode(75, "validation task", "validation-source")]
test = episode(70, "held out task", "test-source")
del test["actions"]
model, report = train_action_model_from_episodes(
    "noe-demonstration-model.dodl", training, validation,
    test_scenarios=[test], epochs=20, seed=7,
)
print(report["validation"]["accuracy"])
print(report["test_scenarios"]["prediction"]["success_rate"])
```

This small, synthetic example does not establish generalization. Use representative demonstrations and independently designed validation and held-out tasks, including conflicting goals.

To prevent source or task leakage, add a non-empty `group` string to every training episode, validation episode, and test scenario. Groups may repeat within a split but must be disjoint across splits. Grouping is optional, and the caller must choose meaningful group identities. The trainer rejects exact duplicate scenarios across sets, but cannot detect subtler leakage.

Demonstrations may also specify `trajectory_objectives`; the trainer rejects a demonstration if its initial state or any post-step state violates them. This is a training-data check, not a guarantee about a trained policy.

Demonstration policies use the `action-context-v2` feature schema: state, compact text features, the active goal's state deficits, and relevance scores for recalled actions. Existing `action-state-text-v1` models retain their original encoding. Neither schema represents the full workspace; the runtime handles workspace-based planning separately. When test scenarios are supplied, `report["test_comparison"]` summarizes each policy's success-rate difference from the rule baseline and its override rate. This comparison still measures only the simulation.

## JSON workflows

The command line can train and evaluate using independently prepared JSON files:

```bash
python3 me.py --train-demonstrations demonstrations.json --output trained.dodl --epochs 20 --seed 7
python3 me.py --evaluate-scenarios scenarios.json --model trained.dodl
python3 me.py --evaluate-outcomes outcomes.json
python3 me.py --evaluate-memory queries.json --model trained.dodl
```

The demonstrations file is an object containing `training` and `validation` episode lists and an optional `test_scenarios` list, using the episode format above. The other files are JSON lists matching the examples in the [evaluation guide](model-evaluation.md). Memory query IDs must refer to episodes in the supplied model. Reports are printed as JSON; training also writes the requested DODL file and its matching GGUF file, replacing existing files at those paths.

Collect task outcomes from the surrounding application and assess them independently. A synthetic scenario or a successful local action is not a real task outcome. Split demonstrations by source or task, reserve separate held-out tasks, and compare the methods on paired tasks before deciding whether to use the trained policy.

## Safety rules

New models mark the low-energy rest rule with `"safety": true`. Enabled safety rules take precedence over adaptive rules regardless of priority, and reward updates and rule evolution do not change or disable them. Older models retain their existing rules; mark a rule explicitly to opt in. A safety rule must be enabled. These rules are application-level safeguards, not a security boundary: trusted code must control model files and any external operations independently.

## Pixel model

Run `python3 me.py --train-pixel` to train the browser's separate steering model. It uses position, velocity, pointer position, and excitement as inputs. Training reports validation error and keeps the best weights.

Use `--samples`, `--epochs`, `--patience`, `--seed`, and `--output` to adjust the run. The command replaces the output DODL file and its matching GGUF file. The default output names are `noe-pixel-model.dodl` and `noe-pixel-model.F32.gguf`.

