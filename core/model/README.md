---
license: mit
tags:
    - noesis
    - stateful-agent
    - custom-model-format
---
# Core Model

Noesis includes a small Python agent that chooses actions from rules, goals, and memory. You can train its action policy or connect a language model to generate replies. The browser pixel demo uses a separate model.

Start with [Quick start](#quick-start) to run the agent, [Training](#training) to train a model, or [Pixel controller](#pixel-controller) to try the browser demo. The agent's actions are local simulation steps, not authorization to perform external operations.

## Quick start

The examples below use Python 3.11 or later and the standard library. NumPy is optional and only speeds up networks larger than the default. Run them from `core/model` so that imports and relative file paths resolve correctly.

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

When you call `step()`, the agent:

1. Reads the input and its current state.
2. Chooses an action using its rules, goals, and, if trained, its action policy. Rules and eligible goals can take priority over the policy. Without a trained policy, it uses rules and behavior.
3. Updates its state, memory, rules, and record of action outcomes. It does not train network weights during a step.

The agent keeps a workspace snapshot of what it decided, predicted, and observed. Memory recall looks for overlapping words, not meaning. When a goal is unmet, past action effects can help guide the next choice, though explicit non-`observe` rules still take priority. Uncertainty values are rough estimates, not calibrated probabilities; provider analysis does not choose actions.

Each snapshot also includes `workspace.presentSelf`, inspired by Present Self Theory. It records the current input as `here`, the timestamp and step cycle as `now`, and the pre-action state, previous action, and simulated bio signals as `self`. It's included in workspace broadcasts and saved with the model, but doesn't affect which action is chosen. `here` is the input, not a physical location.

These records are software traces, not biological measurements or evidence of subjective experience. The model doesn't simulate quantum effects or establish consciousness.

## Training

Train the action policy with `python3 me.py --train-actions --seed 123`. This replaces `noe-action-model.dodl` and its matching GGUF file in the current directory. The generated labels come from the same thresholds the rules use, so this policy imitates the rules; to learn from rewards, see [recorded outcomes](https://github.com/dodle-link/noesis/blob/main/core/docs/model-training.md#train-from-recorded-outcomes).

See the [training guide](https://github.com/dodle-link/noesis/blob/main/core/docs/model-training.md) for options, demonstrations, and safety rules, and the [evaluation guide](https://github.com/dodle-link/noesis/blob/main/core/docs/model-evaluation.md) for measuring results.

## Pixel controller

The browser demo uses a separate network to steer a pixel. To try it, serve `core/model` over HTTP:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/` or try the [live demo](https://noesis.dodle.link/model/). The demo loads the included `noe-pixel-model.dodl` and falls back to built-in steering if the file is missing or invalid.

To train a new pixel model, run:

```bash
python3 me.py --train-pixel
```

This replaces `noe-pixel-model.dodl` and `noe-pixel-model.F32.gguf`, but leaves `noe-model.dodl` unchanged. The browser runs the saved model; it does not train it. See the [training guide](https://github.com/dodle-link/noesis/blob/main/core/docs/model-training.md#pixel-model) for options.

## Files

- `me.py`: Python agent, training, and evaluation commands.
- `model_network.py`, `model_memory.py`, `model_rules.py`, and `model_utils.py`: the network, memory store, rule and behavior engines, and shared helpers that `me.py` re-exports.
- `model_config.py` and `model_formats.py`: model limits and file handling.
- `model_providers.py`: language-model and biocomputation clients.
- `index.html`, `me.js`, and `pixel_model.mjs`: the browser demo.
- `noe-model` and `noe-pixel-model` files: the included agent and pixel models.

## Reference

- [Model files and API](https://github.com/dodle-link/noesis/blob/main/core/docs/model-formats.md): DODL, GGUF, serialization, and merging.
- [Providers](https://github.com/dodle-link/noesis/blob/main/core/docs/model-providers.md): language-model replies and biocomputation gateway integration.
- [Training](https://github.com/dodle-link/noesis/blob/main/core/docs/model-training.md) and [evaluation](https://github.com/dodle-link/noesis/blob/main/core/docs/model-evaluation.md): policy training, demonstrations, and measurement.

## License and contributing

Noesis is released under the [MIT License](LICENSE). Some components include their own license files.

When changing this component, update the documentation if behavior changes and run the relevant checks before opening a pull request.
