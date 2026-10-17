# RetroMount – the server's Amiga library as `Retro:`

RetroMount mounts the server's SMB share `AmigaLibrary` on the Amiga as the volume `Retro:`. It uses **smbfs** (Olaf Barthel, GPL-2.0, version 2.22), which is not included; see [`THIRD_PARTY.md`](../../THIRD_PARTY.md).

```
Run >NIL: smbfs SHARE=//<server>/AmigaLibrary USER=<amiga-user> PASSWORD=<password> VOLUME=Retro PROTOCOL=nt1
```

**Security model:**
- The Amigas log in with a separate, restricted account.
- On the server that share is **read-only**.
- The password is stored on the Amiga in plain text. That is a limitation of smbfs and AmigaDOS scripts.
- Never publish or share the script that contains it. Every script in this repository uses `@@PASSWORD@@`.

## A500 rev. 5 (Wi-Fi)

The *RetroMount* icon in WiFiNet:
- starts Wi-Fi first if it is not running;
- then waits until `Retro:` exists;
- reports the result.

*StopWiFi* unmounts it again. Proven on 13-10-2026.

## A600 – the existing, working installation

Documented from observation. **The script itself was not collected**: it holds the password, and no replacement is made without the owner's permission.

| Observation (16-10-2026) | Source |
|---|---|
| Icon *Mount Retro* in `Work:`, next to *Start Plipbox* | photo of the Work: window |
| Window "Mount Retro" shows `A600 Retro Mount` and `Checking network... OK`, then stays open while `Retro:` is mounted | photos during the print tests |
| The `Retro:` volume appears on the Workbench. Listing and copying in a Shell work, also while a colour page is printing. | owner, photos |
| Not started from any startup file: the keyword scan of `S:` found no `smbfs` or `Retro` | Controle report |
| The window has to stay open, so the mount probably runs in the foreground of that window. Closing the window probably ends `Retro:`. | **assumption**, to be confirmed |

An earlier A600 network boot disk (A600Net v8–v12) used the same smbfs parameters in `S:MountRetroAuto`, started in the background 75 s after boot. Its server address and password are not reproduced here.

**To do, with the owner's permission:** copy the *Mount Retro* script from the A600, remove the password, and document it here.
