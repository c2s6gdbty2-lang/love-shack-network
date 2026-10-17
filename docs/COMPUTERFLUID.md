# Computerfluid Computing

> ### *Born on one platform. Free to compute as another.*
>
> **The Love Shack Network: Where All Tastes of Computers Meet.**

## Definition

**Computerfluid** *(adjective, computing)*

> A state or characteristic of a computer system in which its functional platform identity is not exclusively determined by its original hardware architecture, allowing it to operate as, emulate, or interact with multiple computing platforms.

**Nederlandse definitie**

> Een toestand of eigenschap van een computersysteem waarbij de functionele platformidentiteit niet uitsluitend wordt bepaald door de oorspronkelijke hardwarearchitectuur, waardoor het systeem als meerdere computerplatformen kan functioneren, deze kan emuleren of ermee kan samenwerken.

*Computerfluid Computing* is the practice of building and using computerfluid systems.

## Background and philosophy

Computerfluid describes the freedom to let classic and modern computers work beyond their original platform boundaries.

The Love Shack Network illustrates this philosophy. It connects:
- original retro hardware;
- modern network services;
- shared storage;
- emulated computer systems.

It does this without giving up the project's [principles](../README.md#principles): the original hardware is preserved, and every machine still works on its own.

### Three identities

A computer in this network can be described by three separate identities:

| Identity | What it is | Example |
|---|---|---|
| **Hardware identity** | The physical computer architecture | An Amiga 500 board with a Raspberry Pi 3A+ in its CPU socket (PiStorm) |
| **Software identity** | The operating system or emulated platform | AmigaOS 3.1 on a 68000-compatible CPU, provided by the Emu68 emulator on the Pi's ARM processor |
| **Network identity** | How the system communicates and shares files | An AmiTCP host on the home Wi-Fi that mounts `Retro:` over SMB and prints over IPP |

Computerfluid does **not** mean that these three identities must be the same.

## Examples

The examples are split into what has actually been built in The Love Shack Network and what is technically possible but not done or not tested. Status labels follow the [README](../README.md#principles) where they apply.

### Realised

| Example | Hardware → software → network | Status |
|---|---|---|
| **Amiga 500 rev. 5 with PiStorm** | An ARM Raspberry Pi 3A+ in the 68000 socket runs Emu68, so the Amiga's CPU is itself emulated. The machine runs AmigaOS 3.1 and joins the network over the Pi's own Wi-Fi chip. See [`amiga/a500-pistorm/`](../amiga/a500-pistorm/). | ✅ Proven on real hardware (13- and 14-10-2026) |
| **Original Amigas and a modern Mac sharing one library** | The Amiga 500 rev. 5 and the Amiga 600 mount the server's `AmigaLibrary` share as `Retro:`. The owner's computers, including a Mac, reach the same files through the `RetroFiles` share, of which `AmigaLibrary` is a read-only subfolder. See [`docs/architecture/overview.md`](architecture/overview.md#storage-layout-on-the-server). | ✅ `Retro:` proven on both Amigas. Mac access is the owner's normal SMB use and was not part of the formal tests. |
| **Atari ST(E) emulation on the retro server** | The Raspberry Pi 5 retro server runs Hatari with EmuTOS. Its disks and hard-disk folders live in the central retro storage (`retro-files/Atari ST/`). The same Pi also runs Amiberry. | Set up and in use on the server; tested 08- and 09-10-2026. It is not part of this repository's packages. |
| **Physical and emulated machines working together** | The Amigas, an Atari 800XL with FujiNet and a Commodore 64 Ultimate share one server and one network printer. FujiNet and the C64 Ultimate themselves emulate disk drives and printers in modern hardware. See [What works today](../README.md#what-works-today). | ✅ Proven, per machine as listed in the README |

### Possible extensions (not built or not tested)

| Example | Why it is possible | Open points |
|---|---|---|
| **The PiStorm Amiga running emulators of other platforms** | With Emu68 the A500 rev. 5 has far more CPU power than a stock Amiga, so emulators of other computers that run under AmigaOS become practical. | Not tried. Which emulators run well under Emu68 is not established. |
| **A Commodore 64 emulator on an Amiga, using `Retro:`** | `Retro:` is an ordinary AmigaDOS volume. A C64 emulator for AmigaOS that can open disk images from an AmigaDOS path could load them straight from the server's `Commodore 64/` folder. | Only if the emulator supports this. `AmigaLibrary` is read-only and currently contains only the Amiga tree, so the share layout would need a decision first. Not tested. |
| **The Atari ST emulation sharing files with the Amigas** | Hatari and the Amiga share live on the same server disk. | No shared exchange folder has been set up. |

Nothing in the second table is presented as working. When one of these is built and tested, it moves to the first table with its own test report.

## Origin of the term

The term *Computerfluid* and the definition above were formulated on 17 October 2026, during a discussion within the development of The Love Shack Network about integrating original retro computers, emulation and modern network services.

This records where the term and this definition come from in this project. It is not a claim that the word was never used before anywhere else, and it is not a claim of exclusive or legal ownership of the word.

## The project name

The name *The Love Shack Network* is inspired by the American band **The B-52's** and their songs *Rock Lobster*, *Junebug* and *Love Shack*: a place where very different guests come together, just as very different computers come together here.

This project is not affiliated with or endorsed by The B-52's. No song lyrics are reproduced.

## Licence

This document, including the English and Dutch definitions, is published under the project's MIT licence, `Copyright (c) 2026 The Love Shack Network contributors`; see [`LICENSE`](../LICENSE). This is an exception to the CC BY 4.0 licence used for the rest of the documentation.

The MIT licence covers the text of this document. It does not make the single word *Computerfluid* the property of anyone, and it does not restrict anyone from using the word.
