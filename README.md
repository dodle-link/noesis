# Noesis

> An open-source project exploring synthetic sentience through cognition, memory,
> emotion, perception, and structured state.

Noesis is a collection of experimental components rather than a single packaged
application. The repository combines a Python-based simulation engine, a
platform gateway, the Noesis Object Encoding (`.noe`) language, and a browser
interface for the **Noe** synthetic-sentience pixel.

The project is exploratory and should not be interpreted as a claim that the
software is conscious or sentient.

## Repository at a glance

| Component | Purpose | Start here |
| --- | --- | --- |
| [`core/`](core/) | Noesis simulation engine, including cognition, memory, emotion, perception, and control subsystems | [`core/README.md`](core/README.md) |
| [`gateway/`](gateway/) | Connector and API layer for integrating external systems with Noesis | [`gateway/README.md`](gateway/README.md) |
| [`noe-lang/`](noe-lang/) | `.noe` format specification, parser, linter, and examples | [`noe-lang/README.md`](noe-lang/README.md) |
| [`noe-ui/`](noe-ui/) | Static web interface for the Noe synthetic-sentience pixel | [`noe-ui/README.md`](noe-ui/README.md) |

## Quick start

Clone the repository and choose the component you want to explore:

```bash
git clone https://github.com/dodle-link/noesis.git
cd noesis
```

### Run Noesis Core

The core engine requires Python 3. From the `core/` directory, start the
interactive shell:

```bash
cd core
python3 run.py
```

Useful commands include:

```bash
python3 run.py --help     # Show available options
python3 run.py --version  # Show the installed version
python3 run.py status     # Show terminal status
python3 run.py test       # Run the core test command
python3 run.py --quantum  # Start quantum mode
```

AI-backed features are optional. Install their dependencies using the
recommended installer, or see the [Core README](core/README.md) for
platform-specific alternatives:

```bash
python3 tools/fast_ai_install.py
```

### Run the Gateway

The gateway is a separate Python component. Its command runner is located in
`gateway/`:

```bash
cd gateway
python3 run.py help
python3 run.py start_api
python3 run.py api_status
```

The gateway API defaults to port 3000. See the
[Gateway API documentation](gateway/docs/API.md) for endpoints and `.noe`
processing details.

### Explore the `.noe` language

The [`noe-lang/`](noe-lang/) component contains the version 2 grammar,
reference parser, linter, and sample files. For example:

```bash
cd noe-lang
python3 parser/v2.0.0/noe_parser.py --lint sample/noe/v2.0.0/sample.noe
python3 lint/v2.0.0/noe_lint.py sample/noe/v2.0.0/sample.noe
```

Use [`noe-lang/sample/`](noe-lang/sample/) for complete `.noe`, JSON, and YAML
examples, and [`noe-lang/docs/grammar/v2.0.0/`](noe-lang/docs/grammar/v2.0.0/)
for the formal grammar and syntax changes.

### View the Noe UI

The UI is a dependency-free static site. Open
[`noe-ui/index.html`](noe-ui/index.html) directly in a browser, or serve the
repository with any local static file server:

```bash
cd noe-ui
python3 -m http.server 8000
```

Then visit <http://localhost:8000>. A hosted version is available at
<https://dodle-link.github.io/noesis/noe-ui/>.

When the gateway is unavailable, the pixel can run in disconnected mode with
reduced functionality.

## How the pieces fit together

```text
                         .noe files
                             |
                             v
  Noe UI  <---------->  Gateway API  <---------->  Noesis Core
                             |
                             v
                       noe-lang parser
```

- **Core** provides the simulation subsystems and interactive command shell.
- **Gateway** exposes integration and API operations for external platforms.
- **Noe-lang** defines a structured format for representing state such as
  intent, emotion, memory, and quantum-aware operations.
- **Noe UI** provides a visual, browser-based interface and can operate without
  a live backend.

These components can be explored independently; installing one does not
automatically install or configure the others.

## Project status

Noesis is an active experimental project. Interfaces, file formats, and
installation scripts may change between versions. Read the component-level
documentation and changelogs before building integrations on top of it.

## Documentation

- [Core engine and AI integration](core/README.md)
- [Gateway setup and commands](gateway/README.md)
- [Gateway API reference](gateway/docs/API.md)
- [Noe language specification](noe-lang/README.md)
- [Noe UI documentation](noe-ui/README.md)
- [Core security policy](core/docs/SECURITY.md)
- [Noe language grammar](noe-lang/docs/grammar/v2.0.0/grammar.bnf)

## License

Noesis is released under the [MIT License](LICENSE). Individual components
also include their own license files where applicable.

## Contributing

To contribute, create a focused change in the relevant component, update its
documentation when behavior changes, and run that component's existing checks
before opening a pull request.
