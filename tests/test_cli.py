import pytest
import subprocess
import sys

def test_fixshell_success():
    result = subprocess.run(["poetry", "run", "fixshell", "echo", "hello"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "hello" in result.stdout

def test_fixshell_fail():
    result = subprocess.run(["poetry", "run", "fixshell", "ls", "non_existent"], capture_output=True, text=True)
    assert result.returncode != 0
    assert "No such file" in result.stderr

def test_dash_dash():
    result = subprocess.run(["poetry", "run", "fixshell", "--", "echo", "-n", "hi"], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout == "hi" # no newline
