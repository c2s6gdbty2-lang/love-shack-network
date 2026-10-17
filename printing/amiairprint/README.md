# AmiAirPrint 1.2-ps1

[AmiAirPrint](https://github.com/Andiweli/AmiAirprint) by Andreas "Andiweli" Stürmer is a printer.device driver plus a device that renders PWG Raster and sends it over IPP.

## Licence and provenance (verified 17-10-2026)

| Fact | Evidence |
|---|---|
| Commit `f9cb9fd` ("Update to 1.2", 2026-08-28) is **MIT**-licensed | `LICENSE` at that commit |
| The licence changed to the *AmiAirPrint Non-Commercial License 1.0* in commit `b2baacf` on 2026-09-01 | GitHub history of `LICENSE` |
| The Aminet release 1.2 states "released under the MIT License". Its binaries are dated 2026-08-28, the same as `f9cb9fd`. | `AmiAirPrint.readme` and the archive listing |
| **Everything here derives from the MIT version only** | – |

The upstream copyright notice is kept in [`LICENSE-AmiAirPrint`](LICENSE-AmiAirPrint).

## What the ps1 patch changes ([`AmiAirPrint-1.2-ps1.diff`](AmiAirPrint-1.2-ps1.diff))

1. **bsdsocket.library version.** It asks for version 3 instead of 4. AmiTCP 3.0b2 provides 3.28, and every socket call that is used exists in version 3.
2. **No DOS from a Task.** Under OS 3.1, printer.device runs the driver as an exec Task, and DOS calls from a Task hang. The original read its settings and spooled to `T:` through DOS. The patch reads the settings only in a Process, keeps the last known values otherwise, and spools in memory. [`diag/taaktest.c`](diag/taaktest.c) is the test that demonstrated the hang.

The two prefs programs are the official Aminet 1.2 files with **one byte** changed (`moveq #4` → `moveq #3`, the bsdsocket version):
- `AmiAirPrintPrefs`: the byte at `0x35C1F` (the `moveq` starts at `0x35C1E`);
- `AmiAirPrintPrefsClassic`: the byte at `0x35E33` (the `moveq` starts at `0x35E32`).

In each file this is the only byte that differs from Aminet 1.2 (`04` → `03`). Checked with `cmp -l`.

## Binaries in the packages

| File | SHA-256 | Origin |
|---|---|---|
| `airprint.device` | `1d011b3be6fce4f4a60a182d6dba070e77857f29b28d14ff2073a89b1d3a96c1` | built from `f9cb9fd` + ps1 |
| `AirPrint` (driver) | `4985c532542a1589b26357e38d8adfac38c15bb741e4f653cddf105ee5148152` | built from `f9cb9fd` + ps1 |
| `AirPrintProbe` | `709784093488b4163ce60f846aa2ddae17f6a2c8076a46f255204ba55a2e5145` | built from `f9cb9fd` + ps1 (bsdsocket V3) |
| `AmiAirPrintPrefs` | `af776ce5f0bcfc99f86a8d25bd1a8d3d1f19bad5950dc20010452c29774aa801` | Aminet 1.2, 1 byte patched |
| `AmiAirPrintPrefsClassic` | `465d4c527d6d1edff7fc43f8dd6519a33a0f540d9785862aa8e8309a7067e5ce` | Aminet 1.2, 1 byte patched |
| `AmiAirPrint.info` | `5a16d8a518cf7ccb7c77617fa8a9f86cf2f58ec530bf2e39bc7d3787aa4d4c97` | Aminet 1.2, unchanged |

The embedded 8×8 font comes from `font8x8` (public domain), as noted upstream.
