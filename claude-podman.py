#!/usr/bin/env python3

import argparse
import logging
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
IMAGE_NAME = "claude-code-podman"

log = logging.getLogger(__name__)


def get_git_config(key: str) -> str:
    log.debug("Reading git config: %s", key)
    result = subprocess.run(
        ["git", "config", "--global", key],
        capture_output=True, text=True
    )
    value = result.stdout.strip()
    log.debug("git config %s = %s", key, value)
    return value


def main():
    parser = argparse.ArgumentParser(description="Run Claude Code in a Podman container")
    parser.add_argument("--workspace", required=True, help="Path to project directory to mount as /workspace")
    parser.add_argument("--github-key", help="Path to SSH key for GitHub access")
    parser.add_argument("--claude-config", required=True, help="Path to local dir mounted as ~/.claude/ in the container. Also contains .claude.json.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    workspace = Path(args.workspace).resolve()
    github_key = Path(args.github_key).resolve() if args.github_key else None
    claude_config = Path(args.claude_config).resolve()
    claude_json = claude_config / ".claude.json"
    log.info("Workspace:     %s", workspace)
    log.info("GitHub key:    %s", github_key or "(not provided)")
    log.info("Claude config: %s -> /root/.claude", claude_config)
    log.info("Claude json:   %s -> /root/.claude.json", claude_json)

    if not claude_config.exists():
        log.info("Creating claude config dir: %s", claude_config)
        claude_config.mkdir(parents=True)

    if not claude_json.exists():
        log.info("Creating empty %s", claude_json)
        claude_json.write_text("{}\n")

    log.info("Building image %s ...", IMAGE_NAME)
    subprocess.run(
        ["podman", "build", "-t", IMAGE_NAME, str(SCRIPT_DIR)],
        check=True,
    )

    git_name = get_git_config("user.name")
    git_email = get_git_config("user.email")
    log.info("Git identity: %s <%s>", git_name, git_email)

    run_cmd = [
        "podman", "run",
        "--rm",
        "-it",
        "-v", f"{workspace}:/workspace:Z",
        *(["-v", f"{github_key}:/root/.ssh/id_ed25519:ro,Z"] if github_key else []),
        "-v", f"{claude_config}:/root/.claude:Z",
        "-v", f"{claude_json}:/root/.claude.json:Z",
        "-e", f"GIT_AUTHOR_NAME={git_name}",
        "-e", f"GIT_COMMITTER_NAME={git_name}",
        "-e", f"GIT_AUTHOR_EMAIL={git_email}",
        "-e", f"GIT_COMMITTER_EMAIL={git_email}",
        IMAGE_NAME,
    ]

    log.debug("Run command: %s", run_cmd)
    log.info("Launching container ...")
    sys.exit(subprocess.run(run_cmd).returncode)


if __name__ == "__main__":
    main()
