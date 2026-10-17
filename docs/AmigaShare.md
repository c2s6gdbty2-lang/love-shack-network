# AmigaShare: Shared Read/Write Network Volume

`AmigaShare:` is a normal, writable volume in Workbench and the Shell. The files live centrally on the retro server, and every Amiga that mounts the volume sees the same files.

It sits next to the read-only `Retro:` volume, which stays unchanged.

| Part | Status |
|---|---|
| Server share | ✅ Active, tested with `smbclient` |
| Amiga package (AmigaShare 1.0) | ✅ Proven on real hardware, 17-10-2026: Amiga 500 rev. 5 with PiStorm over Wi-Fi, and Amiga 600 over Plipbox, both mounted at the same time |

> Addresses and names below are examples. No password is stored in this repository or on the install disk. The install disk itself is not in this repository, because it contains GPL binaries (smbfs, AmiTCP `ping`); see [`THIRD_PARTY.md`](../THIRD_PARTY.md).

## Server (Samba)
1. Create a folder on the data disk, not on the system volume. Give it to the existing Samba user that the Amigas already use:
   ```sh
   sudo install -d -o amiga -g amiga -m 2770 /mnt/retro/AmigaShare
   ```
2. Add one share block to `/etc/samba/smb.conf`. The existing shares are not changed.
   ```ini
   [AmigaShare]
      comment = Shared read/write space for the Amigas (smbfs)
      path = /mnt/retro/AmigaShare
      read only = no
      guest ok = no
      valid users = amiga
      force user = amiga
      force group = amiga
      create mask = 0660
      directory mask = 2770
      follow symlinks = no
      root preexec = /usr/bin/mountpoint -q /mnt/retro
      root preexec close = yes
   ```
3. Check and reload: `testparm -s`, then `sudo smbcontrol smbd reload-config`. Open sessions stay connected.

What this gives you:
- **No guest access.** Only the user `amiga` can connect.
- **No escape.** `wide links` is off by default and `follow symlinks = no` blocks symlinks, so nothing outside the folder is reachable.
- **Data disk only.** `root preexec` refuses every connection while the data disk is not mounted, so nothing can end up on the SD card.
- **Undo.** Remove the block and reload; the folder and its files stay.

## Amiga
**Requirements:**
- AmiTCP 3.0b2 with a working connection: Wi-Fi, Plipbox or another route;
- Workbench 3.1;
- a `Work:` volume.

**Installation.** Open the disk *AmigaShare-Installatie* and choose **Installeer**.
1. Answer three questions:
   - which Amiga this is: *A500 PiStorm*, *A600* or another;
   - the server address;
   - the password of the Samba user, entered twice and shown as asterisks.
2. Everything goes into `Work:AmigaShare` only. The startup-sequence, `ENVARC:`, `RetroMount` and the network packages are not changed.
3. *Verwijderen* removes only `Work:AmigaShare`. The files on the server stay.

The same disk works on every Amiga, because the per-machine settings live in `Work:AmigaShare/Prefs`.

| Icon | What it does |
|---|---|
| **AmigaShare Mount** | 1. Checks the connection with a real ping to the server.<br>2. If a network is already running, Wi-Fi or Plipbox, it reuses it and never starts a second AmiTCP.<br>3. If no network is running: on the PiStorm A500 it starts Wi-Fi first (`StartWiFi`); on other Amigas it asks you to start the network yourself.<br>4. Mounts `AmigaShare:` with smbfs 2.22 (`DEVICE=SHARESMB`), then writes and deletes a unique temporary file to prove it can write. |
| **AmigaShare Stop** | Unmounts only `AmigaShare:`. `Retro:` and the network keep running. |

## Real-hardware test (17-10-2026)

| Step | Result |
|---|---|
| Install and **AmigaShare Mount** on the A500 (Wi-Fi) | ✅ The write check passed |
| Copy a file from `RAM:` to the share and read it back | ✅ CRC32 identical |
| Rename, a `.info` icon, a 34-character name | ✅ The icon is visible in Workbench; the server copy is byte-identical |
| A600 (Plipbox) reads the A500's file, renames it and writes a new one | ✅ CRC32 identical |
| A500 reads the A600's file | ✅ CRC32 identical |
| `Retro:` keeps working next to `AmigaShare:` on both machines | ✅ |
| Test files and drawer deleted from the Amiga | ✅ |

## Limitations

| Topic | Behaviour |
|---|---|
| Works | Reading, writing, renaming and moving files; creating and deleting drawers; `.info` icons (stored as ordinary files, byte for byte) |
| Not kept | Amiga protection bits `s`, `p` and `e`, and file comments (`FileNote`). Scripts started with IconX or `Execute` do not need the `s` bit. |
| Long names | Up to 255 characters work on `AmigaShare:`. A name longer than 30 characters cannot be copied to an FFS disk, and some older programs cannot handle such names. |
| Case | Not case-sensitive, like AmigaDOS. |
| Dates | smbfs converts times using the Locale time zone. If Locale has the wrong zone, the times shown are off by hours; on the test A500 they were 7 hours off. An Amiga without a battery clock writes dates that are wrong. |
| Disk icon | Workbench may save a `Disk.info` on the share for the volume icon. That is normal; leave it. |
| Simultaneous use | smbfs is single-threaded. Do not edit the same file on two Amigas at the same time. |
| Stopping | While `AmigaShare:` is mounted, AmiTCP refuses to stop. Choose **AmigaShare Stop** first, or switch the machine off. |
| Credentials | `Work:AmigaShare/Prefs/Wachtwoord` holds the password in plain text. The installer protects it against deletion and execution, but AmigaOS has no user accounts. Do not share that drawer. |
