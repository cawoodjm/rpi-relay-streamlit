"""
This module provides pytest test cases to validate the functionality of the `install.sh` script.
It includes tests for basic execution, directory and environment setup, and systemd service
file creation during the installation process.

The script tests involve mocking inputs and simulating a Raspberry Pi environment, making the
testable parts of the installation script executable in a controlled, temporary test directory.
"""
import subprocess
import os
import shutil
import pytest
from pathlib import Path

@pytest.fixture
def temp_dir(tmp_path):
    """Provides a temporary directory for testing."""
    # Copy project files to temp directory for testing
    project_root = Path(__file__).parent.parent
    files_to_copy = ["install.sh", "relay_app.service", "requirements.txt", "Relay.sh"]
    
    for f in files_to_copy:
        shutil.copy(project_root / f, tmp_path / f)
    
    # Create a mock .env.example if needed, but install.sh doesn't seem to use it
    
    return tmp_path

def test_install_script_basic_execution(temp_dir):
    """
    Tests the install.sh script by mocking inputs.
    We mock the interactive parts using 'printf'.
    """
    script_path = temp_dir / "install.sh"
    
    # Mocking inputs for the script:
    # 1. install_apt: 'n'
    # 2. AUTH_PASS: 'testpassword'
    # 3. install_service: 'n'
    # 4. create_shortcut: 'n'
    # 5. open_browser: 'n'
    
    inputs = "n\ntestpassword\nn\nn\nn\n"
    
    # We need to simulate a Raspberry Pi environment or mock commands like dpkg, systemctl, etc.
    # For a basic test, we'll see if it runs and creates the venv and .env file.
    # Note: Running this on a non-Pi (like MacOS) might fail some checks in the script.
    
    # Create a mock dpkg and apt if they don't exist
    (temp_dir / "bin").mkdir()
    with open(temp_dir / "bin" / "dpkg", "w") as f:
        f.write("#!/bin/bash\necho 'ii python-dev-is-python3'")
    with open(temp_dir / "bin" / "apt", "w") as f:
        f.write("#!/bin/bash\nexit 0")
    with open(temp_dir / "bin" / "systemctl", "w") as f:
        f.write("#!/bin/bash\nexit 0")
    with open(temp_dir / "bin" / "hostname", "w") as f:
        f.write("#!/bin/bash\necho '127.0.0.1'")
    
    os.chmod(temp_dir / "bin" / "dpkg", 0o755)
    os.chmod(temp_dir / "bin" / "apt", 0o755)
    os.chmod(temp_dir / "bin" / "systemctl", 0o755)
    os.chmod(temp_dir / "bin" / "hostname", 0o755)

    env = os.environ.copy()
    env["PATH"] = str(temp_dir / "bin") + ":" + env["PATH"]
    
    result = subprocess.run(
        ["bash", "install.sh"],
        input=inputs,
        capture_output=True,
        text=True,
        cwd=temp_dir,
        env=env
    )
    
    assert result.returncode == 0
    assert (temp_dir / "venv").exists()
    assert (temp_dir / ".env").exists()
    
    with open(temp_dir / ".env", "r") as f:
        content = f.read()
        assert "AUTH_PASSWORD=testpassword" in content

    # Check if Relay.sh became executable
    assert os.access(temp_dir / "Relay.sh", os.X_OK)

def test_install_script_service_creation(temp_dir):
    """Tests if the systemd service file is correctly generated."""
    # Mocking inputs:
    # 1. install_apt: 'n'
    # 2. AUTH_PASS: 'testpassword'
    # 3. install_service: 'y'
    # 4. create_shortcut: 'n'
    # 5. open_browser: 'n'
    inputs = "n\ntestpassword\ny\nn\nn\n"
    
    (temp_dir / "bin").mkdir(exist_ok=True)
    with open(temp_dir / "bin" / "dpkg", "w") as f: f.write("#!/bin/bash\necho 'ii python-dev-is-python3'")
    with open(temp_dir / "bin" / "apt", "w") as f: f.write("#!/bin/bash\nexit 0")
    # Mock sudo to just copy locally instead of to /etc
    with open(temp_dir / "bin" / "sudo", "w") as f:
        f.write("#!/bin/bash\nif [ \"$1\" == \"cp\" ]; then cp \"$2\" \"$3\"; else exit 0; fi")
    with open(temp_dir / "bin" / "systemctl", "w") as f: f.write("#!/bin/bash\nexit 0")
    with open(temp_dir / "bin" / "hostname", "w") as f: f.write("#!/bin/bash\necho '127.0.0.1'")
    
    for cmd in ["dpkg", "apt", "sudo", "systemctl", "hostname"]:
        os.chmod(temp_dir / "bin" / cmd, 0o755)

    env = os.environ.copy()
    env["PATH"] = str(temp_dir / "bin") + ":" + env["PATH"]
    
    # Create the directory where the service would be copied
    os.makedirs(temp_dir / "etc/systemd/system", exist_ok=True)
    
    # We need to trick the script into thinking it's copying to /etc/systemd/system
    # The script uses: sudo cp temp_relay_app.service /etc/systemd/system/relay_app.service
    # Since we mocked sudo, it will try to copy to /etc/systemd/system/relay_app.service
    # on the REAL system unless we change the script or mock the whole root.
    # Actually, our mock sudo handles it if we are careful.
    
    # Let's modify the script slightly in the temp_dir to use a local etc
    with open(temp_dir / "install.sh", "r") as f:
        content = f.read()
    content = content.replace("/etc/systemd/system/", str(temp_dir) + "/etc/systemd/system/")
    with open(temp_dir / "install.sh", "w") as f:
        f.write(content)

    result = subprocess.run(
        ["bash", "install.sh"],
        input=inputs,
        capture_output=True,
        text=True,
        cwd=temp_dir,
        env=env
    )
    
    assert result.returncode == 0
    service_file = temp_dir / "etc/systemd/system/relay_app.service"
    assert service_file.exists()
    with open(service_file, "r") as f:
        content = f.read()
        # In the test environment, whoami might return something else than what we expect
        # Let's check what result.stdout says about whoami if we had it, or just use the same logic as the script.
        expected_user = subprocess.run(["whoami"], capture_output=True, text=True).stdout.strip()
        assert f"User={expected_user}" in content
        assert f"WorkingDirectory={temp_dir}" in content
