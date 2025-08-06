import os
import subprocess

SCRIPTS_DIR = os.path.dirname(__file__) + "/.."

def test_run_script_dry_run():
    # Command to run your script with arguments
    cmd = ["python", f"{SCRIPTS_DIR}/cmm_run.py", "-i", f"{SCRIPTS_DIR}/volumes", "-c", "1"]
    
    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)

    # Check that the script exited successfully
    assert result.returncode == 0, f"Script failed with stderr:\n{result.stderr}"

    # Check that the script printed the expected output
    assert "Arguments: (1, 1, 1, True)" in result.stdout
