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
