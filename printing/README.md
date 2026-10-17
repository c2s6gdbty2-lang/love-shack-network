# Printing

All routes end at one network printer. The tested printer is a Brother MFC-L8390CDW: IPP/2.0, PWG Raster at 600 dpi, sgray_8/srgb_8.

| Source | Route | Format | Status |
|---|---|---|---|
| Amiga A600, A500 rev. 5 | any program → `PRT:` → printer.device 39.6 → AirPrint driver → airprint.device → AmiTCP → **IPP Print-Job directly to the printer** | `image/pwg-raster` | ✅ both machines |
| Atari 800XL | FujiNet printer emulation → PDF at `GET /print` → watcher on the server → CUPS → IPP | PDF | ✅ |
| C64 Ultimate | printer emulation → PNG on USB → FTP → spooler on the server → CUPS → IPP | PNG | ✅ |
| C64 Meatloaf | PDF on the SD card → HTTP → repair → CUPS | PDF | 🛠️ |
| Amiga fallback through the server | file → SMB → spooler → CUPS | text/PS/PDF/IFF | 📋 not activated |

## IPP, PWG Raster and the name "AirPrint"

The Amiga route sends a standard IPP/2.0 `Print-Job` with a PWG Raster document (`image/pwg-raster`), the raster format of *IPP Everywhere*. It needs no driver on a PC and no print server. The package names (A600AirPrint, AirPrintPS) come from AmiAirPrint. **This is not Apple AirPrint and is not supported or certified by Apple.**

- Patch, licence and background: [`amiairprint/`](amiairprint/).
- The server side: [`server/`](../server/).
