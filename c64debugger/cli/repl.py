import cmd
import os
import sys
from typing import Optional, List, Dict, Any
from c64debugger.debugger_core import C64DebuggerCore
from c64debugger.vice_bridge import VICERemoteMonitorBridge
from c64debugger.disasm.memory_map import C64MemoryMap
from c64debugger.disasm.profiler import C64Profiler

HISTORY_FILE = os.path.expanduser("~/.c64debugger_history")

class C64DebuggerREPL(cmd.Cmd):
    intro = (
        "==================================================\n"
        "      C64 Debugger - Shell REPL Interattiva       \n"
        "             Digita 'help' o '?' per i comandi    \n"
        "=================================================="
    )
    prompt = "(c64dbg) "

    def __init__(self, host: str = "127.0.0.1", port: int = 6510, mock_bridge: Optional[Any] = None) -> None:
        super().__init__()
        self.core = C64DebuggerCore()

        # Se viene passato un mock_bridge (per i test), lo usiamo direttamente
        if mock_bridge is not None:
            self.bridge = mock_bridge
        else:
            self.bridge = VICERemoteMonitorBridge(host=host, port=port)

        self.profiler = C64Profiler()
        self.setup_history()

    def setup_history(self) -> None:
        try:
            import readline
            readline.set_history_length(1000)
            if os.path.exists(HISTORY_FILE):
                readline.read_history_file(HISTORY_FILE)
        except ImportError:
            pass

    def postcmd(self, stop: bool, line: str) -> bool:
        try:
            import readline
            readline.write_history_file(HISTORY_FILE)
        except Exception:
            pass
        return stop

    # --- COMANDO: break / b ---
    def do_break(self, arg: str) -> None:
        """
        Imposta un breakpoint.
        Sintassi:
          break <addr>
          break <addr> if <condizione>
          break <addr> hit <limit>
        Esempi:
          break $C000
          break $C000 if A == 0xFF
          break $C000 hit 5
        """
        if not arg:
            print("Errore: specifica un indirizzo (es: $C000 o 49152).")
            return

        parts = arg.split()
        addr_str = parts[0]

        # Converte indirizzo da hex o dec
        try:
            if addr_str.startswith("$"):
                addr = int(addr_str[1:], 16)
            elif addr_str.lower().startswith("0x"):
                addr = int(addr_str, 16)
            else:
                addr = int(addr_str)
        except ValueError:
            print(f"Errore: indirizzo non valido '{addr_str}'.")
            return

        # Controlla se c'è una clausola condizionale o hit count
        if len(parts) >= 3 and parts[1].lower() == "if":
            condition = " ".join(parts[2:])
            self.core.add_conditional_breakpoint(addr, condition)
            self.bridge.set_breakpoint(addr)
        elif len(parts) >= 3 and parts[1].lower() == "hit":
            try:
                limit = int(parts[2])
                self.core.add_hit_count_breakpoint(addr, limit)
                self.bridge.set_breakpoint(addr)
            except ValueError:
                print("Errore: limite hit count non valido.")
        else:
            self.core.add_breakpoint(addr)
            self.bridge.set_breakpoint(addr)

    def do_b(self, arg: str) -> None:
        """Alias per break."""
        self.do_break(arg)

    # --- COMANDO: step / s / z ---
    def do_step(self, arg: str) -> None:
        """Esegue un singolo step di istruzione."""
        regs = self.bridge.step_instruction()
        if not regs or "PC" not in regs:
            print("Errore durante l'esecuzione dello step. VICE è connesso?")
            return

        pc = regs["PC"]
        # Registra nel profiler se attivo
        if self.profiler.is_running:
            self.profiler.record_sample(pc)

        print(f"Step: PC=${pc:04X} A=${regs.get('A', 0):02X} X=${regs.get('X', 0):02X} Y=${regs.get('Y', 0):02X} SP=${regs.get('SP', 0):02X}")

    def do_s(self, arg: str) -> None:
        """Alias per step."""
        self.do_step(arg)

    # --- COMANDO: continue / c / g ---
    def do_continue(self, arg: str) -> None:
        """Riprende l'esecuzione ordinaria dell'emulatore."""
        print("Ripresa dell'esecuzione...")
        self.bridge.resume_execution()

    def do_c(self, arg: str) -> None:
        """Alias per continue."""
        self.do_continue(arg)

    def do_g(self, arg: str) -> None:
        """Alias per continue."""
        self.do_continue(arg)

    # --- COMANDO: info ---
    def do_info(self, arg: str) -> None:
        """
        Mostra informazioni sullo stato del sistema.
        Sintassi: info <categoria>
        Categorie:
          registers / r : Mostra i registri della CPU
          break / b     : Mostra i breakpoint attivi
          memory / m    : Mostra la mappa delle regioni di memoria
          profiler / p  : Mostra il report del profiler
        """
        category = arg.strip().lower() if arg else "registers"

        if category in ("registers", "r"):
            regs = self.bridge.get_registers()
            if not regs or "PC" not in regs:
                print("Errore di comunicazione o registri non disponibili.")
                return
            print("--- REGISTRI CPU 6502 ---")
            for k, v in regs.items():
                if k == "PC":
                    print(f"  {k}: ${v:04X}")
                elif isinstance(v, int):
                    print(f"  {k}: ${v:02X} ({v})")
                else:
                    print(f"  {k}: {v}")

        elif category in ("break", "b"):
            if not self.core.breakpoints:
                print("Nessun breakpoint attivo.")
                return
            print("--- BREAKPOINT ATTIVI ---")
            for addr in sorted(self.core.breakpoints):
                cond = self.core.breakpoint_conditions.get(addr)
                hit = self.core.hit_count_limits.get(addr)
                extra = ""
                if cond:
                    extra = f" (if {cond})"
                elif hit:
                    extra = f" (hit limit: {hit}, current: {self.core.hit_counts.get(addr, 0)})"
                print(f"  ${addr:04X}{extra}")

        elif category in ("memory", "m"):
            print("--- MAPPA DI MEMORIA C64 ---")
            for start, end, name, desc in C64MemoryMap.REGIONS:
                print(f"  ${start:04X}-${end:04X} : {name:<18} | {desc}")

        elif category in ("profiler", "p"):
            print(self.profiler.format_report())

        else:
            print(f"Categoria sconosciuta '{category}'. Scegli tra: registers, break, memory, profiler.")

    # --- COMANDO: x (examine memory) ---
    def do_x(self, arg: str) -> None:
        """
        Esamina la memoria del C64.
        Sintassi: x <start_addr> [end_addr_or_length]
        Esempi:
          x $C000
          x $C000 $C010
          x $C000 16
        """
        if not arg:
            print("Errore: specifica almeno un indirizzo di inizio.")
            return

        parts = arg.split()
        start_str = parts[0]

        try:
            if start_str.startswith("$"):
                start = int(start_str[1:], 16)
            elif start_str.lower().startswith("0x"):
                start = int(start_str, 16)
            else:
                start = int(start_str)
        except ValueError:
            print(f"Errore: indirizzo di inizio non valido '{start_str}'.")
            return

        length = 16
        if len(parts) >= 2:
            end_str = parts[1]
            try:
                if end_str.startswith("$"):
                    end = int(end_str[1:], 16)
                    length = end - start + 1
                elif end_str.lower().startswith("0x"):
                    end = int(end_str, 16)
                    length = end - start + 1
                else:
                    val = int(end_str)
                    if val > start and val < 65536:
                        length = val - start + 1
                    else:
                        length = val
            except ValueError:
                print(f"Errore: parametro lunghezza/fine non valido '{end_str}'.")
                return

        # Legge la memoria dal bridge
        end_addr = min(start + length - 1, 0xFFFF)
        try:
            data = self.bridge.read_memory(start, end_addr)
            if not data:
                print("Nessun dato restituito.")
                return
            lines = C64MemoryMap.format_memory_with_annotations(start, data)
            for line in lines:
                print(line)
        except Exception as e:
            print(f"Errore durante l'esame della memoria: {e}")

    # --- COMANDO: profile ---
    def do_profile(self, arg: str) -> None:
        """
        Gestisce il profiler delle prestazioni integrato.
        Sintassi: profile <start | stop | reset | report>
        """
        cmd = arg.strip().lower()
        if cmd == "start":
            self.profiler.start()
            print("Profiler avviato.")
        elif cmd == "stop":
            self.profiler.stop()
            print("Profiler arrestato.")
        elif cmd == "reset":
            self.profiler.reset()
            print("Dati del profiler resettati.")
        elif cmd in ("report", ""):
            print(self.profiler.format_report())
        else:
            print(f"Sotto-comando profiler sconosciuto '{cmd}'. Scegli tra: start, stop, reset, report.")

    # --- AUTO-COMPLETAMENTO ---
    def complete_info(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        options = ["registers", "break", "memory", "profiler"]
        if not text:
            return options
        return [o for o in options if o.startswith(text)]

    def complete_profile(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        options = ["start", "stop", "reset", "report"]
        if not text:
            return options
        return [o for o in options if o.startswith(text)]

    # --- ESCITA ---
    def do_quit(self, arg: str) -> bool:
        """Esci dal debugger."""
        print("Uscita dal debugger C64. Arrivederci!")
        self.bridge.disconnect()
        return True

    def do_exit(self, arg: str) -> bool:
        """Alias per quit."""
        return self.do_quit(arg)
