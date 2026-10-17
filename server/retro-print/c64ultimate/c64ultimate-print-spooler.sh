#!/bin/bash
# Geport van macOS (~/Library/Scripts/C64UltimatePrinter/c64ultimate-print-spooler.sh) naar Raspberry Pi.
# Logica ongewijzigd t.o.v. het origineel; shasum/stat -f/xxd (macOS) vervangen door
# Linux-equivalenten (sha1sum/stat -c/python3-magic-check), paden naar /opt/retro-print/c64ultimate.
set -u

BASE="${C64U_SPOOL_BASE:-/opt/retro-print/c64ultimate}"
CONFIG="$BASE/c64ultimate-print-spooler.conf"
LOG="$BASE/c64ultimate-print-spooler.log"
STATE="$BASE/printed-jobs.txt"
BUFFER="$BASE/buffer"
ARCHIVE="$BASE/archive"
LOCKDIR="/tmp/c64ultimate-print-spooler.lock"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"
}

# --- Rustig loggen (toegevoegd 2026-10-06) ----------------------------------
# Onbereikbaarheid van het apparaat is normaal (retromachine staat uit) en wordt
# alleen gelogd als statusovergang. Overige niet-succesvolle situaties worden via
# note() één keer gelogd zolang ze bij opeenvolgende polls terugkomen; zodra een
# poll ze niet meer meldt, worden ze bij een volgende keer opnieuw gelogd.
DEVICE_NAME="C64 Ultimate"
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

if [ -f "$CONFIG" ]; then
  # shellcheck disable=SC1090
  . "$CONFIG"
else
  log "Config ontbreekt: $CONFIG"
  exit 0
fi

: "${ULTIMATE_FTP_BASE:?ULTIMATE_FTP_BASE ontbreekt in config}"
: "${ULTIMATE_FTP_BASES:=$ULTIMATE_FTP_BASE}"
: "${PRINTER:=Brother_MFC_L8390CDW_series}"
: "${REMOTE_PATTERNS:=*.pdf *.txt *.prn *.raw *.seq}"
: "${DELETE_AFTER_PRINT:=0}"
: "${POLL_STABILITY_SECONDS:=2}"
: "${CURL_MAX_TIME:=30}"
: "${MIN_REMOTE_MTIME_EPOCH:=0}"

if ! mkdir "$LOCKDIR" 2>/dev/null; then
  exit 0
fi
NOTICES_ACTIVE=1
trap 'save_notices; rmdir "$LOCKDIR" 2>/dev/null || true' EXIT

ftp_join() {
  local base="$1"
  local name="$2"
  base="${base%/}"
  printf '%s/%s' "$base" "$name"
}

ftp_absolute_path() {
  /usr/bin/python3 -c 'import sys, urllib.parse; u=urllib.parse.urlparse(sys.argv[1]); p=(u.path.rstrip("/") + "/" + sys.argv[2]).replace("//", "/"); print(p)' "$1" "$2"
}

url_escape_path_component() {
  /usr/bin/python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$1"
}

matches_patterns() {
  local name="$1"
  local pattern
  for pattern in $REMOTE_PATTERNS; do
    case "$name" in
      $pattern) return 0 ;;
    esac
  done
  return 1
}

base_accepts_all_print_files() {
  local base="$1"
  case "${base%/}" in
    */printer|*/Printer|*/PRINTER) return 0 ;;
  esac
  return 1
}

magic8() {
  # Eerste 8 bytes als hex, zonder afhankelijkheid van xxd (niet standaard op Debian).
  /usr/bin/python3 -c 'import sys; print(open(sys.argv[1],"rb").read(8).hex())' "$1" 2>/dev/null
}

print_file() {
  local file="$1"
  local name="$2"
  local magic
  case "${name##*.}" in
    pdf|PDF)
      /usr/bin/lp -d "$PRINTER" "$file"
      ;;
    png|PNG|jpg|JPG|jpeg|JPEG)
      /usr/bin/lp -d "$PRINTER" "$file"
      ;;
    *)
      magic="$(magic8 "$file")"
      case "$magic" in
        89504e470d0a1a0a)
          /usr/bin/lp -d "$PRINTER" "$file"
          ;;
        25504446*)
          /usr/bin/lp -d "$PRINTER" "$file"
          ;;
        *)
          /usr/bin/lp -d "$PRINTER" -o raw "$file"
          ;;
      esac
      ;;
  esac
}

any_connected=0
unreachable_detail=""
for current_base in $ULTIMATE_FTP_BASES; do
  listing="$BUFFER/listing-$(date '+%Y%m%d-%H%M%S')-$(basename "$current_base").txt"
  parsed_listing="$listing.parsed"
  if ! probe_curl -fsS --max-time "$CURL_MAX_TIME" "$current_base/" -o "$listing"; then
    rm -f "$listing"
    if [ "$CURL_CONNECTED" = 1 ]; then
      any_connected=1
      set_reachable up
      note "Ultimate FTP bereikbaar, maar listing mislukt: $current_base" "$CURL_ERR"
    else
      unreachable_detail="$CURL_ERR"
    fi
    continue
  fi
  any_connected=1
  set_reachable up

  if ! /usr/bin/python3 - "$listing" > "$parsed_listing" <<'PY'
