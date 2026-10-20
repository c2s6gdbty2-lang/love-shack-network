# Third-party components

"In git" means the file is committed to this repository. Everything else is downloaded by the user, who can verify it against the SHA-256 of the tested version listed here.

| Component | Version tested | Licence | Source | Used for | In git? | SHA-256 of the tested binary |
|---|---|---|---|---|---|---|
| **AmiAirPrint**: airprint.device, AirPrint driver, AirPrintProbe | 1.2 from commit `f9cb9fd` (2026-08-28, MIT), rebuilt as **1.2-ps1** | **MIT** © Andreas "Andiweli" Stürmer | github.com/Andiweli/AmiAirprint at `f9cb9fd`. Later commits (from `b2baacf`, 2026-09-01) use a non-commercial licence; nothing here derives from them. | Amiga printing over IPP | **Yes**, inside the package trees, with the MIT licence text | airprint.device `1d011b3b…96c1`, AirPrint `4985c532…8152`, AirPrintProbe `70978409…5145` |
| **AmiAirPrint prefs programs**: AmiAirPrintPrefs(Classic), AmiAirPrint.info | Aminet release 1.2 (binaries dated 2026-08-28; the readme states MIT) | **MIT** | Aminet `driver/print`, AmiAirPrint 1.2 (`AmiAirPrint.lha`, SHA-256 `26b816ef…4ab4`) | settings program | **Yes**. The two programs differ from Aminet by one byte each (bsdsocket version 4 → 3); the .info is unchanged. | PrefsClassic `465d4c52…e5ce`, Prefs `af776ce5…a801`, .info `5a16d8a5…4c97` |
| font8x8, embedded in AmiAirPrint | – | Public domain | github.com/dhepper/font8x8 | glyphs | inside the binary | – |
| **AmiTCP/IP** | 3.0b2 | **GPL-2.0** (exceptions listed in COPYRIGHTS) | Aminet, binary archive `AmiTCP-bin-30b2` ⟨TODO: confirm the exact Aminet path and source archive⟩ | TCP/IP stack on every Amiga | No | AmiTCP `c841308a…cf8d` |
| **plipbox.device** | 0.6 (A600 release binary) | **GPL-2.0** © Christian Vogelgsang et al. | github.com/cnvogelg/plipbox, tag `v0.6` | Plipbox driver | No | `2e0ba8c5…958d` |
| **smbfs** | 2.22 | **GPL-2.0** © Olaf Barthel | Aminet ⟨TODO: path⟩ | RetroMount | No | `31b5f5ae…c657` |
| **WirelessManager** (wpa_supplicant 0.7.3) | 1.5 from prism2v2.lha 2.9 | **GPL-2.0 or BSD** (dual) | Aminet `prism2v2.lha` (SHA-256 `25b400ef…7bc5`); AROS sources | WPA2 on the PiStorm | No | `4f6227d1…5b0c` |
| **WiFiPi.device** | git `1752e4f` (= Emu68-tools v1.1) + PR #1 (`aa07acb`, by tinic) | **not established.** There is no licence file in the repository, and `src/unit.c` has no header; a few other files carry an MPL-2.0 header. The parent project Emu68 is MPL-2.0. | github.com/michalsc/WiFiPi.device | Wi-Fi driver | **No**, not even the patch; only a reference to the upstream PR | PR #1 build `5973b280…09f5` |
| libnix (C runtime linked into CRCLijst and the AmiAirPrint builds; its `libstubs.a` library auto-open stubs are also linked into amiagent and amimon) | amiga-gcc (bebbo) | **public domain** (libnix README) | github.com/bebbo/amiga-gcc | runtime | inside the binaries | – |
| libgcc (support routines) | GCC 6.5.0b (amiga-gcc) | GPL-3.0 with the **GCC Runtime Library Exception** | GCC | runtime, also in amiagent and amimon (`_clz`, `_udivdi3`, `_umoddi3`) | inside the binaries | – |
| **newlib**, bebbo's AmigaOS fork (prebuilt `libc.a` and `crt0.o` shipped in the amiga-gcc repository) | as shipped with amiga-gcc 6.5.0b, commit `2f240d1` (17-07-2026) | Standard newlib parts: the permissive licences in `COPYING.NEWLIB` (Red Hat BSD-style and others). AmigaOS-specific parts: **MIT** (some over public-domain libnix code, two also with the Pipeline Associates notice), as declared by the author in newlib-cygwin commit `012fed9b` (19-10-2026); see the note below | newlib-cygwin, branch `amiga`, at franke.ms/git/bebbo | C runtime of amiagent and amimon (the upstream Makefile uses amiga-gcc's default runtime) | only inside a built ADF, not in git. All notices it requires are in git as `amiga/a500-pistorm/AmiAgent/THIRD_PARTY_NOTICES.txt`, and on the ADF | – |
| Wi-Fi chip firmware | – | proprietary | comes with Emu68 / Raspberry Pi | WiFiPi.device | **Never** | – |
| Kickstart ROM, Workbench 3.1 | KS 40.63 / 45.66, WB 40.42 | proprietary | your own copy | base system | **Never** | – |
| Genesis and other commercial software | – | proprietary | – | not used | **Never** | – |
| amitools (`xdftool`) | – | GPL-2.0 | PyPI `amitools` | build tool only | No | – |
| **amimcp / amiagent, amimon, amimon.info** | 0.13.2, upstream commit `3145dee` (2026), with LSN patches 0001–0003 | **Apache-2.0** © 2026 Thomas Luebker. The upstream NOTICE lists vendored CyberGraphX SDK interface files (phase5), declarations only. | github.com/thomas-luebker/amimcp at `3145dee` | AmiAgent: the agent on the Amiga and the MCP server on the Pi | The source is **not** in git (cloned at build time). In git, all under Apache-2.0: the patches, the unchanged licence text and NOTICE (`amiga/a500-pistorm/AmiAgent/LICENSE-amimcp`, `NOTICE-amimcp`), and `icons/amimon.info` (upstream icon, made by its `mkicon.py`). The built agent with `LICENSE` and `NOTICE` goes onto `AmiAgent-Installatie.adf` | amiagent (READONLY) `bb2f0daf…14ed`, amimon `844f8dee…c06b` |

