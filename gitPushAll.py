#!/opt/homebrew/opt/python@3.12/libexec/bin/python3
# =============================================================================
# Filename: gitPushAll.py
# Project: Git Push All
# Version: 2.02
# Last Modified Date: 2026-07-06
# Category: Tool
# OS: Mac/Linux
# Maintainer: Cloud Box 9
# -----------------------------------------------------------------------------
# Description:
#   Batch commit and push tool for multiple Git repositories.
#
#   Features:
#     • Auto-discover Git repositories in configured directories
#     • Display ALL repos with color-coded status (yellow=changes, white=clean)
#     • Check all repos for uncommitted changes
#     • Batch commit and push multiple repos
#     • Preview changes before committing
#     • Automatic timestamped commit messages
#     • Custom commit message support
#     • Dry-run mode
#     • Detailed logging
#     • Single-line menu navigation
#
# Version History:
#   v2.02 (2026-07-06):
#     • Added [M] Monitor menu option: live-refreshes the repository status
#       table every 60s (config: monitor_interval) with a countdown; pressing
#       any key exits the loop and returns to the menu (_read_key_timeout()).
#     • Main menu now stays open even when all repos are clean, so Monitor is
#       reachable anytime; [A]/[V] report "nothing to do" when there are no
#       changes instead of the script exiting.
#   v2.01 (2026-07-05):
#     • Repo tables (display_all_repos, display_repos_summary) now show a
#       "Folder" column immediately after "Branch" with the repo's local path
#       (home abbreviated to ~ via new short_path() helper)
#   v2.0 (2026-07-05):
#     • After choosing [A] Commit & Push All, prompt for how to enter commit
#       messages: 1) Continue With Generated Message, 2) Enter One Message for
#       All Repos, 3) Enter Individual Messages for Each Repo
#     • commit_all_repos() now builds a per-repo message map and commits each
#       repo with its own message (option 3) or a shared one (options 1/2)
#   v1.9 (2026-04-05):
#     • find_git_repos(): deduplicate results using os.path.realpath so a repo
#       appearing under multiple scan_directories is only counted once
#   v1.8 (2026-03-22):
#     • Added --auto "message" CLI argument for non-interactive mode
#     • auto_push_all(): scans repos, commits+pushes all with changes using
#       the supplied message, prints minimal status, returns exit code
#     • Called by backup42 (and other scripts) with --auto "Backup42"
#   v1.7 (2026-03-22):
#     • Added [L] Log menu item: opens the log file (LOG_FILE) in the default
#       editor; shows error message if file not found
#   v1.6 (2026-03-19):
#     • Moved successAudio and failureAudio paths into gitPushAll_config.json
#     • Script reads sound paths from config; get_project_sound() falls back to
#       config values instead of hardcoded constants
#   v1.5 (2026-03-17):
#     • Integrated Script Sound User Preferences: get_project_sound() checks
#       ~/userProfile.json projectPreferences for successAudio/failureAudio
#       overrides before falling back to the local audio/ defaults
#     • Removed local play_sound(); now uses CB9Lib version
#   v1.4 (2026-03-17):
#     • Added play_sound() helper using afplay (non-blocking subprocess)
#     • Plays success sound (Radar-ping) when all repos push successfully
#     • Plays failure sound (bad-file.wav) when any repo fails
#     • Audio files stored in local audio/ subfolder
#   v1.3 (2026-01-04):
#     • Simplified commit message prompt to single input field
#     • Changed from numbered menu to direct input with Enter for auto-timestamp
#     • Prompt: "Enter a Custom Message or Press Enter: "
#   v1.2 (2025-11-05):
#     • Show all repos in table format (not just ones with changes)
#     • Color-code repos: yellow for changes, white for clean
#     • Single-line menu legend format
#     • Improved CB9Lib integration
#   v1.1 (2025-10-29):
#     • Enhanced menu system with single-keypress navigation
#   v1.0 (2025-10-29):
#     • Initial release
#
# Usage:
#   python3 gitPushAll.py
#
# Notes:
#   • Configuration stored in gitPushAll_config.json
#   • Logs stored in ~/Documents/log/
#   • Follows git best practices (no force push, hooks enabled)
# =============================================================================

