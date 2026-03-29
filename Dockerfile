FROM ubuntu:24.04

# System packages:
#   git, gh          - version control and GitHub CLI
#   openssh-client   - SSH for GitHub push/pull
#   tmux             - terminal multiplexer (run Claude + shell side by side)
#   curl, ca-certs   - fetching resources over HTTPS
#   mc, vim          - file management and text editing
#   build-essential  - C/C++ compiler toolchain (needed by some npm/pip packages)
#   python3-venv     - Python virtual environments
#   zsh              - shell
#   nodejs, npm      - Node.js runtime (required by Claude Code)
RUN apt-get update && \
    apt-get install -y \
        git gh openssh-client tmux \
        curl ca-certificates \
        mc vim build-essential python3-venv \
        zsh nodejs npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set zsh as default shell
RUN chsh -s /usr/bin/zsh

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Pre-populate GitHub's SSH host keys so git operations don't prompt
RUN mkdir -p /root/.ssh && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts 2>/dev/null && \
    chmod 600 /root/.ssh/known_hosts

# Entrypoint launches Claude inside a tmux session
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /workspace

ENTRYPOINT ["/entrypoint.sh"]
