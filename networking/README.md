# Networking

All Amigas use **AmiTCP/IP 3.0b2** with a fixed address. The stack has no DHCP client and no mDNS. Each machine reaches the home LAN in a different way:

| Route | Machine | Hardware | Driver | Status |
|---|---|---|---|---|
| Plipbox | A600, and A500 rev. 5 as reserve | Plipbox on the parallel port (parallel ↔ Ethernet) | plipbox.device 0.6 (SANA-II) | ✅ |
| Wi-Fi | A500 rev. 5 (PiStorm) | the Pi 3A+'s Broadcom Wi-Fi | WiFiPi.device + upstream PR #1 ([notes](wifi/)), WirelessManager 1.5 | ✅ |
| SLIP | A500 rev. 6A (TF536) | Wodem on the serial port, 19200 baud | slip.device + 8n1.device | 🧪 |

| Topic | Page |
|---|---|
| RetroMount: `Retro:` over SMB | [`retromount/`](retromount/) |
| AmiTCP configuration notes | [`amitcp/`](amitcp/) |
| Plipbox notes (MAC address, ports) | [`plipbox/`](plipbox/) |
| Wi-Fi driver fix (upstream reference) and the WiFiLink tool | [`wifi/`](wifi/) |
