# Design Requirements: Claude Code in Podman

## Goal

Run Claude Code CLI in a Podman container on Linux, with persistent storage and GitHub access.

---

## Dockerfile requirements

- Base image: `ubuntu:24.04`
- Install system packages:
  - `git`, `gh` — version control and GitHub CLI
  - `openssh-client` — SSH for GitHub push/pull
  - `tmux` — terminal multiplexer (run Claude and a shell side by side)
  - `curl`, `ca-certificates` — fetching resources over HTTPS
  - `mc`, `vim` — file management and text editing
  - `build-essential` — C/C++ compiler toolchain (needed by some npm/pip packages)
  - `python3-venv` — Python virtual environments
  - `zsh` — default shell
  - `nodejs`, `npm` — Node.js runtime (required by Claude Code)
- Install Claude Code globally via npm: `@anthropic-ai/claude-code`
- Pre-populate GitHub's SSH host keys via `ssh-keyscan` so git operations don't prompt
- Copy and use `entrypoint.sh` which starts Claude Code inside a tmux session
- Working directory: `/workspace`

---

## Script (`claude-podman.py`) requirements

### Arguments

* --workspace - path to the project directory to mount as `/workspace`
* --github-key - path to ssh key to be able to push to github
* --claude-config - path to a local dir mounted as `~/.claude/` inside the container. Created automatically if it doesn't exist. A `.claude.json` file inside this dir is also mounted as `~/.claude.json` (created as empty `{}` if missing).

### Logging

- Use Python's `logging` module
- Default log level: `INFO`
- Support `--verbose` flag to set log level to `DEBUG`
- Log key steps: path resolution, image build, git config retrieval, container launch command
- Log to stderr so it doesn't interfere with the container's interactive TUI on stdout

### Other
- All paths must be resolved to absolute paths
- Builds the Docker image before running (using `podman build`), so it is always up to date
- Passes git author/committer name and email as environment variables, read from host's global git config
- Must be fully interactive (Claude Code is a TUI — stdin and TTY must be properly attached)


