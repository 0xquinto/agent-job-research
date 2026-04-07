import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def test_check_python_version_passes():
    """Current Python should pass the >=3.12 check."""
    from setup_wizard import check_python_version

    # Should not raise
    check_python_version()


def test_check_python_version_fails_on_old():
    """Python <3.12 should fail."""
    from setup_wizard import check_python_version

    with patch.object(sys, "version_info", (3, 11, 0)):
        with pytest.raises(SystemExit):
            check_python_version()


def test_check_command_exists_finds_python():
    """python3 should be found on PATH."""
    from setup_wizard import check_command_exists

    assert check_command_exists("python3") is True


def test_check_command_exists_missing():
    """A nonsense command should not be found."""
    from setup_wizard import check_command_exists

    assert check_command_exists("definitely_not_a_real_command_xyz") is False


def test_copy_template_creates_file(tmp_path):
    """copy_template should copy a source file to dest if dest doesn't exist."""
    from setup_wizard import copy_template

    src = tmp_path / "template.md"
    src.write_text("# Template\n")
    dest = tmp_path / "output.md"

    result = copy_template(src, dest)
    assert result is True
    assert dest.read_text() == "# Template\n"


def test_copy_template_skips_existing(tmp_path):
    """copy_template should not overwrite an existing file."""
    from setup_wizard import copy_template

    src = tmp_path / "template.md"
    src.write_text("# Template\n")
    dest = tmp_path / "output.md"
    dest.write_text("# My custom content\n")

    result = copy_template(src, dest)
    assert result is False
    assert dest.read_text() == "# My custom content\n"


def test_exa_mcp_exists_detects_server():
    """exa_mcp_exists returns True when 'exa:' appears in mcp list output."""
    from setup_wizard import exa_mcp_exists

    fake_output = "exa: https://mcp.exa.ai/mcp?exaApiKey=xxx (HTTP) - Connected\n"
    with patch("setup_wizard.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=fake_output, stderr=""
        )
        assert exa_mcp_exists() is True


def test_exa_mcp_exists_returns_false_when_missing():
    """exa_mcp_exists returns False when no exa server is listed."""
    from setup_wizard import exa_mcp_exists

    fake_output = "slither: /usr/local/bin/slither-mcp - Connected\n"
    with patch("setup_wizard.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=fake_output, stderr=""
        )
        assert exa_mcp_exists() is False


def test_validate_install_success():
    """validate_install should return True using the current interpreter."""
    from setup_wizard import validate_install

    # sys.executable is the Python running this test suite — board_aggregator
    # is installed in that environment, so this always runs without skipping.
    assert validate_install(Path(sys.executable)) is True
