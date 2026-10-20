# AmiAgent: read-only AI diagnostics for a real Amiga

AmiAgent lets an AI assistant (Claude Code, through MCP) **look at** a real Amiga: system information, memory, volumes, directory listings, files, screenshots, windows and menus. It cannot change anything on the Amiga. That restriction is compiled into the agent; it is not a setting.

It is [amimcp](https://github.com/thomas-luebker/amimcp)/amiagent 0.13.2 by Thomas Luebker (Apache-2.0) with three small patches, plus a second safety layer (a client-side filter), an installer disk and tests.

| Status | What |
|---|---|
| ✅ **Proven** | Read-only diagnostics on a real A500 with PiStorm/Emu68 over Wi-Fi: install from the ADF, start with a token, `Avail`/`Version`/`ShowConfig`, system info, directory listings, reading files, screenshots, screen list; the filter refusing write tools |
| 🧪 **Emulator-tested** | The agent itself refusing every write channel even without the filter (E10); recovery after a network drop, a stuck command, and no memory growth over 900 connections (E5, E6, E9); `inet.access` port restriction (E3) |
| 📋 **Planned** | Applying `inet.access` on the real machine; connecting from a Mac through the server |
| ⚠️ **Not suitable** | Bulk file transfer over Wi-Fi (see [Known limitations](#known-limitations)) |

## Tested configurations

Only these. Anything else is untested, even where it should work in theory.

| | Real hardware (18-10-2026) | Emulator (18-10-2026) |
|---|---|---|
| Machine | Amiga 500 rev. 5, PiStorm with Raspberry Pi 3A+, Emu68 (68040 emulation) | Amiberry 8.3.0, 68040 |
| ROM / OS | Kickstart 45.66 (exec 45.25), Workbench 3.1 (40.42) | Kickstart 40.63, Workbench 40.42 |
| TCP/IP | AmiTCP 3.0b2 (bsdsocket 3.28) over Wi-Fi, wifipi.device with upstream PR #1 | AmiTCP 3.0b2 on a2065 (slirp), in an isolated network namespace |
| Server | Raspberry Pi 5, Debian 13, Python 3.13, Claude Code (MCP over stdio) | same |

**Should work, not tested:** other TCP/IP stacks with `bsdsocket.library` v3 or newer (Roadshow, Miami), other 68k Amigas with AmigaOS 2.04+ for the agent itself, the Plipbox transport, and other MCP clients. The installer scripts use `RequestChoice` and were tested on Workbench 3.1 only.

## How it fits together

```
Claude Code ──MCP/stdio──► pi/amimcp-lsn ─► pi/amimcp-ro.py (filter, layer 2) ─► upstream amimcp.py
                                                                                     │ TCP 7846, token
                                                                                     ▼
                                                     Amiga: amiagent 0.13.2-lsn1 READONLY (layer 1)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). The security model, and what "read-only" does *not* protect, is in [docs/SECURITY.md](docs/SECURITY.md).

## Quick start

1. Build the agent and the installer disk: [docs/BUILD.md](docs/BUILD.md).
2. Install it on the Amiga and connect Claude Code: [docs/INSTALL.md](docs/INSTALL.md).

## Files

| Path | What |
|---|---|
| `Installeer`, `Verwijderen`, `AmiAgent Start`, `AmiAgent Stop`, `LeesMij` | AmigaDOS scripts on the disk (Dutch, as tested) |
| `patches/0001-amitcp3-v3.patch` | bsdsocket.library v3, so the agent starts on AmiTCP 3.x |
| `patches/0002-readonly.patch` | the compiled-in READONLY build |
| `patches/0003-tokenfile.patch` | `TOKENFILE=`: the token comes from a file, not the command line |
| `build/build-agent.sh`, `build/build-adf.py` | build from the pinned upstream commit; `build/agent.sha256` holds the tested binaries' hashes |
| `build/amiagent_icons.py` | draws the AmiAgent disk icon (a diskette with a magnifying glass) |
| `icons/` | the other disk icons in `.info` form: this project's own, drawn in code with `amiga/common/tools/icon.py`, except `amimon.info`, which is upstream's (made by its `tools/mkicon/mkicon.py`) |
| `LICENSE-amimcp`, `NOTICE-amimcp` | the Apache-2.0 licence text and NOTICE of upstream amimcp at `3145dee`, unchanged |
| `THIRD_PARTY_NOTICES.txt` | all third-party notices for the two executables on the disk (amimcp, the AmigaOS runtime, newlib, libnix, libgcc), verbatim; also put on the disk |
| `pi/amimcp-ro.py`, `pi/amimcp-lsn`, `pi/lsn-token` | filter, launcher and token generator for the server |
| `pi/mcp.example.json`, `pi/permissions.example.json` | example Claude Code configuration (no real values) |
| `tests/test_filter.py` | offline filter test, runs anywhere |
| `tests/lsntest.py` and helpers | the emulator suite E1–E10 (needs your own Amiberry harness and ROMs) |
| [docs/TESTS.md](docs/TESTS.md) | what was tested where, with results |

The helper tools on the disk come from the shared tools: `WiFiVraag`, `Geladen` and `VrijKB` are assembled from `amiga/common/tools/*.s`, and `CRCLijst` is the A600AirPrint binary (source in `amiga/a600/A600AirPrint/Docs/crclijst.c`).

## Known limitations

- **Read-only means read *everything*.** Whoever has the token can read every file, including the token file itself and any saved Wi-Fi or SMB passwords. AmigaOS has no users or file permissions to stop that.
- **The token travels in cleartext** over the LAN. There is no TLS in this build, and no limit on login attempts (the token has about 119 bits of entropy).
- **Port 7846 is open to the whole LAN** until you restrict it with AmiTCP `inet.access`. That was tested in the emulator, not on the real machine.
- **Bulk transfer over Wi-Fi is unreliable.** In two runs on the real A500 (18-10-2026), files of 20 KB and more started to time out after about 15 minutes; before that, the median was about 35 KB/s. After a demo had loaded the system, throughput stayed below 1 KB/s while small requests still worked. The bottleneck (wifipi.device, AmiTCP, the agent's send path or the Wi-Fi mesh) was not isolated. Use SMB or a disk image for backups.
- **One command at a time**, one connection at a time; a request has a 16 MiB frame limit (upstream).
- **"Read-only" still writes to RAM:** `EXEC` writes its output to `T:amiagent-*.out` and deletes it, and a lookup on a DEFER assign resolves that assign, as any `Lock` does.
- **The filter is stricter than the agent:** it accepts only `Avail`, `Version`, `ShowConfig` with that exact capitalisation, while the agent ignores case.
- **The installer is in Dutch** and installs to `Work:AmiAgent` only (300 KB free needed).

## Licence

| Part | Licence |
|---|---|
| amiagent and amimon (built from upstream), upstream `amimcp.py` (cloned at build time) | Apache-2.0, © 2026 Thomas Luebker. Licence text and NOTICE: [`LICENSE-amimcp`](LICENSE-amimcp), [`NOTICE-amimcp`](NOTICE-amimcp); both also go onto the disk |
| `patches/*.patch` (changes to upstream's `agent/amiagent.c`) | Apache-2.0. The patched source carries prominent `LSN 0001`/`0002`/`0003` notices that say what was changed and why (Apache-2.0 section 4(b)) |
| `icons/amimon.info` | Apache-2.0, upstream |
| Scripts, `pi/`, `build/`, `tests/*.py` and `*.sh`, the other icons | MIT, see the repository's [`LICENSE`](../../../LICENSE) |
| `README.md`, `docs/`, `tests/RESULTATEN-emulator-*.md` | CC BY 4.0, see [`LICENSE-docs`](../../../LICENSE-docs) |
| C runtime inside a built `amiagent`/`amimon` (AmigaOS runtime: MIT; newlib: BSD-style; libnix: public domain; libgcc: GPL-3.0 with the Runtime Library Exception) | their own licences: [`THIRD_PARTY_NOTICES.txt`](THIRD_PARTY_NOTICES.txt) and [`THIRD_PARTY.md`](../../../THIRD_PARTY.md) |

**Binary disk.** Since 19-10-2026 the AmigaOS-specific part of the C runtime has a stated licence (MIT, declared by its author). A built `AmiAgent-Installatie.adf` may therefore be passed on, provided it keeps `THIRD_PARTY_NOTICES` at the disk root and `AmiAgent/Docs/LICENSE-amimcp` and `NOTICE-amimcp`. `build-adf.py` puts them there. The two last points raised with the author (a generated two-line file without a header, and a generic "GPL V2" line in the amiga-gcc README) were resolved by him on 20-10-2026; see [`THIRD_PARTY.md`](../../../THIRD_PARTY.md), section "The C runtime inside amiagent and amimon".
