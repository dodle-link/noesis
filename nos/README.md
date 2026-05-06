# Noesis Open Shell v1.0.0

NOS is a fork of the [fish shell](https://fishshell.com/) that provides all the features you love about fish while allowing for innovation and experimentation beyond the original codebase.

> **Dependency Risk Mitigation**: Nos is designed to maintain compatibility with fish while reducing the dependency risk if fish development were to slow down or stop. Our dual extension system allows for independent evolution while preserving interoperability.

## Key Features

- **Full fish compatibility** - All your existing fish scripts, completions, and configurations continue to work in nos
- **Extension independence** - Introduce new features and syntax without breaking compatibility
- **Upstream synchronization** - Easily integrate upstream fish shell improvements

## Dual Extension System

The core innovation in nos is the dual extension system that allows for a seamless compatibility layer:

### How It Works

- Files can have either `.fish` or `.nos` extensions
- When nos looks for a function, completion, or configuration file:
  1. It first looks for a `.nos` file
  2. If no `.nos` file exists, it falls back to the `.fish` file

This approach lets you:
- Keep using all existing fish shell resources
- Gradually migrate to nos-specific features at your own pace
- Create nos-specific implementations without modifying fish functionality

```
functions/
├── git.fish    # Original fish function
└── git.nos     # Enhanced nos version (takes precedence)
```

### Configuration Files

The dual extension system extends to configuration files:

- Both `~/.config/fish/config.fish` and `~/.config/fish/nos_config.nos` are loaded when present
- The files are loaded in this order:
  1. System config.fish
  2. System nos_config.nos
  3. User config.fish
  4. User nos_config.nos

This allows nos-specific configuration to override or extend fish configuration without breaking compatibility.

```
~/.config/fish/
├── config.fish     # Standard fish configuration
└── nos_config.nos  # Nos-specific overrides and extensions
```

## Why Fork?

This fork allows us to:

1. **Evolve independently** - Introduce new features without being constrained by fish's compatibility requirements
2. **Mitigate dependency risks** - If fish development were to slow down or stop, nos can continue evolving
3. **Maintain compatibility** - Your investment in fish scripts and knowledge isn't lost
4. **Experiment freely** - Test new ideas without the constraints of the fish codebase

## Getting Started

### Installation

```fish
git clone https://github.com/yourusername/nos.git
cd nos
make
sudo make install
```

### Using .nos Files

1. Create a `.nos` file in the same location as the `.fish` file you want to override
2. The nos shell will automatically use your `.nos` file instead of the `.fish` file

### Migration Example

To migrate a fish function to nos:

```fish
# Original: ~/.config/fish/functions/prompt_git.fish
function prompt_git
    echo "Fish git prompt"
end

# Enhanced: ~/.config/fish/functions/prompt_git.nos  
function prompt_git
    echo "Enhanced nos git prompt with more features"
end
```

## How the Compatibility Layer Works

Under the hood, nos implements a file extension abstraction layer that recognizes both `.fish` and `.nos` files:

### Implementation Details

1. **File Extension Handler**: A dedicated module (`file_extension_handler.rs`) handles file extension abstraction
2. **Priority Loading**: When looking for a file, nos first tries the `.nos` extension, then falls back to `.fish`
3. **Shared Parsing**: Both file types are parsed with the same engine, ensuring compatibility
4. **Runtime Detection**: Functions can detect if they're running under nos to enable enhanced features

```rust
// Simplified example of the file extension handler
pub enum ShellExtension {
    Fish,
    Nos,
}

// Try to locate a file with any of the supported extensions
pub fn find_file_with_any_extension(base_path: &wstr, file_name: &wstr) -> Option<(WString, FileId)> {
    // First try .nos extension
    // Then fall back to .fish extension
    // Return the first file found
}
```

## Updating from Upstream

One of the key advantages of our approach is the ability to easily integrate upstream fish shell changes:

### Merge Process

1. **Fetch upstream changes**: 
   ```fish
   git remote add upstream https://github.com/fish-shell/fish-shell.git
   git fetch upstream
   ```

2. **Merge into nos**:
   ```fish
   git checkout main
   git merge upstream/master
   ```

3. **Resolve conflicts**: The file extension abstraction layer is designed to minimize conflicts with upstream changes

4. **Test compatibility**: Run the test suite to ensure both `.fish` and `.nos` files work correctly

### Repository Structure

The nos repository maintains:
1. Original fish shell code
2. Compatibility layer components
3. Nos-specific enhancements

This structure ensures that fish's core functionality remains intact while allowing nos to evolve independently.

## Advanced Features

### Nos Configuration

The `nos_config.nos` file provides nos-specific configuration options while maintaining compatibility with fish:

```fish
# Enable nos-specific features
set -g NOS_EXTENSIONS_ENABLED true

# Show [nos] in the prompt 
set -g nos_shell_indicator true
```

### Extension Scripts

You can create nos-specific extensions in the `~/.config/fish/nos/` directory:

```
~/.config/fish/
├── config.fish       # Standard fish config (loaded by both fish and nos)
├── functions/        # Standard fish functions
└── nos/              # Nos-specific directory
    ├── config.nos    # Nos-specific config
    └── functions/    # Nos-specific functions
```

### Runtime Detection

Your scripts can detect if they're running under nos or fish:

```fish
if set -q NOS_VERSION
    # Nos-specific code
else
    # Regular fish code
end
```

## Contributing

Contributions to nos are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

nos is licensed under the same terms as fish shell. See [COPYING](COPYING) for details.

## Design Philosophy & Long-term Vision

Nos follows several key design principles:

1. **Preservation of Value**: We respect the immense value in fish's existing ecosystem of scripts, completions, and configurations. The compatibility layer ensures this value is preserved.

2. **Progressive Enhancement**: Rather than forcing adoption of new features, nos allows users to enhance their shell experience gradually and selectively.

3. **Sustainable Evolution**: The dual extension system creates a path for sustainable long-term development, regardless of upstream changes.

4. **Community Continuity**: By maintaining compatibility, we provide a smooth transition path that doesn't fragment the fish user community.

### Future Roadmap

- **Enhanced Runtime Features**: Expand nos-specific scripting capabilities while maintaining fish compatibility
- **Performance Optimizations**: Introduce nos-specific performance enhancements
- **Modern Shell Paradigms**: Experiment with new shell paradigms that might be too disruptive for the fish project
- **Specialized Use Cases**: Support specialized use cases that may not align with fish's general-purpose nature

Our long-term vision is to provide a shell that both preserves the user experience that made fish popular while creating space for innovation that might otherwise never happen.

## Acknowledgments

- The fish shell team for creating the amazing foundation that nos builds upon
- All contributors to nos and the fish shell
- The broader shell community for ongoing inspiration
