#!/usr/bin/env python3
"""Guided setup wizard for the agent-job-research pipeline.

Run: python setup_wizard.py

This script uses only the standard library so it works before
the virtual environment exists.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check_python_version():
    """Exit if Python < 3.12."""
    if sys.version_info < (3, 12):
        print(f"ERROR: Python >= 3.12 required (found {sys.version})")
        sys.exit(1)
    print(f"  Python {sys.version_info.major}.{sys.version_info.minor} ✓")


def check_command_exists(cmd: str) -> bool:
    """Return True if cmd is found on PATH."""
    return shutil.which(cmd) is not None


def check_prerequisites():
    """Check all required tools are available."""
    print("\n=== Step 1: Checking prerequisites ===\n")
    check_python_version()

    if check_command_exists("claude"):
        print("  Claude CLI ✓")
    else:
        print("  Claude CLI not found — install from https://claude.ai/download")
        print("  (The scraper works without it, but the pipeline requires it)")

    if check_command_exists("git"):
        print("  git ✓")
    else:
        print("ERROR: git is required")
        sys.exit(1)


def copy_template(src: Path, dest: Path) -> bool:
    """Copy src to dest if dest doesn't exist. Returns True if copied."""
    if dest.exists():
        print(f"  {dest.name} already exists — skipping")
        return False
    shutil.copy2(src, dest)
    print(f"  Created {dest.name} from template")
    return True


def write_env_file(env_path: Path, exa_key: str = "") -> None:
    """Write .env file with API keys. Skips if file exists."""
    if env_path.exists():
        print("  .env already exists — skipping")
        return
    env_path.write_text(
        f"# API keys for agent-job-research pipeline\n"
        f"EXA_API_KEY={exa_key}\n"
    )
    print("  Created .env")


def setup_venv():
    """Create virtual environment and install the package."""
    print("\n=== Step 2: Setting up virtual environment ===\n")
    venv_dir = ROOT / ".venv"
    if venv_dir.exists():
        print("  .venv already exists — skipping creation")
    else:
        print("  Creating .venv ...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print("  .venv created ✓")

    pip = venv_dir / "bin" / "pip"
    print("  Installing board-aggregator + dev deps ...")
    subprocess.run(
        [str(pip), "install", "-e", ".[dev]"],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
    )
    print("  Installed ✓")


def setup_templates():
    """Copy template files for user customization."""
    print("\n=== Step 3: Setting up your profile ===\n")
    templates = ROOT / "templates"

    skills_copied = copy_template(
        templates / "skills-inventory.example.md",
        ROOT / "skills-inventory.md",
    )
    resume_copied = copy_template(
        templates / "resume.example.md",
        ROOT / "resume.md",
    )

    editor = os.environ.get("EDITOR")
    files_to_edit = []
    if skills_copied:
        files_to_edit.append(ROOT / "skills-inventory.md")
    if resume_copied:
        files_to_edit.append(ROOT / "resume.md")

    if files_to_edit and editor:
        for f in files_to_edit:
            print(f"\n  Opening {f.name} in {editor} ...")
            subprocess.run([editor, str(f)])
    elif files_to_edit:
        print("\n  Please edit these files with your information:")
        for f in files_to_edit:
            print(f"    - {f}")


def setup_env():
    """Prompt for API keys and write .env."""
    print("\n=== Step 4: API keys ===\n")
    env_path = ROOT / ".env"
    if env_path.exists():
        print("  .env already exists — skipping")
        return

    print("  Exa API key is required for Phase 3 (contact research).")
    print("  Get one at https://exa.ai")
    exa_key = input("  Exa API key (Enter to skip): ").strip()
    write_env_file(env_path, exa_key=exa_key)
