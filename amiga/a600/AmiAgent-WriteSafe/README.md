# AmiAgent WRITE-SAFE: one new file, by local permission

WRITE-SAFE is a separate, optional build of [AmiAgent](../../a500-pistorm/AmiAgent/). It lets an AI assistant (Claude Code, through MCP) place **new** files in one folder on a real Amiga, but only after someone at the machine has said yes.

AmiAgent itself stays read-only and stays the default. WRITE-SAFE is not a switch inside the READONLY binary: `amiagent` (`bb2f0daf…`) is unchanged and contains no write code. `amiagent-ws` is a second binary that you start on purpose, for one session.

| Status | What |
|---|---|
| ✅ **Proven** | Stock Amiga 600 (details below): first copy, overwrite refusal, path refusal, end of mandate, both Workbench icons, return to READONLY |
| 🧪 **Emulator-tested** | Everything in [docs/TESTING.md](docs/TESTING.md), including network failures, full disks and power loss |
| ⚠️ **Not tested** | Any other Amiga. The read-only AmiAgent has run on other machines; this build has not |

## Tested configuration

Only this one. Anything else is untested.

| | Real hardware (01/02-11-2026) | Emulator |
|---|---|---|
| Machine | Amiga 600, 68000 at 7 MHz, 2 MB chip + 4 MB fast | Amiberry, same CPU and memory, cycle-exact |
| ROM / OS | Kickstart 40.63, Workbench 3.1 (40.42) | same |
| Disk | 8 GB CF; `Work:` is also the boot volume | FFS hard disk images |
| TCP/IP | AmiTCP 3.0b2 with a Plipbox | AmiTCP 3.0b2 on a2065 (slirp) |
| Source of files | `AmigaShare:` (smbfs 2.22) on a Raspberry Pi 5 | smbfs 2.22, test Samba |

## Requirements

- AmiAgent installed in `Work:AmiAgent` (the installer in [`../../a500-pistorm/AmiAgent/`](../../a500-pistorm/AmiAgent/)), with a token.
- `Work:` on a local OFS/FFS volume. Network and RAM volumes are refused.
- A working TCP/IP stack with `bsdsocket.library` v3 or newer.
- A network share mounted as `AmigaShare:` with a folder `WriteSafe/<machine>`; see [`docs/AmigaShare.md`](../../../docs/AmigaShare.md).
- On the server: Python 3, the upstream `server/amiga.py`, and `sudo` rights to write the share as its owner (or `LSN_WS_SUDO=` empty if your user can write there).

## Install

1. Get `amiagent-ws` from the release assets and compare it with `build/agent.sha256`, or build it (see below).
2. Copy `Prefs/WriteSafe.example` to `Prefs/WriteSafe` and set `CLIENT=` to your server's address. Keep the name `WriteSafe`.
3. Put the files on the share and copy them into `Work:AmiAgent/`. Give the **full target name**, because `Copy` keeps the capitals you type and those become the icon names:

   ```
   Copy AmigaShare:WriteSafe/a600/amiagent-ws Work:AmiAgent/amiagent-ws
   Copy AmigaShare:WriteSafe/a600/Prefs/WriteSafe Work:AmiAgent/Prefs/WriteSafe
   Copy "AmigaShare:WriteSafe/a600/AmiAgent Schrijven Aan" "Work:AmiAgent/AmiAgent Schrijven Aan"
   Copy "AmigaShare:WriteSafe/a600/AmiAgent Schrijven Aan.info" "Work:AmiAgent/AmiAgent Schrijven Aan.info"
   Copy "AmigaShare:WriteSafe/a600/AmiAgent Schrijven Uit" "Work:AmiAgent/AmiAgent Schrijven Uit"
   Copy "AmigaShare:WriteSafe/a600/AmiAgent Schrijven Uit.info" "Work:AmiAgent/AmiAgent Schrijven Uit.info"
   ```

