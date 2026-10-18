#!/bin/bash
# build-agent.sh - build amiagent for The Love Shack Network from the pinned
# upstream commit plus the patches in ../patches (in order). Output in ../out/agent/:
#   amiagent          READONLY build (-DAMIAGENT_READONLY) -> for the ADF
#   amimon            status monitor (unchanged upstream)
#   amiagent-rw-test  only with --rw-test: WITHOUT READONLY, for emulator test E6.
#                     Never put it on a disk or in a release.
#
# Needs: git, patch, make, and bebbo's amiga-gcc (m68k-amigaos-gcc) on PATH, or
# AMIGA_GCC_ENV=/path/to/a/shell-file that puts it on PATH.
# Upstream: cloned into ../upstream (git-ignored) from AMIMCP_URL, or use an
# existing clean clone with AMIMCP_DIR=/path/to/amimcp.
set -euo pipefail
K="$(cd "$(dirname "$0")/.." && pwd)"
PIN=3145dee16730dd9f8b14366c5226b315e197b375
URL=${AMIMCP_URL:-https://github.com/thomas-luebker/amimcp.git}
U=${AMIMCP_DIR:-$K/upstream}
RW=0; [ "${1:-}" = --rw-test ] && RW=1

if [ ! -d "$U/.git" ]; then
  [ -n "${AMIMCP_DIR:-}" ] && { echo "AMIMCP_DIR=$U is not a git clone"; exit 1; }
  git clone -q "$URL" "$U"
fi
git -C "$U" cat-file -e "$PIN^{commit}" 2>/dev/null || git -C "$U" fetch -q origin
[ -z "$(git -C "$U" status --porcelain)" ] || { echo "upstream working tree $U has changes"; exit 1; }
[ "$(git -C "$U" rev-parse HEAD)" = "$PIN" ] || git -C "$U" -c advice.detachedHead=false checkout -q "$PIN"
[ "$(git -C "$U" rev-parse HEAD)" = "$PIN" ] || { echo "upstream is not at $PIN"; exit 1; }

[ -n "${AMIGA_GCC_ENV:-}" ] && source "$AMIGA_GCC_ENV"
command -v m68k-amigaos-gcc >/dev/null || { echo "m68k-amigaos-gcc not found (set AMIGA_GCC_ENV or PATH)"; exit 1; }

B="$K/out/build"; rm -rf "$B"; mkdir -p "$B" "$K/out/agent"
git -C "$U" archive "$PIN" agent | tar -x -C "$B"
for p in "$K"/patches/0*.patch; do patch -s -p1 -d "$B" < "$p"; echo "patch: $(basename "$p")"; done
( cd "$B/agent"
  make -s amiagent CC="m68k-amigaos-gcc -DAMIAGENT_READONLY" 2>&1 | grep -E 'error|warning: implicit' || true
  cp amiagent "$K/out/agent/amiagent"; rm -f amiagent
  make -s amimon 2>&1 | grep -E 'error' || true; cp amimon "$K/out/agent/amimon"
  if [ "$RW" = 1 ]; then
    make -s amiagent 2>&1 | grep -E 'error' || true; cp amiagent "$K/out/agent/amiagent-rw-test"
  fi )
cd "$K/out/agent"
grep -aq 'lsn1 READONLY' amiagent || { echo "FOUT: amiagent is not the READONLY build"; exit 1; }
sha256sum amiagent amimon | tee SHA256SUMS
# Reference hashes of the build tested on the real A500 (amiga-gcc 6.5.0b).
# Another compiler version gives different bytes; that is expected, not an error.
if sha256sum --quiet -c "$K/build/agent.sha256" 2>/dev/null; then
  echo "identical to the tested build"
else
  echo "NOTE: differs from the tested build (other compiler version?)"
fi
