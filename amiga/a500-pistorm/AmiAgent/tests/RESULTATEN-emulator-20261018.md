# Emulatortests AmiAgent LSN (18-10-2026)

Amiberry, CPU 68040, Kickstart 40.63/WB 40.42, AmiTCP 3.0b2 (bsdsocket 3.28) via de PlipNet 1.1-testvariant op a2065/slirp.
Fasen basis en E3 in een geisoleerde netwerknamespace (alleen loopback). E8 buiten de namespace (slirp verbindt daarbinnen niet uitgaand);
de test-smbd luisterde alleen op <server-IP>:4450 met hosts allow = <server-IP>, de agent was READONLY met testtoken.

| Test | Controle | Resultaat | Detail |
|---|---|---|---|
| E1 | Start zonder installatie geweigerd | OK | ['--- requester 1: schermafdruk e1a-scherm01.png, gekozen Amiga+V', ''] |
| E1 | installatie, CRC-controle 15/15 | OK |  |
| E1 | token opgeslagen, niet op de ADF | OK |  |
| E1 | Start zonder netwerk geweigerd | OK |  |
| E1 | netwerk (AmiTCP 3.0b2) gestart | OK |  |
| E1 | Start: luistert op 7846 | OK |  |
| E1 | PING met juist token, meldt READONLY | OK | amiagent 0.13.2 (lsn1 READONLY)  AmigaOS dos.library 40  |
| E1 | tweede Start: 'draait al', geen tweede agent | OK |  |
| E1 | precies een amiagent-proces | OK |  |
| E1 | Stop | OK |  |
| E1 | na Stop geen verbinding meer | OK | ConnectionResetError |
| E1 | Stop als hij niet draait: nette melding | OK |  |
| E1 | opnieuw Start werkt | OK |  |
| E2 | fout token geweigerd | OK | bad token |
| E2 | zonder token geweigerd | OK | the agent requires a token — set AMIGA_TOKEN to the same value amiagent was started with |
| E2 | token met 1 teken te weinig geweigerd | OK | bad token |
| E2 | agent draait door na foute pogingen | OK |  |
| E2 | start met ontbrekend TOKENFILE geweigerd | OK | [''] |
| E2 | READONLY-build start niet zonder token | OK |  |
| E2 | token niet zichtbaar in Status | OK |  |
| E4 | filter toont alleen 11 leestools | OK | ['amiga_shell', 'amiga_rexx_ports', 'amiga_read_file', 'amiga_list_dir', 'amiga_screenshot |
| E4 | toegestaan: amiga_shell {"command": "Avail"} | OK | $ Avail return code: 0  Type  Available    In-Use   Maximum   Largest chip     960208      |
| E4 | toegestaan: amiga_shell {"command": "Version"} | OK | $ Version return code: 0  Kickstart 40.63, Workbench 40.42 |
| E4 | toegestaan: amiga_shell {"command": "ShowConfig"} | OK | $ ShowConfig return code: 0  PROCESSOR:	CPU 68040 CUSTOM CHIPS:	Normal PAL Agnus (id=$0000 |
| E4 | toegestaan: amiga_system_info {} | OK | agent             amiagent 0.13.2 build             lsn1 READONLY kickstart         40.10  |
| E4 | toegestaan: amiga_list_dir {"path": "SYS:S"} | OK | SYS:S — 7 entries  DPat                     873  ----rwed  03-Oct-26 20:59:27 Ed-startup   |
| E4 | toegestaan: amiga_read_file {"path": "S:Startup-Sequence"} | OK | S:Startup-Sequence:  ; $VER: Startup-Sequence_LD 40.3 (31.8.93) ; Startup-Sequence for low |
| E4 | geweigerd door filter: amiga_shell {"command": "Delete RAM:x"} | OK | READONLY-filter: amiga_shell only accepts exactly: Avail, ShowConfig, Version |
| E4 | geweigerd door filter: amiga_shell {"command": "Avail FLUSH"} | OK | READONLY-filter: amiga_shell only accepts exactly: Avail, ShowConfig, Version |
| E4 | geweigerd door filter: amiga_shell {"command": "Avail >RAM:x"} | OK | READONLY-filter: amiga_shell only accepts exactly: Avail, ShowConfig, Version |
| E4 | geweigerd door filter: amiga_write_file {"path": "RAM:x", "content": "x"} | OK | READONLY-filter: amiga_write_file is not allowed in read-only mode |
| E4 | geweigerd door filter: amiga_arexx {"source": "say 1"} | OK | READONLY-filter: amiga_arexx is not allowed in read-only mode |
| E4 | geweigerd door filter: amiga_type {"text": "x"} | OK | READONLY-filter: amiga_type is not allowed in read-only mode |
| E4 | geweigerd door filter: amiga_click {"x": 1, "y": 1} | OK | READONLY-filter: amiga_click is not allowed in read-only mode |
| E4 | geweigerd door filter: amiga_break {} | OK | READONLY-filter: amiga_break is not allowed in read-only mode |
| E4 | geweigerd door filter: amiga_menu_select {"item": "Quit"} | OK | READONLY-filter: amiga_menu_select is not allowed in read-only mode |
| E4 | geweigerd door filter: amiga_ui_click {"gadget": "OK"} | OK | READONLY-filter: amiga_ui_click is not allowed in read-only mode |
| E4 | geweigerd door filter: amiga_read_file {"path": "CON:0/0/100/50/x"} | OK | READONLY-filter: amiga_read_file: device handlers and control characters are refused |
| E4 | ShowConfig geeft geheugenindeling | OK | $ ShowConfig return code: 0  PROCESSOR:	CPU 68040 CUSTOM CHIPS:	Normal PAL Agnus (id=$0000 |
| E4 | filter weigert een host buiten LSN_ALLOWED_HOSTS | OK | amimcp-ro: AMIGA_HOST '127.0.0.1' is not in LSN_ALLOWED_HOSTS |
| E7 | amiga_screenshot werkt | OK | Frontmost screen: 640x256, 4-colour (native capture). [image] |
| E7 | amiga_screens werkt | OK | Open screens, front to back:   [0] 640x256 depth 2 mode 0x00008000  Copyright © 1985-1993  |
| E7 | amiga_ui_tree werkt | OK | S 0 640x256 depth=2 "Copyright   1985-1993 Commodore-Amiga, Inc. All Rights Reserved" W 0  |
| E7 | amiga_menus werkt | OK | W "Workbench" M 0 on "Workbench" I 0 0 - 63488 uncheck "B" "Backdrop" I 0 1 - 63520 - "E"  |
| E7 | amiga_pointer werkt | OK | Pointer at (0, 0) on a 640x256 screen. This is Intuition's pointer; SDL programs keep thei |
| E7 | amiga_region_changed werkt | OK | region checksum: f0eca6cf |
| E5 | interface down: geen antwoord (time-out) | OK | ConnectionResetError |
| E5 | interface up: agent weer bereikbaar zonder herstart | OK | OK |
| E5 | client verbreekt midden in een verzoek: agent draait door | OK |  |
| E5 | ongeldig frame: agent draait door | OK |  |
| E6 | rw-test: 'Wait 30' met limiet 3 s -> 'still running' | OK | still running after 3s. The agent is NOT stuck - it is back to accepting connections, and  |
| E6 | rw-test: agent blijft bereikbaar tijdens vastgelopen opdracht | OK |  |
| E6 | rw-test: BREAK stuurt Ctrl-C | OK | sent Ctrl-C to 2 process(es); the command may take a moment to notice, and not every progr |
| E6 | rw-test: na BREAK werkt een nieuwe opdracht | OK | (0, 'na-break\n') |
| E6 | READONLY: BREAK geweigerd | OK | READONLY: BREAK is disabled in this read-only agent |
| E6 | READONLY: 'Wait 30' geweigerd (kan niet vastlopen) | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E6 | rw-test-agent weer gestopt (niet meer bereikbaar) | OK |  |
| E10 | zonder filter geweigerd door agent: amiga_write_file {"path": "RAM:omzeil.txt", "content": "x"} | OK | READONLY: PUT is disabled in this read-only agent |
| E10 | zonder filter geweigerd door agent: amiga_write_file {"path": "Work:omzeil.txt", "content": "x"} | OK | READONLY: PUT is disabled in this read-only agent |
| E10 | zonder filter geweigerd door agent: amiga_shell {"command": "Delete Work:AmiAgent/LeesMij"} | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | zonder filter geweigerd door agent: amiga_shell {"command": "Avail >RAM:omzeil"} | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | zonder filter geweigerd door agent: amiga_arexx {"source": "address command 'Delete Work:AmiAgent/LeesMij'"} | OK | READONLY: AREXX is disabled in this read-only agent |
| E10 | zonder filter geweigerd door agent: amiga_type {"text": "Delete Work:AmiAgent/LeesMij\n"} | OK | READONLY: INPUT is disabled in this read-only agent |
| E10 | zonder filter geweigerd door agent: amiga_click {"x": 100, "y": 100} | OK | READONLY: INPUT is disabled in this read-only agent |
| E10 | zonder filter geweigerd door agent: amiga_key {"key": "return"} | OK | READONLY: INPUT is disabled in this read-only agent |
| E10 | zonder filter geweigerd door agent: amiga_menu_select {"item": "Quit"} | OK | READONLY: UIACT is disabled in this read-only agent |
| E10 | zonder filter geweigerd door agent: amiga_ui_click {"gadget": "OK"} | OK | READONLY: UIACT is disabled in this read-only agent |
| E10 | zonder filter geweigerd door agent: amiga_break {} | OK | READONLY: BREAK is disabled in this read-only agent |
| E10 | zonder filter geweigerd door agent: amiga_screenshot {"method": "sgrab"} | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | protocol rechtstreeks geweigerd: EXEC 'Avail FLUSH' | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | protocol rechtstreeks geweigerd: EXEC 'Avail >RAM:x' | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | protocol rechtstreeks geweigerd: EXEC 'Avail' + newline + Delete | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | protocol rechtstreeks geweigerd: EXEC ' Avail' (spatie) | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | protocol rechtstreeks geweigerd: EXEC 'C:Avail' | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | protocol rechtstreeks geweigerd: EXEC 'Avail;x' | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | protocol rechtstreeks geweigerd: EXEC 'Version Work:AmiAgent/amiagent' | OK | READONLY: only Avail, Version or ShowConfig (exactly that word, no arguments) |
| E10 | protocol rechtstreeks geweigerd: PUT RAM:x | OK | READONLY: PUT is disabled in this read-only agent |
| E10 | protocol rechtstreeks geweigerd: AREXX | OK | READONLY: AREXX is disabled in this read-only agent |
| E10 | protocol rechtstreeks geweigerd: INPUT tekst | OK | READONLY: INPUT is disabled in this read-only agent |
| E10 | protocol rechtstreeks geweigerd: INPUT klik | OK | READONLY: INPUT is disabled in this read-only agent |
| E10 | protocol rechtstreeks geweigerd: UIACT | OK | READONLY: UIACT is disabled in this read-only agent |
| E10 | protocol rechtstreeks geweigerd: BREAK | OK | READONLY: BREAK is disabled in this read-only agent |
| E10 | protocol rechtstreeks geweigerd: GET CON: | OK | cannot open "CON:0/0/200/50/omzeil" for reading (DOS error 209) |
| E10 | protocol rechtstreeks geweigerd: GET RAW: | OK | cannot open "RAW:0/0/200/50/omzeil" for reading (DOS error 209) |
| E10 | protocol rechtstreeks geweigerd: GET SER: | OK | cannot open "SER:" for reading (DOS error 209) |
| E10 | protocol rechtstreeks geweigerd: GET PIPE: | OK | cannot open "PIPE:omzeil" for reading (DOS error 209) |
| E10 | protocol rechtstreeks geweigerd: GET map Work:AmiAgent | OK | cannot open "Work:AmiAgent" for reading (DOS error 212) |
| E10 | protocol rechtstreeks geweigerd: GETRANGE CON: | OK | cannot open "CON:0/0/200/50/omzeil" for reading (DOS error 209) |
| E10 | ruw frame 0x04 geweigerd | OK | b'READONLY: PUT is disabled in this read-only agent' |
| E10 | ruw frame 0x08 geweigerd | OK | b'READONLY: INPUT is disabled in this read-only agent' |
| E10 | ruw frame 0x09 geweigerd | OK | b'READONLY: BREAK is disabled in this read-only agent' |
| E10 | ruw frame 0x0E geweigerd | OK | b'READONLY: UIACT is disabled in this read-only agent' |
| E10 | ruw frame 0x12 geweigerd | OK | b'READONLY: AREXX is disabled in this read-only agent' |
| E10 | ruw frame 0x7F geweigerd | OK | b'unknown command' |
| E10 | leesactie nog steeds toegestaan: EXEC Avail | OK |  |
| E10 | leesactie nog steeds toegestaan: EXEC avail (kleine letters) | OK |  |
| E10 | leesactie nog steeds toegestaan: GET S:Startup-Sequence | OK |  |
| E10 | leesactie nog steeds toegestaan: GETRANGE S:Startup-Sequence | OK |  |
| E10 | lokale ARexx ENTERTEXT -> rc 20 | OK | ['RC= 20'] |
| E10 | lokale ARexx KEY -> rc 20 | OK | ['RC= 20'] |
| E10 | lokale ARexx TASKPRI -> rc 20 | OK | ['RC= 20'] |
| E10 | lokale ARexx ACTIVATEWINDOW -> rc 20 | OK | ['RC= 20'] |
| E10 | lokale ARexx VERSION -> rc 0 | OK | ['RC= 0'] |
| E10 | lokale ARexx TASKLIST -> rc 0 | OK | ['RC= 0'] |
| E10 | Work: byte-identiek na alle pogingen | OK | 3f6f41bda6ae3106 / 3f6f41bda6ae3106 |
| E10 | RAM: ongewijzigd na alle pogingen | OK |  |
| E10 | Work:AmiAgent/LeesMij bestaat nog | OK |  |
| E9 | 900 verbindingen (90x Avail) in 113 s, tempo ~10/s, zonder fout | OK | 0 fouten |
| E9 | Chip RAM: geen groei tussen reeks 2 en 3 | OK | 0 |
| E9 | Fast RAM: geen groei tussen reeks 2 en 3 (<= 16 KB) | OK | 12448 |
| E3 | productieregels (alleen Pi .145 en Mac .30): verbinding geweigerd | OK | ConnectionResetError |
| E3 | productieregels (alleen Pi .145 en Mac .30): AmiTCP-log meldt de beslissing | OK | ['     1 Sun Oct 18 10:45:09 2026 [note ]: Access from host 10.0.2.2 to port 7846 denied'] |
| E3 | testregels (10.0.2.2 speelt de Pi): verbinding toegestaan | OK | OK |
| E3 | testregels (10.0.2.2 speelt de Pi): AmiTCP-log meldt de beslissing | OK | ['     1 Sun Oct 18 10:47:21 2026 [info ]: Access from host 10.0.2.2 to port 7846 allowed' |
| E8 | test-smbd bereikbaar (<server-IP>:4450) | OK |  |
| E8 | smbfs koppelt LSNTest: naast amiagent (zelfde AmiTCP) | OK | ['\x0f', ''] |
| E8 | amiagent bereikbaar terwijl smbfs gekoppeld is | OK |  |
| E8 | amiagent antwoordt tijdens SMB-kopie (10/10) | OK | ['OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK'] |
| E8 | kopie via smbfs byte-identiek (gelezen via amiagent) | OK | 16FE7528 |
| E8 | amiagent kan LSNTest: alleen lezen (LIST) | OK |  |
| E8 | amiagent kan NIET naar de share schrijven | OK | READONLY: PUT is disabled in this read-only agent |
| E8 | na AmiAgent Stop blijft LSNTest: gekoppeld | OK |  |
