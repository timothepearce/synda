#!/usr/bin/env python
"""
Test script to verify that Synda can be installed using uv.
"""
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def main():
    """Create a temporary virtual environment and install Synda using uv."""
    print("Testing Synda installation with uv...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        venv_path = temp_path / "venv"
        
        # Create a virtual environment
        print(f"Creating virtual environment at {venv_path}...")
        venv.create(venv_path, with_pip=True)
        
        # Get the path to the Python executable in the virtual environment
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            python_path = venv_path / "bin" / "python"
        
        # Install uv
        print("Installing uv...")
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "uv"],
            check=True,
        )
        
        # Install Synda in development mode
        print("Installing Synda in development mode...")
        project_dir = Path(__file__).parent.parent.absolute()
        subprocess.run(
            [str(python_path), "-m", "uv", "pip", "install", "-e", str(project_dir)],
            check=True,
        )
        
        # Test importing Synda
        print("Testing import...")
        result = subprocess.run(
            [str(python_path), "-c", "import synda; print('Synda imported successfully')"],
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            print("Success! Synda was imported successfully.")
            print(result.stdout)
        else:
            print("Error importing Synda:")
            print(result.stderr)
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())