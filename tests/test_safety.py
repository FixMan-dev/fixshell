from fixshell.safety import validate_commands

def test_safety_safe():
    cmds = ["ls -l", "chmod +x script.sh", "systemctl status nginx"]
    validated = validate_commands(cmds)
    for cmd, is_safe, warning in validated:
        assert is_safe
        assert warning == ""

def test_safety_dangerous():
    dangerous = ["rm -rf /", "chmod 777 /", "mkfs.ext4 /dev/sda1", "shutdown now"]
    validated = validate_commands(dangerous)
    for cmd, is_safe, warning in validated:
        assert not is_safe
        assert "DANGEROUS" in warning

def test_safety_mixed():
    cmds = ["ls", "rm -rf /"]
    validated = validate_commands(cmds)
    assert validated[0][1] is True
    assert validated[1][1] is False
