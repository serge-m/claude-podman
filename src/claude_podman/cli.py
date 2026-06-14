#!/usr/bin/env python3

import argparse
import logging
import subprocess
import sys
from importlib.resources import as_file, files
from pathlib import Path
from typing import Sequence

CLAUDE_IMAGE_NAME = "claude-code-podman"
HERMES_IMAGE_NAME = "hermes-podman"

log = logging.getLogger(__name__)


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="{asctime}|{module:12.12s}|{lineno:4d}|{process}|{threadName}|{levelname:4.4s}|{message}",
        style="{",
        stream=sys.stderr,
    )


def get_git_config(key: str) -> str:
    log.debug("Reading git config: %s", key)
    result = subprocess.run(
        ["git", "config", "--global", key],
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    log.debug("git config %s = %s", key, value)
    return value


def add_shared_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", required=True, help="Path to project directory to mount as /workspace")
    parser.add_argument("--github-key", help="Path to SSH key for GitHub access")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")


def build_image(image_name: str, dockerfile_name: str, build_args: Sequence[str] = ()) -> None:
    pkg_files = files("claude_podman")
    with as_file(pkg_files) as build_context:
        dockerfile = Path(build_context) / dockerfile_name
        log.info("Build context: %s", build_context)
        log.info("Dockerfile:    %s", dockerfile)
        log.info("Building image %s ...", image_name)
        cmd = ["podman", "build", "-t", image_name, "-f", str(dockerfile)]
        for build_arg in build_args:
            cmd.extend(["--build-arg", build_arg])
        cmd.append(str(build_context))
        log.debug("Build command: %s", cmd)
        subprocess.run(cmd, check=True)


def shared_run_options(workspace: Path, github_key: Path | None) -> list[str]:
    git_name = get_git_config("user.name")
    git_email = get_git_config("user.email")
    log.info("Git identity: %s <%s>", git_name, git_email)

    return [
        "podman", "run",
        "--rm",
        "-it",
        "-v", f"{workspace}:/workspace:Z",
        *(["-v", f"{github_key}:/root/.ssh/id_ed25519:ro,Z"] if github_key else []),
        "-e", f"GIT_AUTHOR_NAME={git_name}",
        "-e", f"GIT_COMMITTER_NAME={git_name}",
        "-e", f"GIT_AUTHOR_EMAIL={git_email}",
        "-e", f"GIT_COMMITTER_EMAIL={git_email}",
    ]


def run_container(run_cmd: Sequence[str]) -> int:
    log.debug("Run command: %s", list(run_cmd))
    log.info("Launching container ...")
    return subprocess.run(list(run_cmd)).returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Claude Code in a Podman container")
    add_shared_args(parser)
    parser.add_argument(
        "--claude-config",
        required=True,
        help="Path to local dir mounted as ~/.claude/ in the container. Also contains .claude.json.",
    )
    args = parser.parse_args()

    configure_logging(args.verbose)
    log.info("Claude Code in Podman - by https://serge-m.github.io/")

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

    build_image(CLAUDE_IMAGE_NAME, "Dockerfile.claude")

    run_cmd = shared_run_options(workspace, github_key)
    run_cmd.extend([
        "-v", f"{claude_config}:/root/.claude:Z",
        "-v", f"{claude_json}:/root/.claude.json:Z",
        CLAUDE_IMAGE_NAME,
    ])

    sys.exit(run_container(run_cmd))


def hermes_main() -> None:
    parser = argparse.ArgumentParser(description="Run Hermes in a Podman container")
    add_shared_args(parser)
    parser.add_argument(
        "--hermes-config",
        required=True,
        help="Path to local dir mounted as ~/.hermes/ in the container.",
    )
    args = parser.parse_args()

    configure_logging(args.verbose)
    log.info("Hermes in Podman - by https://serge-m.github.io/")

    workspace = Path(args.workspace).resolve()
    github_key = Path(args.github_key).resolve() if args.github_key else None
    hermes_config = Path(args.hermes_config).resolve()

    log.info("Workspace:    %s", workspace)
    log.info("GitHub key:   %s", github_key or "(not provided)")
    log.info("Hermes config: %s -> /root/.hermes", hermes_config)

    if not hermes_config.exists():
        log.info("Creating hermes config dir: %s", hermes_config)
        hermes_config.mkdir(parents=True)

    build_image(HERMES_IMAGE_NAME, "Dockerfile.hermes")

    run_cmd = shared_run_options(workspace, github_key)
    run_cmd.extend([
        "-v", f"{hermes_config}:/root/.hermes:Z",
        "-e", "HERMES_HOME=/root/.hermes",
        "-e", "BROWSER=chromium-browser",
        "-e", "CHROME_BIN=/usr/bin/chromium-browser",
        HERMES_IMAGE_NAME,
    ])

    sys.exit(run_container(run_cmd))

if __name__ == "__main__":
    main()
