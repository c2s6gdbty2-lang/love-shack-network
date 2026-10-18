# Installing AmiAgent

You need the disk image you built yourself with [BUILD.md](BUILD.md) (it is not published, see the README, Licence), a running TCP/IP stack on the Amiga, and a Linux server that runs Claude Code (tested: Raspberry Pi 5). Replace every example address (`192.168.1.70` for the Amiga, `192.168.1.145` for the server) with your own.

## 1. Server: make the token

```sh
amiga/a500-pistorm/AmiAgent/pi/lsn-token
```

This writes a new 24-character token to `~/.config/amiagent-lsn/token` (mode 600) and shows it in groups of five for typing. It refuses to overwrite an existing token unless you pass `--nieuw`.

## 2. Amiga: install

1. Get `AmiAgent-Installatie.adf` onto the Amiga: a real floppy, a Gotek, or copied over the network and mounted.
2. Start your network first (for example Wi-Fi or a Plipbox). `AmiAgent Start` refuses to run without `bsdsocket.library`.
3. Open the disk and double-click **Installeer**.
   - It checks the disk, `Work:` and 300 KB of free space.
   - It asks for the token twice (hidden input; at least 16 characters, no spaces).
   - It installs only to `Work:AmiAgent`, checks every file with CRCLijst, and stores the token in `Work:AmiAgent/Prefs/Token` with protection `r`.
   - It never overwrites anything: if `Work:AmiAgent` exists, use **Verwijderen** first.
4. Open `Work:AmiAgent` and double-click **AmiAgent Start**. It listens on port 7846. **AmiAgent Status** shows activity; **AmiAgent Stop** stops it. After a reboot it is not running; nothing starts automatically.

The scripts and messages are in Dutch, as they were tested.

## 3. Optional: restrict port 7846 (inet.access)

See [SECURITY.md](SECURITY.md#what-it-does-not-protect-against). The installer does not do this for you. It was tested in the emulator only.

## 4. Server: connect Claude Code

```sh
cd amiga/a500-pistorm/AmiAgent && ./build/build-agent.sh      # also provides ./upstream/server/amimcp.py
claude mcp add amiga-a500 \
  -e AMIGA_HOST=192.168.1.70 -e LSN_ALLOWED_HOSTS=192.168.1.70 \
  -e LSN_MIN_INTERVAL=1.0 -e AMIGA_TIMEOUT=30 \
  -- "$PWD/pi/amimcp-lsn"
claude mcp list            # should show amiga-a500 as connected
```

Or copy `pi/mcp.example.json` outside the repository and fill it in. `amimcp-lsn` refuses to start without `AMIGA_HOST` and `LSN_ALLOWED_HOSTS`, without the token file, or if that file is not mode 600.

Optionally add the rules from `pi/permissions.example.json` to your Claude Code settings:
- `allow` lets Claude run `amiga_shell`, `amiga_system_info`, `amiga_screenshot` and `amiga_screens` without asking. Every other read tool still asks.
- `deny` blocks the upstream write tools by name. They would be refused by the filter and the agent anyway; the rule is a third layer.

Audit log: `~/.local/state/amiagent-lsn/audit.log` (override with `LSN_AUDIT_LOG`). It records each call and its arguments, never the token.

## 5. Check

In Claude Code, ask for the Amiga's system information. `amiga_system_info` should report `build lsn1 READONLY`. A request to write a file must be refused with `READONLY-filter: ...`.

## Removing

On the Amiga: **AmiAgent Stop**, then **Verwijderen** from the installer disk. It removes only `Work:AmiAgent` and `Work:AmiAgent.info`. On the server: `claude mcp remove amiga-a500`, and delete `~/.config/amiagent-lsn/token` if you no longer need it.
