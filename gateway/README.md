# Noesis Gateway v1.1.0

This module serves as the gateway for connecting various platforms and systems to the Noesis synthetic consciousness system.

## Overview

Noesis Gateway is a fully independent platform connector that provides standardized interfaces for integrating various systems and platforms. It uses the MIT license to facilitate integration with external libraries and systems, and communicates with Noesis Core only through a well-defined API.

## Structure

```
gateway/
├── LICENSE (MIT License)
├── README.md
├── run.py                      # Central control script
├── docs/
│   ├── API.md                  # API documentation
│   └── changelogs/
│       └── CHANGELOG_v1.0.0.md
├── src/
│   ├── api/                    # API components
│   │   ├── config.py
│   │   ├── noe_api.py
│   │   ├── noe_processor.py
│   │   └── request_handler.py
│   ├── core/                   # Core functionality
│   │   ├── add_external_lib.py
│   │   ├── install_dependency.py
│   │   └── launch_noesis_env.py
│   └── tools/                  # Utility tools and helpers
│       ├── install.py
│       ├── link_fish.py
│       ├── link_fish.sh
│       └── link_libraries.py
└── tests/                      # Test suite
```

## Installation

### Prerequisites

- Python 3
- git
- pkg-config
- cmake (version 3.10 or newer)
- socat (for API server functionality)
- libssl-dev
- zlib1g-dev

### Steps

1. **Install Noesis Gateway**

   ```bash
   python3 run.py install
   ```

2. **Install Noesis Core (if not already installed)**

   ```bash
   python3 run.py install_dep
   ```

3. **Link Libraries with Core (Optional)**

   ```bash
   python3 run.py link_libraries
   ```

## Running

To run Noesis Gateway:

```bash
python3 run.py run
```

To run in a specialized Noesis environment:

```bash
python3 run.py launch_env
```

### Using the API

To start the NOE API server:

```bash
python3 run.py start_api
```

To check the API status:

```bash
python3 run.py api_status
```

To process a .noe file:

```bash
python3 run.py process_noe path/to/file.noe
```

To stop the API server:

```bash
python3 run.py stop_api
```

For more information on the API, see [API Documentation](docs/API.md).

## Command Reference

```bash
python3 run.py [command] [arguments]
```

Available commands:
- `run` - Run Noesis Gateway
- `install` - Install Noesis Gateway
- `link_libraries` - Link with Core Libraries
- `install_dep` - Install Core Dependencies
- `add_lib` - Add External Library
- `launch_env` - Launch Noesis Environment
- `cleanup_struct` - Clean up Structure
- `cleanup_aggr` - Clean up Structure Aggressively
- `start_api` - Start NOE API Server
- `stop_api` - Stop NOE API Server
- `api_status` - Check NOE API Status
- `process_noe` - Process a .noe file
- `exec_noe` - Execute a command in noe-lang repository
- `help` - Show the command menu

## NOE API Integration

The Noesis Gateway provides an API for communication with noe-lang repositories via `.noe` files, enabling seamless integration between the gateway and external systems.

### API Features

- RESTful API endpoints for communication with noe-lang
- Process .noe files through a standardized interface
- Execute commands in the noe-lang repository
- Check the status of the noe-lang connection

For detailed information on the API, including request formats and endpoints, see the [API Documentation](docs/API.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
