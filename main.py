#!/usr/bin/env python3
"""
gpx - A lightweight pipx-like installer for GitHub repositories.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Configuration paths
GPX_HOME = Path.home() / ".local" / "share" / "gpx"
BIN_DIR = Path.home() / ".local" / "bin"

def setup_environment():
    """Ensure our target directories exist."""
    GPX_HOME.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if BIN_DIR is in PATH
    if str(BIN_DIR) not in os.environ.get("PATH", ""):
        print(f"Warning: {BIN_DIR} is not in your PATH.")
        print("Add 'export PATH=\"$HOME/.local/bin:$PATH\"' to your shell profile.")

def run_command(cmd, cwd=None):
    """Run a shell command safely."""
    try:
        subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing {' '.join(cmd)}: {e.stderr.strip()}")
        sys.exit(1)

def install(repo, executable_name=None):
    """Clone a repo and symlink its executable."""
    if "/" not in repo:
        print("Error: Repository must be in the format 'username/repo' (e.g., 'torvalds/linux')")
        sys.exit(1)

    repo_name = repo.split("/")[-1]
    target_dir = GPX_HOME / repo_name

    if target_dir.exists():
        print(f"Repository '{repo_name}' is already installed. Use 'gpx update {repo_name}' to update.")
        sys.exit(1)

    print(f"Fetching {repo} from GitHub...")
    clone_url = f"https://github.com/{repo}.git"
    run_command(["git", "clone", "--depth", "1", clone_url, str(target_dir)])

    # Determine what to link
    exec_target = target_dir / (executable_name or repo_name)
    
    # Fallbacks if the specific executable isn't found
    if not exec_target.exists():
        fallbacks = [f"{repo_name}.py", f"{repo_name}.sh", "main.py", "run.sh", "app.py"]
        for fallback in fallbacks:
            if (target_dir / fallback).exists():
                exec_target = target_dir / fallback
                break

    if exec_target.exists():
        # Ensure it is executable
        exec_target.chmod(exec_target.stat().st_mode | 0o111)
        
        symlink_path = BIN_DIR / repo_name
        if symlink_path.exists():
            symlink_path.unlink()
            
        symlink_path.symlink_to(exec_target)
        print(f"Successfully installed '{repo_name}'!")
        print(f"You can now run it globally using: {repo_name}")
    else:
        print(f"Cloned successfully to {target_dir}, but no executable found.")
        print("You can manually link an executable using the --exec flag next time.")

def remove(repo_name):
    """Remove a cloned repository and its symlink."""
    target_dir = GPX_HOME / repo_name
    symlink_path = BIN_DIR / repo_name

    if not target_dir.exists():
        print(f"Error: '{repo_name}' is not installed.")
        sys.exit(1)

    print(f"Removing '{repo_name}'...")
    shutil.rmtree(target_dir)
    
    if symlink_path.exists() and symlink_path.is_symlink():
        symlink_path.unlink()
        
    print("Done.")

def update(repo_name):
    """Pull the latest changes for an installed repository."""
    target_dir = GPX_HOME / repo_name

    if not target_dir.exists():
        print(f"Error: '{repo_name}' is not installed.")
        sys.exit(1)

    print(f"Updating '{repo_name}'...")
    run_command(["git", "pull"], cwd=target_dir)
    print("Update complete.")

def list_repos():
    """List all installed repositories."""
    if not GPX_HOME.exists() or not any(GPX_HOME.iterdir()):
        print("No repositories installed yet.")
        return

    print("Installed repositories:")
    for item in GPX_HOME.iterdir():
        if item.is_dir() and (item / ".git").exists():
            symlink_path = BIN_DIR / item.name
            linked = f"(Linked: {symlink_path})" if symlink_path.exists() else "(No global executable)"
            print(f"  - {item.name} {linked}")

def main():
    parser = argparse.ArgumentParser(description="gpx - A lightweight GitHub repo installer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Install command
    install_parser = subparsers.add_parser("install", help="Install a GitHub repository")
    install_parser.add_argument("repo", help="Repository in 'user/repo' format")
    install_parser.add_argument("--exec", help="Specific executable file to link (optional)", default=None)

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove an installed repository")
    remove_parser.add_argument("repo_name", help="Name of the repository to remove")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an installed repository")
    update_parser.add_argument("repo_name", help="Name of the repository to update")

    # List command
    subparsers.add_parser("list", help="List all installed repositories")

    args = parser.parse_args()
    setup_environment()

    if args.command == "install":
        install(args.repo, args.exec)
    elif args.command == "remove":
        remove(args.repo_name)
    elif args.command == "update":
        update(args.repo_name)
    elif args.command == "list":
        list_repos()

if __name__ == "__main__":
    main()
