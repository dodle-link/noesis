# Providers

Examples use Python 3 and run from `core/model`. See the [model README](../model/README.md) for a quick start.

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

