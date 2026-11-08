# Issue 0004 – GUI-SAFE does not enforce the CLIENT address

| | |
|---|---|
| Component | AmiAgent GUI-SAFE (`amiagent-gs`, patch 0005, `src/guisafe.c`) on the Amiga 600 |
| Severity | security deviation: a documented restriction is not enforced |
| Status | **open**. Found while documenting v2, 08-11-2026. Blocks a GUI-SAFE release |
| Not affected | READONLY (`amiagent`) and WRITE-SAFE (`amiagent-ws`, which does compare `CLIENT` with the peer address) |

## Symptom
The GUI-SAFE mandate requires `CLIENT=<address>`. `gs_arm()` checks that it is present and not too long, stores it and
prints it, but no code compares it with the address of the connecting host. During an open session any host that
holds the token can send LAUNCH, INPUT and GSEND.

## Impact
- The token is still required, and the session still needs the local yes, the allowlist, the volume protection and
  the window gate. The deviation widens **who** can use an open session, not **what** it can do.
- The token travels unencrypted, so on a shared network the deviation matters.
- A host restriction in the TCP stack (AmiTCP `inet.access`) would limit this further; on the tested A600 such a
  restriction is **not verified** and must not be assumed.

## Proposed fix
1. In the GUI-SAFE build, compare the peer address of every connection with `g_gs.client` (as WRITE-SAFE does with
   `WS:CLIENT`), before LAUNCH, INPUT and GSEND are processed, and also for `gs_touch()` (idle timer).
2. Refuse with `GUI-SAFE: CLIENT this client address is not in the mandate`, log `GEWEIGERD client <address>`.
3. Validate `CLIENT` at arming as a dotted IPv4 address; refuse the mandate otherwise (fail-closed).
4. Keep READONLY requests (INFO, files, screenshots) as they are, so the user can still check the state.
5. New binary hash; READONLY build must stay byte-identical to `bb2f0daf…`.

## Regression tests
| Test | Expected |
|---|---|
| R1 LAUNCH/INPUT/GSEND from the mandated address | accepted |
| R2 LAUNCH/INPUT/GSEND from another address with the valid token | refused, logged, session state unchanged |
| R3 INFO from another address | answered (read-only) |
| R4 idle timer: only the mandated address keeps the session alive | session closes after IDLESEC when only another host talks |
| R5 `CLIENT=` empty, `CLIENT=abc`, `CLIENT=999.1.1.1` | mandate refused, READONLY restored by the script |
| R6 full G0/G1 regression and v2 scripts V0–V15 | unchanged results |
| R7 READONLY build | sha256 `bb2f0daf…` |
| R8 physical acceptance on the A600 (7 steps) | 7/7 PASS |

In the emulator a second client address can be made with a second address on the namespace's dummy interface.
