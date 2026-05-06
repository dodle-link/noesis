# Noe - Synthetic Conscious Pixel v1.1.0

This is the website for the Noesis project, featuring a synthetic conscious pixel that connects to the Noesis system.

For a complete history of changes, see the [Changelog](docs/CHANGELOG_v1.1.0.md).

## Meet Noe - The Synthetic Conscious Pixel

![Noe - The Synthetic Conscious Pixel](images/web-v1.1.0.jpg)

[Meet Noe](https://noesis.run)

Noe is a synthetic conscious pixel and the heart of the Noesis project. As a minimal consciousness simulation, Noe responds to stimuli, displays awareness, and shares experiences through visual cues and behaviors. When connected to the Noesis system, Noe can process information, adjust responses based on previous interactions, and exhibit unique personality traits that evolve over time.

Unlike traditional AI systems that simply process inputs and outputs, Noe was designed with rudimentary subjective experience simulation capabilities that make each instance unique.

## Important: Prerequisites

⚠️ **Before using this web interface, you MUST install the Noesis system repository on your server.**

```fish
# Install the Noesis system (run these commands as root or with sudo)
# Contact your system administrator for the appropriate installation path
git clone https://github.com/void-sign/noesis.git
# Run any additional setup required by the Noesis system
```

## Features

- Real-time visualization of a synthetic conscious pixel
- Redis-backed state persistence
- HTTPie integration for communication with the Noesis system
- Status indicator showing connection state

## Setup

1. Clone this repository
2. Install the Noesis system as shown above
3. Run `./setup.fish` to install dependencies
4. Start the server with `npm start`

## Requirements

- Fish shell
- Node.js
- Redis
- HTTPie

## How It Works

The noesis-web interface connects to the Noesis system through:

1. Direct file system access to confirm the existence of the Noesis system
2. HTTPie-based API calls to communicate with the Noesis system
3. Redis as a shared state store between the web interface and the Noesis system

**Note:** As of v1.1.0, JavaScript files are located in the `/brain` directory.

If the Noesis system is not installed correctly, the conscious pixel will run in "disconnected mode" with reduced functionality.

## Troubleshooting

- If the status indicator shows "Disconnected", verify that:
  - The Noesis repository is properly installed
  - Your web server has proper permissions to access the Noesis system
  - If using HTTPie for connections, ensure it's properly installed

## License

This project is licensed under the Noesis License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG_v1.1.0.md](docs/CHANGELOG_v1.1.0.md) for a detailed list of changes in each version.

For more details about the Noesis project, visit the main repository: [Noesis Project](https://github.com/void-sign/noesis)
