# AmiTCP 3.0b2 – configuration notes

AmiTCP is **not** included in this repository: it is GPL-2.0, and its binary archive contains programs whose sources are not included. Download it from Aminet and check the SHA-256 values in [`THIRD_PARTY.md`](../../THIRD_PARTY.md).

## Minimal configuration used on the Amigas

`AmiTCP:db/interfaces`, one line per SANA-II device:

```
plip  DEV=DEVS:Networks/plipbox.device UNIT=0 IPTYPE=2048 ARPTYPE=2054 ARPHDR=1 IPREQ=16 ARPREQ=4 WRITEREQ=16
wifi  DEV=WiFiNet:Devs/wifipi.device UNIT=0 IPTYPE=2048 ARPTYPE=2054 ARPHDR=1 IPREQ=16 ARPREQ=4 WRITEREQ=16 NOTRACKING
```

The `NOTRACKING` flag is needed because `wifipi.device` does not implement `S2_TRACKTYPE`.

`AmiTCP:db/netdb-myhost`, with example values:

```
HOST 192.168.1.62 amiga600.lan amiga600
DOMAIN lan
NAMESERVER 192.168.1.1
```

Start by hand (example):

```
Run >NIL: AmiTCP:AmiTCP
AmiTCP:bin/ifconfig lo0 127.0.0.1
AmiTCP:bin/ifconfig plip0 192.168.1.62 netmask 255.255.255.0
AmiTCP:bin/route add default 192.168.1.1
```

## Lessons learned

- **No leading zeros in addresses.** `070` is read as octal.
- **Extra libraries.** AmiTCP 3.0b2 needs `rexxsyslib.library` and `mathieeedoubbas.library`. Without them it exits silently with return code 20.
- **Check the process, not only the library.** `bsdsocket.library` can disappear while the AmiTCP process still hangs, so also check `Status COMMAND=AmiTCP:AmiTCP`.
- **"Unit is currently online".** The AmiTCP `online` command prints this message; it means OK.
- **A launcher that sets the address must also check it numerically.** In the A600 launcher, only the text strings were changed to a new address; the numeric compare still held the old one, so the check reported a failure. When you change an address, change every place it appears.
