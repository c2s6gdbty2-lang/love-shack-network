# Plipbox notes

A [Plipbox](https://github.com/cnvogelg/plipbox) bridges the Amiga parallel port to Ethernet. On the Amiga side it uses `plipbox.device` 0.6 (GPL-2.0), which is not included here; download it from the project's `v0.6` release.

- **MAC address.** With plipbox 0.6, the *Amiga driver* sets the MAC address, and the box stores it. The A600 release binary contains a fixed MAC address at file offset 0x412.
  - Every additional Plipbox on the same LAN needs its own MAC address.
  - The A500 copy was patched in two bytes for this.
- **Parallel port.** The Plipbox occupies the parallel port. Set printer.device to the serial port when you print with AmiAirPrint; see the [A600 example](../../amiga/a600/).
- **No box connected.** Without a box, `plipbox.device` does not fail at `ifconfig`/`online`. It only fails when you ping the router.
- **Start scripts.** The A600 start scripts (*Start Plipbox*, `A600NetStart`) contain fixed addresses, and one is a binary launcher. They are not published until a configurable version has been built and tested.
