# Atari 800XL – FujiNet

| Item | Value | Status |
|---|---|---|
| Network | FujiNet (ESP32) over Wi-Fi | ✅ |
| Printing | FujiNet emulates a printer and serves the latest print-out as a PDF at `GET /print`. The Pi watcher polls every 45 s, skips duplicates by SHA-1, and prints through CUPS. | ✅ two print-outs archived, 03-10-2026 |
| Fixed address | FujiNet has a fixed address, because mDNS (`fujinet.local`) proved unreliable | see the address plan |

Details: [`server/retro-print/fujinet/`](../../server/retro-print/fujinet/).
