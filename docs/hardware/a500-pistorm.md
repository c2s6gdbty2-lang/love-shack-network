# Amiga 500 rev. 5 – PiStorm

> Separate machine. Do not confuse it with the [A500 rev. 6A + TF536](a500-tf536.md).

| Item | Value | Source |
|---|---|---|
| Board | Amiga 500, revision 5 | owner |
| Accelerator | PiStorm with a Raspberry Pi 3A+, Emu68 | owner, inventory 14-10-2026 |
| Video | **Framethrower** | owner. ⟨**TODO:** model, firmware, settings and how it is connected⟩ |
| Kickstart | 45.66, exec 45.25 | Inventaris photo, 14-10-2026 |
| Workbench | 3.1 modules: workbench 40.5, dos 40.3, intuition 40.85, printer.device 39.6 | Inventaris photo |
| Network, primary | Wi-Fi through the Pi 3A+: WiFiPi.device (git `1752e4f` + PR #1), WirelessManager 1.5, AmiTCP 3.0b2 | [example](../../amiga/a500-pistorm/) |
| Network, reserve | Plipbox #2 on the parallel port (PlipNet), with its own MAC address | not part of the first release |
| Serial port | **Receive side defective.** An ATK loopback test showed all inputs red, most likely the MC1489. Outputs work. | test 08-10-2026 |
| Floppy | Gotek | owner |
| Printing | AirPrintPS 1.0, proven 14-10-2026 | [example](../../amiga/a500-pistorm/) |

Open items: the Framethrower specification, the storage details, and the formal runtime test list for WiFiNet 1.1.
