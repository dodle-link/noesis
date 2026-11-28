# Model files and API

Examples use Python 3 and run from `core/model`. See the [model README](../model/README.md) for a quick start.

## Decision traces

Each step records a workspace snapshot with the input, active goal, recalled episodes, candidate predictions, expected and actual outcomes, and `decisionSource`. A trained action policy can choose among `rest`, `explore`, `learn`, and `observe`.

Recall matches case- and punctuation-normalized words with light stemming (for example, "learning" and "learned" both match "learn") and adjacent word pairs, weighting rarer query words more heavily and using recency to break ties. It is lexical matching, not semantic understanding. When the memory limit is reached, the entry with the lowest combined score of importance, recency, and reward is evicted, so a new low-importance entry is not automatically the first to go. When a goal is unmet, observed action effects can guide the choice; unknown actions fall back to the existing policy. Uncertainty values are heuristics based on observation counts and word overlap, not calibrated probabilities.

Signals such as `novelty`, `stress`, `recovery`, and `arousal` are bounded software values, not biological measurements.

## Model files

DODL stores the full model: its state, memory, rules, behavior, and network. New workspace fields and training metadata have defaults for older version-2 DODL files.

GGUF stores network tensors, dimensions, training method, feature schema, and tensor-layout metadata, but not live state. `F32` means the tensors use 32-bit floating-point values. This file uses Noesis' custom `noesis` architecture and needs a compatible runtime; it is not a general-purpose language model. Older files without provenance are marked `unspecified` when loaded and exported.

The files are binary, not text or JSON. The serializer and loader support files up to 1 MiB and check the file version, dimensions, tensor lengths, and values. Use `create_model_file(path)` to write a DODL model, then pass the returned model to `create_gguf_model_file(path, model)` if you also need a matching GGUF file. The destination folder must already exist.

## Merge models

`merge_models(model_a, model_b, alpha=0.5)` blends network weights. Model B supplies the output architecture. For overlapping dimensions, an `alpha` of `0` uses model A's weights and `1` uses model B's; dimensions present only in model B use model B's weights at any `alpha`. The result keeps model A's state, rules, memory, behavior, and goals. Its action policy is marked as trained only if both input policies are trained, and trained policies must have matching feature schemas. Merging weights does not merge the other parts of the models, and averaging independently trained networks may reduce their quality.

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