4. On the server, register `pi/mcp-amiga-ws.example.json` with Claude Code after filling in your paths and address. It reuses the AmiAgent token file `~/.config/amiagent-lsn/token-<machine>`. Set `LSN_UPSTREAM_DIR` to the `server` folder of an amimcp clone at the pinned commit (AmiAgent's build makes one in `../../a500-pistorm/AmiAgent/upstream`), `LSN_WS_STAGE` to the share folder on the server, and `LSN_WS_OUTBOX` to the folder files may be sent from.

`Work:Inbox` and `Work:AmiAgent/Log` are created the first time a mandate is given. There is no autostart, and there should never be one.

## Using it from Workbench

The scripts and their messages are in Dutch: they are the tested originals. Two icons appear in the `AmiAgent` drawer.

| Icon | Meaning | What happens |
|---|---|---|
| 🔓 **AmiAgent Schrijven Aan** ("write on") | open padlock | Asks yes or no at the machine. On yes: stops the READONLY agent and starts `amiagent-ws` with the mandate |
| 🔒 **AmiAgent Schrijven Uit** ("write off") | closed padlock | Stops `amiagent-ws`, starts the READONLY agent again, confirms |

A small console window stays open while an agent that was started this way runs. Closing it is safe, the agent keeps running. The open padlock stays highlighted during the session. Closing the "WRITE-SAFE is actief" requester does **not** end the session.

## Remove

Use **AmiAgent Schrijven Uit**. Then delete `amiagent-ws`, the two scripts, their `.info` files and `Prefs/WriteSafe` from `Work:AmiAgent`. `AmiAgent Start` and `AmiAgent Stop` still work. `Work:Inbox` and `Work:AmiAgent/Log` hold your files and the log; remove them yourself if you want to.

## How it fits together

```
Claude Code ─MCP/stdio─► pi/amimcp-ws-lsn ─► pi/amimcp-ws.py ─ stages the file on the share
                                                 │ TCP 7846, token, COPYIN
                                                 ▼
Amiga: amiagent-ws (READONLY build + COPYIN) ── reads AmigaShare:WriteSafe/<machine>
                                                 │ only under a local mandate
                                                 ▼
                                            Work:Inbox
```

COPYIN carries no file data over the agent connection: the Amiga fetches the file from the share itself. The server filter adds no authority. Every rule that matters is enforced on the Amiga, see [docs/SECURITY.md](docs/SECURITY.md).

## Build

`amiagent-ws` is upstream amimcp at the same pinned commit as AmiAgent, with patches `0001`–`0003` from AmiAgent and `patches/0004-writesafe.patch`, with `src/writesafe.c` copied next to `amiagent.c`:

```
make -s amiagent CC="m68k-amigaos-gcc -DAMIAGENT_READONLY -DAMIAGENT_WRITESAFE"
```

Without `-DAMIAGENT_WRITESAFE`, patch 0004 changes nothing: the READONLY build stays byte-identical to `bb2f0daf…`. That check was part of every test build. The extra flag `-DAMIAGENT_WS_TEST` adds fault injection for the emulator. Never use that build on a real machine. The release binary does not contain the hooks; it still accepts and ignores a `TESTHOOK=` argument.

## Licence

| Part | Licence |
|---|---|
| `patches/0004-writesafe.patch`, `src/writesafe.c` (changes to upstream's agent) | Apache-2.0, see `LICENSE-amimcp` and `NOTICE-amimcp` in [`../../a500-pistorm/AmiAgent/`](../../a500-pistorm/AmiAgent/) |
| Scripts, icons, `pi/`, `Prefs/`, `build/` | MIT, see the repository's [`LICENSE`](../../../LICENSE) |
| `README.md`, `docs/` | CC BY 4.0, see [`LICENSE-docs`](../../../LICENSE-docs) |
| C runtime inside the binary | see [`THIRD_PARTY_NOTICES.txt`](THIRD_PARTY_NOTICES.txt) |
