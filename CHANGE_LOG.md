# gitPushAll — Change Log

---

## v2.02 — Jul 6, 2026

- **Added `[M] Monitor`** menu option — live-refreshes the repository status table every 60 seconds (configurable via `monitor_interval`) with a countdown to the next refresh
  - Pressing **any key** exits the monitor loop and returns to the menu (no Enter needed)
  - Added `_read_key_timeout()` (cbreak + `select`) and `_flush_input()` helpers
- Main menu now stays open even when all repos are clean, so Monitor is reachable anytime; `[A]` / `[V]` report "nothing to do" instead of the script exiting

---

## v2.01 — Jul 6, 2026

- Change log started at the current version (v2.01); future changes will be recorded here.
- Earlier history, if any, is documented in the script header's revision notes.

---

Copyright © 2026 Cloud Box 9 Inc. All rights reserved.