### AmiAirPrint licence check (repeated 17-10-2026)

| Check | Result |
|---|---|
| `LICENSE` at `f9cb9fd`, fetched from GitHub | MIT, © 2026 Andreas "Andiweli" Stuermer |
| History of `LICENSE` | `c7a2938`/`b78dc1f` MIT (22-08) → `b2baacf` non-commercial (01-09-2026) |
| Source code between `f9cb9fd` and the current `main` | **identical**: only `LICENSE` and `README.md` changed |
| Base of `AmiAirPrint-1.2-ps1.diff` | the `index` blobs of all four patched files equal those at `f9cb9fd` |
| Aminet readme (fetched again 17-10-2026) | unchanged; "released under the MIT License" |
| Prefs programs and `.info` | byte-equal to the Aminet 1.2 archive, except the documented single byte in each program |
| Current upstream licence | *AmiAirPrint Non-Commercial License 1.0*. It allows non-commercial use, modification and **free redistribution**. |

**Conclusion.**
- The AmiAirPrint parts are distributed under the MIT licence of `f9cb9fd`, with the original notice.
- Free, non-commercial distribution would also be allowed under the current upstream licence.
- Out of respect for the author's current wishes, this project does not sell or bundle AmiAirPrint commercially, and asks downstream users to do the same.

## Original work in this repository (MIT; documentation and photos CC BY 4.0)

