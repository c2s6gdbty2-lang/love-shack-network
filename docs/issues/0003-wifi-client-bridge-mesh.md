# Issue 0003 – Wi-Fi client bridges are unreliable for the Plipbox on a Wi-Fi mesh

| | |
|---|---|
| Component | the Ethernet side of the Plipboxes (Amiga 600, A500 TF536): a TP-Link TL-WR902AC travel router in *Client* mode as a wireless Ethernet bridge to a Google Nest Wifi mesh |
| Status | **solved** by replacing the bridge with an Ethernet cable to a Nest Wifi *router* unit used as a mesh point. ✅ Measured on the real hardware, 25-10-2026. |
| Not affected | machines with their own Wi-Fi (A500 PiStorm, FujiNet), and the retro server |

## Symptom
Over the bridge, the Plipbox Amigas worked at times, but never reliably:
- **Duplicate replies.** Ping showed packet loss and duplicate replies (DUPs), with round trips of up to 2.5 s.
  - The bridge itself showed the same DUPs.
  - The duplicates had increasing IP IDs. The bridge passed on the same request more than once; the Amiga was not the cause.
- **Silent drop-outs.** Twice the bridge stopped passing any traffic while it stayed associated with the mesh, with a "good" signal in the Nest app. Every Amiga behind it disappeared at the same moment.
- **Shared address.** All Amigas behind the bridge appeared on the LAN with the bridge's hardware address, not with their own Plipbox MAC address.

## Cause
A Wi-Fi client may use only its own MAC address towards the access point. A true transparent bridge needs 4-address mode (WDS), and the Nest mesh does not offer that.

In *Client* mode the TL-WR902AC therefore translates hardware addresses (MAC NAT) for everything behind its Ethernet port. On this mesh the translation was the weak point.

**Second unit.** A second TL-WR902AC, freshly configured in *Client* mode, behaved the same or worse:
- After a power cycle it did not rejoin the mesh within 15 minutes.
- It came up only after a restart from its web interface, and then lost 30–40 % of the pings to itself.

The problem is therefore not one faulty unit.

## Solution
- Connect the Plipbox by **cable** to a Nest Wifi **router** unit that works as a mesh point. Use a small unmanaged switch for more than one Plipbox.
  - The router unit has two Ethernet ports; the point units with a speaker have none.
  - On a router unit used as a point, both ports worked for wired devices, the globe (WAN) port included.
- The mesh then carries the traffic itself. No address translation takes place, and every Amiga keeps its own MAC address.
- Nothing changes on the Amigas: same scripts, same fixed addresses.

## Result
Measured from the retro server, 50 pings per machine:

| Machine | Address seen on the LAN | Loss | DUPs | Average round trip |
|---|---|---|---|---|
| Amiga 600 (Plipbox, via switch) | own Plipbox MAC | 0 % | 0 | 19 ms |
| A500 TF536 (Plipbox, direct) | own Plipbox MAC | 0 % | 0 | 24 ms |

The A600 was also clean over 100 pings. On the TF536, `Retro:` and `AmigaShare:` mount, and the read-only diagnostic agent answers.

## Notes
- **Moving the router unit.** Check the mesh after you move it. Here the retro server's own Wi-Fi link got better (−59 → −43 dBm).
- **Do not connect the bridge to a server with a DHCP client on Ethernet.** For diagnosis we connected the bridge to the retro server's Ethernet port. The server then obtained a second address through it and moved its default route onto the bridge. Take the Ethernet interface out of automatic configuration first.
- **One Plipbox unit did not get a link.** On the TF536 the original Plipbox got no connection through the switch, while the A600's Plipbox worked on the same switch. The TF536 now uses the unit that was the A500 PiStorm's reserve route. Because the plipbox 0.6 driver sets the MAC address, the swap needed no configuration change. The cause for the first unit is not yet known.
- **Powerline adapters** are a real Layer-2 bridge without address translation and might also work. They were not tested.
