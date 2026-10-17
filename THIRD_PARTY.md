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
| libnix (C runtime linked into CRCLijst and the AmiAirPrint builds) | amiga-gcc (bebbo) | **public domain** (libnix README) | github.com/bebbo/amiga-gcc | runtime | inside the binaries | – |
| libgcc (support routines) | GCC 6.5.0b (amiga-gcc) | GPL-3.0 with the **GCC Runtime Library Exception** | GCC | runtime | inside the binaries | – |
| Wi-Fi chip firmware | – | proprietary | comes with Emu68 / Raspberry Pi | WiFiPi.device | **Never** | – |
| Kickstart ROM, Workbench 3.1 | KS 40.63 / 45.66, WB 40.42 | proprietary | your own copy | base system | **Never** | – |
| Genesis and other commercial software | – | proprietary | – | not used | **Never** | – |
| amitools (`xdftool`) | – | GPL-2.0 | PyPI `amitools` | build tool only | No | – |

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
  - the build scripts `build_public.py`, `icon.py` and `asm68k.py`;
  - `publish-check.py`.
- **Assets**: the icons (made with `icon.py`) and the test image `TestBeeld.iff`.
- **Server scripts**: the print-watcher scripts and systemd units in `server/retro-print/`. They combine the owner's macOS originals, a port of 03-10-2026 whose author is not recorded, and assistant-made changes of 06-10-2026. See [`server/retro-print/PROVENANCE.md`](server/retro-print/PROVENANCE.md). No exclusive authorship is claimed.

One derivative work keeps its upstream licence:

| File | Licence |
|---|---|
| `AmiAirPrint-1.2-ps1.diff` | MIT |
