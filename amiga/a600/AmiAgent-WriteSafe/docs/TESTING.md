# WRITE-SAFE test status

Two kinds of test, kept apart: the **real** Amiga 600 and the **emulator**. Emulator results say something about the logic on this configuration. They are not proof for other hardware.

All tests ran against the same binary, `amiagent-ws` `202f731f…`. The READONLY build `bb2f0daf…` was rebuilt byte-identical alongside it.

## Real Amiga 600 (01/02-11-2026)

See the [README](../README.md) for the configuration. There was no disk backup, so the test was kept deliberately small.

| What | Result |
|---|---|
| Installed from the share; hashes measured on the Amiga itself | ✅ |
| Mandate given locally; agent reports `lsn1 WRITE-SAFE`, `write=armed` | ✅ |
| One 60-byte text file copied to `Work:Inbox`; byte-identical | ✅ |
| Same copy again: `WS:EXISTS`, file unchanged | ✅ |
| Copy to `Work:S`: `WS:PATH`, nothing created | ✅ |
| `Schrijven Uit`: COPYIN answers `unknown command` | ✅ |
| Icon **Aan** by double-click: yes/no requester; No leaves READONLY untouched | ✅ |
| Icon **Aan**, Yes: active while the requester is open and after window and requester are closed | ✅ |
| Second double-click: refused, mandate unchanged | ✅ |
| Icon **Uit**: WRITE-SAFE stops; READONLY reachable from the server; COPYIN unavailable | ✅ |
| Before/after listing of 13 folders: only the expected changes | ✅ |

**Not done on real hardware:** expiry after 30 minutes, the limit of 20, refusal of secret files, larger files, any failure case (no network cuts, no power cuts, no full disk), the Workbench icons with a real file copy, any other Amiga.

## Emulator

Amiberry, isolated network and filesystem namespace. `Work:` and a 512 KB volume were real FFS disk images. After every phase all disks were unpacked and compared with their starting state. Fault injection used a separate build.

| Phase | Subject | Result |
|---|---|---|
| W1 | Mandate, READONLY channels stay closed, secrets, limits, refused starts | 67/67 |
| W2 | Paths, assigns, soft and hard links, names, sources, malformed frames, duplicate volume name | 116/116 |
| W3 | No overwriting: each layer alone, 9 forms of an existing name, race, name clash, negative control | 86/86 |
| W4 | Temporary files stay in the target folder | 21/21 |
| W5 | Source changes, server dies, share gone, interface down, disk full, write protect, log unwritable, client gone, Ctrl-C | 56/56 |
| W5h | Server frozen and verified frozen; recovery; Ctrl-C during a hang; frozen then killed | 24/24 |
| W5f | Power loss after the temporary file reached the disk | 24/24 |
| W6 | Normal use, sizes up to 1024 KB, MCP server end to end, READONLY afterwards | 38/38 |
| W7 | `Work:` also holding `SYS:`, `S:`, `C:`, `DEVS:`, `LIBS:`, `L:` (assigns, not a real boot) | 22/22 |
| W8 | Workbench: real double-clicks on both icons, requesters, windows, refused mandate, recovery | 45/45 |
| W5p | Power cut during a 1 MB copy, 3 × `C:Copy`, 3 × `amiagent-ws` | all 6 ended with a validation error |

499 checks, of which 4 are measurements without a pass condition. W1, W6, W7 and W8 ran on the final scripts. W2 to W5 test the binary directly and ran on the same binary with the earlier script version.

1 MB took 56.5 seconds, over an emulated network card. The speed over a Plipbox was not measured.

## Not tested anywhere

- Other Amigas, CPUs, Kickstarts or TCP/IP stacks, including Miami and Roadshow.
- SFS, PFS or any filesystem other than OFS/FFS. The mandate refuses them.
- Hanging share during **AmiAgent Schrijven Uit** through the icon.
- The test harness itself is not part of this release: it depends on local paths. Others cannot rerun these tests yet.
- A build from this repository's layout. The binary was built from the same sources in the development kit.