import datetime
import sys

months = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}
now = datetime.datetime.now()

with open(sys.argv[1], "r", errors="replace") as handle:
    for raw in handle:
        line = raw.rstrip("\r\n")
        if not line or line[0] != "-":
            continue

        parts = line.split(maxsplit=8)
        if len(parts) < 9:
            continue

        size = parts[4]
        month = months.get(parts[5])
        if month is None:
            continue

        try:
            day = int(parts[6])
        except ValueError:
            continue

        year_or_time = parts[7]
        if ":" in year_or_time:
            hour, minute = [int(piece) for piece in year_or_time.split(":", 1)]
            candidate = datetime.datetime(now.year, month, day, hour, minute)
            if candidate > now + datetime.timedelta(days=1):
                candidate = candidate.replace(year=now.year - 1)
        else:
            candidate = datetime.datetime(int(year_or_time), month, day, 0, 0)

        print(f"{size}\t{int(candidate.timestamp())}\t{parts[8]}")
PY
  then
    note "FTP listing parseren mislukt: $current_base"
    rm -f "$listing" "$parsed_listing"
    continue
  fi

  while IFS=$'\t' read -r remote_listed_size remote_mtime_epoch remote_name; do
  remote_name="${remote_name%$'\r'}"
  [ -n "$remote_name" ] || continue
  case "$remote_name" in
    .|..|*/) continue ;;
  esac
  if ! base_accepts_all_print_files "$current_base"; then
    matches_patterns "$remote_name" || continue
  fi

  if [ "$MIN_REMOTE_MTIME_EPOCH" -gt 0 ] && [ "$remote_mtime_epoch" -lt "$MIN_REMOTE_MTIME_EPOCH" ]; then
    continue
  fi

  escaped_name="$(url_escape_path_component "$remote_name")"
  remote_url="$(ftp_join "$current_base" "$escaped_name")"
  stamp="$(date '+%Y%m%d-%H%M%S')"
  first="$BUFFER/$stamp-$remote_name.first"
  second="$BUFFER/$stamp-$remote_name"

  if ! probe_curl -fsS --max-time "$CURL_MAX_TIME" "$remote_url" -o "$first"; then
    note "Download mislukt: $remote_name" "$CURL_ERR"
    rm -f "$first" "$second"
    continue
  fi

  sleep "$POLL_STABILITY_SECONDS"

  if ! probe_curl -fsS --max-time "$CURL_MAX_TIME" "$remote_url" -o "$second"; then
    note "Tweede download mislukt, overgeslagen: $remote_name" "$CURL_ERR"
    rm -f "$first" "$second"
    continue
  fi

  size1="$(/usr/bin/stat -c '%s' "$first" 2>/dev/null || echo 0)"
  size2="$(/usr/bin/stat -c '%s' "$second" 2>/dev/null || echo 0)"
  sha1="$(/usr/bin/sha1sum "$first" | /usr/bin/awk '{print $1}')"
  sha2="$(/usr/bin/sha1sum "$second" | /usr/bin/awk '{print $1}')"

  if [ "$size2" = "0" ]; then
    note "Overgeslagen, 0-byte printjob: $remote_name"
    rm -f "$first" "$second"
    continue
  fi

  if [ "$size1" != "$size2" ] || [ "$sha1" != "$sha2" ]; then
    # Normaal: de Ultimate schrijft nog; de volgende poll pakt de job op (niet loggen).
    rm -f "$first" "$second"
    continue
  fi

  key="$current_base|$remote_name|$size2|$sha2"
  if /usr/bin/grep -Fxq "$key" "$STATE"; then
    # Normaal: al geprint (verwijderen mislukte eerder en is toen al gelogd).
    rm -f "$first" "$second"
    continue
  fi

  if lp_out="$(print_file "$second" "$remote_name" 2>&1)"; then
    [ -n "$lp_out" ] && printf '%s\n' "$lp_out" >> "$LOG"
    printf '%s\n' "$key" >> "$STATE"
    cp "$second" "$ARCHIVE/$stamp-$remote_name" 2>>"$LOG" || true
    log "Geprint op $PRINTER: $remote_name ($size2 bytes)"

    if [ "$DELETE_AFTER_PRINT" = "1" ]; then
      remote_abs_path="$(ftp_absolute_path "$current_base" "$remote_name")"
      if /usr/bin/curl -fsS --max-time "$CURL_MAX_TIME" -Q "DELE $remote_abs_path" "$ULTIMATE_FTP_BASE/" >/dev/null 2>>"$LOG"; then
        log "Remote printjob verwijderd: $remote_name"
      else
        log "Print OK, maar remote verwijderen mislukt: $remote_name"
      fi
    fi
  else
    note "Printen mislukt, remote blijft staan: $remote_name" "$(printf '%s' "$lp_out" | tr '\n' ' ')"
  fi

    rm -f "$first" "$second"
  done < "$parsed_listing"

  rm -f "$listing" "$parsed_listing"
done

if [ "$any_connected" = 0 ]; then
  set_reachable down "$unreachable_detail"
fi
