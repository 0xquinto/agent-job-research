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


def validate_install(python_path: Path | None = None) -> bool:
    """Run smoke tests to verify the installation works."""
    print("\n=== Step 5: Validating installation ===\n")
    python = str(python_path) if python_path else str(ROOT / ".venv" / "bin" / "python")

    # Test import
    result = subprocess.run(
        [python, "-c", "from board_aggregator import __version__; print(__version__)"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("  FAIL: could not import board_aggregator")
        print(f"  {result.stderr.strip()}")
        return False
    print(f"  board_aggregator {result.stdout.strip()} ✓")

    # Test CLI
    board_agg = Path(python).parent / "board-aggregator"
    result = subprocess.run(
        [str(board_agg), "--list-scrapers"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("  FAIL: board-aggregator CLI not working")
        return False
    scraper_count = len([l for l in result.stdout.strip().split("\n") if l.strip().startswith("-")])
    print(f"  board-aggregator CLI ({scraper_count} scrapers) ✓")

    return True


def print_next_steps():
    """Print what the user should do next."""
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print()
    print("Next steps:")
    print()
    print("  1. Edit your skills inventory:")
    print("     skills-inventory.md")
    print()
    print("  2. Edit your resume:")
    print("     resume.md")
    print()
    print("  3. Run the pipeline:")
    print("     claude --agent lead-0")
    print()


def main():
    """Run the full setup wizard."""
    print("=" * 50)
    print("agent-job-research — Setup Wizard")
    print("=" * 50)

    check_prerequisites()
    setup_venv()
    setup_templates()
    setup_env()

    python = ROOT / ".venv" / "bin" / "python"
    if not validate_install(python):
        print("\nSetup had errors. Please check the messages above.")
        sys.exit(1)

    print_next_steps()


if __name__ == "__main__":
    main()
