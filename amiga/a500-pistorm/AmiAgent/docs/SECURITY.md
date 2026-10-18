# AmiAgent security

## What is enforced, and by what

| Measure | Enforced by | Proven where |
|---|---|---|
| No writes, no input, no ARexx, no Ctrl-C to other processes | code in the agent (patch 0002, compiled in) | emulator E10 (50 checks, also with the filter bypassed); real A500: the build reports `lsn1 READONLY` |
| `EXEC` only `Avail`, `Version`, `ShowConfig`, no arguments | code in the agent | emulator E10 (including `Avail FLUSH`, `Avail >RAM:x`, a newline plus `Delete`, `C:Avail`) |
| `GET` only real files, no handlers or directories | code in the agent | emulator E10 (`CON:`, `RAW:`, `SER:`, `PIPE:`, a directory) |
| Token required; agent refuses to start without one | code in the agent | emulator E1/E2; real A500 |
| Token not on the command line or in `Status` | patch 0003 (`TOKENFILE=`) | emulator E2 |
| Only 11 read tools reach the agent | code on the server (`pi/amimcp-ro.py`) | `tests/test_filter.py` (32/32, offline); emulator E4; real A500 (`Dir` and `write_file` refused) |
| Agent address cannot be redirected | code on the server (`LSN_ALLOWED_HOSTS`) | `tests/test_filter.py`; emulator E4 |
| Only listed hosts reach port 7846 | AmiTCP `inet.access` (configuration on the Amiga) | emulator E3 only. **Not applied by the installer**; see below |
| Which tools Claude may use without asking | Claude Code permissions (configuration) | – |

## What it does not protect against

- **Anyone with the token can read every file on the Amiga.** That includes `Work:AmiAgent/Prefs/Token`, and passwords that other packages store (Wi-Fi, SMB). Protect the token as you would those passwords.
- **The token travels in cleartext.** Someone who can sniff your LAN can read it. Keep the agent on a network you trust and **never forward port 7846** from the internet.
- **Nothing limits login attempts.** A wrong token closes the connection, but a client may try again at once. With the generated 24-character token (about 119 bits) guessing is not practical; a short self-chosen token is.
- **Without `inet.access`, every device on the LAN can reach port 7846.** To restrict it, add lines like these to the active `AmiTCP/db/inet.access` and restart AmiTCP. They were tested in the emulator only:
  ```
  7846	192.168.1.145	allow	LOG
  7846	*.*.*.*		deny	LOG
  ```
- **Anyone on the server who can read the token can skip the filter.** Layer 1 (the agent) still refuses all writes.
- **Read-only is about the Amiga's disks.** The agent still uses memory, CPU and `T:` (in RAM:), and a heavy read load slows the machine down.

## Configuring your secrets (never in git)

| Secret | Where it lives | How it is made |
|---|---|---|
| AmiAgent token, server side | `~/.config/amiagent-lsn/token`, mode 600 | `pi/lsn-token` (24 characters from `secrets`; refuses to overwrite without `--nieuw`) |
| AmiAgent token, Amiga side | `Work:AmiAgent/Prefs/Token`, protection `r` | typed twice into `Installeer` (hidden input); never on the disk image |
| Amiga address | the `env` block of your MCP configuration | copy `pi/mcp.example.json` outside the repository, or use `claude mcp add ... -e AMIGA_HOST=...` |
| Test token (emulator suite) | `tests/testtoken`, mode 600 | created by `tests/lsntest.py` on first run |

The token never goes on the command line, into the audit log, into the MCP configuration or into a file in this repository. `.gitignore` excludes `out/`, `upstream/`, `log/`, `tests/testtoken`, `tests/resultaten/`, `*.local.json` and any file named `token`.

Before you publish a fork, run the project's scanner with your own list of private strings:
```sh
printf '%s\n' 'my-wifi-password' 'name:MySSID' > ~/.lsn-secrets      # outside the repository
python3 tools/publish-check.py --strict-ip amiga/a500-pistorm/AmiAgent
```

## Reporting a problem

Open an issue without secrets. For a vulnerability in amiagent itself, also tell upstream (github.com/thomas-luebker/amimcp).