import os
import sys
import json
import subprocess
import shutil
import time
from datetime import datetime
from pathlib import Path

# Unix single-keypress support (for Monitor mode). Mac/Linux only.
try:
    import select
    import termios
    import tty
    _RAWKEY_OK = True
except ImportError:
    _RAWKEY_OK = False

# CB9Lib imports
from CB9Lib.colors import (
    color_text, RED, GREEN, YELLOW, BLUE, CYAN, MAGENTA, WHITE,
    BRIGHT_RED, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_BLUE,
    BRIGHT_CYAN, BRIGHT_MAGENTA, BRIGHT_WHITE,
    BOLD, DIM, ITALIC, UNDERLINE, RESET
)
from CB9Lib.func import (
    clear_screen, pause, file_exists, folder_exists, ensure_folder,
    write_log, log_header, log_footer, load_json_config, save_json_config,
    header, footerMenu, menu, select_list, confirm, print_table, print_dict_table,
    get_project_sound, play_sound,
)
from CB9Lib.globals import LOG_DIR


# -----------------------------------------------------------------------------
# Global Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "Git Push All"
VERSION = "v2.02"
CONFIG_FILE = None
LOG_FILE = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Default sound fallbacks (used only if not specified in config)
_DEFAULT_SOUND_SUCCESS = os.path.join(SCRIPT_DIR, "audio", "Radar-ping-sound-effect.mp3")
_DEFAULT_SOUND_FAILURE = os.path.join(SCRIPT_DIR, "audio", "tunetank.com_bad-file.wav")


# -----------------------------------------------------------------------------
# Configuration Management
# -----------------------------------------------------------------------------

def find_config_file():
    """
    Search for configuration file in multiple locations.

    Search order:
    1. Script's directory
    2. ~/Documents/script
    3. Home directory

    Returns:
        str: Path to config file
    """
    config_filename = "gitPushAll_config.json"

    # Get script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    search_paths = [
        os.path.join(script_dir, config_filename),
        os.path.expanduser(f"~/Documents/script/gitPushAll/{config_filename}"),
        os.path.expanduser(f"~/{config_filename}")
    ]

    # Check if config exists in any location
    for config_path in search_paths:
        if os.path.exists(config_path):
            return config_path

    # Config file not found - create default in script's directory
    default_path = search_paths[0]
    config_dir = os.path.dirname(default_path)
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)

    print(color_text(f"Config not found. Creating default at: {default_path}", YELLOW))
    return default_path


def create_default_config():
    """
    Create default configuration file.
    """
    default_config = {
        "_metadata": {
            "project": "Git Push All",
            "version": "1.0",
            "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
            "description": "Batch Git commit and push configuration"
        },
        "scan_directories": [
            "~/Documents/script",
            "~/Documents/sites"
        ],
        "excluded_repos": [],
        "default_commit_message": "Auto-commit: {timestamp}",
        "auto_push": True,
        "dry_run_first": False,
        "monitor_interval": 60
    }

    save_json_config(CONFIG_FILE, default_config)
    return default_config


def load_config():
    """
    Load configuration from JSON file.

    Returns:
        dict: Configuration data
    """
    global CONFIG_FILE

    CONFIG_FILE = find_config_file()

    if not file_exists(CONFIG_FILE):
        print(color_text("Creating default configuration...", YELLOW))
        return create_default_config()

    return load_json_config(CONFIG_FILE)


# -----------------------------------------------------------------------------
# Git Repository Discovery
# -----------------------------------------------------------------------------

