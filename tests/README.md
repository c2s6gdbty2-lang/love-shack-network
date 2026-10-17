# Tests

Three levels, always reported separately:

| Level | What it proves | What it does not prove |
|---|---|---|
| **Emulator** (Amiberry 8.3.0, scratch disk copies) | Script logic, file changes (snapshots of every file before and after), and the exact IPP job bytes. A fake IPP printer (`ippeveprinter` + a proxy) accepts and stores the jobs. A logger records every byte on the emulated serial port. | Real network hardware (Plipbox, Wi-Fi), the real printer, paper |
| **Printer validation** | The real printer accepted the exact job bytes with IPP `Validate-Job` | Printing on paper |
| **Real hardware** | The whole chain on the real machine, with photos | Byte-level details of the jobs |

| Report | Contents |
|---|---|
| [`a600/`](a600/) | A600AirPrint: original package, public ADF in a clean emulator, real A600 |
| [`a500-pistorm/`](a500-pistorm/) | AirPrintPS: public ADF in a clean emulator, real A500 rev. 5 |

The emulator test harness (Amiberry IPC, keystroke and mouse helpers, snapshot and serial logger) is not part of this release yet. It still contains machine-specific paths.
