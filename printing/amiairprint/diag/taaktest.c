/* taaktest - doet in een KALE exec-Task (geen Process, zoals printer.device onder
 * OS 3.1) achtereenvolgens: A = DOS Open/Write/Close van T:taaktest.tmp,
 * B = OpenLibrary("bsdsocket.library",3) + socket + connect naar 192.168.1.145:8631.
 * Elke stap meldt zich via een signaal; na 10 s zonder melding = HANGT. */
#include <exec/execbase.h>
#include <exec/tasks.h>
#include <exec/memory.h>
#include <dos/dos.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/alib.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <proto/bsdsocket.h>
extern struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
static struct Task *ouder; static volatile LONG stap, fout, modus;
static BYTE sig;
static void taak(void) {
    struct Library *SocketBase;
    struct Library *db = OpenLibrary((CONST_STRPTR)"dos.library", 36);
    if (modus == 0) {
        struct DosLibrary *DOSBase = (struct DosLibrary *)db;
        BPTR f;
        stap = 1; Signal(ouder, 1L << sig);
        f = Open((CONST_STRPTR)"T:taaktest.tmp", MODE_NEWFILE);
        stap = 2; Signal(ouder, 1L << sig);
        if (f) { Write(f, (APTR)"ok\n", 3); Close(f); } else fout = 1;
        stap = 3; Signal(ouder, 1L << sig);
    } else {
        struct sockaddr_in a; int s;
        stap = 1; Signal(ouder, 1L << sig);
        SocketBase = OpenLibrary((CONST_STRPTR)"bsdsocket.library", 3);
        stap = 2; Signal(ouder, 1L << sig);
        if (SocketBase) {
            s = socket(AF_INET, SOCK_STREAM, 0);
            memset(&a, 0, sizeof a); a.sin_family = AF_INET; a.sin_port = 8631;
            a.sin_addr.s_addr = (192UL << 24) | (168UL << 16) | (1UL << 8) | 145UL;
            if (s < 0 || connect(s, (struct sockaddr *)&a, sizeof a) < 0) fout = 2;
            if (s >= 0) CloseSocket(s);
            CloseLibrary(SocketBase);
        } else fout = 3;
        stap = 3; Signal(ouder, 1L << sig);
    }
    CloseLibrary(db);
    Forbid();  /* taak eindigt; ouder ruimt op */
    stap = 4; Signal(ouder, 1L << sig);
}
int main(int argc, char **argv) {
    struct Task *t; int i;
    modus = (argc > 1 && argv[1][0] == 'B');
    ouder = FindTask(NULL); sig = AllocSignal(-1);
    t = CreateTask((CONST_STRPTR)(modus ? "taaktest-socket" : "taaktest-dos"), 0, (APTR)taak, 8192);
    if (!t) { printf("CreateTask mislukt\n"); return 20; }
    for (i = 0; i < 100 && stap < 4; i++) { SetSignal(0, 1L << sig); if (stap < 4) Delay(5); }
    printf("modus %s: laatste stap %ld van 4, fout %ld -> %s\n", modus ? "B (bsdsocket)" : "A (DOS)",
           (long)stap, (long)fout, stap >= 4 ? (fout ? "FOUT" : "OK") : "HANGT (kale Task)");
    if (stap < 4) return 10;   /* taak blijft hangen; niet verwijderen */
    FreeSignal(sig); return fout ? 5 : 0;
}
