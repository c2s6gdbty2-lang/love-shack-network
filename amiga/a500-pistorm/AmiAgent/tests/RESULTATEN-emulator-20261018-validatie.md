# Emulator validation of the release disk (18-10-2026, evening)

Environment: Amiberry 8.3.0, 68040, Kickstart 40.63 / Workbench 40.42, AmiTCP 3.0b2 on a2065 (slirp), in an unprivileged network namespace with loopback only. Disk: `AmiAgent-Installatie.adf` built from this repository (agent byte-identical to the build tested on the real A500; Disk.info, AmiAgent.info and WiFiVraag changed). Token: a generated test token only.

This is an **emulator** result, not a real-hardware result. Real-hardware results: see [docs/TESTS.md](../docs/TESTS.md).

**131/131 checks passed.** Screenshots of the icons on Workbench were checked by eye (disk icon on the desktop, drawer icon in the Work window).

| Phase | Test | Check | Result |
|---|---|---|---|
| basis | E1 | Start zonder installatie geweigerd | OK |
| basis | E1 | installatie, CRC-controle 15/15 | OK |
| basis | E1 | token opgeslagen, niet op de ADF | OK |
| basis | E1 | Start zonder netwerk geweigerd | OK |
| basis | E1 | netwerk (AmiTCP 3.0b2) gestart | OK |
| basis | E1 | Start: luistert op 7846 | OK |
| basis | E1 | PING met juist token, meldt READONLY | OK |
| basis | E1 | tweede Start: 'draait al', geen tweede agent | OK |
| basis | E1 | precies een amiagent-proces | OK |
| basis | E1 | Stop | OK |
| basis | E1 | na Stop geen verbinding meer | OK |
| basis | E1 | Stop als hij niet draait: nette melding | OK |
| basis | E1 | opnieuw Start werkt | OK |
| basis | E2 | fout token geweigerd | OK |
| basis | E2 | zonder token geweigerd | OK |
| basis | E2 | token met 1 teken te weinig geweigerd | OK |
| basis | E2 | agent draait door na foute pogingen | OK |
| basis | E2 | start met ontbrekend TOKENFILE geweigerd | OK |
| basis | E2 | READONLY-build start niet zonder token | OK |
| basis | E2 | token niet zichtbaar in Status | OK |
| basis | E4 | filter toont alleen 11 leestools | OK |
| basis | E4 | toegestaan: amiga_shell {"command": "Avail"} | OK |
| basis | E4 | toegestaan: amiga_shell {"command": "Version"} | OK |
| basis | E4 | toegestaan: amiga_shell {"command": "ShowConfig"} | OK |
| basis | E4 | toegestaan: amiga_system_info {} | OK |
| basis | E4 | toegestaan: amiga_list_dir {"path": "SYS:S"} | OK |
| basis | E4 | toegestaan: amiga_read_file {"path": "S:Startup-Sequence"} | OK |
| basis | E4 | geweigerd door filter: amiga_shell {"command": "Delete RAM:x"} | OK |
| basis | E4 | geweigerd door filter: amiga_shell {"command": "Avail FLUSH"} | OK |
| basis | E4 | geweigerd door filter: amiga_shell {"command": "Avail >RAM:x"} | OK |
| basis | E4 | geweigerd door filter: amiga_write_file {"path": "RAM:x", "content": "x"} | OK |
| basis | E4 | geweigerd door filter: amiga_arexx {"source": "say 1"} | OK |
| basis | E4 | geweigerd door filter: amiga_type {"text": "x"} | OK |
| basis | E4 | geweigerd door filter: amiga_click {"x": 1, "y": 1} | OK |
| basis | E4 | geweigerd door filter: amiga_break {} | OK |
| basis | E4 | geweigerd door filter: amiga_menu_select {"item": "Quit"} | OK |
| basis | E4 | geweigerd door filter: amiga_ui_click {"gadget": "OK"} | OK |
| basis | E4 | geweigerd door filter: amiga_read_file {"path": "CON:0/0/100/50/x"} | OK |
| basis | E4 | ShowConfig geeft geheugenindeling | OK |
| basis | E4 | filter weigert een host buiten LSN_ALLOWED_HOSTS | OK |
| basis | E7 | amiga_screenshot werkt | OK |
| basis | E7 | amiga_screens werkt | OK |
| basis | E7 | amiga_ui_tree werkt | OK |
| basis | E7 | amiga_menus werkt | OK |
| basis | E7 | amiga_pointer werkt | OK |
| basis | E7 | amiga_region_changed werkt | OK |
| basis | E5 | interface down: geen antwoord (time-out) | OK |
| basis | E5 | interface up: agent weer bereikbaar zonder herstart | OK |
| basis | E5 | client verbreekt midden in een verzoek: agent draait door | OK |
| basis | E5 | ongeldig frame: agent draait door | OK |
| basis | E6 | rw-test: 'Wait 30' met limiet 3 s -> 'still running' | OK |
| basis | E6 | rw-test: agent blijft bereikbaar tijdens vastgelopen opdracht | OK |
| basis | E6 | rw-test: BREAK stuurt Ctrl-C | OK |
| basis | E6 | rw-test: na BREAK werkt een nieuwe opdracht | OK |
| basis | E6 | READONLY: BREAK geweigerd | OK |
| basis | E6 | READONLY: 'Wait 30' geweigerd (kan niet vastlopen) | OK |
| basis | E6 | rw-test-agent weer gestopt (niet meer bereikbaar) | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_write_file {"path": "RAM:omzeil.txt", "content": "x"} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_write_file {"path": "Work:omzeil.txt", "content": "x"} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_shell {"command": "Delete Work:AmiAgent/LeesMij"} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_shell {"command": "Avail >RAM:omzeil"} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_arexx {"source": "address command 'Delete Work:AmiAgent/LeesMij'"} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_type {"text": "Delete Work:AmiAgent/LeesMij\n"} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_click {"x": 100, "y": 100} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_key {"key": "return"} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_menu_select {"item": "Quit"} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_ui_click {"gadget": "OK"} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_break {} | OK |
| basis | E10 | zonder filter geweigerd door agent: amiga_screenshot {"method": "sgrab"} | OK |
| basis | E10 | protocol rechtstreeks geweigerd: EXEC 'Avail FLUSH' | OK |
| basis | E10 | protocol rechtstreeks geweigerd: EXEC 'Avail >RAM:x' | OK |
| basis | E10 | protocol rechtstreeks geweigerd: EXEC 'Avail' + newline + Delete | OK |
| basis | E10 | protocol rechtstreeks geweigerd: EXEC ' Avail' (spatie) | OK |
| basis | E10 | protocol rechtstreeks geweigerd: EXEC 'C:Avail' | OK |
| basis | E10 | protocol rechtstreeks geweigerd: EXEC 'Avail;x' | OK |
| basis | E10 | protocol rechtstreeks geweigerd: EXEC 'Version Work:AmiAgent/amiagent' | OK |
| basis | E10 | protocol rechtstreeks geweigerd: PUT RAM:x | OK |
| basis | E10 | protocol rechtstreeks geweigerd: AREXX | OK |
| basis | E10 | protocol rechtstreeks geweigerd: INPUT tekst | OK |
| basis | E10 | protocol rechtstreeks geweigerd: INPUT klik | OK |
| basis | E10 | protocol rechtstreeks geweigerd: UIACT | OK |
| basis | E10 | protocol rechtstreeks geweigerd: BREAK | OK |
| basis | E10 | protocol rechtstreeks geweigerd: GET CON: | OK |
| basis | E10 | protocol rechtstreeks geweigerd: GET RAW: | OK |
| basis | E10 | protocol rechtstreeks geweigerd: GET SER: | OK |
| basis | E10 | protocol rechtstreeks geweigerd: GET PIPE: | OK |
| basis | E10 | protocol rechtstreeks geweigerd: GET map Work:AmiAgent | OK |
| basis | E10 | protocol rechtstreeks geweigerd: GETRANGE CON: | OK |
| basis | E10 | ruw frame 0x04 geweigerd | OK |
| basis | E10 | ruw frame 0x08 geweigerd | OK |
| basis | E10 | ruw frame 0x09 geweigerd | OK |
| basis | E10 | ruw frame 0x0E geweigerd | OK |
| basis | E10 | ruw frame 0x12 geweigerd | OK |
| basis | E10 | ruw frame 0x7F geweigerd | OK |
| basis | E10 | leesactie nog steeds toegestaan: EXEC Avail | OK |
| basis | E10 | leesactie nog steeds toegestaan: EXEC avail (kleine letters) | OK |
| basis | E10 | leesactie nog steeds toegestaan: GET S:Startup-Sequence | OK |
| basis | E10 | leesactie nog steeds toegestaan: GETRANGE S:Startup-Sequence | OK |
| basis | E10 | lokale ARexx ENTERTEXT -> rc 20 | OK |
| basis | E10 | lokale ARexx KEY -> rc 20 | OK |
| basis | E10 | lokale ARexx TASKPRI -> rc 20 | OK |
| basis | E10 | lokale ARexx ACTIVATEWINDOW -> rc 20 | OK |
| basis | E10 | lokale ARexx VERSION -> rc 0 | OK |
| basis | E10 | lokale ARexx TASKLIST -> rc 0 | OK |
| basis | E10 | Work: byte-identiek na alle pogingen | OK |
| basis | E10 | RAM: ongewijzigd na alle pogingen | OK |
| basis | E10 | Work:AmiAgent/LeesMij bestaat nog | OK |
| basis | E9 | 900 verbindingen (90x Avail) in 114 s, tempo ~10/s, zonder fout | OK |
| basis | E9 | Chip RAM: geen groei tussen reeks 2 en 3 | OK |
| basis | E9 | Fast RAM: geen groei tussen reeks 2 en 3 (<= 16 KB) | OK |
| e3 | E3 | productieregels (alleen Pi en Mac, voorbeeldadressen): verbinding geweigerd | OK |
| e3 | E3 | productieregels (alleen Pi en Mac, voorbeeldadressen): AmiTCP-log meldt de beslissing | OK |
| e3 | E3 | testregels (10.0.2.2 speelt de Pi): verbinding toegestaan | OK |
| e3 | E3 | testregels (10.0.2.2 speelt de Pi): AmiTCP-log meldt de beslissing | OK |
| e11 | E11 | Workbench-schermafdruk na boot (Disk.info van DF0 zichtbaar) | OK |
| e11 | E11 | Installeer via WiFiVraag: token correct opgeslagen | OK |
| e11 | E11 | WiFiVraag HIDE: token niet in klare tekst in het venster | OK |
| e11 | E11 | lade-icoon Work:AmiAgent.info geplaatst (keuze Ja) | OK |
| e11 | E11 | Work:AmiAgent.info byte-gelijk aan de gebouwde AmiAgent.info | OK |
| e11 | E11 | WiFiVraag IP: foutmelding toont 'Voorbeeld: 192.168.10.70' (3x) | OK |
| e11 | E11 | WiFiVraag IP: oude voorbeeldtekst (eigen netwerk) komt niet voor | OK |
| e11 | E11 | WiFiVraag IP: na drie ongeldige pogingen rc 10, geen bestand | OK |
| e11 | E11 | WiFiVraag IP: geldig adres geschreven, rc 0 | OK |
| e11 | E11 | WiFiVraag HIDE/MIN: te kort geweigerd, daarna geschreven zonder regeleinde | OK |
| e11 | E11 | WiFiVraag HIDE: invoer niet zichtbaar in het venster | OK |
| e11 | E11 | netwerk gestart | OK |
| e11 | E11 | agent GET AmiAgent-Installatie:Disk.info byte-gelijk aan de build | OK |
| e11 | E11 | agent GET Work:AmiAgent.info byte-gelijk aan de build | OK |
| e11 | E11 | agent GET AmiAgent-Installatie:C/WiFiVraag byte-gelijk aan de build | OK |
| e11 | E11 | agent LIST AmiAgent-Installatie: toont Disk.info | OK |
| e11 | E11 | Workbench-schermafdruk met agent actief | OK |
