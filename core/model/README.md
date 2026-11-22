---
license: mit
tags:
    - noesis
    - stateful-agent
    - custom-model-format
---
# Core Model

`me.py` is a stateful Python agent that selects actions using rules, goals, memory, and a trained neural policy. An optional language model can write replies, but the agent controls actions.

## Files in this folder

- `me.py` implements the Python model, training commands, and DODL/GGUF file support.
- `model_config.py` holds shared model and file-format limits; `model_formats.py` validates, serializes, and deserializes model data.
- `model_providers.py` connects to OpenAI, Gemini, OpenAI-compatible APIs, and remote biocomputation services.
- `index.html` and `me.js` run the browser-based pixel demo. This demo uses its own steering model; it is separate from the Python agent.
- `noe-model.dodl` and `noe-model.F32.gguf` are the default Python model files. The `noe-pixel-model` files belong to the pixel demo.

## Quick start

From this directory, create the default model files:

```bash
python3 me.py
```

Load the DODL file and run one step:

```python
from me import AIEngine, deserialize_model

with open("noe-model.dodl", "rb") as model_file:
    model = deserialize_model(model_file.read())

engine = AIEngine(model)
result = engine.step({"type": "user_input", "value": "hello"})
print(result["action"])
```

The engine updates its state as it runs. Save the latest state with `engine.export_model()` when you want to keep those updates.

## How it works

Each step reads the input and current state, chooses an action, runs it, and updates the model. Rules and eligible goals can take priority. A model trained with `--train-actions` can use its network to choose among `rest`, `explore`, `learn`, and `observe`. Untrained models keep their existing rules and behavior.

The engine also records a workspace snapshot: what it focused on, which goal was active, what it expected, and what happened. This is a software trace, not evidence of subjective experience. Values such as `novelty`, `stress`, `recovery`, and `arousal` are bounded software signals. They are not biological measurements, and the model does not simulate quantum effects or establish consciousness.

## Training

### Action policy

From this directory, train the Python model's action policy:

```bash
python3 me.py --train-actions --seed 123
```

The command writes `noe-action-model.dodl` and a GGUF companion. It trains on a generated policy and selects checkpoints using 100 fixed validation scenarios. Evaluation also reports results on a separate 100-scenario held-out set, including accuracy and support for each action; held-out results do not affect checkpoint selection. Use `--samples`, `--epochs`, and `--patience` to adjust training, `--output` to choose a file path, and `--seed` to make a run repeatable. The engine uses the trained policy unless a rule or eligible goal takes priority.

Evaluation reports both a majority-class baseline and `rule_baseline_accuracy`. The generated labels are defined by the same threshold policy used by the rule baseline, so a perfect rule-baseline score is expected; compare against real task scenarios before preferring the neural policy.

### Pixel controller

The browser demo has a separate network that steers a pixel using its position, velocity, pointer position, and excitement level. Train it with:

```bash
python3 me.py --train-pixel
```

This writes `noe-pixel-model.dodl` without changing `noe-model.dodl`. Training reports validation error and keeps the best weights. You can also use `--samples`, `--epochs`, `--patience`, `--seed`, and `--output` to adjust the run. The browser runs the saved model; it does not train it.

To try the browser demo, serve this folder over HTTP:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000/`. The demo loads `noe-pixel-model.dodl`. If the file is missing or invalid, it uses built-in steering instead.

You can also try the [live demo](https://noesis.dodle.link/model/).

## Model files

DODL stores the full model: its state, memory, rules, behavior, and network. GGUF stores the network tensors and dimensions, but not the live model state. The `F32` suffix means the GGUF tensors use 32-bit floating-point values. The GGUF file uses Noesis' custom `noesis` architecture and needs a compatible runtime.

The files are binary, not text or JSON. The serializer and loader support files up to 1 MiB and check the file version, dimensions, tensor lengths, and values. Use `create_model_file(path)` to write a DODL model, or pass its returned model to `create_gguf_model_file(path, model)` to write the matching GGUF file. The destination folder must already exist.

## Use a language model for replies

`LLMProvider` can request replies from OpenAI, Gemini, or an OpenAI-compatible server. It uses Python's standard library, so you do not need a provider SDK. Requests and responses are limited to 1 MiB, and the timeout must be a positive finite number. Provider settings and API keys are read at runtime and are never saved in the model file.

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

with open("noe-model.dodl", "wb") as model_file:
    model_file.write(engine.export_model())
```

The provider writes the reply and may return a short analysis. The local engine still chooses and runs the action. Provider request failures raise `LLMProviderError`.

## Connect a biocomputation service

`BiocomputationProvider` is a client for a separately deployed gateway. Noesis does not perform biological computation, operate bacteria, or control lab equipment. Connect the gateway to an existing, approved platform; do not expose platform controls directly to model-generated text.

Set `NOESIS_BIOCOMPUTE_URL` and, if needed, `NOESIS_BIOCOMPUTE_API_KEY`. For asynchronous jobs, also set `NOESIS_BIOCOMPUTE_JOBS_URL` to a same-origin URL without a query or fragment. Remote URLs must use HTTPS; HTTP is allowed for localhost development. The key is sent as a bearer token and is not stored in the model. Requests time out after 30 seconds by default and are not retried.

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
- `merge_models(model_a, model_b, alpha=0.5)` blends network weights.
- `LLMProvider(...)` configures a text-generation service; `AIEngine.respond(...)` requests a reply and runs one local cycle.
- `BiocomputationProvider(...)` configures an allowlisted gateway client; `AIEngine.compute_biological(...)` submits an approved task without changing model state. `submit_task()`, `get_job()`, and `cancel_job()` provide asynchronous job handling.

Model validation checks network tensors and runtime metadata used by the engine. Serialization does not mutate its input; `AIEngine.export_model()` synchronizes live state and the update timestamp before serializing.

## License and contributing

Noesis is released under the [MIT License](LICENSE). Some components include their own license files.

When changing this component, update the documentation if behavior changes and run the relevant checks before opening a pull request.
