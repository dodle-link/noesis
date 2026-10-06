---
license: mit
tags:
    - noesis
    - stateful-agent
    - custom-model-format
---

# Core Model

`me.py` implements a small stateful AI model. It combines a feed-forward neural network with state, goals, memory, rules, and a behavior program. It uses only the Python standard library.

## Create a model file

Run the script from the `core/model/` directory:

```bash
cd core/model
python3 me.py
```

This creates `noe-model.dodl` in the current directory. `create_model_file(path)` is also available when creating a model from Python; it writes the binary DODL format and returns the model object.

The path may be a string or another path-like value. Its parent directory must already exist. The file is binary; open it with `"rb"` when reading.

## Load and use a model

Deserialize the file into a model, then pass it to `AIEngine`:

```python
from model.me import AIEngine, deserialize_model

with open("noe-model.dodl", "rb") as model_file:
    model = deserialize_model(model_file.read())

engine = AIEngine(model)
result = engine.step({"type": "user_input", "value": "hello"})
print(result["action"])
```

Alternatively, `AIEngine.import_model(data)` constructs an engine directly from serialized bytes. `AIEngine.export_model()` returns the engine's current model as serialized bytes; write those bytes to a file to persist the latest state:

```python
with open("noe-model.dodl", "wb") as model_file:
    model_file.write(engine.export_model())
```

## Model format and limits

The file starts with the `DODL` magic signature and a versioned header. It stores JSON metadata followed by the neural network's float32 arrays. The format is intended for this module's serializer and deserializer; it is not a JSON document.

`serialize_model()` validates the memory, rule, and behavior limits and rejects files larger than 1 MiB. `deserialize_model()` checks the signature, format version, network shape, and encoded size before returning a model.

## Main API

- `create_model()` returns a fresh model in memory.
- `create_model_file(path)` creates a fresh model and writes it to `path`.
- `serialize_model(model)` converts a model to DODL bytes.
- `deserialize_model(data)` converts DODL bytes back to a model.
- `AIEngine(model=None)` runs and updates a model; without an argument it creates a fresh one.
- `AIEngine.step(input_value)` observes input, chooses and executes an action, evaluates it, learns, updates state, and returns the cycle result.
- `AIEngine.export_model()` serializes the engine's current model.
