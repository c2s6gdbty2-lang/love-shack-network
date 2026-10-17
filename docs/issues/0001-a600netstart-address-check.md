# Issue 0001 – A600NetStart: an address change patched only the text, not the numeric check

| | |
|---|---|
| Component | `C:A600NetStart`, the 68000 network launcher of the A600 Plipbox setup (A600Net v11 and the derived *Start Plipbox* package). Not published in this release. |
| Severity | medium. With the new address the launcher always fails. With the old address it works, but that address collides with another device on the LAN. |
| Status | **open, analysis only.** The working configuration on the real A600 was deliberately **not** changed. |
| Found | 16/17-10-2026, while investigating an address conflict |

## Symptom

The real A600 still runs on its **old** address (A), although the network package on the server had been changed to a **new** address (B) because A is also used by a FujiNet.

With the package that uses address B, the launcher reports:

```
Configuring plip0...
ERROR: ifconfig did not set <B> on plip0
... A600NetStart failed returncode 20
```

## Cause (shown by inspection and reproduced in the emulator)

1. The launcher source (`A600NetStart.s`) defines the address twice:
   - as text in the `ifconfig` command and in the messages;
   - as a 32-bit constant: `MYIP equ $C0A8xxxx`.
2. The constant is used to compare against the address the stack reports (`SIOCGIFADDR`). This happens in the "already configured?" check and in the final check.
3. The change from A to B was made as a **binary patch of the strings only**, which are the same length. The constant was left unchanged.
4. In the patched binary, the old value occurs **three times** (file offsets `0x24A`, `0x29E`, `0x2F6`), and the new value does not occur at all.
5. **Result:**
   - The launcher does not recognise an interface that is already up with B, so it configures it again.
   - Its own check then fails: B ≠ A.
   - It exits with return code 20 **before** adding the default route.

**Reproduction (scratch emulator, 17-10-2026):** AmiTCP was up with `plip0` = B, and the packaged launcher was run. Output as above, return code 20. The screenshot is kept with the internal test records and is not published, because it shows real addresses.

## Impact

- With address B, the network does not start through the launcher. This explains why the machine was left on A.
- Address A collides with the FujiNet as soon as both devices are on. At inventory time the conflict was **latent**: neither device answered ARP.
- Printing (A600AirPrint) is not affected. It uses whatever address AmiTCP has.

## Proposed fix (needs separate approval; not done)

1. Change `MYIP` in `A600NetStart.s` to B, reassemble it with `asm68k.py`, and check that the constant equals the address in the strings.
2. Better: read the address from a configuration file (for example `AmiTCP:db/netdb-myhost`), so that text and number cannot drift apart.
3. Test in the emulator:
   - cold start;
   - "already up";
   - the wrong-address case;
   - the default route added exactly once.
4. Then, with the owner's approval:
   - back up the A600's current network folder;
   - install the fix;
   - reserve address B in the router;
   - run a real test.

## Lesson

When you change a value that a program also checks, change **every** representation of it: text, binary constant and any copies. Then search the result for both the old and the new value. Here only the text was searched.
