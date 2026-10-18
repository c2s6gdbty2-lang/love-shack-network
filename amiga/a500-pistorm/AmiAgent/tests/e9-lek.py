#!/usr/bin/env python3
"""e9-lek.py - meet het verloop van vrij Chip/Fast RAM over 5 x 300 PINGs en 2 x 100 Avail (in de namespace)."""
import os, sys, time
sys.argv = [sys.argv[0], "basis"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lsntest.py")).read().split("# ---------------------------------------------------------------------------")[0])
boot(); install(); network(); start()
a = ami()
def free():
    time.sleep(2); i = a.system_info(); return int(i["chipram_free"]), int(i["fastram_free"])
c0, f0 = free(); say(f"start            chip {c0} fast {f0}")
fouten = 0
for b in range(3):
    for _ in range(300):
        st, v = try_(lambda: a.ping()); fouten += st != "OK"
        time.sleep(0.05)
    c, f = free(); say(f"na {300*(b+1):4d} PING     chip {c} fast {f}  (fast -{f0-f})  fouten totaal {fouten}")
for w in (30, 60, 90, 150):
    time.sleep(w - (0 if w == 30 else [30, 60, 90, 150][[30, 60, 90, 150].index(w) - 1]))
    c, f = free(); say(f"{w:3d} s rust          chip {c} fast {f}  (fast -{f0-f})")
for _ in range(100):
    st, v = try_(lambda: a.exec_command("Avail")); fouten += st != "OK"
c, f = free(); say(f"na 100 Avail        chip {c} fast {f}  (fast -{f0-f})  fouten totaal {fouten}")
time.sleep(120)
c, f = free(); say(f"120 s rust          chip {c} fast {f}  (fast -{f0-f})")
stop()
c, f = int(aux("av", 15, "Avail FAST").split()[-1]) if False else (0, 0)
out = aux("av", 15, "Avail")
say(out.strip())
subprocess.run([os.path.join(H, "emu-stop.sh")])
open(os.path.join(RES, "e9-lek.txt"), "w").write("\n".join(log) + "\n")
