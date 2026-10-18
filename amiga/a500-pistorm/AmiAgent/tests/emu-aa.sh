#!/bin/bash
# emu-aa.sh - scratch-testemulator voor AmiAgent LSN (draai via: ns.sh run ./emu-aa.sh).
# Work: = PlipNet 1.1-testvariant op a2065 (slirp; AmiTCP 3.0b2 = stack van de A500),
# Work:Test = smbfs (E8) + amiagent-rw-test (E6), DF0 = AmiAgent-Installatie.adf.
# Optioneel INETACCESS="regels" (printf %b) achter AmiTCP:db/inet.access van de KOPIE (E3).
# slirp_redir 17846/17847 -> gast 7846/7847; alleen zinvol in de namespace. Raakt alleen $LSN_EMU aan. Bouw eerst met build-agent.sh --rw-test.
set -e
# Configure your own harness (see docs/TESTS.md); nothing here has a default:
#   LSN_HARNESS, LSN_EMU, LSN_WORK_TEMPLATE (a Work: tree with PlipNet 1.1),
#   LSN_PLIPBOX_START (the "Plipbox Start" script of PlipNet 1.1), LSN_SMBFS (smbfs 2.22 binary)
K="$(cd "$(dirname "$0")/.." && pwd)"
H=${LSN_HARNESS:?set LSN_HARNESS}; E=${LSN_EMU:?set LSN_EMU}
: "${LSN_WORK_TEMPLATE:?set LSN_WORK_TEMPLATE}" "${LSN_PLIPBOX_START:?set LSN_PLIPBOX_START}" "${LSN_SMBFS:?set LSN_SMBFS}"
cd "$H"
./emu-stop.sh
rm -rf "$E/work"; cp -a "$LSN_WORK_TEMPLATE" "$E/work"
W="$E/work/PlipNet"
cp "$LSN_PLIPBOX_START" "$W/Plipbox Start"
cp "$H/a2065.device" "$W/Devs/Networks/a2065.device"
sed -i 's#^plip DEV=PlipNet:Devs/Networks/plipbox.device#plip DEV=PlipNet:Devs/Networks/a2065.device#' "$W/AmiTCP/db/interfaces"
grep -q "a2065.device" "$W/AmiTCP/db/interfaces"
printf '10.0.2.15' > "$W/Prefs/IP"; printf '10.0.2.2' > "$W/Prefs/Gateway"; printf 'a2065.device' > "$W/Prefs/Device"
[ -n "${INETACCESS:-}" ] && printf "%b" "$INETACCESS" >> "$W/AmiTCP/db/inet.access"
mkdir -p "$E/work/Test"
cp "$LSN_SMBFS" "$E/work/Test/smbfs"
cp "$K/out/agent/amiagent-rw-test" "$E/work/Test/amiagent-rw-test"
rm -f "$E/adf/AmiAgent-Installatie.adf"; cp "$K/out/AmiAgent-Installatie.adf" "$E/adf/"; chmod 444 "$E/adf/AmiAgent-Installatie.adf"
./maakhdf.sh geen
python3 -I mkconf.py aa cpu=68040 df0="$E/adf/AmiAgent-Installatie.adf" a2065=1 >/dev/null
printf 'slirp_redir=tcp:17846:7846:127.0.0.1\nslirp_redir=tcp:17847:7847:127.0.0.1\n' >> "$H/emu/aa.uae"
./emu-boot.sh aa
