# AmiAgent architecture

```
┌──────────────┐  MCP (JSON-RPC over stdio)  ┌───────────────────────── server (Raspberry Pi) ─────────────────────────┐
│ Claude Code  │ ──────────────────────────► │ pi/amimcp-lsn                                                           │
│ (layer 3:    │                             │   reads ~/.config/amiagent-lsn/token (mode 600), checks AMIGA_HOST      │
│  permissions)│ ◄────────────────────────── │   └─► pi/amimcp-ro.py   READONLY filter (layer 2), audit log            │
└──────────────┘                             │         └─► upstream/server/amimcp.py   (child process, unchanged)      │
                                             └──────────────────────────────┬──────────────────────────────────────────┘
                                                                            │ TCP 7846: framed binary protocol,
                                                                            │ AUTH with the shared token (cleartext)
                                             ┌──────────────────────────────▼──────────────────────────────────────────┐
                                             │ Amiga: AmiTCP 3.0b2 (optional inet.access, layer 0)                     │
                                             │   amiagent 0.13.2-lsn1 READONLY (layer 1), started by "AmiAgent Start"  │
                                             │   with TOKENFILE=Work:AmiAgent/Prefs/Token                              │
                                             └─────────────────────────────────────────────────────────────────────────┘
```

## Layers

| Layer | Where | Enforced by | Does |
|---|---|---|---|
| 0 | AmiTCP `inet.access` | the TCP stack, before the agent sees the connection | only listed hosts may connect to port 7846. **Optional; not applied on the tested real machine** |
| 1 | `amiagent` READONLY build | compiled code (patch 0002) | refuses `PUT`, `AREXX`, `INPUT`, `UIACT`, `BREAK`; `EXEC` only `Avail`/`Version`/`ShowConfig` with a fixed command line; `GET` only real files; refuses to start without a token |
| 2 | `pi/amimcp-ro.py` | code on the server | lists and forwards only 11 read tools; `amiga_shell` only the three exact words; screenshots forced to the agent's own capture (no program runs on the Amiga); device paths refused; `AMIGA_HOST` must be in `LSN_ALLOWED_HOSTS`; one call at a time; audit log without the token |
| 3 | Claude Code permissions | configuration | which tools may run without asking (see `pi/permissions.example.json`) |

Layer 1 is the one that matters: a client that skips layers 2 and 3 still cannot write. That was shown in the emulator (E10: every write channel sent straight over the protocol was refused, and Work: and RAM: were byte-identical afterwards).

## The 11 tools that pass the filter

`amiga_shell` (Avail, Version, ShowConfig), `amiga_system_info`, `amiga_list_dir`, `amiga_read_file`, `amiga_screenshot`, `amiga_screens`, `amiga_pointer`, `amiga_region_changed`, `amiga_ui_tree`, `amiga_menus`, `amiga_rexx_ports`. Any other upstream tool, including future ones, is hidden and refused (allowlist).

## On the Amiga

`Installeer` creates only `Work:AmiAgent` (plus, after a Yes, the drawer icon `Work:AmiAgent.info`). Nothing starts automatically: there are no changes to the Startup-Sequence, User-Startup, WBStartup, ENVARC:, DEVS: or the network packages. `AmiAgent Start` refuses to run without a running `bsdsocket.library`, and refuses a second copy. `AmiAgent Stop` sends Ctrl-C to the agent only. `Verwijderen` removes `Work:AmiAgent` and refuses while the agent runs.

## Build

The agent is built from the pinned upstream commit `3145dee` plus `patches/` (see [BUILD.md](BUILD.md)). Upstream is not copied into this repository.
