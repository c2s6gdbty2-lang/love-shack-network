#!/usr/bin/env python3
"""e11-wijzigingen.py - emulatortest van de drie bestanden die afwijken van de op de echte A500
geteste disk: Disk.info (nieuw ontwerp), AmiAgent.info (eigen lade-icoon) en C/WiFiVraag.
Draai IN de namespace, met dezelfde LSN_*-variabelen als lsntest.py (zie docs/TESTS.md):
    tests/ns.sh run python3 -I tests/e11-wijzigingen.py
Gebruikt alleen het testtoken en de scratch-emulator ($LSN_EMU)."""
import os, sys, time, subprocess, hashlib
K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.argv = [os.path.join(K, "tests", "lsntest.py"), "e11"]
__file__ = sys.argv[0]
exec(open(sys.argv[0]).read().split("# ---------------------------------------------------------------------------")[0])

E = os.environ["LSN_EMU"]; HN = os.environ["LSN_HARNESS"]
SHOTS = os.path.join(RES, "e11"); os.makedirs(SHOTS, exist_ok=True)
built = os.path.join(K, "out", "AmiAgent-Installatie")


def ipcshot(name):
    p = os.path.join(SHOTS, name)
    if os.path.exists(p):
        os.remove(p)
    subprocess.run([sys.executable, "-I", os.path.join(HN, "tools", "ipc.py"), "SCREENSHOT", p], capture_output=True)
    for _ in range(40):
        if os.path.exists(p) and os.path.getsize(p) > 0:
            time.sleep(0.3); return p
        time.sleep(0.1)
    return None


boot()
time.sleep(5)
check("E11", "Workbench-schermafdruk na boot (Disk.info van DF0 zichtbaar)", ipcshot("wb-na-boot.png"))

# WiFiVraag: de token-invoer van Installeer (HIDE, MIN 16 MAX 63, NOLF)
out = install()
tok = open(os.path.join(E, "work", "AmiAgent", "Prefs", "Token"), "rb").read()
check("E11", "Installeer via WiFiVraag: token correct opgeslagen", tok == TOKEN.encode() and "Installatie klaar" in out)
check("E11", "WiFiVraag HIDE: token niet in klare tekst in het venster", TOKEN not in out.replace("<token>", ""))
check("E11", "lade-icoon Work:AmiAgent.info geplaatst (keuze Ja)", os.path.exists(os.path.join(E, "work", "AmiAgent.info")))
check("E11", "Work:AmiAgent.info byte-gelijk aan de gebouwde AmiAgent.info",
      open(os.path.join(E, "work", "AmiAgent.info"), "rb").read() == open(os.path.join(built, "AmiAgent.info"), "rb").read())

# WiFiVraag: gewijzigde voorbeeldtekst in de IP-modus, drie ongeldige pogingen -> rc 10
out = aux("wv1", 40, 'AmiAgent-Installatie:C/WiFiVraag "Adres: " TO Tst:wv1.txt IP', "", "abc|1.2.3|300.1.1.1")
check("E11", "WiFiVraag IP: foutmelding toont 'Voorbeeld: 192.168.10.70' (3x)", out.count("Voorbeeld: 192.168.10.70") == 3, out[-300:])
check("E11", "WiFiVraag IP: oude voorbeeldtekst (eigen netwerk) komt niet voor", "192.168.86" not in out)
rc = aux("wv1rc", 10, 'Echo "RC=$RC"')
check("E11", "WiFiVraag IP: na drie ongeldige pogingen rc 10, geen bestand", "RC=10" in rc and not os.path.exists(os.path.join(E, "tst", "wv1.txt")), rc[-80:])
out = aux("wv2", 30, 'AmiAgent-Installatie:C/WiFiVraag "Adres: " TO Tst:wv2.txt IP', "", "192.168.1.70")
rc = aux("wv2rc", 10, 'Echo "RC=$RC"')
f = os.path.join(E, "tst", "wv2.txt")
check("E11", "WiFiVraag IP: geldig adres geschreven, rc 0", "RC=0" in rc and os.path.exists(f) and open(f).read().strip() == "192.168.1.70",
      open(f).read() if os.path.exists(f) else rc[-80:])
out = aux("wv3", 30, 'AmiAgent-Installatie:C/WiFiVraag "Geheim: " TO Tst:wv3.txt MIN 16 MAX 63 HIDE NOLF', "", "kort|dummygeheim-1234567")
rc = aux("wv3rc", 10, 'Echo "RC=$RC"')
f = os.path.join(E, "tst", "wv3.txt")
check("E11", "WiFiVraag HIDE/MIN: te kort geweigerd, daarna geschreven zonder regeleinde",
      "RC=0" in rc and os.path.exists(f) and open(f, "rb").read() == b"dummygeheim-1234567", rc[-80:])
check("E11", "WiFiVraag HIDE: invoer niet zichtbaar in het venster", "dummygeheim" not in out and "kort" not in out.split("Geheim:")[-1][:40], out[-200:])

# Agent leest de pictogrammen terug (leesfunctie) en ze zijn byte-gelijk aan de build
check("E11", "netwerk gestart", network())
start()
a = ami()
for amiga, rel in (("AmiAgent-Installatie:Disk.info", "Disk.info"), ("Work:AmiAgent.info", "AmiAgent.info"),
                   ("AmiAgent-Installatie:C/WiFiVraag", "C/WiFiVraag")):
    st, v = try_(lambda: a.read_file(amiga))
    check("E11", f"agent GET {amiga} byte-gelijk aan de build", st == "OK" and v == open(os.path.join(built, rel), "rb").read())
st, v = try_(lambda: a.list_dir("AmiAgent-Installatie:"))
check("E11", "agent LIST AmiAgent-Installatie: toont Disk.info", st == "OK" and any(e.name == "Disk.info" for e in v))
check("E11", "Workbench-schermafdruk met agent actief", ipcshot("wb-na-installatie.png"))
stop()

import json
json.dump(checks, open(os.path.join(RES, "e11.json"), "w"), indent=1)
open(os.path.join(RES, "e11.txt"), "w").write("\n".join(log) + "\n")
subprocess.run([os.path.join(HN, "emu-stop.sh")])
print(f"E11: {sum(c['ok'] for c in checks)}/{len(checks)} OK")
