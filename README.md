# Claude Code in Podman

Run [Claude Code](https://claude.ai/claude-code) CLI inside a Podman container with GitHub access, persistent configuration, and a tmux session that lets you switch between Claude and a regular terminal.

## Why?

Claude Code runs as a full CLI agent that can read, edit, and execute code in your project. Running it inside a container provides isolation — Claude operates in a sandboxed environment rather than directly on your host system.

The container includes tmux so you can open a shell alongside Claude (e.g. to run tests, inspect files, or use git) without leaving the container.

## What's in the box

| File | Purpose |
|---|---|
| `src/claude_podman/cli.py` | CLI entry point — builds the image and launches the container |
| `src/claude_podman/Dockerfile` | Container image definition (see below for installed packages) |
| `src/claude_podman/entrypoint.sh` | Starts Claude inside a tmux session |
| `pyproject.toml` | Python package definition |
| `DESIGN.md` | Original design requirements |

## Prerequisites

- [Podman](https://podman.io/) installed
- Python 3.10+
- A Claude Code account (you'll authenticate on first run)
- An SSH key for GitHub access (optional)

## Quick start

### Run from PyPI (no clone needed)

```bash
uvx claude-podman \
    --workspace ~/my-project \
    --github-key ~/.ssh/id_ed25519 \
    --claude-config ./claude-auth
```

### Run directly from GitHub (no clone needed)

Not recommended - better check what you are running first!
```bash
uvx --from git+https://github.com/serge-m/claude-podman claude-podman \
    --workspace ~/my-project \
    --github-key ~/.ssh/id_ed25519 \
    --claude-config ./claude-auth
```

### Run from a local clone

```bash
git clone https://github.com/serge-m/claude-podman.git
cd claude-podman
uv run claude-podman \
    --workspace ~/my-project \
    --github-key ~/.ssh/id_ed25519 \
    --claude-config ./claude-auth
```

### Arguments

| Argument | Description |
|---|---|
| `--workspace` | Path to your project directory (mounted as `/workspace` in the container) |
| `--github-key` | *(optional)* Path to your SSH private key for GitHub (mounted read-only as `/root/.ssh/id_ed25519` inside the container) |
| `--claude-config` | Directory for Claude's persistent config (mounted as `~/.claude`). Created automatically if it doesn't exist. Contains auth tokens, session history, etc. |
| `--verbose` | Enable debug logging |

## Using tmux inside the container

Claude starts in a tmux session. Standard tmux keybindings apply:

| Keys | Action |
|---|---|
| `Ctrl-b c` | Open a new terminal window |
| `Ctrl-b n` / `Ctrl-b p` | Switch to next / previous window |
| `Ctrl-b d` | Detach from tmux (exits the container) |
| `Ctrl-b 0-9` | Switch to window by number |

## What's installed in the container

| Package | Why |
|---|---|
| `git`, `gh` | Version control and GitHub CLI |
| `openssh-client` | SSH for GitHub push/pull |
| `tmux` | Terminal multiplexer — run Claude and a shell side by side |
| `curl`, `ca-certificates` | Fetching resources over HTTPS |
| `mc`, `vim` | File management and text editing |
| `build-essential` | C/C++ compiler toolchain (needed by some npm/pip packages) |
| `python3-venv` | Python virtual environments |
| `zsh` | Default shell |
| `nodejs`, `npm` | Node.js runtime (required by Claude Code) |
| `@anthropic-ai/claude-code` | Claude Code CLI (installed via npm) |

GitHub's SSH host keys are pre-populated at build time via `ssh-keyscan`, so git operations won't prompt for host verification.

## How it works

1. **`claude-podman`** resolves all paths, reads your git identity from the host, extracts the bundled Dockerfile from the package, builds the container image, and runs it with the appropriate volume mounts.
2. **`entrypoint.sh`** launches Claude inside a tmux session.
3. Your workspace is bind-mounted into the container, so changes Claude makes are reflected on your host filesystem immediately.

## Persistent config

The `--claude-config` directory stores Claude's authentication and session data. Point this at the same directory across runs to avoid re-authenticating each time. A `.claude.json` file is automatically created inside it if missing.

> **Note:** The config directory contains auth credentials. Don't commit it to version control.
