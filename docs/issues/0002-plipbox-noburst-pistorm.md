# Issue 0002 – Plipbox burst mode does not work under PiStorm/Emu68

| | |
|---|---|
| Component | plipbox.device 0.6 on the Amiga 500 rev. 5 with a PiStorm (Raspberry Pi 3A+, Emu68), reserve network route *PlipNet* |
| Status | **solved** with NOBURST (PlipNet 1.1). ✅ Confirmed on the real hardware, 17-10-2026. |
| Not affected | the Amiga 600 (stock 68000), which keeps the default burst mode |

## Problem
plipbox.device 0.6 uses a fast *burst* transfer by default: the Amiga sends bytes over the parallel port without waiting for the box to acknowledge each one.
- With the original 68000 this worked.
- Under PiStorm/Emu68 the CPU runs so much faster between port accesses that the box can no longer keep up.
- The network does not come up: no ping to the router, no ARP reply.

## Solution
Before the driver is opened for the first time, PlipNet 1.1's *Plipbox Start* creates:

```
ENV:SANA2/plipbox.config     (contents: NOBURST)
```

- The driver reads this file only at its first `OpenDevice`. With NOBURST it falls back to the slower protocol with a handshake per byte.
- The file lives in RAM only, and *Plipbox Start* creates it again after every cold boot. *RetroMount* goes through *Plipbox Start*, so it is covered too.
- *Plipbox Start* never overwrites an existing config. It refuses to start if the driver is already loaded without NOBURST.
- Nothing changes in the startup-sequence, `ENVARC:`, the driver binary or the Emu68 settings.

The manual equivalent, in a Shell after a cold boot and before the network is started:

```
MakeDir ENV:SANA2
Echo >ENV:SANA2/plipbox.config "NOBURST"
```

## Result
The Plipbox works as a fallback network next to Wi-Fi, which stays the main connection:
- the router and the server answer to ping;
- `Retro:` mounts through the Plipbox, and a test file copied correctly.

## Limitations
- **Switching takes a cold boot.** To change between Wi-Fi and the Plipbox, switch the Amiga off and on again.
  - *Plipbox Start* refuses while `wifipi.device` is in memory.
  - *StartWiFi* refuses while PlipNet is active.
- **Slower transfers.** NOBURST is slower than burst, but it is sufficient for normal RetroMount use.
- **Bridge on the Ethernet side.** In this network the box's Ethernet link goes through a wireless Ethernet bridge. The bridge translates hardware addresses and adds some latency.
- **Not every PiStorm setup is fixed.** Upstream report cnvogelg/plipbox#19 describes a PiStorm setup where NOBURST did not help. Reports #3 and #16 recommend or confirm NOBURST for fast CPUs.
