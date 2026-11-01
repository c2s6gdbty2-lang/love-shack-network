# WRITE-SAFE security

## The model

**The server is not a security boundary.** Whoever can run commands as the server user can read the token and talk to the agent directly, so a filter there can only prevent mistakes. Every limit below is enforced by `amiagent-ws` on the Amiga. The only thing that opens writing is a local action at the machine.

## What is enforced

| Rule | How | Proven where |
|---|---|---|
| Explicit local yes/no | The mandate exists only as arguments of a process started by a script with a yes/no requester. Nothing on the network can start it: EXEC, ARexx, input and gadget commands stay refused | real A600; emulator |
| One mandate per process | Held in RAM only. It cannot be extended or re-armed. A second activation is refused. Once closed it stays closed, also if the clock is set back | real A600 (second activation); emulator (rest) |
| Session of at most 30 minutes | `WRITEMIN=30` in `Prefs/WriteSafe`; the agent caps it at 120 | emulator, with a 1-minute setting |
| At most 20 copies | `WRITEMAX=20`; the agent caps it at 100. A copy that reaches the writing stage counts even if it then fails. Requests refused beforehand do not count | emulator |
| Files up to 1024 KB | `MAXKB=1024`; the agent caps it at 4096 | emulator; 1024 KB exact and 1 byte over |
| Only `Work:Inbox` and folders inside it | The target is judged by what it **is** on disk: its lock is walked up with `ParentDir()`/`SameLock()` until it meets the held root lock. Assigns, `/` paths, device names, soft links, hard links and a second volume with the same name do not get around that | real A600 (`Work:S` refused); emulator (all) |
| Root must be safe | Refused at start: a volume root, anything containing or inside `S:`, `C:`, `L:`, `DEVS:`, `LIBS:`, `ENVARC:`, `SYS:WBStartup` or the agent's own folder, anything containing `SYS:`, and network or RAM volumes | emulator |
| No overwriting | Independent layers: a directory scan before the copy and again before the rename, which sees dangling links too; `Rename()`, which does not replace; and a live probe when the mandate is given, which refuses the mandate if `Rename()` would replace a file on this filesystem. The final name is never opened for writing | real A600 (`WS:EXISTS`); emulator, each layer alone, a race, and a negative control |
| Plain names only | Letters, digits, `. _ + -` and spaces, 30 characters at most, no `.info`, no leading dot | emulator |
| Only one source folder | A plain name inside `SRCROOT`, a real file, of the announced size and CRC32 | emulator |
| Only one client address | `CLIENT=` is compared with the peer address | emulator |
| Copy is verified | Read back from the local disk and compared by CRC32 before the rename. A failed copy leaves no final file | real A600 (byte-identical); emulator |
| Secrets not served | This build refuses to read the agent's `Prefs` folder and the folders in `NOREAD=`. A `NOREAD` folder that does not exist refuses the mandate | emulator |
| Everything logged | `Work:AmiAgent/Log/write.log`, and an audit log on the server with SHA-256 and CRC, never the contents. If the log cannot be written, no copy happens | real A600; emulator |
| Explicit end | **AmiAgent Schrijven Uit**, Ctrl-C, or a restart. There is no autostart | real A600 |
| Back to READONLY | **AmiAgent Schrijven Uit** starts the unchanged READONLY agent and a refused mandate restores it | real A600; emulator |

**What this is not.** It adds one command, COPYIN. PUT, EXEC beyond the fixed three words, ARexx, mouse, keyboard, gadget and menu commands all stay refused, also during a mandate. There is no general remote write access and no remote control of Workbench. It cannot overwrite, delete, rename, create folders or set protection bits.

## Known limitations

- **The READONLY agent can read sensitive files.** Anyone with the token can use the normal `amiagent` to read `Prefs/Token`, the SMB password and any other file. Only `amiagent-ws` blocks those folders. This is a known issue of the read-only build and is not fixed here.
- **WRITE-SAFE depends on a working share.** If the share is gone, COPYIN fails cleanly. There is nothing to copy from.
- **A hanging share can prevent the return to READONLY.** While the server hangs, the agent does not answer and does not react to Ctrl-C. **AmiAgent Schrijven Uit** then says so and deliberately does not start READONLY. When the server returns the copy finishes or aborts. If it never does, restart the Amiga, which also ends the mandate. That script path was not exercised; the hang itself was tested in the emulator.
- **FFS and power loss.** If the power fails during a write, FFS may fail to validate the volume ("Error validating") and it stays read-only until repaired. In the emulator this happened in 6 of 6 cuts during a 1 MB copy: 3 with the standard `C:Copy` and 3 with `amiagent-ws`. It is not specific to this tool, but on a machine that boots from `Work:` it can stop the machine from starting. Keep a backup. If the cut comes after the temporary file is on disk, the volume stays valid and the next mandate removes the leftover.
- **The IconX console window.** `amiagent` writes to the console, so a small window stays until you close it. Closing it does not stop the agent. The agent's output does not reach `T:AmiAgent*.log`, so the reason for a refused mandate is only visible when you run the script from a Shell.
- **Cleartext token.** As in AmiAgent, the token and all traffic are unencrypted. Someone who can sniff the LAN and fake the client address can write to the Inbox during a session.
- **The requester text is fixed.** It says 30 minutes and 20 files. If you change `Prefs/WriteSafe`, the text no longer matches the mandate.
- **CRC32 detects mistakes, not tampering** on the share.
- **A folder on the share can be written by every Amiga using it.** Use one folder per machine.
