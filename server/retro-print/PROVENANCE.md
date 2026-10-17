# Provenance of the print-watcher scripts

Established on 17-10-2026 from:
- the files themselves;
- the server's backup of 06-10-2026 (`_backup_20261006-204700`, with its SHA256SUMS);
- the assistant's session logs on the server, which start on 06-10-2026.

**Exclusive authorship is not claimed for any file.** The table separates what can be shown from what cannot.

## Three stages

| Stage | Date | What happened | Who | Evidence |
|---|---|---|---|---|
| 1. Originals on macOS | before 03-10-2026 | `c64ultimate-print-spooler.sh` and `meatloaf-print-watch.sh`, probably also `repair_meatloaf_pdf.py`, ran on the owner's Mac under `~/Library/Scripts/…` | **the owner, by the owner's account.** The macOS originals are not on the server, so this was not verified file by file. | the scripts' own header comments ("Geport van macOS (~/Library/Scripts/…)") |
| 2. Port to the Pi, and the new FujiNet watcher | 03-10-2026 | The macOS commands (`shasum`, `stat -f`, `xxd`) were replaced with Linux equivalents and the paths moved to `/opt/retro-print/`. The headers say the logic is otherwise unchanged. `fujinet-print-watch.sh` was written new, modelled on the other two. | **not recorded.** This happened before the session logs on the server begin. | file dates and the backup hashes below |
| 3. Quiet logging | 06-10-2026 | The block marked `# --- Rustig loggen (toegevoegd 2026-10-06)`: `note()`, `save_notices()`, `set_reachable()`, `probe_curl()` and their call sites. An unreachable device is logged only as a state change. Print logic, polling intervals, addresses and protocols were not changed. | **the AI assistant (Claude), at the owner's request**, in an assistant session on the server | the owner's request in that session, and the diff against the backup |

The **publication copies** in this folder differ from the files in use only in the device addresses (replaced by examples) and in the service account in the units (`User=retro`). Replacements:

| File | Replacement | Count |
|---|---|---|
| `fujinet/fujinet-print-watch.sh` | home FujiNet address → `192.168.1.60` | 1 |
| `fujinet/fujinet-print-watch.conf.example` | home FujiNet address → `192.168.1.60` | 1 |
| `c64ultimate/c64ultimate-print-spooler.conf.example` | home Ultimate address → `192.168.1.78` | 4 |
| `systemd/*.service` (3 files) | owner account → `User=retro` | 1 each |

## Per file

| File | Stage 1 (owner, macOS) | Stage 2 (03-10, author not recorded) | Stage 3 (06-10, Claude) | Third-party code |
|---|---|---|---|---|
| `c64ultimate/c64ultimate-print-spooler.sh` | original logic | port; SHA-256 `4f592553cef0…` | +91 / −14 lines; current SHA-256 `c646c8ac16f9…` | none found: shell with `curl`, `lp`, `sha1sum`, `python3` |
| `c64ultimate/c64ultimate-print-spooler.conf` | original settings | ported comment, unchanged since 03-10 (`aa5dbe261c92…`) | – | – |
| `meatloaf/meatloaf-print-watch.sh` | original logic | port (`df28b3c9ec4d…`) | +86 / −14 lines (`bfa801e33c51…`) | none found |
| `meatloaf/repair_meatloaf_pdf.py` | probably original; it has no port header | unchanged since 03-10 (`8a5448595342…`) | – | none found: Python standard library only, with a hand-written minimal PDF writer, no licence header or URL |
| `fujinet/fujinet-print-watch.sh` | – | **new script** (`44fc94d23b04…`), modelled on the two above | +79 / −8 lines (`2b924545c9bf…`) | none found |
| `fujinet/fujinet-print-watch.conf` | – | new (`699bc9fbff04…`) | – | – |
| `systemd/*.service`, `*.timer` | – | 03-10, author not recorded | unchanged (identical to the backup) | – |

"None found" means:
- no licence or copyright header;
- no reference to an external source;
- only standard tools and the Python standard library.

It is not a legal guarantee that no snippet was ever copied.

## Licence

The owner releases these files under the project licence: MIT, `Copyright (c) 2026 The Love Shack Network contributors`. The *contributors* are the owner (stage 1), the unrecorded author of stage 2, and the assistant-made changes of stage 3, which were made on the owner's instructions.
- **If the stage-2 author turns out to be a third party**, this file is updated and their notice is added.
- **The copyright status of AI-generated changes** depends on jurisdiction. Here they are contributed under the same licence.
