import os
import subprocess
import pytest

def run_fixshell(cmd_args):
    """Helper to run fixshell via poetry."""
    full_cmd = ["poetry", "run", "fixshell"] + cmd_args
    return subprocess.run(full_cmd, capture_output=True, text=True)

def test_scenario_permission_denied():
    # ls /root normally fails on these systems
    result = run_fixshell(["ls", "/root"])
    assert result.returncode == 2
    assert "FIXSHELL DIAGNOSIS" in result.stdout
    assert "Permission" in result.stdout

def test_scenario_command_not_found():
    result = run_fixshell(["nonexistentcommand12345"])
    assert result.returncode == 127
    assert "Command 'nonexistentcommand12345' not found" in result.stderr

def test_scenario_python_error():
    # Error: ModuleNotFoundError
    result = run_fixshell(["python3", "-c", "import non_existent_pkg"])
    assert result.returncode != 0
    assert "FIXSHELL DIAGNOSIS" in result.stdout
    assert "ModuleNotFoundError" in result.stdout or "module" in result.stdout.lower()

# Note: Hardware-dependent tests like Disk Full or Port Conflict 
# are better suited for mock-based unit tests than live integration 
# in this environment to avoid system side effects.
