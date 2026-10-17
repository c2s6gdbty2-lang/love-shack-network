# Retro server

Hardware, services and a diagram: [`docs/hardware/retroserver.md`](../docs/hardware/retroserver.md).

## Print watchers ([`retro-print/`](retro-print/))

Each 8-bit machine gets a small shell script, run by a systemd timer. Each script:
- **polls** the device;
- **downloads** the print-out;
- **deduplicates** it, and prints it through the local CUPS queue;
- **archives** the result.

When a device is switched off, only the state change is logged.

| Script | Device | Interval | Dedup / safety |
|---|---|---|---|
| `fujinet/fujinet-print-watch.sh` | FujiNet, `GET http://<fujinet>/print` | 45 s | SHA-1 of the PDF (FujiNet keeps returning the last print-out) |
| `c64ultimate/c64ultimate-print-spooler.sh` | Ultimate, FTP `USB1/` | 30 s | prints only after two identical downloads, then deletes the remote file; ignores files older than a set time |
| `meatloaf/meatloaf-print-watch.sh` + `repair_meatloaf_pdf.py` | Meatloaf, HTTP from the SD card | 60 s | rebuilds a valid PDF from the text lines |

**Install on your own server.** Copy each folder to `/opt/retro-print/<name>/`. Copy `*.conf.example` to `*.conf` and enter your device address and CUPS queue name. Install the units from `systemd/`; they use the account `retro`, so adjust it. Then run `systemctl enable --now <name>.timer`.

**Remove.** `systemctl disable --now <name>.timer`, then delete the folder. CUPS itself is not changed by these scripts.

The scripts are copies of the working ones. Only the device addresses and the service account were replaced. Provenance of each file (owner's originals, the port, the assistant's changes) and the replacements: [`retro-print/PROVENANCE.md`](retro-print/PROVENANCE.md).

## Samba layout

| Share | Path | Access |
|---|---|---|
| `AmigaLibrary` | `retro-files/Amiga/amiga` | the Amiga account, **read-only**; this is `Retro:` |
| `RetroFiles` | `retro-files` | owner, read/write |
| `PrintServer` | `printserver` | owner, read/write (spool drop for the planned fallback) |

Use the SMB1/NT1 dialect for smbfs 2.22 (`PROTOCOL=nt1`), and limit that to the LAN.
