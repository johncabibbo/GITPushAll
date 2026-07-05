# Git Push All

**Commit and push every Git repo across your machine in one pass.**

`gitPushAll.py` auto-discovers Git repositories under the directories you configure, shows each one's status (color-coded: changes vs. clean), and lets you commit and push them all in a single batch. It supports a preview, custom or auto-timestamped commit messages, a dry-run mode, and a fully non-interactive `--auto` mode for calling from other scripts. CB9Lib is bundled.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Alias Setup — Run From Anywhere](#alias-setup--run-from-anywhere)
6. [Configuration](#configuration)
7. [Usage & Examples](#usage--examples)
8. [Troubleshooting](#troubleshooting)
9. [License / Copyright](#license--copyright)

---

## Overview

If you keep many small repos (scripts, sites, notes), committing them one by one is tedious. Git Push All scans your configured folders, finds every repo, and pushes them together — great for an end-of-day sweep or an automated backup step.

---

## Features

- **Auto-discovery** — finds Git repos under your `scan_directories` (deduplicated by real path).
- **Status overview** — every repo listed; yellow = uncommitted changes, white = clean.
- **Batch commit + push** — handle all dirty repos at once.
- **Preview** — see what changed before committing.
- **Commit messages** — custom, or auto-timestamped (`Auto-commit: {timestamp}`).
- **Dry-run mode** — rehearse without touching anything.
- **`--auto` mode** — non-interactive; used by Backup42 and other scripts.
- **Logging** — detailed run log, openable from the menu (`[L]`).

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| **macOS / Linux** | Unix terminal for the menu. |
| **Python 3.10+** | CB9Lib is **bundled** — no separate install. |
| **git** | Must be installed and on your `PATH`, with push credentials configured. |

---

## Installation

```bash
git clone <REPOSITORY_URL> GITPushAll
cd GITPushAll
python3 gitPushAll.py
```

---

## Alias Setup — Run From Anywhere

Launch from any directory by typing `gitpushall`.

### macOS / Linux (zsh or bash)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
alias gitpushall='python3 ~/path/to/GITPushAll/gitPushAll.py'
```

Reload and run:

```bash
source ~/.zshrc
gitpushall
```

> **Windows:** not supported natively (Unix terminal). Use **WSL** and the Linux steps.

---

## Configuration

Edit **`gitPushAll_config.json`**:

```json
{
  "scan_directories": [
    "~/Documents/script",
    "~/Documents/sites",
    "~/Documents/devNotes"
  ],
  "excluded_repos": [],
  "default_commit_message": "Auto-commit: {timestamp}",
  "auto_push": true,
  "dry_run_first": false,
  "successAudio": "https://.../beep.wav",
  "failureAudio": "~/path/to/GITPushAll/audio/bad-file.wav"
}
```

| Key | Description |
|-----|-------------|
| `scan_directories[]` | Folders to search for Git repos. |
| `excluded_repos[]` | Repos to skip. |
| `default_commit_message` | Template; `{timestamp}` is substituted. |
| `auto_push` | Push after committing. |
| `dry_run_first` | Preview before doing anything. |
| `successAudio` / `failureAudio` | Optional sounds on completion. |

---

## Usage & Examples

```bash
python3 gitPushAll.py                       # interactive menu
python3 gitPushAll.py --auto "Nightly sync" # non-interactive: commit+push all dirty repos
```

**Cron example — nightly at 11 PM:**

```cron
0 23 * * * /usr/bin/python3 ~/path/to/GITPushAll/gitPushAll.py --auto "Nightly" >> ~/Documents/log/gitPushAll.log 2>&1
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| A repo isn't found | Confirm it's under a `scan_directories` path and not in `excluded_repos`. |
| Push fails / asks for a password | Configure Git credentials (SSH keys or a credential helper). |
| A repo is listed twice | Fixed in v1.9 (dedup by real path); ensure you're on the current version. |
| Nothing to push | Repos with no changes are shown white/clean and skipped. |

---

## License / Copyright

---
**Version:** 1.9
**Author:** Cloud Box 9 Inc.
**Maintainer / Owner:** Cloud Box 9 Inc.
**Last Updated:** Jul 5, 2026

Copyright © 2026 Cloud Box 9 Inc. All rights reserved.
