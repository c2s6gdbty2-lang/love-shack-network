# Commodore 64 Ultimate

| Item | Value | Status |
|---|---|---|
| Network | built-in network of the Ultimate ⟨**TODO:** LAN or Wi-Fi⟩ | ✅ |
| Printing | The Ultimate's printer emulation writes `printer-NNN.png` to USB. The Pi spooler fetches it by FTP every 30 s, prints only after two identical downloads, and then deletes the remote file. | ✅ "Printed … c64print-001/002.png", 03-10-2026 |
| Meatloaf (second C64 route) | PDF from the SD card over HTTP, repaired, then printed through CUPS | 🛠️ installed, no recorded print yet |

Details: [`server/retro-print/`](../../server/retro-print/).
