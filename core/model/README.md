---
license: mit
tags:
    - noesis
    - stateful-agent
    - custom-model-format
---
# Core Model

The core model includes a small, stateful Python agent and a separate browser demo. The agent chooses actions using rules, goals, memory, and, when trained, a neural policy. You can connect a language model to write replies, but the local agent still decides what action to take.

Start with [Quick start](#quick-start) to run the agent, [Training](#training) to train a model, or [Pixel controller](#pixel-controller) to try the browser demo.

## Files

- `me.py` implements the Python model, training commands, and DODL/GGUF file support.
- `model_config.py` defines model and file-format limits. `model_formats.py` validates, reads, and writes model data.
- `model_providers.py` connects to OpenAI, Gemini, OpenAI-compatible APIs, and remote biocomputation services.
- `index.html`, `me.js`, and `pixel_model.mjs` run the browser-based pixel demo. It uses its own steering model, separate from the Python agent.
- `noe-model.dodl` and `noe-model.F32.gguf` are the default Python model files. The `noe-pixel-model` files belong to the pixel demo.

## Quick start

The examples below use Python 3 and the standard library. Run them from `core/model` so that imports and relative file paths resolve correctly.

The repository includes `noe-model.dodl`, so you can load it directly:

```python
from me import AIEngine, load_model_file

engine = AIEngine(load_model_file("noe-model.dodl"))
result = engine.step({"type": "user_input", "value": "hello"})
print(result["action"])
```

`step()` updates the engine's state in memory and returns a snapshot containing the action, state, and other details. To keep the updated state between runs, write the exported model to a file:

```python
with open("my-model.dodl", "wb") as model_file:
    model_file.write(engine.export_model())
```

Load `my-model.dodl` on the next run to continue from that state. Saving to a different file keeps the original model unchanged.

To create a fresh default model instead, run:

```bash
python3 me.py
```

This writes `noe-model.dodl` and `noe-model.F32.gguf` in the current directory, replacing files with those names. Run it in another directory if you want to preserve the included files.

## How it works

Each step reads the input and current state, chooses an action, runs it, and updates the model. Rules and eligible goals can take priority. A model trained with `--train-actions` can use its network to choose among `rest`, `explore`, `learn`, and `observe`. An untrained model uses its existing rules and behavior instead. Steps update memory, rules, and the outcome self-model, but do not train network weights online.

The engine records a workspace snapshot for each step. This includes the input, active goal, recalled episodes, candidate predictions, expected outcome, actual outcome, and `decisionSource`. Episodes are selected by case- and punctuation-normalized word overlap, with rarer query words weighted more heavily and recency used to break ties. This is lexical matching, not semantic understanding.

When a goal is unmet, previously observed action effects can help guide the choice. Explicit non-`observe` rules still take priority, and unknown actions fall back to the existing policy. Uncertainty values are simple heuristics based on observation counts and word overlap, not calibrated probabilities. Provider analysis does not control actions.

These are software traces and decision heuristics, not evidence of subjective experience. Values such as `novelty`, `stress`, `recovery`, and `arousal` are bounded software signals. They are not biological measurements, and the model does not simulate quantum effects or establish consciousness.

## Training

### Action policy

From this directory, train the Python model's action policy:

```bash
python3 me.py --train-actions --seed 123
```

The command writes `noe-action-model.dodl` and `noe-action-model.F32.gguf`, replacing files with those names. It trains on generated examples and chooses a checkpoint using 100 fixed validation scenarios. It also reports accuracy and support for each action on a separate 100-scenario held-out set, which is not used to select the checkpoint.

Use `--samples`, `--epochs`, and `--patience` to adjust training, `--output` to choose a DODL path, and `--seed` to make a run repeatable. The GGUF file uses the same path and base name. Load the trained DODL file to use its policy; rules or eligible goals can still take priority.

Evaluation reports both a majority-class baseline and `rule_baseline_accuracy`. The generated labels are defined by the same threshold policy used by the rule baseline, so a perfect rule-baseline score is expected; compare against real task scenarios before preferring the neural policy.

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

### Train from task demonstrations

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

This example is intentionally small and synthetic; it does not establish generalization. Supply larger, representative demonstrations and independently designed validation and held-out tasks, including conflicting goals. To prevent source or task leakage, add a non-empty `group` string to every training episode, validation episode, and test scenario. Groups may repeat within a split but must be disjoint across splits. Grouping is optional for compatibility; the caller must select meaningful group identities. The trainer also rejects exact duplicate scenarios across the sets, but cannot detect subtler leakage.

Demonstrations may also specify `trajectory_objectives`; the trainer rejects a demonstration if its initial state or any post-step state violates them. This is a training-data check, not a guarantee about a trained policy.

Demonstration policies use the `action-context-v2` feature schema: state, compact text features, the active goal's state deficits, and relevance scores for recalled actions. Existing `action-state-text-v1` models retain their original encoding. Neither schema represents the full workspace; the runtime handles workspace-based planning separately. When test scenarios are supplied, `report["test_comparison"]` summarizes each policy's success-rate difference from the rule baseline and its override rate. This comparison still measures only the simulation.

### Evaluate application outcomes

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

### Evaluate memory retrieval

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

### JSON workflows

The command line can train and evaluate using independently prepared JSON files:

```bash
python3 me.py --train-demonstrations demonstrations.json --output trained.dodl --epochs 20 --seed 7
python3 me.py --evaluate-scenarios scenarios.json --model trained.dodl
python3 me.py --evaluate-outcomes outcomes.json
python3 me.py --evaluate-memory queries.json --model trained.dodl
```

The demonstrations file is an object containing `training` and `validation` episode lists and an optional `test_scenarios` list, using the episode format above. The other files are JSON lists matching the corresponding API examples. Memory query IDs must refer to episodes in the supplied model. Reports are printed as JSON; training also writes the requested DODL file and its matching GGUF file, replacing existing files at those paths.

Collect task outcomes from the surrounding application and assess them independently. A synthetic scenario or a successful local action is not a real task outcome. Split demonstrations by source or task, reserve separate held-out tasks, and compare the methods on paired tasks before deciding whether to use the trained policy.

### Safety rules

New models mark the low-energy rest rule with `"safety": true`. Enabled safety rules take precedence over adaptive rules regardless of priority, and reward updates and rule evolution do not change or disable them. Older models retain their existing rules; mark a rule explicitly to opt in. A safety rule must be enabled. These rules are application-level safeguards, not a security boundary: trusted code must control model files and any external operations independently.

### Pixel controller

The browser demo has a separate network that steers a pixel using its position, velocity, pointer position, and excitement level. Train it with:

```bash
python3 me.py --train-pixel
```

This writes `noe-pixel-model.dodl` and `noe-pixel-model.F32.gguf`, replacing files with those names but leaving `noe-model.dodl` unchanged. Training reports validation error and keeps the best weights. You can also use `--samples`, `--epochs`, `--patience`, `--seed`, and `--output` to adjust the run. The browser runs the saved DODL model; it does not train it.

To try the browser demo, serve `core/model` over HTTP:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000/`. The demo loads `noe-pixel-model.dodl`. If the file is missing or invalid, it uses built-in steering instead.

You can also try the [live demo](https://noesis.dodle.link/model/).

## Model files

DODL stores the full model: its state, memory, rules, behavior, and network. New workspace fields and training metadata have defaults for older version-2 DODL files. GGUF stores the network tensors, dimensions, training method, feature schema, and tensor-layout metadata, but not the live model state. The `F32` suffix means the GGUF tensors use 32-bit floating-point values. The GGUF file uses Noesis' custom `noesis` architecture and needs a compatible runtime; it is not a general-purpose language model. Older files without provenance are marked `unspecified` when loaded and exported.

The files are binary, not text or JSON. The serializer and loader support files up to 1 MiB and check the file version, dimensions, tensor lengths, and values. Use `create_model_file(path)` to write a DODL model, then pass the returned model to `create_gguf_model_file(path, model)` if you also need a matching GGUF file. The destination folder must already exist.

## Use a language model for replies

`LLMProvider` can request replies from OpenAI, Gemini, or an OpenAI-compatible server. It uses Python's standard library, so you do not need a provider SDK. Provider settings and API keys are read at runtime and are never saved in the model file. Requests and responses are limited to 1 MiB; the default timeout is 30 seconds.

For OpenAI, set:

```bash
export NOESIS_PROVIDER=openai
export OPENAI_API_KEY=your-api-key
```

For Gemini, set `NOESIS_PROVIDER=gemini` and `GEMINI_API_KEY`. The default models are `gpt-4o-mini` and `gemini-2.0-flash`; set `OPENAI_MODEL` or `GEMINI_MODEL` to use another model.

For a local OpenAI-compatible server, such as Ollama, set:

```bash
export NOESIS_PROVIDER=openai-compatible
export NOESIS_BASE_URL=http://localhost:11434/v1
export NOESIS_MODEL=llama3.2
```

`NOESIS_API_KEY` is optional for local servers. Set it if your server requires a key.

```python
from me import AIEngine, LLMProvider

with open("noe-model.dodl", "rb") as model_file:
    engine = AIEngine.import_model(model_file.read())

result = engine.respond(
    {"type": "user_input", "value": "Hello!"},
    LLMProvider(),
)
print(result["reply"])

with open("my-model.dodl", "wb") as model_file:
    model_file.write(engine.export_model())
```

The provider writes the reply and may return a short analysis. The local engine still chooses and runs the action. `respond()` updates the engine just like `step()`, so export the model if you want to keep the new state. Load `my-model.dodl` in a later run to continue from it. Provider request failures raise `LLMProviderError`.

The returned action describes a local simulation step, not permission to perform an external operation. Application code must independently authenticate, authorize, validate, and, where required, obtain approval for external operations; provider analysis and local decision traces are not authorization.

By default, `respond()` sends the current input and the numeric energy, curiosity, confidence, and stability signals, but no stored memory or workspace. The current input can itself contain sensitive information. To redact it or explicitly include selected context, pass a trusted `context_filter` callable. It receives copies of `user_input`, full `state` (including the pre-action workspace), and recalled `memories`, and must return a dictionary with exactly those three keys:

```python
def select_context(context):
    return {
        "user_input": {"type": "user_input", "value": "[redacted]"},
        "state": {},
        "memories": [],
    }

result = engine.respond({"type": "user_input", "value": "private"},
                        LLMProvider(), context_filter=select_context)
```

This changes what the provider sees, not the input processed locally or stored in the model. The filter must redact every sensitive field it chooses to include. Calling `LLMProvider.generate()` directly sends the context supplied by its caller.

Retries are disabled by default. `LLMProvider(max_retries=1)` opts into at most one retry (maximum two are allowed) for HTTP 429 or 503, with bounded backoff. Numeric `Retry-After` values up to two seconds are honored; longer, malformed, or HTTP-date values are not retried. Other HTTP failures and transport errors are not retried. Retrying generation can incur additional cost and extend total latency; the timeout applies per request.

### Observability

Pass an `event_callback` to `AIEngine` to receive content-free provider and local decision events:

```python
events = []
engine = AIEngine(event_callback=events.append)
engine.step({"type": "user_input", "value": "hello"})
print(events[-1])
```

Provider events report success or error and elapsed seconds, without inputs, replies, or exception messages. Decision events report the decision source, action, and local execution success. Local success is not an independently measured application outcome. Callback exceptions are ignored so a telemetry failure does not alter model behavior; the callback is responsible for exporting or storing events safely.

## Connect a biocomputation service

`BiocomputationProvider` is a client for a separately deployed gateway. Noesis does not perform biological computation, operate bacteria, or control lab equipment. Connect the gateway to an existing, approved platform; do not expose platform controls directly to model-generated text.

Set `NOESIS_BIOCOMPUTE_URL` and, if needed, `NOESIS_BIOCOMPUTE_API_KEY`. For asynchronous jobs, also set `NOESIS_BIOCOMPUTE_JOBS_URL` to a same-origin URL without a query or fragment. Remote URLs must use HTTPS; HTTP is allowed for localhost development.

The key is sent as a bearer token and is not stored in the model. Requests time out after 30 seconds by default and are not retried.

Configure an explicit allowlist of platform operations and their input schemas in trusted application code. The provider supports a JSON Schema subset: `type`, `enum`, `properties`, `required`, `additionalProperties`, `items`, length/item limits, and numeric bounds. Unknown operations and extra fields can be rejected before they leave the client. A human approval ID is required for every submission; the gateway must independently verify that approval and the caller's authorization.

```python
from me import AIEngine, BiocomputationProvider

provider = BiocomputationProvider(
    operation_schemas={
        "read-approved-sample": {
            "type": "object",
            "properties": {
                "sample_ref": {"type": "string", "minLength": 1, "maxLength": 128}
            },
            "required": ["sample_ref"],
            "additionalProperties": False,
        }
    }
)
engine = AIEngine()
result = engine.compute_biological(
    {"operation": "read-approved-sample", "inputs": {"sample_ref": "sample-123"}},
    provider=provider,
    approval_id="approval-issued-by-your-review-system",
)
print(result["result"])
```

The synchronous request body is:

```json
{
    "protocol": "noesis-biocompute/v1",
    "task": {"operation": "read-approved-sample", "inputs": {"sample_ref": "sample-123"}},
    "approval_id": "approval-issued-by-your-review-system"
}
```

The gateway must return JSON with the same protocol and a `result` field. It should include a `provenance` object describing the platform, method/assay version, timestamps, and quality-control outcome. `AIEngine.compute_biological()` does not change model state.

For long-running work, the gateway accepts `POST` at `NOESIS_BIOCOMPUTE_URL`, with an `Idempotency-Key` header, and returns a job object:

```json
{
    "protocol": "noesis-biocompute/v1",
    "job": {"id": "job-123", "status": "queued"}
}
```

Use `provider.submit_task(task, approval_id=..., idempotency_key=...)` to submit, `provider.get_job(job_id)` to poll `NOESIS_BIOCOMPUTE_JOBS_URL/{job_id}`, and `provider.cancel_job(job_id, approval_id=..., idempotency_key=...)` to request cancellation at `/cancel`. Valid statuses are `queued`, `running`, `succeeded`, `failed`, and `cancelled`; a succeeded job includes `result`. Cancellation is a request to the gateway, not a guarantee that a running platform operation can be stopped.

The protocol is an integration contract, not a biological-computation standard or a platform adapter. The gateway must enforce permissions and operational limits, audit approvals and submissions, provide a platform-side stop procedure, and return sanitized errors. Test with mocks and the platform sandbox first, and follow the platform's and institution's applicable biosafety review before any real deployment.

## Merge models

`merge_models(model_a, model_b, alpha=0.5)` blends network weights. An `alpha` of `0` keeps model A's weights; `1` uses model B's. Model B supplies the output architecture. The result keeps model A's state, rules, memory, behavior, and goals. Merging weights does not merge those parts of the models, and averaging independently trained networks may reduce their quality.

You can pass DODL models or supported model paths. ONNX loading requires `pip install onnx` and supports a `Gemm -> Relu -> Gemm` network with weights and biases stored as initializers.

## Main API

- `create_model()` creates a model in memory; `create_model_file(path)` also writes it to disk.
- `serialize_model(model)` and `deserialize_model(data)` convert to and from DODL bytes.
- `serialize_gguf_model(model)` and `create_gguf_model_file(path, model)` write GGUF data.
- `AIEngine(model=None)` runs a model. `step(input_value)` performs one cycle, and `export_model()` returns the updated model as bytes.
- `train_action_model(...)` trains an action policy; `evaluate_action_model(model)` reports validation and held-out results, including per-action accuracy and support.
- `evaluate_action_scenarios(model, scenarios)` compares multi-step task outcomes against the threshold rule baseline.
- `merge_models(model_a, model_b, alpha=0.5)` blends network weights.
- `LLMProvider(...)` configures a text-generation service; `AIEngine.respond(...)` requests a reply and runs one local cycle.
- `BiocomputationProvider(...)` configures an allowlisted gateway client; `AIEngine.compute_biological(...)` submits an approved task without changing model state. `submit_task()`, `get_job()`, and `cancel_job()` provide asynchronous job handling.

Model validation checks network tensors and runtime metadata used by the engine. Serialization does not mutate its input; `AIEngine.export_model()` synchronizes live state and the update timestamp before serializing.

## License and contributing

Noesis is released under the [MIT License](LICENSE). Some components include their own license files.

When changing this component, update the documentation if behavior changes and run the relevant checks before opening a pull request.
