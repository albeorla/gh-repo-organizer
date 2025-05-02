# CLI Migration Guide

This guide helps you transition from the previous version of the GitHub Repository Organizer CLI to the new command group structure.

## Overview of Changes

The CLI has been reorganized into logical command groups to improve usability and maintainability. Key changes include:

1. Commands are now organized into groups (`repo`, `reports`, `logs`, `actions`)
2. Single entry point with command groups instead of multiple commands
3. Improved shell completion support
4. Simplified command aliases (`repo` and `ro`)

## Command Mapping

Here's how the old commands map to the new structure:

### Repository Analysis Commands

| Old Command | New Command | Description |
|------------|-------------|-------------|
| `analyze-repo` | `repo repo analyze` | Analyze repositories |
| `analyze-repo --owner` | `repo repo analyze --owner` | Analyze specific user's repos |
| `analyze-repo --single` | `repo repo analyze --single` | Analyze single repository |
| `cleanup` | `repo repo cleanup` | Clean up analysis files |
| `reset` | `repo repo reset` | Reset analysis data |

### Report Commands

| Old Command | New Command | Description |
|------------|-------------|-------------|
| `list-reports` | `repo reports list` | List available reports |
| `show-report` | `repo reports show` | Show specific report |
| `summary` | `repo reports summary` | Show analysis summary |

### Log Commands

| Old Command | New Command | Description |
|------------|-------------|-------------|
| `latest-log` | `repo logs latest` | Show latest log |
| `list-logs` | `repo logs all` | List all logs |
| `view-log` | `repo logs view` | View specific log |

### Action Commands

| Old Command | New Command | Description |
|------------|-------------|-------------|
| `list-actions` | `repo actions list` | List pending actions |
| `execute-actions` | `repo actions execute` | Execute actions |
| `dry-run` | `repo actions dry-run` | Simulate execution |

## Option Changes

Some command options have been renamed for consistency:

- `--single-repo` is now `--single`
- `--output-dir` short option changed from `-o` to `-d` (to avoid conflict with `--owner`)
- `--debug` no longer uses `-d` (to avoid conflict with `--output-dir`)

## Shell Completion

Shell completion is now easier to set up:

```bash
# Old way
repo completion --install

# New way (auto-detects shell)
repo completion install

# New way (specify shell)
repo completion install --shell bash
repo completion install --shell zsh
repo completion install --shell fish
```

## Common Workflows

### Example 1: Analyzing Your Repositories

Old way:
```bash
analyze-repo
```

New way:
```bash
repo repo analyze
# or using the shorter alias
ro repo analyze
```

### Example 2: Viewing a Report

Old way:
```bash
show-report repository-name
```

New way:
```bash
repo reports show repository-name
# or using the shorter alias
ro reports show repository-name
```

### Example 3: Executing Actions

Old way:
```bash
execute-actions --dry-run
execute-actions
```

New way:
```bash
repo actions dry-run
repo actions execute
```

## Getting Help

The new CLI structure provides improved help documentation:

```bash
# Show main help
repo --help

# Show help for a command group
repo repo --help
repo reports --help
repo logs --help
repo actions --help

# Show help for a specific command
repo repo analyze --help
repo reports show --help
```

## Troubleshooting

1. **Old Commands Not Found**
   - This is expected as old commands have been replaced
   - Use the new command structure as shown in the mapping above
   - Use command help (`--help`) to see available options

2. **Shell Completion Not Working**
   - Reinstall shell completion with: `repo completion install`
   - Make sure your shell configuration file is properly sourced
   - For manual shell setup, see the shell-specific instructions in `repo completion install --help`

3. **Command Aliases**
   - If the `ro` alias isn't working, try reinstalling the package
   - For development installs, run: `poetry install`
   - For global installs, run: `pipx install --force gh-repo-organizer`

## Need More Help?

If you encounter any issues migrating to the new CLI structure:

1. Check the command help with `--help` flag
2. Review the [README.md](../../README.md) for updated documentation
3. Open an issue on GitHub if you need further assistance 