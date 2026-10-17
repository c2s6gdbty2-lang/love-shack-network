#!/bin/bash
# Geport van macOS (~/Library/Scripts/MeatloafPrinter/meatloaf-print-watch.sh) naar Raspberry Pi.
# Logica ongewijzigd t.o.v. het origineel; alleen macOS-specifieke commando's (shasum, stat -f)
# vervangen door hun Linux-equivalenten en paden verplaatst naar /opt/retro-print/meatloaf.
set -u

BASE="/opt/retro-print/meatloaf"
BUFFER="$BASE/buffer"
REPAIRED="$BASE/repaired"
STATE="$BASE/delete-failed-paper-files.txt"
LOG="$BASE/meatloaf-print-watch.log"
LOCKDIR="/tmp/meatloaf-print-watch.lock"
REPAIR="$BASE/repair_meatloaf_pdf.py"
SD_ROOT="http://meatloaf.local/sd"
ARCHIVE_ROOT="$SD_ROOT/_printed_archive"
PRINTER="Brother_MFC_L8390CDW_series"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"
}

# --- Rustig loggen (toegevoegd 2026-10-06) ----------------------------------
# Onbereikbaarheid van het apparaat is normaal (retromachine staat uit) en wordt
# alleen gelogd als statusovergang. Overige niet-succesvolle situaties worden via
# note() één keer gelogd zolang ze bij opeenvolgende polls terugkomen; zodra een
# poll ze niet meer meldt, worden ze bij een volgende keer opnieuw gelogd.
DEVICE_NAME="Meatloaf"
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

url_escape() {
  /usr/bin/python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$1"
}

if ! mkdir "$LOCKDIR" 2>/dev/null; then
  exit 0
fi
NOTICES_ACTIVE=1
trap 'save_notices; rmdir "$LOCKDIR" 2>/dev/null || true' EXIT

mkdir -p "$BUFFER" "$REPAIRED" 2>/dev/null || {
  log "Kan lokale buffer/repaired map niet maken."
  exit 1
}

touch "$STATE" 2>/dev/null || {
  log "Kan foutlijst niet openen: $STATE"
  exit 1
}

root_listing="$BUFFER/propfind-root-$(date '+%Y%m%d-%H%M%S').xml"
print_listing="$BUFFER/propfind-print-$(date '+%Y%m%d-%H%M%S').xml"

if ! probe_curl -fsS -X PROPFIND -H Depth:1 --max-time 30 "$SD_ROOT/" -o "$root_listing"; then
  rm -f "$root_listing" "$print_listing"
  if [ "$CURL_CONNECTED" = 1 ]; then
    set_reachable up
    note "Meatloaf bereikbaar, maar WebDAV PROPFIND op SD-map mislukt." "$CURL_ERR"
  else
    set_reachable down "$CURL_ERR"
  fi
  exit 0
fi
set_reachable up

if /usr/bin/grep -q "<D:href>/sd/.print</D:href>" "$root_listing"; then
  probe_curl -fsS -X PROPFIND -H Depth:1 --max-time 30 "$SD_ROOT/.print/" -o "$print_listing" || {
    note "WebDAV PROPFIND op .print mislukt." "$CURL_ERR"
    rm -f "$print_listing"
  }
else
  : > "$print_listing"
fi

if [ ! -s "$root_listing" ]; then
  rm -f "$root_listing" "$print_listing"
  note "Meatloaf WebDAV SD-map gaf een lege listing."
  exit 0
fi

while IFS='|' read -r listing href path name; do
  if [ ! -s "$listing" ] || ! /usr/bin/grep -q "<D:href>$href</D:href>" "$listing"; then
    continue
  fi

  escaped_path="$(url_escape "$path")"
  stamp="$(date '+%Y%m%d-%H%M%S')"
  probe="$BUFFER/${stamp}-${name}.download"
  buffered="$BUFFER/${stamp}-${name}.pdf"
  fixed="$REPAIRED/${stamp}-${name}.pdf"
  source_url="$SD_ROOT/$escaped_path"

  if ! probe_curl -fsS --max-time 30 "$source_url" -o "$probe"; then
    rm -f "$probe"
    note "Download mislukt via WebDAV: $path" "$CURL_ERR"
    continue
  fi

  if [ ! -s "$probe" ]; then
    rm -f "$probe"
    note "Overgeslagen, leeg bestand via WebDAV: $path"
    continue
  fi

  if [ "$(/usr/bin/head -c 5 "$probe" 2>/dev/null)" != "%PDF-" ]; then
    rm -f "$probe"
    note "Overgeslagen, geen PDF-inhoud via WebDAV: $path"
    continue
  fi

  size="$(/usr/bin/stat -c '%s' "$probe" 2>/dev/null || echo 0)"
  sha="$(/usr/bin/sha1sum "$probe" | /usr/bin/awk '{print $1}')"
  key="$path|$size|$sha"

  delete_failed_key="delete-failed|$key"
  if grep -Fxq "$delete_failed_key" "$STATE"; then
    rm -f "$probe"
    note "Overgeslagen om dubbele print te voorkomen; eerder verwijderen mislukte: $path"
    continue
  fi

  mv "$probe" "$buffered"

  if ! repair_out="$(/usr/bin/python3 "$REPAIR" "$buffered" "$fixed" 2>&1)"; then
    note "Reparatie mislukt, origineel blijft op Meatloaf staan: $path" "$(printf '%s' "$repair_out" | tr '\n' ' ')"
    continue
  fi
  [ -n "$repair_out" ] && printf '%s\n' "$repair_out" >> "$LOG"

  if ! lp_err="$(/usr/bin/lp -d "$PRINTER" "$fixed" 2>&1 >/dev/null)"; then
    note "Printen van gerepareerde PDF mislukt, origineel blijft op Meatloaf staan: $path" "$(printf '%s' "$lp_err" | tr '\n' ' ')"
    continue
  fi

  archive_name="${stamp}-${name}"
  archive_url="$ARCHIVE_ROOT/$(url_escape "$archive_name")"
  if ! /usr/bin/curl -fsS --max-time 30 -T "$buffered" "$archive_url" >/dev/null 2>>"$LOG"; then
    log "Geprint, maar upload naar archief mislukt; origineel blijft staan: $path"
    continue
  fi

  if /usr/bin/curl -fsS --max-time 30 -X DELETE "$source_url" >/dev/null 2>>"$LOG"; then
    state_tmp="$BUFFER/state-$(date '+%Y%m%d-%H%M%S').tmp"
    /usr/bin/grep -Fvx "$delete_failed_key" "$STATE" > "$state_tmp" 2>/dev/null || true
    mv "$state_tmp" "$STATE"
    log "Via WebDAV gebufferd, gerepareerd, geprint en gearchiveerd: $path -> $archive_name"
  else
    printf '%s\n' "$delete_failed_key" >> "$STATE"
    log "Geprint en archiefkopie gemaakt, maar origineel verwijderen mislukt: $path"
  fi
done <<JOBS
$print_listing|/sd/.print/paper.pdf|.print/paper.pdf|paper.pdf
$print_listing|/sd/.print/paper|.print/paper|paper
$root_listing|/sd/paper.pdf|paper.pdf|paper.pdf
$root_listing|/sd/paper|paper|paper
JOBS

rm -f "$root_listing" "$print_listing"
