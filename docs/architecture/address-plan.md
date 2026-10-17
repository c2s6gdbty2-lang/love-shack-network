# Address plan (template)

AmiTCP 3.0b2 has no DHCP client and no mDNS, so every retro machine, the printer and the server need **fixed addresses**. Two rules avoid most problems:

1. **Reserve every fixed address in the router**, or pick it from a range the router's DHCP pool does not hand out.
2. **Keep one table, and check it before you give a device an address.** The two failure modes seen in this network were:
   - Two devices configured with the same address. The second one gets "duplicate IP address" in AmiTCP.
   - An address changed in only some of the places that define it: text strings changed, but a numeric compare in a launcher was not.

| Block (example LAN 192.168.1.0/24) | Use | Example |
|---|---|---|
| .1 | router, DNS | 192.168.1.1 |
| .20–.29 | printers | 192.168.1.23 network printer |
| .60–.79 | retro machines with fixed addresses | 192.168.1.60 FujiNet, 192.168.1.62 Amiga 600, 192.168.1.64 A500 Plipbox, 192.168.1.70 A500 Wi-Fi, 192.168.1.78 C64 Ultimate |
| .140–.149 | servers | 192.168.1.145 retro server |
| separate /30 or /24 | point-to-point SLIP | 192.168.250.1 ↔ .2 (Wodem, example) |

## Where an Amiga's address is defined

When you change an address, change it in **every** place:

| Place | File |
|---|---|
| AmiTCP host entry | `AmiTCP:db/netdb-myhost` (`HOST …`) |
| interface start | an `ifconfig` line in your start script or launcher. If the launcher is a binary, its compiled-in address and every compare against it count too. |
| AirPrint printer address | `ENVARC:AirPrint.prefs` (`HOST=`), set in SYS:Prefs/AmiAirPrint, or with `build_public.py` |
| server address | the `smbfs SHARE=//<server>/…` line in your RetroMount script |
| on the server | the print-watcher `.conf` files hold the 8-bit devices' addresses |
