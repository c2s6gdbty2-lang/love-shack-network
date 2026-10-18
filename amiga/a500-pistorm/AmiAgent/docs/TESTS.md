# AmiAgent test status

Three kinds of test, kept strictly apart: the **real** A500, the **emulator**, and **offline** tests that need no Amiga at all.

## Real Amiga 500 (PiStorm/Emu68, Workbench 3.1, AmiTCP 3.0b2 over Wi-Fi), 18-10-2026

| What | Result |
|---|---|
| Install from the ADF; token stored; `AmiAgent Start`; agent listening on 7846 | ✅ |
| PING with the right token; build reports `lsn1 READONLY` | ✅ |
| `Avail`, `Version`, `ShowConfig`; `amiga_system_info`; `amiga_screens`; `amiga_screenshot` (native, 640×1024) | ✅ |
| `amiga_list_dir` (full recursive inventory of 5 volumes, 6495 files) and `amiga_read_file` (360 files read in full, up to 643 KB, every byte count matching the listing) | ✅ |
| The filter refuses `Dir` and `amiga_write_file` | ✅ |
| Claude Code connected through MCP, filter and permissions as in `pi/` | ✅ |
| ~1800 calls in one afternoon; free Fast RAM afterwards within 1.4 KB of the start | ✅ observed, not a formal test |
| Agent reachable again without a restart after the network dropped while a demo ran | ✅ observed, not a formal test |
| Bulk transfer over Wi-Fi | ❌ unreliable; see the README, Known limitations |
| The agent refusing writes **without** the filter (E10) | not done on real hardware (it deliberately sends write attempts) |
| `inet.access`, Plipbox transport, connecting from a Mac | not done |

This was the build in `build/agent.sha256`. The ADF in this repository differs from the tested disk in three files:
- `AmiAgent.info`: the project's own drawer icon, replacing a Workbench icon;
- `Disk.info`: a new AmiAgent design, replacing a Workbench icon;
- `WiFiVraag`: two bytes of example text.

Those three files have not been run on real hardware. They were tested in the emulator (see below, E11).

## Emulator (Amiberry 8.3.0, 68040, Kickstart 40.63/Workbench 40.42, AmiTCP 3.0b2 on a2065/slirp), 18-10-2026

122 of 122 checks passed. Full list: [`tests/RESULTATEN-emulator-20261018.md`](../tests/RESULTATEN-emulator-20261018.md).

| Test | Checks | What |
|---|---|---|
| E1 | 13 | install, CRC check, start/stop, a second start refused |
| E2 | 7 | wrong, missing or short token refused; missing TOKENFILE refused; token not in `Status` |
| E3 | 4 | `inet.access`: unlisted host refused by AmiTCP and logged |
| E4 | 20 | the filter: 11 tools listed, allowed calls work, write tools and shell tricks refused, host check |
| E5 | 4 | interface down and up, client disconnecting mid-request, invalid frame |
| E6 | 7 | stuck command and BREAK (with the rw-test agent); READONLY refuses BREAK and `Wait` |
| E7 | 6 | screenshot, screens, UI tree, menus, pointer, region checksum |
| E8 | 8 | agent and smbfs side by side (test smbd in a sandbox) |
| E9 | 3 | 900 connections, no Chip or Fast RAM growth |
| E10 | 50 | every write channel sent straight over the protocol, bypassing the filter, refused by the agent; Work: and RAM: byte-identical afterwards |

### Validation of the release disk (18-10-2026, evening)

The disk built from this repository was installed and tested in an isolated copy of the same harness: **131 of 131 checks passed**. Full list: [`tests/RESULTATEN-emulator-20261018-validatie.md`](../tests/RESULTATEN-emulator-20261018-validatie.md).

| Phase | Checks | What |
|---|---|---|
| basis (E1 E2 E4 E5 E6 E7 E9 E10) | 110 | as above, same counts per test |
| E3 | 4 | `inet.access` |
| E11 | 17 | the three changed files: |

E11 covered:
- `Disk.info` shown on the Workbench desktop and read back byte-identical by the agent;
- `AmiAgent.info` placed by `Installeer`, byte-identical, and shown in the Work window;
- `WiFiVraag`:
  - token input with hidden echo;
  - the new example text in IP mode;
  - rc 10 after three wrong entries, rc 0 for a valid entry;
  - `MIN` length check.

The disk icons were also checked by eye on screenshots.

Running the suite yourself needs an Amiberry harness of your own, which is not part of this repository because it needs your own Kickstart and Workbench. Set `LSN_HARNESS`, `LSN_EMU`, `LSN_WORK_TEMPLATE`, `LSN_PLIPBOX_START` and `LSN_SMBFS`, build with `build-agent.sh --rw-test`, then:
```sh
tests/ns.sh start
tests/ns.sh run python3 -I tests/lsntest.py basis      # E1 E2 E4 E5 E6 E7 E9 E10
tests/ns.sh run python3 -I tests/lsntest.py e3
tests/ns.sh run python3 -I tests/e11-wijzigingen.py      # the three changed files
tests/ns.sh stop
```
`ns.sh` makes an unprivileged network namespace with loopback only, so the emulated agent is never reachable from the LAN. E8 also needs `LSN_SERVER_IP` and starts a separate test smbd with `sudo`; read `tests/e8-smbd.sh` before running it.

## Offline, in this repository (18-10-2026)

| Test | Result |
|---|---|
| `tests/test_filter.py`: the unchanged filter against a fake upstream; 11 tools listed, 8 allowed calls forwarded, 17 refused, timeout capped, screenshot forced native, audit log without the token, host checks | 32/32 |
| `build/build-agent.sh` from a fresh upstream clone (`3145dee`) with amiga-gcc 6.5.0b | `amiagent` and `amimon` byte-identical to the tested binaries |
| `amiga/common/tools/build_tools.py` | `Geladen`, `VrijKB` identical to the tested binaries; `WiFiVraag` differs only in the two changed example digits |
| `build/build-adf.py` | 27 files: 24 identical to the tested disk, plus the 3 intended differences; every file read back from the ADF identical; `LICENSE-amimcp` and `NOTICE-amimcp` checked against upstream |
