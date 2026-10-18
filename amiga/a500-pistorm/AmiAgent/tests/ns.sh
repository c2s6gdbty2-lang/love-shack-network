#!/bin/bash
# ns.sh start|run CMD...|stop - geisoleerde netwerknamespace (gebruikersnamespace, geen root)
# voor de testemulator: alleen loopback, onbereikbaar vanaf het LAN, weg na 'stop'.
PF="$(cd "$(dirname "$0")" && pwd)/ns.pid"
case "$1" in
  start) [ -f "$PF" ] && kill -0 "$(cat "$PF")" 2>/dev/null && { echo "ns draait al ($(cat "$PF"))"; exit 0; }
         setsid unshare -rn --kill-child sleep infinity >/dev/null 2>&1 < /dev/null &
         sleep 1; pgrep -n -f '^sleep infinity$' > "$PF"
         nsenter -t "$(cat "$PF")" -U -n --preserve-credentials ip link set lo up; echo "ns pid $(cat "$PF")";;
  run) shift; exec nsenter -t "$(cat "$PF")" -U -n --preserve-credentials "$@";;
  stop) kill "$(cat "$PF")" 2>/dev/null; rm -f "$PF"; echo "ns gestopt";;
esac
