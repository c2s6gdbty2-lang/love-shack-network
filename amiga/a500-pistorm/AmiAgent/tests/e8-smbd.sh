#!/bin/bash
# e8-smbd.sh start|stop - TEST-smbd voor E8, als root maar UITSLUITEND in de netwerknamespace (dummy 10.99.0.1)
# van ns.sh (alleen loopback, poort 4450). Eigen config, passdb en mappen in tests/smbd/.
# De productie-Samba (/etc/samba, poort 445) wordt niet gelezen of gewijzigd.
# Modus "lan" (E8 buiten de namespace, omdat slirp daarbinnen niet uitgaand verbindt):
# luistert op $LSN_SERVER_IP:4450 en accepteert ALLEEN verbindingen vanaf dat adres zelf.
set -e
D="$(cd "$(dirname "$0")" && pwd)"; T="$D/smbd"; MODE="${2:-ns}"
U=$(id -un)
if [ "$MODE" = lan ]; then IF=${LSN_SERVER_IP:?set LSN_SERVER_IP}; RUN=""; else IF=10.99.0.1; NS=$(cat "$D/ns.pid"); RUN="nsenter -t $NS -n"; fi
case "$1" in
start)
  rm -rf "$T"; mkdir -p "$T"/{share,private,lock,state,cache,pid,log}
  cat > "$T/smb.conf" <<CONF
[global]
   interfaces = $IF
   hosts allow = $IF
   follow symlinks = no
   bind interfaces only = yes
   smb ports = 4450
   disable netbios = yes
   server role = standalone server
   server min protocol = NT1
   ntlm auth = ntlmv1-permitted
   passdb backend = tdbsam:$T/private/passdb.tdb
   private dir = $T/private
   lock directory = $T/lock
   state directory = $T/state
   cache directory = $T/cache
   pid directory = $T/pid
   log file = $T/log/log.%m
   load printers = no
   printing = bsd
   printcap name = /dev/null
[LSNTest]
   path = $T/share
   read only = no
   valid users = $U
   force user = $U
CONF
  printf 'e8-testwachtwoord\ne8-testwachtwoord\n' | sudo -n smbpasswd -c "$T/smb.conf" -s -a "$U" >/dev/null
  sudo -n $RUN /usr/sbin/smbd --daemon --no-process-group --configfile="$T/smb.conf" -l "$T/log"
  sleep 2
  if [ "$MODE" = lan ]; then ss -ltn | grep -q "$IF:4450" && echo "test-smbd luistert op $IF:4450 (alleen vanaf $IF)"
  else "$D/ns.sh" run ss -ltn | grep -q "$IF:4450" && echo "test-smbd luistert in de namespace op $IF:4450"; fi;;
stop)
  [ -f "$T/pid/smbd.pid" ] && sudo -n kill "$(cat "$T/pid/smbd.pid")" 2>/dev/null; sleep 1; echo "test-smbd gestopt";;
esac
