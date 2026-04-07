import subprocess
import sys
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
