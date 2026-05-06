Nos Dual Extension System
========================

The nos shell implements a dual extension system that allows for files with either `.fish` or `.nos` extensions. This system is designed to ensure compatibility with the fish shell ecosystem while allowing for independent evolution of the nos shell.

Implementation Details
---------------------

The dual extension system operates through a file extension abstraction layer that:

1. Recognizes both `.fish` and `.nos` file extensions
2. Prioritizes `.nos` files when both exist for the same command
3. Falls back to `.fish` files when no `.nos` equivalent exists
4. Uses the same parsing engine for both file types

Configuration System
-------------------

The dual extension system extends to configuration files as well:

1. Both `~/.config/fish/config.fish` and `~/.config/fish/nos_config.nos` are loaded when present
2. The `config.fish` file is loaded first, followed by `nos_config.nos`
3. This allows nos-specific configuration to override or extend fish configuration
4. System-wide configuration follows the same pattern with both `/etc/fish/config.fish` and `/etc/fish/nos_config.nos`

The embedded configuration files (`share/config.fish` and `share/nos_config.nos`) follow the same loading pattern.

Usage Guidelines
---------------

This system provides several advantages:

- **Gradual Migration**: Users can selectively override fish functionalities with nos-specific enhancements
- **Backward Compatibility**: All existing fish scripts remain functional in the nos environment
- **Forward Innovation**: New nos features can be developed without modifying fish code
- **Risk Mitigation**: If fish development were to slow down, nos could continue evolving independently

For function files, the dual extension approach allows you to:

- Create `.nos` versions of existing functions to override their behavior
- Develop new `.nos` functionality that doesn't exist in fish
- Keep existing `.fish` files as fallbacks

The dual extension system is fundamental to the nos design philosophy of preserving value while enabling innovation.

Environment Variables
-------------------

Several environment variables control the behavior of the dual extension system:

- `NOS_EXTENSIONS_ENABLED` (default: `true`): Controls whether nos-specific extensions are active
- `NOS_FISH_COMPATIBILITY` (default: `true`): Ensures compatibility with standard fish scripts
- `nos_shell_indicator` (default: `true`): When set, shows a visual indicator that nos shell is active

Licensing
--------

All components of this system, including the original fish code and the nos-specific extensions, are licensed under the GNU General Public License, version 2, as described in the main license documentation.

For more information about how the dual extension system works, please see the README.md file in the nos repository.