def find_git_repos(scan_dirs):
    """
    Find all Git repositories in specified directories.

    Args:
        scan_dirs: List of directories to scan

    Returns:
        list: List of repository paths
    """
    repos = []
    seen = set()  # canonical real paths — prevents duplicates when scan dirs overlap

    for scan_dir in scan_dirs:
        scan_path = os.path.expanduser(scan_dir)

        if not os.path.exists(scan_path):
            write_log(f"Scan directory not found: {scan_path}", LOG_FILE)
            continue

        # Check if scan_dir itself is a repo
        if os.path.isdir(os.path.join(scan_path, '.git')):
            real = os.path.realpath(scan_path)
            if real not in seen:
                seen.add(real)
                repos.append(scan_path)

        # Check subdirectories
        try:
            for item in os.listdir(scan_path):
                item_path = os.path.join(scan_path, item)
                if os.path.isdir(item_path) and os.path.isdir(os.path.join(item_path, '.git')):
                    real = os.path.realpath(item_path)
                    if real not in seen:
                        seen.add(real)
                        repos.append(item_path)
        except PermissionError:
            write_log(f"Permission denied: {scan_path}", LOG_FILE)

    # Alphabetical by repository name (basename), case-insensitive
    return sorted(repos, key=lambda p: os.path.basename(p).lower())


