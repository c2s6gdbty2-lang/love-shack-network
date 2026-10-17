# The Love Shack Network

> ### *Combining the future with the past, in the now.*
> ### *Keeping the soul of the machine alive.*

The Love Shack Network is a home network of original retro computers built around a Raspberry Pi 5 retro server:
- a Commodore Amiga 500 rev. 5 and an Amiga 500 rev. 6A;
- a Commodore Amiga 600;
- an Atari 800XL with FujiNet;
- a Commodore 64 Ultimate.

It documents working, reproducible ways to give unmodified classic machines modern network features: shared file storage, and direct printing to a current network printer.

Every solution here was first built and tested in an emulator. It is called *proven* only after it ran on the real machine.

## Principles

The two lines at the top are the project's guiding principles. In practice they mean:

1. **Preserve the original hardware.** No permanent modifications. Every installer can be undone and leaves the existing configuration untouched.
2. **Standalone first.** Each machine still works fully without a network. Networking is an extension you start by hand.
3. **Local protocols and open standards.**
   - SMB for files.
   - IPP with PWG Raster for printing.
   - Plipbox, Wi-Fi and SLIP for transport.
   - No cloud services.
4. **Reproducible.** Every package comes with:
   - a build script and checksums;
   - a read-only pre-check;
   - an installer that makes a backup first;
   - a remover that restores the previous state.
5. **Honest status.** Each feature is labelled with one of these statuses:

| Status | Meaning |
|---|---|
| ✅ **Proven** | Built, tested in an emulator, and confirmed on real hardware |
| 🧪 **Emulator-tested** | Works in Amiberry; real-hardware test still open |
| 🛠️ **Built** | Package exists; testing incomplete |
| 📋 **Planned** | Design or idea only |

## What works today

