# Changelog – AmiAgent A600

## v2 (unreleased) – 08-11-2026

Status: installed and accepted on a real Amiga 600 (7/7 PASS). **Not released**: waiting for the fix of
[Issue 0004](../../../docs/issues/0004-guisafe-client-not-enforced.md) (`CLIENT` not enforced in GUI-SAFE).

### Added
- **GUI-SAFE** (`amiagent-gs`, patch 0005 + `src/guisafe.c`): local mandate, one allow-listed program, filesystem
  write protection of all local volumes with a live probe, window gate, key and text filters, limits, tripwire, audit log.
- One Workbench drawer for READONLY, WRITE-SAFE and GUI-SAFE, with an explanation sign per mode.
- `GSTest Stop` (new): unmounts the test share; refuses during GUI-SAFE and while files are open.
- `GUI-SAFE Status` (new): read-only overview of mode, mounts and last messages.
- `AmiAgent v2 Installeren` / `AmiAgent v2 Herstellen`: install with backup (`Work:AmiAgent/Backup-v1`) and rollback.
- Dutch user manual and technical manual (Markdown and PDF).

### Changed
- `AmiAgent Bedienen Aan` 0.1 → 2.0: all checks **before** the read-only agent is stopped; refuses while WRITE-SAFE
  runs, while AmigaShare is mounted, or without a registered `GSTest:`; checks again after the yes; agent output to
  `T:AmiAgent-gs.out`; READONLY restarted only if it is not running.
- `AmiAgent Bedienen Uit` 0.1 → 2.0: repeated Ctrl-C, waits for READONLY and starts it itself after 10 s (not while
  WRITE-SAFE runs), clear messages.
- `GSTest Mount` 0.1 → 2.0: `SETENV`, so the smbfs process is registered and can be stopped; refuses double or
  unregistered mounts, a mounted AmigaShare, or no network.
- `AmiAgent Schrijven Aan` 1.1 → 1.2: refuses while GUI-SAFE runs (two identical guard blocks). Nothing else changed.

### Fixed (found in the first physical pilot)
- A refusal in `Bedienen Aan` 0.1 could leave no agent running.
- `GSTest:` could not be unmounted (no `SETENV`).
- WRITE-SAFE and GUI-SAFE exclusion relied only on both binding the same port.

### Unchanged
- `amiagent` (READONLY) `bb2f0daf…`, `amiagent-ws` `202f731f…`, `amiagent-gs` `34c74cf7…`, AmiAgent Start/Stop/Status,
  Schrijven Uit, all settings files.

### Tests
| Where | What | Result |
|---|---|---|
| Emulator (A600 profile) | prototype G0, G1, G2 series, G3, G3sc | G0 11/11, G1 35/35, G2 OK, G3 10/12 + SC1 6/6 (failures were harness faults) |
| Emulator | v2 scripts V0–V15 | run 2: 24/25 (one counting error in the test), V4 repeated: 7/7 |
| Emulator | installation, second installation refused, rollback | 9/9 |
| Emulator | Workbench double-click | PASS |
| Real A600 | first pilot with 0.1 scripts | steps 0–10 PASS, step 11 partial (no unmount) |
| Real A600 | installation of v2 | PASS (all files byte-identical; icon positions later changed by *Clean Up*) |
| Real A600 | **GUI-SAFE acceptance test** | **7/7 PASS**, including one save refused by the server and the return to READONLY |