def get_repo_status(repo_path):
    """
    Get Git status for a repository.

    Args:
        repo_path: Path to repository

    Returns:
        dict: Repository status information
    """
    try:
        # Get status
        result = subprocess.run(
            ['git', '-C', repo_path, 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=10
        )

        status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []

        # Get current branch
        branch_result = subprocess.run(
            ['git', '-C', repo_path, 'branch', '--show-current'],
            capture_output=True,
            text=True,
            timeout=10
        )
        branch = branch_result.stdout.strip()

        # Count changes
        modified = sum(1 for line in status_lines if line.startswith(' M') or line.startswith('M'))
        added = sum(1 for line in status_lines if line.startswith('A') or line.startswith('??'))
        deleted = sum(1 for line in status_lines if line.startswith(' D') or line.startswith('D'))

        has_changes = len(status_lines) > 0

        return {
            'path': repo_path,
            'name': os.path.basename(repo_path),
            'branch': branch,
            'has_changes': has_changes,
            'modified': modified,
            'added': added,
            'deleted': deleted,
            'total_changes': len(status_lines),
            'status_lines': status_lines
        }

    except subprocess.TimeoutExpired:
        write_log(f"Timeout checking status: {repo_path}", LOG_FILE)
        return None
    except Exception as e:
        write_log(f"Error checking status for {repo_path}: {e}", LOG_FILE)
        return None


# -----------------------------------------------------------------------------
# Git Operations
# -----------------------------------------------------------------------------

def commit_and_push_repo(repo_info, commit_message, dry_run=False):
    """
    Commit and push changes for a repository.

    Args:
        repo_info: Repository information dict
        commit_message: Commit message
        dry_run: If True, show what would be done

    Returns:
        dict: Results with success/error information
    """
    repo_path = repo_info['path']
    repo_name = repo_info['name']

    if dry_run:
        return {
            'success': True,
            'repo': repo_name,
            'message': 'Dry run - no changes made',
            'dry_run': True
        }

    try:
        # Add all changes
        add_result = subprocess.run(
            ['git', '-C', repo_path, 'add', '.'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if add_result.returncode != 0:
            return {
                'success': False,
                'repo': repo_name,
                'error': f"git add failed: {add_result.stderr}"
            }

        # Commit with message
        commit_result = subprocess.run(
            ['git', '-C', repo_path, 'commit', '-m', commit_message],
            capture_output=True,
            text=True,
            timeout=30
        )

        if commit_result.returncode != 0:
            return {
                'success': False,
                'repo': repo_name,
                'error': f"git commit failed: {commit_result.stderr}"
            }

        # Push to remote
        push_result = subprocess.run(
            ['git', '-C', repo_path, 'push'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if push_result.returncode != 0:
            return {
                'success': False,
                'repo': repo_name,
                'error': f"git push failed: {push_result.stderr}"
            }

        return {
            'success': True,
            'repo': repo_name,
            'message': 'Committed and pushed successfully'
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'repo': repo_name,
            'error': 'Operation timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'repo': repo_name,
            'error': str(e)
        }


# -----------------------------------------------------------------------------
# Display Functions
# -----------------------------------------------------------------------------

def short_path(path):
    """Return a repo's local folder path with the home directory abbreviated to ~."""
    home = os.path.expanduser("~")
    if path == home:
        return "~"
    if path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def display_all_repos(all_repos_status):
    """
    Display table of all repositories with color coding.
    Repos with changes shown in yellow, clean repos in white.

    Args:
        all_repos_status: List of all repo info dicts
    """
    if not all_repos_status:
        print(color_text("✓ No repositories found", YELLOW, style=BOLD))
        return

    # Count repos with changes
    repos_with_changes = [r for r in all_repos_status if r and r['has_changes']]
    clean_repos = [r for r in all_repos_status if r and not r['has_changes']]

    print(color_text(f"Found {len(all_repos_status)} repositories", BRIGHT_CYAN, style=BOLD), end='')
    if repos_with_changes:
        print(color_text(f"  •  {len(repos_with_changes)} with changes", BRIGHT_YELLOW), end='')
    if clean_repos:
        print(color_text(f"  •  {len(clean_repos)} clean", WHITE), end='')
    print("\n")

    # Print custom table with row color coding
    headers = ["#", "Repository", "Branch", "Folder", "M", "A", "D", "T"]
    align = ['center', 'left', 'left', 'left', 'center', 'center', 'center', 'center']

    # Calculate column widths
    col_widths = [len(str(h)) for h in headers]
    for repo in all_repos_status:
        if not repo:
            continue
        row_data = [
            str(all_repos_status.index(repo) + 1),
            repo['name'],
            repo['branch'],
            short_path(repo['path']),
            str(repo['modified']),
            str(repo['added']),
            str(repo['deleted']),
            str(repo['total_changes'])
        ]
        for i, cell in enumerate(row_data):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Print header
    header_parts = []
    for i, header_text in enumerate(headers):
        width = col_widths[i]
        if align[i] == 'right':
            header_parts.append(str(header_text).rjust(width))
        elif align[i] == 'center':
            header_parts.append(str(header_text).center(width))
        else:
            header_parts.append(str(header_text).ljust(width))

    separator = "─" * (sum(col_widths) + len(headers) * 3 - 1)
    print("┌" + separator + "┐")
    print("│ " + color_text(" │ ".join(header_parts), fg=CYAN, style=BOLD) + " │")
    print("├" + separator + "┤")

    # Print rows with color coding
    for idx, repo in enumerate(all_repos_status, 1):
        if not repo:
            continue

        row_data = [
            str(idx),
            repo['name'],
            repo['branch'],
            short_path(repo['path']),
            str(repo['modified']),
            str(repo['added']),
            str(repo['deleted']),
            str(repo['total_changes'])
        ]

        # Format row with alignment
        row_parts = []
        for i, cell in enumerate(row_data):
            width = col_widths[i]
            if align[i] == 'right':
                row_parts.append(str(cell).rjust(width))
            elif align[i] == 'center':
                row_parts.append(str(cell).center(width))
            else:
                row_parts.append(str(cell).ljust(width))

        # Color code: yellow for changes, white for clean
        row_color = BRIGHT_YELLOW if repo['has_changes'] else WHITE
        print("│ " + color_text(" │ ".join(row_parts), fg=row_color) + " │")

    print("└" + separator + "┘")
    print(color_text(" Legend: ", DIM) + color_text("Yellow", BRIGHT_YELLOW) + color_text(" = Changes  ", DIM) + color_text("White", WHITE) + color_text(" = Clean", DIM))


def display_repos_summary(repos_with_changes):
    """
    Display summary table of repositories with changes (for commit screen).

    Args:
        repos_with_changes: List of repo info dicts with changes
    """
    if not repos_with_changes:
        print(color_text("✓ No repositories with uncommitted changes", GREEN, style=BOLD))
        return

    print(color_text(f"\n{len(repos_with_changes)} repositories with changes:", BRIGHT_YELLOW, style=BOLD))
    print()

    headers = ["#", "Repository", "Branch", "Folder", "M", "A", "D", "T"]
    rows = []

    for idx, repo in enumerate(repos_with_changes, 1):
        rows.append([
            str(idx),
            repo['name'],
            repo['branch'],
            short_path(repo['path']),
            str(repo['modified']),
            str(repo['added']),
            str(repo['deleted']),
            str(repo['total_changes'])
        ])

    print_table(headers, rows, align=['center', 'left', 'left', 'left', 'center', 'center', 'center', 'center'])
    print()


def display_repo_changes(repo_info):
    """
    Display detailed changes for a repository.

    Args:
        repo_info: Repository information dict
    """
    clear_screen()
    header(SCRIPT_NAME, VERSION, subtitle=f"Changes: {repo_info['name']}")

    print(color_text(f"Repository: {repo_info['name']}", BRIGHT_CYAN, style=BOLD))
    print(color_text(f"Branch: {repo_info['branch']}", CYAN))
    print(color_text(f"Path: {repo_info['path']}", DIM))
    print()

    if not repo_info['status_lines']:
        print(color_text("No changes", GREEN))
        return

    print(color_text("Changes:", YELLOW, style=BOLD))
    for line in repo_info['status_lines']:
        status = line[:2]
        filename = line[3:] if len(line) > 3 else ''

        if status.startswith('??'):
            print(color_text(f"  [NEW]     {filename}", GREEN))
        elif 'M' in status:
            print(color_text(f"  [MODIFIED] {filename}", YELLOW))
        elif 'D' in status:
            print(color_text(f"  [DELETED]  {filename}", RED))
        elif 'A' in status:
            print(color_text(f"  [ADDED]    {filename}", CYAN))
        else:
            print(color_text(f"  [{status}]  {filename}", WHITE))

    print()


# -----------------------------------------------------------------------------
# Monitor Mode
# -----------------------------------------------------------------------------

def _read_key_timeout(timeout):
    """Wait up to `timeout` seconds for a single keypress (no Enter required).

    Returns the character pressed, or None if the timeout elapsed. Puts the
    terminal in cbreak mode so a single key is read immediately. Falls back to
    a plain sleep when raw-key support is unavailable or stdin isn't a TTY.
    """
    if not _RAWKEY_OK or not sys.stdin.isatty():
        time.sleep(max(0, timeout))
        return None
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ready, _, _ = select.select([fd], [], [], timeout)
        if ready:
            return os.read(fd, 1).decode('utf-8', errors='replace')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return None


def _flush_input():
    """Discard any pending/unread bytes on stdin (e.g. arrow-key remnants)."""
    if _RAWKEY_OK and sys.stdin.isatty():
        try:
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        except Exception:
            pass


def monitor_repos(config):
    """Live-monitor screen: re-scan and redraw the repo status table on a fixed
    interval (default 60s, config key 'monitor_interval'). A countdown shows the
    time to the next refresh; pressing ANY key exits back to the main menu.
    """
    try:
        interval = int(config.get('monitor_interval', 60))
    except (TypeError, ValueError):
        interval = 60
    if interval < 1:
        interval = 60

    while True:
        clear_screen()
        header(SCRIPT_NAME, VERSION, subtitle="Monitor — auto-refresh")

        # Re-scan repositories and their status on every refresh
        repos = find_git_repos(config['scan_directories'])
        all_repos_status = []
        for repo in repos:
            status = get_repo_status(repo)
            if status:
                all_repos_status.append(status)

        display_all_repos(all_repos_status)

        updated = datetime.now().strftime("%-I:%M:%S %p").lower()
        width = shutil.get_terminal_size().columns
        print()
        print("-" * width)

        # Countdown to next refresh; any keypress returns to the menu
        key = None
        for remaining in range(interval, 0, -1):
            status_line = (
                color_text("● Monitoring", BRIGHT_GREEN, style=BOLD) +
                color_text(f"   Last updated {updated}", DIM) +
                color_text(f"   •   next refresh in {remaining:2d}s", CYAN) +
                color_text("   •   press any key to return to menu", BRIGHT_YELLOW)
            )
            sys.stdout.write("\r\033[K" + status_line)
            sys.stdout.flush()
            key = _read_key_timeout(1)
            if key is not None:
                break

        if key is not None:
            _flush_input()   # drop any trailing bytes so they don't leak into the menu prompt
            print()          # move the cursor off the status line
            return


# -----------------------------------------------------------------------------
# Main Menu
# -----------------------------------------------------------------------------

def main_menu(config):
    """
    Display main menu and handle user actions.

    Args:
        config: Configuration dictionary
    """
    while True:
        clear_screen()
        header(SCRIPT_NAME, VERSION)

        print(color_text("Scanning for Git repositories...", CYAN), end=' ')
        repos = find_git_repos(config['scan_directories'])

        if not repos:
            print(color_text("None found!", YELLOW))
            print(color_text(f"Searched in: {', '.join(config['scan_directories'])}", DIM))
            print()
            input(color_text("Press Enter to exit...", YELLOW))
            break

        print(color_text(f"Found {len(repos)}", GREEN), end='  ')
        print(color_text("• Checking for changes...", CYAN), end=' ', flush=True)

        # Check status of ALL repos
        all_repos_status = []
        repos_with_changes = []
        for repo in repos:
            status = get_repo_status(repo)
            if status:
                all_repos_status.append(status)
                if status['has_changes']:
                    repos_with_changes.append(status)

        print(color_text("✓ Done", GREEN))

        # Display all repos with color coding
        display_all_repos(all_repos_status)

        # Menu options on one line (always shown — Monitor works even when clean)
        width = shutil.get_terminal_size().columns
        print("-" * width)
        legend = (
            color_text("[A]", BRIGHT_YELLOW, style=BOLD) + " Commit & Push All  " +
            color_text("[M]", BRIGHT_YELLOW, style=BOLD) + " Monitor  " +
            color_text("[V]", BRIGHT_YELLOW, style=BOLD) + " View Changes  " +
            color_text("[L]", BRIGHT_YELLOW, style=BOLD) + " Log  " +
            color_text("[Q/Enter]", BRIGHT_YELLOW, style=BOLD) + " Quit"
        )
        print(legend)
        print("-" * width)

        choice = input(color_text("Option: ", WHITE, style=BOLD)).strip().lower()

        if choice == 'q' or choice == '':
            break
        elif choice == 'a':
            if repos_with_changes:
                commit_all_repos(repos_with_changes, config)
            else:
                print(color_text("\n✓ Nothing to commit — all repositories are clean.", GREEN, style=BOLD))
                input(color_text("\nPress Enter to return to menu...", YELLOW))
        elif choice == 'm':
            monitor_repos(config)
        elif choice == 'v':
            if repos_with_changes:
                view_changes_menu(repos_with_changes)
            else:
                print(color_text("\n✓ No changes to view — all repositories are clean.", GREEN, style=BOLD))
                input(color_text("\nPress Enter to return to menu...", YELLOW))
        elif choice == 'l':
            if LOG_FILE and os.path.exists(LOG_FILE):
                print(color_text(f"Opening {LOG_FILE} in default editor...", YELLOW))
                os.system(f'open "{LOG_FILE}"')
            else:
                print(color_text(f"Log file not found: {LOG_FILE}", RED))
            input(color_text("\nPress Enter to return to menu...", YELLOW))


def commit_all_repos(repos_with_changes, config):
    """
    Commit and push all repositories with changes.

    Args:
        repos_with_changes: List of repo info dicts
        config: Configuration dictionary
    """
    clear_screen()
    header(SCRIPT_NAME, VERSION, subtitle="Commit All Repositories")

    display_repos_summary(repos_with_changes)

    # Ask how commit messages should be entered
    print()
    print(color_text("Commit message options:", WHITE, style=BOLD))
    print(color_text("  1. Continue With Generated Message", WHITE))
    print(color_text("  2. Enter One Message for All Repos", WHITE))
    print(color_text("  3. Enter Individual Messages for Each Repo", WHITE))
    print()
    msg_choice = input(color_text("Option [1]: ", WHITE, style=BOLD)).strip().lower()

    if msg_choice in ('q', 'quit', 'esc'):
        print(color_text("Cancelled", YELLOW))
        pause()
        return

    # Auto-generated timestamp message (default and per-repo fallback)
    generated = datetime.now().strftime("%Y-%m-%d_%I%p").lower()

    # Build a per-repo message map (repo path -> message, before footer)
    messages = {}
    if msg_choice == '2':
        one_message = input(color_text("Enter one message for all repos (Enter = generated): ", WHITE, style=BOLD)).strip()
        base = one_message if one_message else generated
        for r in repos_with_changes:
            messages[r['path']] = base
    elif msg_choice == '3':
        print()
        print(color_text("Enter a message for each repo (Enter = generated message):", CYAN))
        for r in repos_with_changes:
            entered = input(color_text(f"  [{r['name']}]: ", WHITE, style=BOLD)).strip()
            messages[r['path']] = entered if entered else generated
    else:
        # Option 1 (default / blank): generated message for every repo
        for r in repos_with_changes:
            messages[r['path']] = generated

    # Claude Code footer appended to every commit message
    footer = "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

    # Preview the message(s)
    print()
    if msg_choice == '3':
        print(color_text("Commit messages:", CYAN, style=BOLD))
        for r in repos_with_changes:
            print(color_text(f"  {r['name']}: {messages[r['path']].splitlines()[0]}", CYAN))
    else:
        sample = next(iter(messages.values()), generated)
        print(color_text(f"Commit message: {sample.splitlines()[0]}", CYAN))
    print()

    if not confirm("Proceed with commit and push?", default=True):
        print(color_text("Cancelled", YELLOW))
        pause()
        return

    # Process each repo
    print()
    print(color_text("Processing repositories...", BRIGHT_CYAN, style=BOLD))
    print()

    results = []
    for repo_info in repos_with_changes:
        full_message = messages[repo_info['path']] + footer
        print(f"[{repo_info['name']}] ", end='')
        result = commit_and_push_repo(repo_info, full_message)
        results.append(result)

        if result['success']:
            print(color_text("✓", GREEN))
            write_log(f"Success: {repo_info['name']}", LOG_FILE)
        else:
            print(color_text("✗", RED))
            write_log(f"Failed: {repo_info['name']} - {result.get('error', 'Unknown error')}", LOG_FILE)
            print(color_text(f"  Error: {result.get('error', 'Unknown')}", RED))

    # Summary
    print()
    print(color_text("─" * 80, DIM))
    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    print(color_text(f"Completed: {success_count} success, {fail_count} failed", WHITE, style=BOLD))
    print()
    _s = config.get('successAudio', _DEFAULT_SOUND_SUCCESS)
    sound_success = _s if _s.startswith('http') else os.path.expanduser(_s)
    _f = config.get('failureAudio', _DEFAULT_SOUND_FAILURE)
    sound_failure = _f if _f.startswith('http') else os.path.expanduser(_f)
    if fail_count == 0:
        play_sound(get_project_sound(SCRIPT_NAME, 'successAudio', sound_success))
    else:
        play_sound(get_project_sound(SCRIPT_NAME, 'failureAudio', sound_failure))
    pause()


def select_and_commit_repos(repos_with_changes, config):
    """
    Allow user to select specific repositories to commit.

    Args:
        repos_with_changes: List of repo info dicts
        config: Configuration dictionary
    """
    clear_screen()
    header(SCRIPT_NAME, VERSION, subtitle="Select Repositories")

    # Create selection list
    options = [f"{r['name']} ({r['total_changes']} changes)" for r in repos_with_changes]

    selected_indices = select_list("Select repositories to commit:", options)

    if not selected_indices:
        print(color_text("No repositories selected", YELLOW))
        pause()
        return

    selected_repos = [repos_with_changes[i] for i in selected_indices]

    # Now commit selected repos
    commit_all_repos(selected_repos, config)


def view_changes_menu(repos_with_changes):
    """
    View detailed changes for repositories.

    Args:
        repos_with_changes: List of repo info dicts
    """
    while True:
        clear_screen()
        header(SCRIPT_NAME, VERSION, subtitle="View Changes")

        options = [f"{r['name']} ({r['total_changes']} changes)" for r in repos_with_changes]
        options.append("← Back to Main Menu")

        choice = menu("Select repository to view:", options, allow_back=False, allow_quit=False)

        if choice == 'quit' or choice == str(len(options)):
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(repos_with_changes):
                display_repo_changes(repos_with_changes[idx])
                pause()
        except (ValueError, IndexError):
            pass


# -----------------------------------------------------------------------------
# Auto Push (non-interactive)
# -----------------------------------------------------------------------------

def auto_push_all(config, commit_message):
    """
    Non-interactive mode: commit and push all repos with changes using the
    given commit message. Called with --auto "message" from the CLI.

    Args:
        config: Configuration dictionary
        commit_message: Commit message to use for all repos

    Returns:
        int: Exit code (0 = all success, 1 = any failure)
    """
    repos = find_git_repos(config['scan_directories'])
    if not repos:
        print(color_text("  Git Push All: no repositories found.", YELLOW))
        return 0

    repos_with_changes = []
    for repo in repos:
        status = get_repo_status(repo)
        if status and status['has_changes']:
            repos_with_changes.append(status)

    if not repos_with_changes:
        print(color_text("  Git Push All: all repositories are clean — nothing to push.", GREEN))
        return 0

    print(color_text(f"  Git Push All: {len(repos_with_changes)} repo(s) with changes — committing...", CYAN))

    results = []
    for repo_info in repos_with_changes:
        print(f"    [{repo_info['name']}] ", end='', flush=True)
        result = commit_and_push_repo(repo_info, commit_message)
        results.append(result)
        if result['success']:
            print(color_text("✓", GREEN))
            write_log(f"Auto-push success: {repo_info['name']}", LOG_FILE)
        else:
            print(color_text("✗", RED))
            err = result.get('error', 'Unknown error')
            write_log(f"Auto-push failed: {repo_info['name']} - {err}", LOG_FILE)
            print(color_text(f"      Error: {err}", RED))

    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    status_color = GREEN if fail_count == 0 else YELLOW
    print(color_text(f"  Git Push All: {success_count} success, {fail_count} failed.", status_color))
    return 0 if fail_count == 0 else 1


# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

def main():
    """
    Main entry point.
    """
    global LOG_FILE

    # Initialize logging
    LOG_FILE = os.path.expanduser("~/Documents/log/gitPushAll.log")
    ensure_folder(os.path.dirname(LOG_FILE))
    log_header(SCRIPT_NAME, VERSION, LOG_FILE)

    # Check for --auto "message" CLI argument (non-interactive mode)
    args = sys.argv[1:]
    if '--auto' in args:
        idx = args.index('--auto')
        auto_message = args[idx + 1] if idx + 1 < len(args) else 'Auto-commit'
        try:
            config = load_config()
            exit_code = auto_push_all(config, auto_message)
        except Exception as e:
            print(color_text(f"  Git Push All error: {e}", RED))
            exit_code = 1
        sys.exit(exit_code)

    try:
        # Load configuration
        config = load_config()

        # Run main menu
        main_menu(config)

        # Exit screen
        clear_screen()
        header(SCRIPT_NAME, VERSION)
        print(color_text("Git Push All exiting...", CYAN))
        print(color_text("\nCopyright © 2025 Cloud Box 9 Inc. All rights reserved.\n", YELLOW))

    except KeyboardInterrupt:
        clear_screen()
        header(SCRIPT_NAME, VERSION)
        print(color_text("Git Push All exiting...", CYAN))
        print(color_text("\nCopyright © 2025 Cloud Box 9 Inc. All rights reserved.\n", YELLOW))
    except Exception as e:
        print(color_text(f"\nError: {e}", RED, style=BOLD))
        write_log(f"Fatal error: {e}", LOG_FILE)
    #finally:
    #    log_footer(SCRIPT_NAME, VERSION, LOG_FILE)


if __name__ == "__main__":
    main()
