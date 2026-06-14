# Design Requirements: AI Coding Agents in Podman

## Goal

Run coding-agent CLIs in Podman containers on Linux, with persistent storage and GitHub access.

The package should provide:

- `claude-podman`: the existing Claude Code container launcher.
- `hermes-podman`: a new Hermes container launcher that works similarly to `claude-podman`, but builds an image with the Hermes AI agent and Chromium instead of Claude Code.

---

## Shared container requirements

- Base image: `ubuntu:24.04`
- Install system packages:
  - `git`, `gh` — version control and GitHub CLI
  - `openssh-client` — SSH for GitHub push/pull
  - `tmux` — terminal multiplexer (run an agent and a shell side by side)
  - `curl`, `ca-certificates` — fetching resources over HTTPS
  - `mc`, `vim` — file management and text editing
  - `build-essential` — C/C++ compiler toolchain (needed by some npm/pip packages)
  - `python3-venv`, `python3-pip` — Python virtual environments and pip
  - `zsh` — default shell
  - `nodejs`, `npm` — Node.js runtime
- Pre-populate GitHub's SSH host keys via `ssh-keyscan` so git operations don't prompt
- Working directory: `/workspace`

---

## Claude image requirements

- Install Claude Code globally via npm: `@anthropic-ai/claude-code`
- Copy and use a Claude-specific entrypoint which starts Claude Code inside a tmux session
- Image name: `claude-code-podman`
- Entrypoint command: `tmux new-session -s claude "claude"`

---

## Hermes image requirements

- Install Chromium from Ubuntu packages.
  - Include the browser runtime dependencies needed for Chromium to start inside the container.
  - Set a default browser environment variable if Hermes needs to open OAuth/browser flows.
- Install Hermes AI agent.
  - Install `uv` and run Hermes through `uvx --from hermes-agent hermes`.
  - Make the user-local binary directory available on `PATH` in the image so `uvx` and the `hermes` wrapper are runnable by root.
  - Keep Hermes config under a mounted user directory such as `~/.hermes`.
- Copy and use a Hermes-specific entrypoint which starts Hermes inside a tmux session
- Image name: `hermes-podman`
- Entrypoint command: `tmux new-session -s hermes "hermes"`

---

## Shared CLI requirements

### Arguments

* --workspace - path to the project directory to mount as `/workspace`
* --github-key - path to ssh key to be able to push to github

### Logging

- Use Python's `logging` module
- Default log level: `INFO`
- Support `--verbose` flag to set log level to `DEBUG`
- Log key steps: path resolution, image build, git config retrieval, container launch command
- Log to stderr so it doesn't interfere with the container's interactive TUI on stdout

### Other

- All paths must be resolved to absolute paths
- Builds the Docker image before running, so it is always up to date
- Passes git author/committer name and email as environment variables, read from host's global git config
- Must be fully interactive; stdin and TTY must be properly attached

---

## Claude CLI requirements

### Command

`claude-podman`

### Arguments

* --claude-config - path to a local dir mounted as `~/.claude/` inside the container. Created automatically if it doesn't exist. A `.claude.json` file inside this dir is also mounted as `~/.claude.json` (created as empty `{}` if missing).

### Runtime behavior

- Builds the Claude image before running.
- Mounts the workspace as `/workspace`.
- Mounts the optional GitHub SSH key as `/root/.ssh/id_ed25519`.
- Mounts the Claude config directory as `/root/.claude`.
- Mounts the Claude JSON file as `/root/.claude.json`.
- Starts the Claude TUI inside tmux.

---

## Hermes CLI requirements

### Command

`hermes-podman`

### Arguments

* --hermes-config - path to a local dir mounted as `~/.hermes/` inside the container. Created automatically if it doesn't exist.

### Runtime behavior

- Builds the Hermes image before running.
- Mounts the workspace as `/workspace`.
- Mounts the optional GitHub SSH key as `/root/.ssh/id_ed25519`.
- Mounts the Hermes config directory as `/root/.hermes`.
- Preserves Hermes auth/session state between runs.
- Supports Hermes authentication through the mounted config directory. Hermes stores file-based credentials under `~/.hermes/auth.json`; this file must be treated as a secret and must not be committed.
- Starts Hermes inside tmux.
- Chromium must be available in the container for browser-based login flows and browser-capable agent workflows.
