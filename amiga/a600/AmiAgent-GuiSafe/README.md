# AmiAgent A600 v2: GUI-SAFE and one Workbench drawer for all three modes

AmiAgent A600 v2 brings the three AmiAgent modes together in one Workbench drawer on the Amiga 600, and adds **GUI-SAFE**: after someone says yes at the machine, an AI assistant may start and operate **one** allow-listed program (TextEngine 5.2) for a limited time, saving only into one test folder on an isolated network share.

| Mode | What the assistant can do | Started by | Binary |
|---|---|---|---|
| **READONLY** (default) | look: system info, files, screenshots, windows and menus | AmiAgent Start | `amiagent` `bb2f0daf…` (unchanged) |
| **WRITE-SAFE** | place **new** files in `Work:Inbox` (30 min, 20 files, 1024 KB each) | Schrijven Aan + local yes | `amiagent-ws` `202f731f…` (unchanged) |
| **GUI-SAFE** | start one program and drive it with mouse and keyboard; save only in `GSTest:Tests/A600` | Bedienen Aan + local yes | `amiagent-gs` `34c74cf7…` |

Only one mode runs at a time. Every extra permission is given **at the machine**; nothing on the network can raise the mode.

| Status | What |
|---|---|
| ✅ **Proven on real hardware** | Amiga 600 (68000, 2 + 4 MB, KS/WB 3.1, AmiTCP 3.0b2, Plipbox), 08-11-2026: installation of v2 and the GUI-SAFE acceptance test, **7/7 PASS** (below) |
| 🧪 **Emulator-tested** | v2 scripts V0–V15, WRITE-SAFE ↔ GUI-SAFE exclusion (7/7), installation and rollback (9/9), the GUI-SAFE prototype series G0–G3 |
| ⚠️ **Not fully security-validated** | GUI-SAFE is physically tested but **not** fully security-validated. See [Known limitations](#known-limitations), in particular the `CLIENT` restriction |
| ❌ **Not released** | There is no release for GUI-SAFE. A release waits for the fix of [Issue 0004](../../../docs/issues/0004-guisafe-client-not-enforced.md) and its regression tests |

## The Workbench drawer

| Icon | Mode | Double-click does |
|---|---|---|
| AmiAgent Status | READONLY | status window of the running agent (amimon) |
| AmiAgent Start / AmiAgent Stop | READONLY | start / stop the read-only agent |
| LeesMij | READONLY | short read-me |
| **READONLY** (sign) | – | explains the mode (message only) |
| AmiAgent Schrijven Aan / Uit | WRITE-SAFE | give / end a write mandate |
| **WRITE-SAFE** (sign) | – | explains the mode |
| **GSTest Mount** | GUI-SAFE | mounts the isolated test share as `GSTest:`, registers the smbfs process (`SETENV`) |
| **GSTest Stop** | GUI-SAFE | unmounts `GSTest:`; refuses during GUI-SAFE and while files are open |
| **GUI-SAFE Status** | GUI-SAFE | read-only window: running mode, mounts, last messages |
| **AmiAgent Bedienen Aan** | GUI-SAFE | checks everything, asks yes/no, starts `amiagent-gs` |
| **AmiAgent Bedienen Uit** | GUI-SAFE | local emergency stop, verifies that READONLY returns |
| **GUI-SAFE** (sign) | – | explains the mode and the order of steps |

The scripts and messages are Dutch, as tested. The manuals in [`docs/`](docs/) are Dutch as well.

## How GUI-SAFE is enforced

**Preventive (in `amiagent-gs` on the Amiga):**
- a local mandate file; the program must be in a local allowlist; the agent starts it itself (LoadSeg + CreateNewProc, no shell);
- every mounted volume must be listed as PROTECT or EXEMPT; each PROTECT volume is write-protected through the filesystem (`ACTION_WRITE_PROTECT`) and checked with a live probe, otherwise the mandate is refused (fail-closed);
- input only into the program's own windows; a key filter (no Amiga-Amiga, no left-Amiga shortcuts except V/B); typed paths must start with the test folder;
- limits: time, number of actions, idle time, focus loss; the READONLY wall stays (no free EXEC, PUT, ARexx, UIACT, BREAK).

**Server side:** the share `GuiSafeTest` is writable only in `Tests/A600`; the original program files are read-only for the share user. Example: [`samba/GuiSafeTest.example.conf`](samba/GuiSafeTest.example.conf).

**Detection only:** a tripwire on `SYS:S`, `SYS:C`, `ENVARC:` closes the session **after** a change; an audit log in `RAM:` and `Work:AmiAgent/Log/gui.log`.

## Acceptance test on the real A600 (08-11-2026)

1. Start state: READONLY, AmigaShare mounted, GSTest not mounted, WRITE-SAFE off – PASS
2. AmigaShare Stop → GSTest Mount (registered) → Bedienen Aan, yes: GUI-SAFE active, Work and Games protected – PASS
3. TextEngine started by the agent, text typed. The first save with RAmiga+S on an untitled document tried to write into the program folder and was **refused by the server** (nothing written). After the user's go-ahead: Save As into `GSTest:Tests/A600`, quit, start again, reopen – PASS
4. Work: write-protected during the session, shown by the agent log and status (no new write attempt) – PASS
5. Bedienen Uit: volumes released, **READONLY back** – PASS
6. GSTest Stop: share really unmounted – PASS
7. AmigaShare Mount; end state byte-identical to the installed state, `amiagent` still `bb2f0daf…` – PASS

Full details: [technical manual](docs/TECHNISCHE-HANDLEIDING-A600-V2.md) (§9).

## Known limitations

- **`CLIENT` is not enforced in GUI-SAFE.** The mandate's `CLIENT=` value is checked for length, stored and printed, but `amiagent-gs` does **not** compare it with the peer address. Any host that holds the token can send GUI-SAFE commands during an open session. (WRITE-SAFE does enforce its `CLIENT`.) Tracked as [Issue 0004](../../../docs/issues/0004-guisafe-client-not-enforced.md).
- The token travels unencrypted; use only on a trusted home network.
- EXEMPT volumes (`RAM:`, `GSTest:`) are not protected by the agent; `GSTest:` is limited by the server.
- The text filter covers typed paths only, not mouse navigation in a file requester.
- The tripwire detects, it does not prevent.
- No memory protection on AmigaOS: malicious code on the Amiga can change the agent or the mandate.
- Floppy and Gotek volumes cannot be write-protected; GUI-SAFE then refuses to start (eject them first).
- Power loss during a session removes the protection (it is held in RAM).
- The header comment of `src/guisafe.c` still says "PROTOTYPE, emulator only"; the file is kept byte-identical to the source of the tested binary.
- Tested on one Amiga 600 only; not on the PiStorm or any other machine, and only with TextEngine 5.2.

## What is in this directory, and what may be distributed

| Item | In git | Licence | Notes |
|---|---|---|---|
| `patches/0005-guisafe.patch`, `src/guisafe.c` | yes | Apache-2.0 (changes to upstream amimcp) | the source of the tested `amiagent-gs` together with upstream `3145dee` and patches 0001–0003 |
| Scripts (Bedienen Aan/Uit, GSTest Mount/Stop, GUI-SAFE Status, the three signs), `install/` | yes | MIT | `GSTest Mount` uses the fictive server address 192.168.1.145; set your own |
| Icons (`*.info`) | yes | MIT | drawn in code by this project |
| `Prefs/*.example`, `samba/*.example.conf` | yes | MIT | fictive addresses; no tokens or passwords |
| `build/agent-gs.sha256` | yes | – | hash of the tested binary |
| `docs/` (manuals in Markdown and PDF, screenshots, photo) | yes | CC BY 4.0 | screenshots show TextEngine 5.2 and Workbench windows for documentation only |
| `amiagent-gs` binary | **no** | Apache-2.0 + runtime notices | could be distributed later with `THIRD_PARTY_NOTICES` (as for WRITE-SAFE), **not before Issue 0004 is fixed** |
| TextEngine 5.2 | **no** | third-party freeware | download it yourself; it is not part of this project |
| smbfs, AmiTCP, Workbench, Kickstart | **no** | GPL-2.0 / proprietary | see the repository's `THIRD_PARTY.md` |
| Production settings, tokens, passwords, logs, the Pi test driver | **no** | – | never published |

The install scripts in `install/` expect the tested staging layout `AmigaShare:AmiAgent-v2/a600/` with the scripts and icons in `AmiAgent/` and the drawer icon in `Work-lade/`. That layout (and the drawer icon) is part of a future release package, not of this directory.

`AmiAgent Schrijven Aan` in [`../AmiAgent-WriteSafe/`](../AmiAgent-WriteSafe/) is updated to 1.2: two identical blocks refuse WRITE-SAFE while GUI-SAFE runs. Nothing else in WRITE-SAFE changed.

## Licence

| Part | Licence |
|---|---|
| `patches/0005-guisafe.patch`, `src/guisafe.c` | Apache-2.0, see `LICENSE-amimcp` and `NOTICE-amimcp` in [`../../a500-pistorm/AmiAgent/`](../../a500-pistorm/AmiAgent/) |
| Scripts, icons, `install/`, `Prefs/`, `samba/`, `build/` | MIT, see [`LICENSE`](../../../LICENSE) |
| `README.md`, `CHANGELOG.md`, `docs/` | CC BY 4.0, see [`LICENSE-docs`](../../../LICENSE-docs) |
