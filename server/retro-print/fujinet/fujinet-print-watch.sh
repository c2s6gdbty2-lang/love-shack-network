#!/bin/bash
# Nieuwe watcher voor Atari/FujiNet, naar analogie van meatloaf-print-watch.sh en
# c64ultimate-print-spooler.sh. FujiNet heeft geen bestandslijst/delete-API; het biedt
# alleen een vast endpoint GET /print dat de meest recente print-out als kant-en-klare
# PDF teruggeeft (geen reparatie nodig, in tegenstelling tot Meatloaf). Omdat dezelfde
# print-out bij herhaalde polls steeds opnieuw wordt teruggegeven totdat er een nieuwe
# printopdracht is gegeven, dedupliceren we op sha1-hash van de inhoud in plaats van op
# bestandsnaam/pad.
set -u

BASE="/opt/retro-print/fujinet"
CONFIG="$BASE/fujinet-print-watch.conf"
BUFFER="$BASE/buffer"
ARCHIVE="$BASE/archive"
STATE="$BASE/last-printed.sha1"
LOG="$BASE/fujinet-print-watch.log"
LOCKDIR="/tmp/fujinet-print-watch.lock"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"
}

# --- Rustig loggen (toegevoegd 2026-10-06) ----------------------------------
# Onbereikbaarheid van het apparaat is normaal (retromachine staat uit) en wordt
# alleen gelogd als statusovergang. Overige niet-succesvolle situaties worden via
# note() één keer gelogd zolang ze bij opeenvolgende polls terugkomen; zodra een
# poll ze niet meer meldt, worden ze bij een volgende keer opnieuw gelogd.
DEVICE_NAME="FujiNet"
STATUS_FILE="$BASE/device-status"
NOTICES_FILE="$BASE/device-notices"
NOTICES_RUN=""
NOTICES_ACTIVE=0

# note <melding> [detail]: alleen <melding> bepaalt of het een herhaling is, zodat
# wisselende details (ms-tijden in curl-fouten e.d.) de onderdrukking niet breken.
note() {
  local msg="$1" detail="${2:-}"
  NOTICES_RUN+="$msg"$'\n'
  if ! /usr/bin/grep -Fxq -- "$msg" "$NOTICES_FILE" 2>/dev/null; then
    if [ -n "$detail" ]; then log "$msg ($detail)"; else log "$msg"; fi
  fi
}

save_notices() {
  [ "$NOTICES_ACTIVE" = 1 ] || return 0
  local new old
  new="$(printf '%s' "$NOTICES_RUN" | /usr/bin/sort -u)"
  old="$(cat "$NOTICES_FILE" 2>/dev/null || true)"
  [ "$new" = "$old" ] || printf '%s\n' "$new" > "$NOTICES_FILE"
}

# set_reachable up|down [detail]: logt alleen bij een wijziging t.o.v. de vorige poll.
set_reachable() {
  local new="$1" detail="${2:-}" old="" since="" now
  [ -r "$STATUS_FILE" ] && read -r old since < "$STATUS_FILE"
  [ "$old" = "$new" ] && return 0
  now="$(date +%s)"
  printf '%s %s\n' "$new" "$now" > "$STATUS_FILE"
  if [ "$new" = "down" ]; then
    log "Status: $DEVICE_NAME ONBEREIKBAAR${detail:+ ($detail)}; volgende mislukte polls worden niet gelogd."
  elif [ -n "$old" ] && [ -n "$since" ]; then
    log "Status: $DEVICE_NAME weer BEREIKBAAR (onbereikbaar sinds $(date -d "@$since" '+%Y-%m-%d %H:%M:%S'))."
  else
    log "Status: $DEVICE_NAME BEREIKBAAR."
  fi
}

