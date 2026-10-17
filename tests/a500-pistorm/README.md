# AirPrintPS (A500 rev. 5, PiStorm) – test report

## 1. Clean emulator, public ADF (17-10-2026)

**Environment.**
- The same clean disk copy as for the A600 test.
- Network over the emulated card only. plip0 was **not** configured, so the parallel port stayed free, as on the Wi-Fi A500.
- The CPU ran at maximum speed (a stand-in for the PiStorm). Port setting: *Parallel*.

| # | Test | Result |
|---|---|---|
| A1 | **Inventaris** | ✅ read-only: 593 files, 0 differences |
| A3 | **Installeer** | ✅ [1]–[3] OK (Classic prefs). **15 files added, 0 changed.** |
| A2 | **ControleerPrinter** | ✅ IPP 0x0000, PWG Raster, address taken from the build configuration |
| A4 | **TestTekst** | ✅ 20 s, 33,633 B, `9a95cedb…`. **Byte-identical** to the original AirPrintPS job, which the real printer accepted with `Validate-Job`. |
| A5 | **TestGrafiek** | ✅ 118,971 B, `be169384…`, byte-identical |
| A7 | **Reboot + TestTekst** | ✅ same job (`9a95cedb…`) |
| A8 | **Verwijderen** | ✅ "de vorige printerinstelling staat terug". **0 differences** with the state before installation, apart from the `.oud` backup folder. |

## 2. Real Amiga 500 rev. 5 (14-10-2026, performed by the owner)

| Step | Result |
|---|---|
| Inventaris | ✅ KS 45.66, WB 40.42 modules, printer.device 39.6 |
| ControleerPrinter | ✅ IPP 0x0000, PWG Raster 600×600 |
| Installeer | ✅ [1]–[3] OK |
| TestTekst | ✅ on paper |
| TestGrafiek (colour) | ✅ on paper |
| SysInfo → PRINT → `PRT:` (a real application) | ✅ on paper |
| Reboot → StartWiFi → TestTekst | ✅ same page |

Photos: [`images/a500-pistorm/`](../../images/a500-pistorm/).
