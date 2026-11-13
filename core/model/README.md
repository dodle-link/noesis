---
license: mit
tags:
    - noesis
    - stateful-agent
    - custom-model-format
---
# Core Model

`me.py` is a small, stateful AI model built with Python's standard library. It combines a neural network with goals, memory, rules, and a behavior program.

This guide starts with the basics, then covers training, model files, and optional integrations. It also distinguishes what the software does today from the ideas it uses as inspiration.

## Quick start

Create the default model files from this directory:

```bash
python3 me.py
```

This writes `noe-model.dodl` and `noe-model.F32.gguf` in the current directory. Load the DODL file and run one model step like this:

```python
from me import AIEngine, deserialize_model

with open("noe-model.dodl", "rb") as model_file:
    model = deserialize_model(model_file.read())

engine = AIEngine(model)
result = engine.step({"type": "user_input", "value": "hello"})
print(result["action"])
```

## How the model works

Enabled rules choose actions first. If no rule applies, the behavior program is used. The neural network processes each input, and its output is available in the step's interpretation, but it does not choose the action.

Each step saves a workspace snapshot with the input focus, active goal, intention, predicted state, observed outcome, and prediction error. This is a practical self-monitoring trace, not evidence that the model has subjective experience. When the default `observe` action would otherwise be chosen, an active `learn` goal can guide the model to learn instead.

The model tracks `bioSignals` named `novelty`, `stress`, `recovery`, and `arousal`. These bounded software variables can influence exploration and learning. They are biological analogies, not chemical measurements or biological computation. The model also does not simulate quantum effects or establish consciousness.

