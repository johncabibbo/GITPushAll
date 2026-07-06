# Git Push All

Batch commit and push tool for multiple Git repositories.

## Project Information

- **Version:** 2.02
- **Category:** Git Tool
- **OS:** Mac/Linux
- **Maintainer:** Cloud Box 9 Inc.

## Description

Git Push All is a batch processing tool that automatically discovers Git repositories, checks for uncommitted changes, and allows batch commit and push operations across multiple repositories with a single command.

## Features

- **Auto-Discovery** - Finds all Git repositories in configured directories
- **Color-Coded Status** - Yellow for repos with changes, white for clean
- **All Repos Display** - Shows every repository, not just those with changes
- **Monitor Mode** - `[M]` live-refreshes the status table every 60s (configurable via `monitor_interval`); press any key to return to the menu
- **Batch Operations** - Commit and push multiple repos at once
- **Preview Changes** - View changes before committing
- **Auto-Timestamped Messages** - Generate commit messages automatically
- **Custom Messages** - Option for manual commit messages
- **Dry-Run Mode** - Test operations without making changes
- **Detailed Logging** - Track all operations with timestamps
- **Single-Line Menu** - Clean, efficient interface

## Scripts

### gitPushAll.py
Main batch Git operations manager.

**Usage:**
```bash
python3 gitPushAll.py
```

**Interactive Menu Options:**
- **[A]** - Commit & Push All (repos with changes)
- **[M]** - Monitor: auto-refresh the status table every 60s; press any key to return
- **[V]** - View Changes (detailed diff for each repo)
- **[L]** - Log (open the log file)
- **[Q/Enter]** - Quit

**Commit Message Prompt:**
Type a custom message or press Enter for auto-generated timestamp message.

Auto-generated format: `YYYY-MM-DD_HHam/pm`  
Example: `2026-01-09_03pm`

All commits include Claude Code attribution footer automatically.

## Requirements

- Python 3.10+
- CB9Lib (Cloud Box 9 Python Library)
- Git command-line tools
- Configuration file: gitPushAll_config.json

## Configuration

The configuration file (gitPushAll_config.json) defines:
- Scan directories to search for Git repositories
- Excluded repositories (optional)
- Default commit message format
- Auto-push settings
- Dry-run preferences

### Default Scan Directories
- ~/Documents/script
- ~/Documents/sites

## Repository Status Display

The tool displays all repositories in a formatted table:

| # | Repository | Branch | Modified | Added | Deleted | Total |
|---|------------|--------|----------|-------|---------|-------|
| Color-coded rows indicate status:
- **Yellow** - Repository has uncommitted changes
- **White** - Repository is clean (no changes)

## Batch Operations

When committing all repos with changes:
1. Displays summary of repos to be committed
2. Prompts for commit message (or Enter for auto-timestamp)
3. Confirms before proceeding
4. Processes each repository sequentially
5. Shows success/failure status for each
6. Displays final summary with counts

## Logging

- Log file: ~/Documents/logs/gitPushAll.log
- Tracks all operations with timestamps
- Records successes and failures
- Includes error details for troubleshooting

## Git Best Practices

The tool follows git best practices:
- No force push operations
- Hooks are enabled (not skipped)
- Proper commit message formatting
- Sequential repository processing

## Copyright

Copyright © 2025 Cloud Box 9 Inc. All rights reserved.
