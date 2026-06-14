# AI Coding Agents in Podman

Run coding-agent CLIs inside Podman containers with GitHub access, persistent configuration, and a tmux session that lets you switch between the agent and a regular terminal.

The package currently provides:

- `claude-podman` for [Claude Code](https://claude.ai/claude-code).
- `hermes-podman` for the Hermes AI agent and Chromium.

## Why?

Coding agents run as full CLI agents that can read, edit, and execute code in your project. Running them inside containers provides isolation: the agent operates in a sandboxed environment rather than directly on your host system.

Each container includes tmux so you can open a shell alongside the agent, for example to run tests, inspect files, or use git without leaving the container.

## What's in the box

| File | Purpose |
|---|---|
| `src/claude_podman/cli.py` | CLI entry points — build images and launch containers |
| `src/claude_podman/Dockerfile.claude` | Claude Code container image definition |
| `src/claude_podman/Dockerfile.hermes` | Hermes and Chromium container image definition |
| `src/claude_podman/entrypoint-claude.sh` | Starts Claude inside a tmux session |
| `src/claude_podman/entrypoint-hermes.sh` | Starts Hermes inside a tmux session |
| `pyproject.toml` | Python package definition |
| `DESIGN.md` | Original design requirements |

## Prerequisites

- [Podman](https://podman.io/) installed
- Python 3.10+
- A Claude Code account for `claude-podman`, or Hermes access for `hermes-podman`
- An SSH key for GitHub access (optional)

## Quick start

### Run Claude from PyPI (no clone needed)

```bash
uvx claude-podman \
    --workspace ~/my-project \
    --github-key ~/.ssh/id_ed25519 \
    --claude-config ./claude-auth
```

### Run Hermes from PyPI (no clone needed)

```bash
uvx --from claude-podman hermes-podman \
    --workspace ~/my-project \
    --github-key ~/.ssh/id_ed25519 \
    --hermes-config ./hermes-auth
```

### Run directly from GitHub (no clone needed)

Not recommended - better check what you are running first!
```bash
uvx --from git+https://github.com/serge-m/claude-podman claude-podman \
    --workspace ~/my-project \
    --github-key ~/.ssh/id_ed25519 \
    --claude-config ./claude-auth
```

### Run Hermes directly from GitHub (no clone needed)

```bash
uvx --from git+https://github.com/serge-m/claude-podman hermes-podman \
    --workspace ~/my-project \
    --github-key ~/.ssh/id_ed25519 \
    --hermes-config ./hermes-auth
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

For Hermes from a local clone:

```bash
uv run hermes-podman \
    --workspace ~/my-project \
    --github-key ~/.ssh/id_ed25519 \
    --hermes-config ./hermes-auth
```

### Arguments

| Argument | Description |
|---|---|
| `--workspace` | Path to your project directory (mounted as `/workspace` in the container) |
| `--github-key` | *(optional)* Path to your SSH private key for GitHub (mounted read-only as `/root/.ssh/id_ed25519` inside the container) |
| `--claude-config` | Directory for Claude's persistent config (mounted as `~/.claude`). Created automatically if it doesn't exist. Contains auth tokens, session history, etc. |
| `--hermes-config` | Directory for Hermes persistent config (mounted as `~/.hermes`). Created automatically if it doesn't exist. Contains auth tokens, session history, etc. |
| `--verbose` | Enable debug logging |

## Using tmux inside the container

The selected agent starts in a tmux session. Standard tmux keybindings apply:

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
| `tmux` | Terminal multiplexer — run an agent and a shell side by side |
| `curl`, `ca-certificates` | Fetching resources over HTTPS |
| `mc`, `vim` | File management and text editing |
| `build-essential` | C/C++ compiler toolchain (needed by some npm/pip packages) |
| `python3-venv` | Python virtual environments |
| `zsh` | Default shell |
| `nodejs`, `npm` | Node.js runtime |
| `chromium-browser` | Browser package for Hermes browser flows in the Hermes image |
| `uv` | Provides `uvx` for running Hermes without system Python packaging |
| `@anthropic-ai/claude-code` | Claude Code CLI in the Claude image |
| Hermes AI agent | Run in the Hermes image with `uvx --from hermes-agent hermes` |

GitHub's SSH host keys are pre-populated at build time via `ssh-keyscan`, so git operations won't prompt for host verification.

## How it works

1. **`claude-podman`** and **`hermes-podman`** resolve all paths, read your git identity from the host, select the bundled Dockerfile, build the container image, and run it with the appropriate volume mounts.
2. The selected entrypoint launches Claude or Hermes inside a tmux session.
3. Your workspace is bind-mounted into the container, so changes the agent makes are reflected on your host filesystem immediately.

## Persistent config

The `--claude-config` directory stores Claude's authentication and session data. Point this at the same directory across runs to avoid re-authenticating each time. A `.claude.json` file is automatically created inside it if missing.

The `--hermes-config` directory stores Hermes authentication and session data under `~/.hermes` in the container. Hermes file-based credentials may include `auth.json`.

> **Note:** Agent config directories contain auth credentials. Don't commit them to version control.