# probe_curl <curl-args>: als curl (met -o), maar vangt stderr af in CURL_ERR (één
# regel) en zet CURL_CONNECTED=1 als er een verbinding met het apparaat tot stand
# kwam. Zonder verbinding (DNS, geweigerd, connect-timeout) = onbereikbaar.
probe_curl() {
  local errf out
  errf="$(mktemp /tmp/retro-print-curl.XXXXXX)"
  out="$(/usr/bin/curl -w '%{num_connects}' "$@" 2>"$errf")"
  CURL_RC=$?
  CURL_ERR="$(tr '\n' ' ' < "$errf" | sed 's/ *$//')"
  rm -f "$errf"
  CURL_CONNECTED=0
  [ "${out:-0}" -gt 0 ] 2>/dev/null && CURL_CONNECTED=1
  return "$CURL_RC"
}
# -----------------------------------------------------------------------------

mkdir -p "$BASE" "$BUFFER" "$ARCHIVE" 2>/dev/null || exit 1
touch "$STATE" "$LOG" 2>/dev/null || exit 1

FUJINET_HOST="192.168.1.60"
PRINTER="Brother_MFC_L8390CDW_series"
CURL_MAX_TIME=20
RETRIES=3
RETRY_DELAY=4

if [ -f "$CONFIG" ]; then
  # shellcheck disable=SC1090
  . "$CONFIG"
fi

if ! mkdir "$LOCKDIR" 2>/dev/null; then
  exit 0
fi
NOTICES_ACTIVE=1
trap 'save_notices; rmdir "$LOCKDIR" 2>/dev/null || true' EXIT

PRINT_URL="http://$FUJINET_HOST/print"
stamp="$(date '+%Y%m%d-%H%M%S')"
probe="$BUFFER/${stamp}-printout.download"

# FujiNet (ESP32) kan traag/onregelmatig reageren terwijl het de SIO-bus met de Atari
# bedient; een paar korte herpogingen vangen dat beter op dan direct opgeven.
ok=0
connected=0
attempt=1
while [ "$attempt" -le "$RETRIES" ]; do
  if probe_curl -fsS --max-time "$CURL_MAX_TIME" "$PRINT_URL" -o "$probe"; then
    ok=1
    connected=1
    break
  fi
  [ "$CURL_CONNECTED" = 1 ] && connected=1
  rm -f "$probe"
  attempt=$((attempt + 1))
  [ "$attempt" -le "$RETRIES" ] && sleep "$RETRY_DELAY"
done

if [ "$connected" -ne 1 ]; then
  set_reachable down "$CURL_ERR"
  exit 0
fi
set_reachable up

if [ "$ok" -ne 1 ]; then
  note "FujiNet bereikbaar, maar geen print-out na $RETRIES poging(en): $PRINT_URL" "$CURL_ERR"
  exit 0
fi

if [ ! -s "$probe" ]; then
  rm -f "$probe"
  note "Overgeslagen, leeg antwoord van FujiNet."
  exit 0
fi

if [ "$(/usr/bin/head -c 5 "$probe" 2>/dev/null)" != "%PDF-" ]; then
  rm -f "$probe"
  note "Overgeslagen, geen PDF beschikbaar (printer busy/leeg of foutpagina)."
  exit 0
fi

sha="$(/usr/bin/sha1sum "$probe" | /usr/bin/awk '{print $1}')"
last_sha="$(cat "$STATE" 2>/dev/null || true)"

if [ -n "$last_sha" ] && [ "$sha" = "$last_sha" ]; then
  rm -f "$probe"
  # Normaal: FujiNet geeft de laatste print-out terug totdat er een nieuwe is (niet loggen).
  exit 0
fi

pdf="$BUFFER/${stamp}-printout.pdf"
mv "$probe" "$pdf"

if ! lp_err="$(/usr/bin/lp -d "$PRINTER" "$pdf" 2>&1 >/dev/null)"; then
  note "Printen mislukt voor FujiNet print-out" "$pdf; $(printf '%s' "$lp_err" | tr '\n' ' ')"
  exit 0
fi

cp "$pdf" "$ARCHIVE/${stamp}-printout.pdf" 2>>"$LOG" || true
printf '%s\n' "$sha" > "$STATE"
log "FujiNet print-out geprint en gearchiveerd: ${stamp}-printout.pdf ($sha)"
rm -f "$pdf"