- **Scripts**: Controle, Installeer, Verwijderen, ControleerPrinter, TestTekst, TestGrafiek, Inventaris, Hulp/*, LeesMij.
- **Tools**:
  - CRCLijst, binary plus `crclijst.c` source;
  - WiFiLink, source;
  - WiFiVraag, Geladen and VrijKB, sources, assembled by `build_tools.py`;
  - AmiAgent: the scripts, `amimcp-ro.py`, `amimcp-lsn`, `lsn-token`, the build scripts (including `amiagent_icons.py`) and the tests;
  - the build scripts `build_public.py`, `icon.py` and `asm68k.py`;
  - `publish-check.py`.
- **Assets**: the icons (made with `icon.py`; the AmiAgent disk icon is drawn by `amiagent_icons.py`) and the test image `TestBeeld.iff`. Exception: `amiga/a500-pistorm/AmiAgent/icons/amimon.info` is upstream amimcp's (Apache-2.0).
- **Server scripts**: the print-watcher scripts and systemd units in `server/retro-print/`. They combine the owner's macOS originals, a port of 03-10-2026 whose author is not recorded, and assistant-made changes of 06-10-2026. See [`server/retro-print/PROVENANCE.md`](server/retro-print/PROVENANCE.md). No exclusive authorship is claimed.

Two derivative works keep their upstream licence:

| File | Licence |
|---|---|
| `AmiAirPrint-1.2-ps1.diff` | MIT |
| `amiga/a500-pistorm/AmiAgent/patches/*.patch` | Apache-2.0 (changes to amimcp's `agent/amiagent.c`) |

### The C runtime inside amiagent and amimon (checked 18-10-2026)

This matters only for a **binary** release of `AmiAgent-Installatie.adf`. No amiagent binary is in git. Updated 19-10-2026 after the author clarified the licence.

- **Link line**, read from the linker's verbose output and a link map; the map does not change the output: `crt0.o`, then `-lgcc -lc -lstubs -lamiga -lgcc`.
- **What is pulled in:**
  - 77 (amiagent) or 74 (amimon) objects from newlib's `libc.a`;
  - 3 from libgcc;
  - 5 (amiagent) or 2 (amimon) from libnix's `libstubs.a`;
  - **no objects from `libamiga.a`.** That file is a prebuilt binary in the amiga-gcc repository. Judging by its member names, it is libnix's `amiga.lib` replacement plus stubs generated from NDK `.fd` files; its exact build is not documented. It does not end up in the binaries.
- **Amiga-specific objects** come from `newlib/libc/sys/amigaos` in bebbo's fork: `__dosbase`, `open`, `__nocommandline`, `__stdiowin`, `__mathieeedoubbas`, the IEEE maths wrappers, `malloc.cpp`, `dummy` and `crt0`.
  - **Author:** according to the fork's git history, Stefan "Bebbo" Franke is the only author of the linked versions.
  - **Licence:** on 19-10-2026, after our question, he added licence headers in newlib-cygwin commit `012fed9b` ("add copyright"), and an MIT notice for his AmigaOS work to `COPYING.NEWLIB`. His e-mail sums it up as "MIT, MIT (over Public Domain) and Pat Wood Permissive + MIT". The headers in the source match that:

    | Header | Files |
    |---|---|
    | MIT, "Copyright (c) 2018-2026" or "1996-2026 Stefan "Bebbo" Franke" | `crt0.c`, `open.c`, `malloc.cpp` |
    | MIT over public-domain libnix code (no copyright line, authors named) | `__nocommandline.c`, `startup.h`, `__dosbase.c`, `__stdiowin.c`, `dummy.c`, the IEEE wrappers, `__divsi3.c`, `__mulsi3.c`, `__udivsi3.c` |
    | Pipeline Associates notice kept, plus MIT | `__cmpxf2.c`, `__unorddf2.c` |
    | MIT over public-domain libnix code, added on 20-10-2026 in newlib-cygwin commit `29f226ee` ("add copyright header"); the same header as `__dosbase.c`. The code itself is unchanged | `__mathieeedoubbas.c` |

  - **Unchanged runtime:** the commit changed comments only, apart from whitespace in `__dosbase.c`. The prebuilt `libc.a` and `crt0.o` in amiga-gcc are unchanged since `2f240d1`, so they are the same objects as in our binaries. `crt0.c` and `__nocommandline.c` later received a change by another contributor (newlib-cygwin `998257d`, 08-09-2026); that change is not in the prebuilt runtime we link.
- **README brought in line:** on 20-10-2026 the author updated the amiga-gcc README (commit `621b85c`). It now lists newlib as "Red Hat / Cygnus Solutions and contributors, Permissive (BSD/MIT-style mix)" instead of "GNU GENERAL PUBLIC LICENSE V2".
- **Both questions asked on 19-10-2026 are resolved.** `THIRD_PARTY_NOTICES.txt` was frozen with the v1.0 disk before the answer and still lists them as open questions; its contents are complete, because the new header of `__mathieeedoubbas.c` is the same MIT-over-public-domain text it already reproduces for `__dosbase.c` and the other generated files.
- **Standard newlib objects:** the linked ones fall under permissive terms: Red Hat, UC Berkeley (3-clause, the older "paragraph" wording, and the 1987 acknowledgement wording), FreeBSD, Todd C. Miller, David M. Gay. Several of them require the notice, or an acknowledgement, in the documentation of a binary distribution.
- **Compatibility:** MIT, the Pipeline Associates notice, public domain, the BSD-style newlib terms and the GCC Runtime Library Exception all allow combination with Apache-2.0 code in one binary. Their conditions are to keep the notices, which `THIRD_PARTY_NOTICES.txt` does, and not to use the names for endorsement. This is our reading, not legal advice.
- **A binary ADF may be distributed** if it carries `THIRD_PARTY_NOTICES` (at the disk root) and `AmiAgent/Docs/LICENSE-amimcp` and `NOTICE-amimcp`, as `build-adf.py` does.
- The source release in git is not affected.