Live Preview: [noesis.dodle.link/model](https://noesis.dodle.link/model/)

## Create a model file

Run the script from the `core/model/` directory:

```bash
python3 me.py
```

The `F32` suffix identifies the GGUF file's float32 tensor type. DODL stores the complete model, including its state, memory, rules, behavior, and network. GGUF stores the network's four float32 tensors, architecture dimensions, and workspace format/version markers. It uses the custom `noesis` architecture and requires a compatible runtime. Live workspace state stays in DODL.

`create_model_file(path)` is also available when creating a model from Python; it writes the binary DODL format and returns the model object. Pass that model to `create_gguf_model_file(path, model)` to write the matching GGUF file.

The path may be a string or another path-like value. Its parent directory must already exist. The file is binary; open it with `"rb"` when reading.

## Train the pixel controller

The pixel demo also uses DODL, but has a network specialized for steering. It takes eight normalized inputs (pixel position and velocity, pointer offset and presence, and excitement) and produces two steering outputs. Train it from `core/model/`:

```bash
python3 me.py --train-pixel
```

This writes `noe-pixel-model.dodl` and leaves `noe-model.dodl` untouched. Training uses a built-in steering policy that moves away from a nearby pointer and screen edges. Use `--samples` and `--epochs` to adjust training, `--seed` to make it repeatable, or `--output` to choose another path. The browser only runs the trained model; it does not train it.

Serve `core/model/` over HTTP so the browser can load the model:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/`. The page loads `me.js`, which fetches `noe-pixel-model.dodl`. If the file is missing or has the wrong model type, the demo uses its built-in steering behavior instead.

## Load and use a model

Load the saved model into `AIEngine`:

```python
from me import AIEngine, deserialize_model

with open("noe-model.dodl", "rb") as model_file:
    model = deserialize_model(model_file.read())

engine = AIEngine(model)
result = engine.step({"type": "user_input", "value": "hello"})
print(result["action"])
```

`AIEngine.import_model(data)` loads a model from serialized bytes. `AIEngine.export_model()` returns the current model as bytes, which you can save to keep the latest state:

```python
with open("noe-model.dodl", "wb") as model_file:
    model_file.write(engine.export_model())
```

## Merge compatible models

`merge_models(model_a, model_b, alpha=0.5)` interpolates corresponding network parameters. `alpha=0` keeps model A's parameters, `alpha=1` uses model B's, and values in between blend the two. Model B defines the merged network architecture; when dimensions differ, overlapping parameters from model A are mapped by index and any additional dimensions retain model B's parameters. The merged model keeps model A's state, rules, memory, behavior, and goals, while receiving a new ID and timestamps.

Pass DODL model dictionaries or supported model-file paths, merge them, then serialize the result:

```python
from me import merge_models, serialize_model

merged = merge_models("model-a.dodl", "model-b.onnx", alpha=0.5)
with open("merged-model.dodl", "wb") as model_file:
    model_file.write(serialize_model(merged))
```

ONNX loading requires `pip install onnx` and supports a graph consisting of `Gemm → Relu → Gemm` with weights and biases stored as initializers. The imported ONNX dimensions are preserved in the merged DODL model. This merges weights and biases only; it does not combine memories, rules, or other model metadata. Direct parameter averaging may work poorly for independently trained networks, even when their shapes match.

## Generate a reply with an external model

`LLMProvider` sends the input, current state, and up to five recent memories to OpenAI, Gemini, or an OpenAI-compatible endpoint. It uses Python's standard library, so no provider SDK is required. Credentials and endpoint configuration are runtime-only and are never stored in the DODL file:

```bash
export NOESIS_PROVIDER=openai  # or gemini
export OPENAI_API_KEY=your-api-key
```

For Gemini, set `GEMINI_API_KEY` instead. `NOESIS_PROVIDER` defaults to `openai`. The default models are `gpt-4o-mini` and `gemini-2.0-flash`; override them with `OPENAI_MODEL` or `GEMINI_MODEL` if needed.

For a local server with an OpenAI-compatible API, such as Ollama or vLLM, configure:

```bash
export NOESIS_PROVIDER=openai-compatible
export NOESIS_BASE_URL=http://localhost:11434/v1
export NOESIS_MODEL=llama3.2
```

`NOESIS_API_KEY` is optional for local servers and can be set when the endpoint requires a key. Pass `base_url` directly to `LLMProvider` to override the environment setting.

```python
from me import AIEngine, LLMProvider

with open("noe-model.dodl", "rb") as model_file:
    engine = AIEngine.import_model(model_file.read())

provider = LLMProvider()  # Reads NOESIS_PROVIDER and the matching API key
result = engine.respond({"type": "user_input", "value": "Hello!"}, provider)
print(result["reply"])

with open("noe-model.dodl", "wb") as model_file:
    model_file.write(engine.export_model())
```

`respond()` asks the provider for a reply and structured analysis, then runs one local engine step. The analysis is bounded and stored in the workspace as `providerAnalysis`, where it is included in the cycle broadcast. Providers that only implement the older `generate()` method remain supported and produce no analysis. The provider does not choose the engine's action; local rules and behavior remain in control. This self-monitoring architecture is not evidence of subjective experience. `LLMProviderError` is raised for provider request or response errors.

## Connect a biological-computation platform

`BiocomputationProvider` lets Noesis send a task to a lab or vendor service that performs computation using a biological system. Noesis does not perform that computation itself, synthesize DNA, or control lab equipment. The remote service is responsible for translating Noesis tasks into operations its platform supports.

The provider sends a JSON `POST` request in this format:

```json
{
    "protocol": "noesis-biocompute/v1",
    "task": {"operation": "your-platform-operation", "inputs": {"value": 1}}
}
```

The service must return JSON with the same `protocol` and a `result` field. It can also include `provider` and `run_id` to identify the service and run. Set `NOESIS_BIOCOMPUTE_URL` and, if needed, `NOESIS_BIOCOMPUTE_API_KEY`. Remote endpoints must use HTTPS; HTTP is allowed for localhost development. The API key is sent as a bearer token and is never saved in the model file.

```python
from me import AIEngine, BiocomputationProvider

engine = AIEngine()
provider = BiocomputationProvider()  # Reads the URL and optional API key from the environment
result = engine.compute_biological(
        {"operation": "your-platform-operation", "inputs": {"value": 1}},
        provider=provider,
)
print(result["result"])
```

This call is explicit and does not change model state. The protocol is a transport contract, not a standard format for biological computation. Your platform needs an adapter that understands its operations and results. Validate the integration for your platform and follow appropriate lab safety procedures before connecting it to biological processes or equipment.

## Model format and limits

The file starts with the `DODL` magic signature and a versioned header. It stores JSON metadata followed by the neural network's float32 arrays. The format is intended for this module's serializer and deserializer; it is not a JSON document.

`serialize_model()` validates the memory, rule, and behavior limits, requires positive network dimensions and matching tensor lengths, and rejects non-finite tensor values. It rejects files larger than 1 MiB. `deserialize_model()` checks the signature, format version, metadata version, positive network dimensions, tensor lengths, and payload size; files larger than 1 MiB are rejected.

## Main API

- `create_model()` returns a fresh model in memory.
- `create_model_file(path)` creates a fresh model and writes it to `path`.
- `serialize_model(model)` converts a model to DODL bytes.
- `deserialize_model(data)` converts DODL bytes back to a model.
- `serialize_gguf_model(model)` converts the network tensors to GGUF v3 bytes.
- `create_gguf_model_file(path, model)` writes those GGUF bytes to `path`.
- `merge_models(model_a, model_b, alpha=0.5)` blends compatible models' network parameters.
- `AIEngine(model=None)` runs and updates a model; without an argument it creates a fresh one.
- `AIEngine.step(input_value)` observes input, chooses and executes an action, evaluates it, learns, updates state, and returns the cycle result.
- `LLMProvider(provider=None)` configures an OpenAI, Gemini, or OpenAI-compatible text-generation adapter from environment variables.
- `AIEngine.respond(input_value, provider=None)` generates a provider reply and runs one local engine step.
- `BiocomputationProvider(endpoint=None, api_key=None)` submits explicit tasks to a remote biocomputation service.
- `AIEngine.compute_biological(task, provider=None)` submits a task without changing model state.
- `AIEngine.export_model()` serializes the engine's current model.

## License

Noesis is released under the [MIT License](https://huggingface.co/dodle/noesis/blob/main/LICENSE). Individual components
also include their own license files where applicable.

## Contributing

To contribute, create a focused change in the relevant component, update its
documentation when behavior changes, and run that component's existing checks
before opening a pull request.
