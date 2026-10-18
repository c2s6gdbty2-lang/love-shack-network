# Building AmiAgent

Everything is built from this repository plus the pinned upstream commit. Nothing depends on a particular home directory.

## Requirements

| What | Version used for the tested build | Needed for |
|---|---|---|
| git, patch, make, bash | Debian 13 | `build-agent.sh` |
| bebbo's amiga-gcc (`m68k-amigaos-gcc`) | GCC 6.5.0b | compiling amiagent and amimon |
| Python | 3.8 or newer (tested with 3.13) | `build-adf.py`, `build_tools.py`, tests |
| amitools (`xdftool`) | 0.8.1 | writing and reading back the ADF |
| network access to github.com | – | the first `build-agent.sh` run clones upstream |

amiga-gcc: see github.com/bebbo/amiga-gcc. If it is not on `PATH`, put the lines that set it up into a small shell file and pass it with `AMIGA_GCC_ENV=/path/to/file`. amitools: `pip install amitools` (a virtual environment is fine; pass `XDFTOOL=/path/to/venv/bin/xdftool`).

## Steps

```sh
cd amiga/a500-pistorm/AmiAgent
./build/build-agent.sh                 # clones upstream into ./upstream, checks out 3145dee, applies patches/
python3 build/build-adf.py             # assembles the tools, writes out/AmiAgent-Installatie.adf + out/MANIFEST.txt
```

`build-agent.sh`:
- refuses to build if the upstream working tree has changes;
- builds the READONLY `amiagent` and the unchanged `amimon` into `out/agent/`;
- checks that the result really is the READONLY build;
- compares the hashes with `build/agent.sha256`, the binaries tested on the real A500. With amiga-gcc 6.5.0b the result is byte-identical; another compiler version gives other bytes, which is reported as a note.

Options:
- `AMIMCP_DIR=/path/to/clean/clone` uses an existing upstream clone instead of cloning.
- `--rw-test` also builds `amiagent-rw-test` **without** READONLY, for emulator test E6 only. It never goes onto the disk; `build-adf.py` refuses a non-READONLY agent.

`build-adf.py`:
- runs `amiga/common/tools/build_tools.py`, which assembles `WiFiVraag`, `Geladen` and `VrijKB` and checks them against `tools.sha256`;
- takes `CRCLijst` from A600AirPrint after a hash check;
- puts `LICENSE-amimcp` and `NOTICE-amimcp` on the disk, after checking that they are identical to `LICENSE` and `NOTICE` of the pinned upstream (Apache-2.0 sections 4(a) and 4(d));
- takes the drawer icon from A600AirPrint (`Hulp/Lade.info`) and draws the disk icon with `build/amiagent_icons.py` (a diskette with a magnifying glass); the A600AirPrint `Disk.info` serves only as the structure template;
- puts `NOTICE-runtime-newlib` at the disk root (the notices of the linked C runtime; outside `AmiAgent/`, so the installer and its CRC list stay as tested);
- writes the ADF and reads every file back.

**Keep the ADF to yourself.** You may build and use it, but do not distribute it publicly until the licence of the AmigaOS-specific runtime files is settled (see the README, Licence).

The ADF image itself is not byte-reproducible, because xdftool stores the build time. Compare the files with `out/MANIFEST.txt` instead.

## The helper tools on their own

```sh
python3 amiga/common/tools/build_tools.py /tmp/tools        # WiFiVraag Geladen VrijKB
```

| Tool | Use | Notes |
|---|---|---|
| `WiFiVraag PROMPT/A,TO/A/K,IP/S,NET/K,MIN/K/N,MAX/K/N,PREFIX/K,SUFFIX/K,HIDE/S,APPEND/S,NOLF/S` | asks for a value in the Shell window, checks it, writes one line to a file; `HIDE` shows asterisks | AmigaOS 2.04+; return codes 0/5/10/20. The installer uses it for the token (`MIN 16 MAX 63 HIDE NOLF`) |
| `Geladen NAAM/A,DEV/S,PORT/S` | is a library, device or public port in memory? No output, opens nothing | return code 0 = present, 5 = not present. `AmiAgent Start` uses it to check `bsdsocket.library` |
| `VrijKB PAD/A,NODIG/A/N` | free space in KB, and is the volume writable? | return code 0 / 5 too little / 10 write-protected / 20 not found |

All three are pure 68000, one code hunk without relocations, using only exec and dos.library. A source line containing only `PAD` marks where `build_tools.py` may insert one padding word, which it does when the variable block is not longword aligned; that is the rule of the original build kits. `Geladen` and `VrijKB` are byte-identical to the tested binaries. `WiFiVraag` differs in two bytes: the example address in its error text was changed from the author's home network to `192.168.10.70`.

## Verification after a build

```sh
(cd out/agent && sha256sum -c ../../build/agent.sha256)   # compiler-dependent, see above
python3 tests/test_filter.py                        # offline, no Amiga needed
```