| Machine | Network | Files | Printing | Status |
|---|---|---|---|---|
| Amiga 500 rev. 5, PiStorm (Pi 3A+, Emu68), Framethrower | Wi-Fi WPA2 (WiFiPi.device + PR #1, WirelessManager, AmiTCP 3.0b2) | RetroMount (`Retro:`) | AmiAirPrint → IPP → printer | ✅ |
| Amiga 600, 68000 at 7 MHz, no accelerator | Plipbox, AmiTCP 3.0b2 | RetroMount | AmiAirPrint → IPP → printer | ✅ |
| Amiga 500 rev. 6A, TerribleFire TF536 | Wodem, SLIP at 19200 baud | RetroMount | – | 🧪 / 🛠️ |
| Atari 800XL, FujiNet | Wi-Fi (FujiNet) | FujiNet | FujiNet printer → server watcher → CUPS | ✅ |
| Commodore 64 Ultimate | Ultimate network | FTP | Ultimate printer → server spooler → CUPS | ✅ |
| Raspberry Pi 5 retro server | LAN | Samba, FTP | CUPS queue, print watchers | ✅ |

See [`docs/architecture/`](docs/architecture/) for the network architecture, [`docs/hardware/`](docs/hardware/) for each machine and [`docs/issues/`](docs/issues/) for known technical issues.

## Computerfluid Computing

> ***Born on one platform. Free to compute as another.***

**Computerfluid** *(adjective, computing)*: a state or characteristic of a computer system in which its functional platform identity is not exclusively determined by its original hardware architecture, allowing it to operate as, emulate, or interact with multiple computing platforms.

The Love Shack Network puts this into practice. For example, the Amiga 500 rev. 5 runs AmigaOS on an emulated 68000 CPU, provided by a Raspberry Pi in its CPU socket. The original Amigas also share one file library with modern computers.

*The Love Shack Network: Where All Tastes of Computers Meet.*

Read the full definition, the Dutch definition, the three identities (hardware, software and network), realised and possible examples, and the origin of the term and the project name in [`docs/COMPUTERFLUID.md`](docs/COMPUTERFLUID.md).

## Featured examples

### [Amiga 600: direct IPP printing over a Plipbox, no coprocessor](amiga/a600/)
A stock 68000 Amiga 600 prints from any Workbench program straight to the network printer.
- **Proven** on the real machine, on paper.
- The public disk image was **retested in a clean emulator**: its print jobs are byte-identical to those of the tested original.

### [Amiga 500 with PiStorm: Wi-Fi, RetroMount and direct printing](amiga/a500-pistorm/)
- WPA2 Wi-Fi through the Pi's own wireless chip.
- `Retro:` from the server.
- The same printing route as on the A600.

Making this work required two documented fixes: a Wi-Fi driver fix and an OS 3.1 fix for the printer driver.

## Releases

| Image | Contents |
|---|---|
| `A600AirPrint-public.adf` | A600AirPrint 1.0. The printer address is a placeholder; rebuild the image with [`amiga/build/build_public.py`](amiga/build/), or set the address after installation. |
| `AirPrintPS-public.adf` | AirPrintPS 1.0, direct route only. Same configuration method. |

The images contain only this project's files plus the MIT-licensed AmiAirPrint binaries. They contain **no** Workbench files, ROMs, TCP/IP stack or credentials.

## Repository layout

```
docs/COMPUTERFLUID.md  the Computerfluid Computing concept
docs/architecture/   network architecture, diagrams, address plan
docs/hardware/       one page per machine
docs/issues/         known technical issues (analysis, no unapproved fixes)
amiga/a600/          A600AirPrint package (tested files, network details as tokens) + guide
amiga/a500-pistorm/  AirPrintPS package + guide (Wi-Fi and RetroMount documented)
amiga/a500-tf536/    status only (not in this release)
amiga/build/         build_public.py and network.example.ini
amiga/common/tools/  icon.py (Amiga icons), asm68k.py (small 68000 assembler)
printing/            print routes; AmiAirPrint patch, licence, provenance
networking/          AmiTCP, Plipbox, Wi-Fi patch + WiFiLink, RetroMount
server/              retro server: Samba layout, print watchers + systemd units
tests/               anonymised test reports and screenshots
images/              photos of the real-hardware tests (metadata removed)
tools/               publish-check.py, the pre-publication scanner
```

## Not in this repository

- **Kickstart ROMs or Workbench files.** Use your own legally obtained copies.
- **Third-party binaries in git, except the MIT-licensed AmiAirPrint.**
  - AmiTCP, plipbox.device, smbfs and WirelessManager are GPL. Download them; [`THIRD_PARTY.md`](THIRD_PARTY.md) lists sources and the SHA-256 of each tested version.
  - The Wi-Fi driver fix is only referenced (upstream PR #1), because its licence terms are not established.
- **Credentials or private network data.**
  - Scripts use `@@PASSWORD@@`.
  - Addresses in the documentation are examples (`192.168.1.x`).
  - `tools/publish-check.py` scans every commit, including inside ADFs and archives.

## Language

The Amiga scripts and their on-screen texts are **Dutch**. They are the exact files that were tested on real hardware, and they are deliberately not translated. The documentation is in English and explains every message.

## Licence

| Part | Licence |
|---|---|
| Original code | MIT, see [`LICENSE`](LICENSE) |
| Original documentation and photos | CC BY 4.0, see [`LICENSE-docs`](LICENSE-docs) |
| [`docs/COMPUTERFLUID.md`](docs/COMPUTERFLUID.md) | MIT, see [`LICENSE`](LICENSE) |
| Third-party components | their own licences, see [`THIRD_PARTY.md`](THIRD_PARTY.md) |

## Trademarks

- Amiga is a trademark of Amiga Corporation. Atari and Commodore are trademarks of their respective owners.
- **AirPrint is a trademark of Apple Inc.** The package names A600AirPrint and AirPrintPS come from AmiAirPrint, on which they are based. The printing route uses the open IPP/2.0 standard with PWG Raster. It is **not supported or certified by Apple**.
- This project is not affiliated with any of these companies.
