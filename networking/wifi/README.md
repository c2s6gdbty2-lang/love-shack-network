# Wi-Fi on the PiStorm (Emu68)

| File | Licence | Purpose |
|---|---|---|
| *(not included)* WiFiPi.device PR #1 | see below | Fixes WPA2 with WirelessManager. Without it, the second `S2_SETOPTIONS` call wiped the join parameters, giving "Associated with ff:ff:ff:ff:ff:ff". |
| [`WiFiLink.s`](WiFiLink.s) | MIT | `WiFiLink DEVICE/A,UNIT/K/N,TIMEOUT/K/N,QUIET/S` waits (with a time limit) until a SANA-II Wi-Fi driver is connected. It polls `S2_GETSIGNALQUALITY` once per second. It replaces WaitForLink 1.1, which waits for `S2EVENT_LINKUP`, an event wifipi.device does not support. Assemble it with [`asm68k.py`](../../amiga/common/tools/asm68k.py). |

## The driver fix: use upstream PR #1, which is not copied here

- **The fix:** pull request #1 by *tinic* to [michalsc/WiFiPi.device](https://github.com/michalsc/WiFiPi.device), "Apply only supplied wireless options; join only for a named network", commit `aa07acb`, which changes only `src/unit.c`.
- **Tested build:** base `1752e4f` (= Emu68-tools v1.1) + `aa07acb` gives `wifipi.device` 49,692 bytes, `$VER: WiFiPi 0.4 … git:aa07acb`, SHA-256 `5973b2803b9b8465b0ff502e6f050f8f53da3c60c85b71daaa11fa4a0be509f5`.
- **Why the patch is not copied here:** at the time of writing, the WiFiPi.device repository has **no licence file**, and `src/unit.c` has no licence header; only a few other files carry an MPL-2.0 header. The distribution terms for that file are therefore not established, and the fix is the PR author's work. Build it from upstream yourself, or wait until the PR is merged.

The firmware for the Wi-Fi chip comes with Emu68 and the Raspberry Pi. It is never distributed here.

## Proven on real hardware (A500 rev. 5, 13-10-2026)

The log showed the following sequence:
1. `Trying to associate with <BSSID>`;
2. `Associated with <BSSID>`;
3. `RX message 3 of 4`;
4. `WPA: Key negotiation completed (CCMP)`;
5. `CTRL-EVENT-CONNECTED`.

After that, AmiTCP was used with a fixed address, ARP and ping to the server worked, and `Retro:` was mounted. The Samba journal on the server shows the sessions.
