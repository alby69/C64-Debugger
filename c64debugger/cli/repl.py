import cmd
import os
import sys
from typing import Optional, List, Dict, Any, Union
from c64debugger.debugger_core import C64DebuggerCore
from c64debugger.vice_bridge import VICERemoteMonitorBridge
from c64debugger.disasm.memory_map import C64MemoryMap
from c64debugger.disasm.profiler import C64Profiler
from c64debugger.symbols.symbol_manager import C64SymbolManager
from c64debugger.hw_state import VICState, SIDState, CIAState
from c64debugger.heatmap import MemoryHeatmap
from c64debugger.reverse import TimelineEngine
from c64debugger.watches import WatchManager
from c64debugger.xref import XRefDatabase

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
        self.symbol_manager = C64SymbolManager()
        self.heatmap = MemoryHeatmap()
        self.timeline = TimelineEngine()
        self.watch_manager = WatchManager()
        self.core.watch_manager = self.watch_manager
        self.xref_db = XRefDatabase()
        self.core.xref_db = self.xref_db
        self.setup_history()
        from c64debugger.plugin.plugin_manager import C64PluginManager
        self.plugin_manager = C64PluginManager(core=self.core, bridge=self.bridge, repl=self)

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

    def parse_address(self, addr_str: str) -> Optional[int]:
        """
        Risolve un indirizzo a partire da una stringa, che può essere un simbolo (label)
        o un valore esadecimale ($C000, 0xC000) o decimale (49152).
        """
        # Prova a risolverlo tramite il Symbol Manager
        addr = self.symbol_manager.get_address(addr_str)
        if addr is not None:
            return addr

        # Prova a fare il parsing numerico standard (hex/dec)
        try:
            if addr_str.startswith("$"):
                return int(addr_str[1:], 16)
            elif addr_str.lower().startswith("0x"):
                return int(addr_str, 16)
            else:
                return int(addr_str)
        except ValueError:
            return None

    # --- COMANDO: break / b ---
    def do_break(self, arg: str) -> None:
        """
        Imposta un breakpoint.
        Sintassi:
          break <addr|simbolo>
          break <addr|simbolo> if <condizione>
          break <addr|simbolo> hit <limit>
        Esempi:
          break $C000
          break start_label
          break $C000 if A == 0xFF
          break start_label hit 5
        """
        if not arg:
            print("Errore: specifica un indirizzo o un simbolo (es: $C000, start_label, 49152).")
            return

        parts = arg.split()
        addr_str = parts[0]

        addr = self.parse_address(addr_str)
        if addr is None:
            print(f"Errore: indirizzo o simbolo non valido '{addr_str}'.")
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

    # --- COMANDO: watch ---
    def do_watch(self, arg: str) -> None:
        """
        Imposta un watchpoint su un indirizzo di memoria (o simbolo).
        Sintassi: watch <addr|simbolo>
        """
        if not arg:
            print("Errore: specifica un indirizzo o un simbolo.")
            return
        addr = self.parse_address(arg)
        if addr is None:
            print(f"Errore: indirizzo o simbolo non valido '{arg}'.")
            return
        self.core.add_watchpoint(addr)

    def do_watch_range(self, arg: str) -> None:
        """
        Imposta un watchpoint range su un intervallo di indirizzi.
        Sintassi: watch_range <start_addr|simbolo> <end_addr|simbolo>
        """
        parts = arg.split()
        if len(parts) < 2:
            print("Errore: specifica inizio e fine del range.")
            return
        start = self.parse_address(parts[0])
        end = self.parse_address(parts[1])
        if start is None or end is None:
            print("Errore: indirizzo/simbolo iniziale o finale non valido.")
            return
        self.core.add_watchpoint_range(start, end)

    def do_add_watch(self, arg: str) -> None:
        """
        Aggiunge una watch di memoria formattata.
        Sintassi: add_watch <indirizzo|simbolo> [formato]
        Formati validi: hex8, hex16, hex32, s8, u8, s16, u16, s32, u32, text
        Default: hex8
        """
        parts = arg.split()
        if not parts:
            print("Errore: specifica un indirizzo o simbolo.")
            return
        name_or_addr = parts[0]
        fmt = parts[1] if len(parts) >= 2 else "hex8"
        self.watch_manager.add_watch(name_or_addr, fmt)
        print(f"Watch aggiunta per '{name_or_addr}' con formato '{fmt}'.")

    def do_remove_watch(self, arg: str) -> None:
        """
        Rimuove una watch di memoria.
        Sintassi: remove_watch <indirizzo|simbolo>
        """
        if not arg:
            print("Errore: specifica l'indirizzo o simbolo della watch da rimuovere.")
            return
        removed = self.watch_manager.remove_watch(arg)
        if removed:
            print(f"Watch per '{arg}' rimossa.")
        else:
            print(f"Watch per '{arg}' non trovata.")

    def do_watches(self, arg: str) -> None:
        """
        Mostra tutte le watch configurate e i loro valori correnti valutati.
        Sintassi: watches
        """
        results = self.watch_manager.evaluate_watches(self.bridge, self.symbol_manager.get_address)
        if not results:
            print("Nessuna watch configurata.")
            return
        print("--- WATCH IN MEMORIA ---")
        for r in results:
            addr_str = f" (${r['address']:04X})" if r['address'] is not None else ""
            print(f"  {r['name']}{addr_str:<8} [{r['format']}]: {r['value']}")

    def complete_add_watch(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        parts = line.split()
        if len(parts) >= 2 and not line.endswith(" "):
            if len(parts) == 3 or (len(parts) == 2 and text in WatchManager.VALID_FORMATS):
                return [f for f in WatchManager.VALID_FORMATS if f.startswith(text)]
        return [name for name in self.symbol_manager.all_symbols().keys() if name.startswith(text)]

    def complete_remove_watch(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        return [name for name in self.watch_manager.list_watches().keys() if name.startswith(text)]

    # --- COMANDO: step / s / z ---
    def do_step(self, arg: str) -> None:
        """Esegue un singolo step di istruzione."""
        try:
            regs_before = self.bridge.get_registers()
        except Exception:
            regs_before = {}
        self.plugin_manager.trigger_hook("pre_step", regs_before)

        regs = self.bridge.step_instruction()
        if not regs or "PC" not in regs:
            print("Errore durante l'esecuzione dello step. VICE è connesso?")
            return

        self.plugin_manager.trigger_hook("post_step", regs)

        pc = regs["PC"]
        # Registra nel profiler se attivo
        if self.profiler.is_running:
            self.profiler.record_sample(pc)

        # XRef tracking
        try:
            import re
            disasm_line = self.bridge.send_command(f"d {pc:04x} {pc:04x}")
            from c64debugger.disasm.disassembler import VICEDisassemblerParser
            instructions = VICEDisassemblerParser.parse_disassembly(disasm_line)
            if instructions:
                instr = instructions[0]
                for offset in range(len(instr.bytes_data)):
                    self.xref_db.record_access(pc + offset, pc, "X")

                clean_op = instr.operand.strip()
                if clean_op and not clean_op.startswith("#"):
                    clean_op = re.sub(r'[(),]', ' ', clean_op).split()[0].strip()
                    accessed_addr = self.parse_address(clean_op)
                    if accessed_addr is not None:
                        mnemonic = instr.mnemonic.upper()
                        if mnemonic in ("STA", "STX", "STY"):
                            self.xref_db.record_access(accessed_addr, pc, "W")
                        elif mnemonic in ("ASL", "LSR", "ROL", "ROR", "INC", "DEC"):
                            self.xref_db.record_access(accessed_addr, pc, "R")
                            self.xref_db.record_access(accessed_addr, pc, "W")
                        elif mnemonic not in ("JMP", "JSR"):
                            self.xref_db.record_access(accessed_addr, pc, "R")
        except Exception as e:
            pass

        # Heatmap tracking
        if self.heatmap.enabled:
            self.heatmap.record_access(pc, 'X', pm=self.plugin_manager)
            disasm_line = self.bridge.send_command(f"d {pc:04x} {pc:04x}")
            from c64debugger.disasm.disassembler import VICEDisassemblerParser
            instructions = VICEDisassemblerParser.parse_disassembly(disasm_line)
            if instructions:
                instr = instructions[0]
                import re
                hex_match = re.search(r'\$([0-9a-fA-F]+)', instr.operand)
                if hex_match:
                    try:
                        accessed_addr = int(hex_match.group(1), 16)
                        mnemonic = instr.mnemonic.upper()
                        if mnemonic in ("STA", "STX", "STY"):
                            self.heatmap.record_access(accessed_addr, 'W', pm=self.plugin_manager)
                        elif mnemonic in ("ASL", "LSR", "ROL", "ROR", "INC", "DEC"):
                            self.heatmap.record_access(accessed_addr, 'R', pm=self.plugin_manager)
                            self.heatmap.record_access(accessed_addr, 'W', pm=self.plugin_manager)
                        elif mnemonic not in ("JMP", "JSR"):
                            self.heatmap.record_access(accessed_addr, 'R', pm=self.plugin_manager)
                    except ValueError:
                        pass

        # Timeline recording
        if self.timeline.enabled:
            try:
                ram = self.bridge.read_memory(0, 0xFFFF)
                if len(ram) == 65536:
                    self.timeline.record_state(ram, regs)
            except Exception:
                pass

        # Mostra i simboli corrispondenti se disponibili
        syms = self.symbol_manager.get_symbols(pc)
        sym_suffix = f" ({', '.join(syms)})" if syms else ""

        print(f"Step: PC=${pc:04X}{sym_suffix} A=${regs.get('A', 0):02X} X=${regs.get('X', 0):02X} Y=${regs.get('Y', 0):02X} SP=${regs.get('SP', 0):02X}")

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
          symbols / sym : Mostra la tabella dei simboli caricati
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
                    syms = self.symbol_manager.get_symbols(v)
                    sym_suffix = f" ({', '.join(syms)})" if syms else ""
                    print(f"  {k}: ${v:04X}{sym_suffix}")
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
                syms = self.symbol_manager.get_symbols(addr)
                sym_suffix = f" [{', '.join(syms)}]" if syms else ""
                extra = ""
                if cond:
                    extra = f" (if {cond})"
                elif hit:
                    extra = f" (hit limit: {hit}, current: {self.core.hit_counts.get(addr, 0)})"
                print(f"  ${addr:04X}{sym_suffix}{extra}")

        elif category in ("memory", "m"):
            print("--- MAPPA DI MEMORIA C64 ---")
            for start, end, name, desc in C64MemoryMap.REGIONS:
                print(f"  ${start:04X}-${end:04X} : {name:<18} | {desc}")

        elif category in ("profiler", "p"):
            print(self.profiler.format_report())

        elif category in ("symbols", "sym"):
            symbols = self.symbol_manager.all_symbols()
            if not symbols:
                print("Nessun simbolo caricato.")
                return
            print("--- TABELLA DEI SIMBOLI ---")
            for name, addr in sorted(symbols.items(), key=lambda x: x[1]):
                print(f"  {name:<25} -> ${addr:04X} ({addr})")

        elif category in ("watches", "w"):
            self.do_watches("")

        elif category in ("xref", "x"):
            parts = arg.split()
            if len(parts) >= 2:
                self.do_xref(parts[1])
            else:
                print("Errore: specifica un indirizzo per l'info xref. Es: info xref $C000")

        else:
            print(f"Categoria sconosciuta '{category}'. Scegli tra: registers, break, memory, profiler, symbols, watches, xref.")

    # --- COMANDO: x (examine memory) ---
    def do_x(self, arg: str) -> None:
        """
        Esamina la memoria del C64.
        Sintassi: x <start_addr|simbolo> [end_addr_or_length|simbolo]
        Esempi:
          x $C000
          x start_label
          x $C000 $C010
          x start_label 16
        """
        if not arg:
            print("Errore: specifica almeno un indirizzo di inizio.")
            return

        parts = arg.split()
        start_str = parts[0]

        start = self.parse_address(start_str)
        if start is None:
            print(f"Errore: indirizzo di inizio o simbolo non valido '{start_str}'.")
            return

        length = 16
        if len(parts) >= 2:
            end_str = parts[1]
            end_val = self.parse_address(end_str)
            if end_val is not None:
                if end_val >= start:
                    length = end_val - start + 1
                else:
                    length = end_val
            else:
                try:
                    length = int(end_str)
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

    # --- COMANDO: load_symbols ---
    def do_load_symbols(self, arg: str) -> None:
        """
        Carica simboli (label) da un file.
        Sintassi: load_symbols <filepath>
        """
        if not arg:
            print("Errore: specifica il percorso del file dei simboli.")
            return
        try:
            count = self.symbol_manager.load_from_file(arg)
            print(f"Caricati con successo {count} simboli da '{arg}'.")
        except Exception as e:
            print(f"Errore durante il caricamento dei simboli: {e}")

    # --- COMANDI DI SESSIONE & SNAPSHOT ---
    def do_save_session(self, arg: str) -> None:
        """
        Salva la sessione di debug corrente (breakpoint, watchpoint, simboli) in un file JSON .c64dbg.
        Sintassi: save_session <filepath>
        """
        if not arg:
            print("Errore: specifica il percorso del file di sessione (es: session.c64dbg).")
            return
        try:
            from c64debugger.session import C64SessionManager
            C64SessionManager.save_session(arg, self.core, self.symbol_manager.loaded_filepath)
            print(f"Sessione di debug salvata in '{arg}'")
        except Exception as e:
            print(f"Errore durante il salvataggio della sessione: {e}")

    def do_load_session(self, arg: str) -> None:
        """
        Carica una sessione di debug salvata, ripristinando breakpoint, watchpoint e simboli.
        Sintassi: load_session <filepath>
        """
        if not arg:
            print("Errore: specifica il percorso del file di sessione (.c64dbg).")
            return
        try:
            from c64debugger.session import C64SessionManager
            data = C64SessionManager.load_session(arg, self.core)
            print(f"Sessione di debug caricata con successo da '{arg}'")

            sym_path = data.get("loaded_symbols_path")
            if sym_path:
                try:
                    count = self.symbol_manager.load_from_file(sym_path)
                    print(f"Ripristinati {count} simboli da '{sym_path}'")
                except Exception:
                    print(f"Avviso: impossibile caricare il file simboli memorizzato '{sym_path}'")

            # Applica i breakpoint a livello di bridge
            for addr in self.core.breakpoints:
                self.bridge.set_breakpoint(addr)
        except Exception as e:
            print(f"Errore durante il caricamento della sessione: {e}")

    def do_save_snapshot(self, arg: str) -> None:
        """
        Salva lo snapshot binario completo della RAM del Commodore 64.
        Sintassi: save_snapshot <filepath>
        """
        if not arg:
            print("Errore: specifica il percorso del file snapshot (es: ram.bin).")
            return
        try:
            from c64debugger.session import C64SnapshotManager
            C64SnapshotManager.save_ram_snapshot(arg, self.bridge)
            print(f"Snapshot RAM salvato in '{arg}'")
        except Exception as e:
            print(f"Errore durante il salvataggio dello snapshot: {e}")

    def do_load_snapshot(self, arg: str) -> None:
        """
        Carica uno snapshot binario completo ripristinando la RAM del Commodore 64.
        Sintassi: load_snapshot <filepath>
        """
        if not arg:
            print("Errore: specifica il percorso del file snapshot (.bin).")
            return
        try:
            from c64debugger.session import C64SnapshotManager
            C64SnapshotManager.load_ram_snapshot(arg, self.bridge)
            print(f"Snapshot RAM ripristinato da '{arg}'")
        except Exception as e:
            print(f"Errore durante il caricamento dello snapshot: {e}")

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

    # --- COMANDO: tui ---
    def do_tui(self, arg: str) -> None:
        """
        Avvia l'interfaccia utente a pieno schermo (TUI Dashboard) interattiva.
        Sintassi: tui
        """
        from c64debugger.tui.tui_manager import C64DebuggerTUI
        tui = C64DebuggerTUI(self.bridge, self.core, heatmap=self.heatmap, timeline=self.timeline)
        tui.run()

    # --- AUTO-COMPLETAMENTO ---
    def do_xref(self, arg: str) -> None:
        """
        Interroga le cross-reference di un indirizzo di memoria.
        Mostra chi ha letto, scritto o eseguito quella cella.
        Sintassi: xref <indirizzo|simbolo>
        """
        if not arg:
            print("Errore: specifica un indirizzo o simbolo.")
            return
        addr = self.parse_address(arg)
        if addr is None:
            print(f"Errore: indirizzo o simbolo non valido '{arg}'.")
            return

        refs = self.xref_db.get_references(addr)
        if not refs:
            print(f"Nessuna cross-reference registrata per ${addr:04X}.")
            return

        print(f"--- CROSS-REFERENCES PER ${addr:04X} ---")
        for r in sorted(refs, key=lambda x: x["timestamp"]):
            context_str = ""
            try:
                disasm_line = self.bridge.send_command(f"d {r['pc']:04x} {r['pc']:04x}")
                from c64debugger.disasm.disassembler import VICEDisassemblerParser
                instrs = VICEDisassemblerParser.parse_disassembly(disasm_line)
                if instrs:
                    context_str = f" ({instrs[0].mnemonic} {instrs[0].operand})"
            except Exception:
                pass

            type_label = "Read" if r["type"] == "R" else "Write" if r["type"] == "W" else "Execute"
            print(f"  - {type_label:<8} da ${r['pc']:04X}{context_str}")

    def complete_xref(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        return [name for name in self.symbol_manager.all_symbols().keys() if name.startswith(text)]

    def complete_info(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        options = ["registers", "break", "memory", "profiler", "symbols", "watches", "xref"]
        if not text:
            return options
        return [o for o in options if o.startswith(text)]

    def complete_profile(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        options = ["start", "stop", "reset", "report"]
        if not text:
            return options
        return [o for o in options if o.startswith(text)]

    def complete_break(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        return [name for name in self.symbol_manager.all_symbols().keys() if name.startswith(text)]

    def complete_b(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        return self.complete_break(text, line, begidx, endidx)

    def complete_x(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        return [name for name in self.symbol_manager.all_symbols().keys() if name.startswith(text)]

    def complete_watch(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        return [name for name in self.symbol_manager.all_symbols().keys() if name.startswith(text)]

    # --- COMANDI PLUGINS ---
    def do_load_plugin(self, arg: str) -> None:
        """
        Carica un plugin dinamico da un file Python.
        Sintassi: load_plugin <filepath>
        """
        if not arg:
            print("Errore: specifica il percorso del file del plugin.")
            return
        plugin = self.plugin_manager.load_plugin(arg)
        if plugin:
            print(f"Plugin '{plugin.name}' caricato con successo (v{getattr(plugin, 'version', '1.0.0')}).")
        else:
            print(f"Errore durante il caricamento del plugin da '{arg}'.")

    def do_unload_plugin(self, arg: str) -> None:
        """
        Scollega e rimuove un plugin precedentemente caricato.
        Sintassi: unload_plugin <nome_plugin>
        """
        if not arg:
            print("Errore: specifica il nome del plugin da rimuovere.")
            return
        success = self.plugin_manager.unload_plugin(arg)
        if success:
            print(f"Plugin '{arg}' rimosso con successo.")
        else:
            print(f"Errore: plugin '{arg}' non trovato o non rimosso.")

    def do_list_plugins(self, arg: str) -> None:
        """
        Elenca tutti i plugin caricati in memoria.
        Sintassi: list_plugins
        """
        plugins = self.plugin_manager.list_plugins()
        if not plugins:
            print("Nessun plugin attualmente caricato.")
            return
        print("--- PLUGIN CARICATI ---")
        for name, p in plugins.items():
            desc = getattr(p, "description", "Nessuna descrizione")
            ver = getattr(p, "version", "1.0.0")
            print(f"  {name} v{ver} - {desc}")

    # --- USCITA ---
    def do_quit(self, arg: str) -> bool:
        """Esci dal debugger."""
        print("Uscita dal debugger C64. Arrivederci!")
        self.bridge.disconnect()
        return True

    def do_exit(self, arg: str) -> bool:
        """Alias per quit."""
        return self.do_quit(arg)

    def do_vic_state(self, arg: str) -> None:
        """Mostra lo stato del chip video VIC-II."""
        try:
            data = self.bridge.read_memory(0xD000, 0xD02E)
            vic = VICState(data)
            info = vic.to_dict()
            print("--- STATO CHIP VIC-II ---")
            print(f"  Riga Raster: {info['raster_line']} (Bad Line: {'SI' if info['bad_line'] else 'NO'})")
            print(f"  Schermo Abilitato: {'SI' if info['screen_on'] else 'NO'}")
            print(f"  Bitmap Mode: {'SI' if info['bitmap_mode'] else 'NO'} | Multicolor: {'SI' if info['multicolor_mode'] else 'NO'}")
            print(f"  ECM: {'SI' if info['ecm'] else 'NO'} | Righe: {info['row_select']} | Colonne: {info['column_select']}")
            print(f"  Video Matrix Offset: ${info['screen_matrix_base_offset']:04X}")
            print(f"  Colore Bordo: {info['border_color']} | Background: {info['background_color']}")
            print("  Sprite Abilitati:", ", ".join(f"S{i}" for i, en in enumerate(info['sprite_enable']) if en) or "Nessuno")
        except Exception as e:
            print(f"Errore lettura stato VIC-II: {e}")

    def do_sid_state(self, arg: str) -> None:
        """Mostra lo stato del chip audio SID."""
        try:
            data = self.bridge.read_memory(0xD400, 0xD41C)
            sid = SIDState(data)
            info = sid.to_dict()
            print("--- STATO CHIP SID ---")
            print(f"  Volume Generale: {info['volume']} | Cutoff: {info['cutoff_freq']} | Resonance: {info['resonance']}")
            for v in info["voices"]:
                print(f"  Voce {v['voice_index']}: Freq: {v['frequency_hz']} Hz | Nota: {v['note']} | Forma d'onda: {v['waveform']} | Gate: {'ON' if v['gate'] else 'OFF'}")
        except Exception as e:
            print(f"Errore lettura stato SID: {e}")

    def do_cia_state(self, arg: str) -> None:
        """Mostra lo stato dei chip CIA1 e CIA2."""
        try:
            data1 = self.bridge.read_memory(0xDC00, 0xDC0F)
            cia1 = CIAState(data1, "CIA1")
            info1 = cia1.to_dict()
            print("--- STATO CHIP CIA1 (DC00-DC0F) ---")
            print(f"  Timer A: {info1['timer_a']} ({'ATTIVO' if info1['timer_a_active'] else 'FERMO'})")
            print(f"  Timer B: {info1['timer_b']} ({'ATTIVO' if info1['timer_b_active'] else 'FERMO'})")
            print(f"  TOD Clock: {info1['tod']} (PM: {info1['tod_pm']})")
            print(f"  Port A: ${info1['port_a']:02X} | Port B: ${info1['port_b']:02X}")

            data2 = self.bridge.read_memory(0xDD00, 0xDD0F)
            cia2 = CIAState(data2, "CIA2")
            info2 = cia2.to_dict()
            print("\n--- STATO CHIP CIA2 (DD00-DD0F) ---")
            print(f"  Timer A: {info2['timer_a']} ({'ATTIVO' if info2['timer_a_active'] else 'FERMO'})")
            print(f"  Timer B: {info2['timer_b']} ({'ATTIVO' if info2['timer_b_active'] else 'FERMO'})")
            print(f"  TOD Clock: {info2['tod']} (PM: {info2['tod_pm']})")
            print(f"  Port A: ${info2['port_a']:02X} | Port B: ${info2['port_b']:02X}")
        except Exception as e:
            print(f"Errore lettura stato CIA: {e}")

    def do_heatmap(self, arg: str) -> None:
        """
        Controlla o visualizza il tracciamento della memory heatmap.
        Sintassi:
          heatmap [on|off|reset]
          heatmap show [indirizzo_inizio] [lunghezza]
        """
        cmd = arg.strip().lower()
        if not cmd:
            print(f"Heatmap abilitata: {'SI' if self.heatmap.enabled else 'NO'}")
            return

        parts = cmd.split()
        subcmd = parts[0]

        if subcmd == "on":
            self.heatmap.enabled = True
            print("Memory heatmap abilitata.")
        elif subcmd == "off":
            self.heatmap.enabled = False
            print("Memory heatmap disabilitata.")
        elif subcmd == "reset":
            self.heatmap.reset()
            print("Dati heatmap resettati.")
        elif subcmd == "show":
            start_addr = 0xC000
            length = 256
            if len(parts) >= 2:
                res = self.parse_address(parts[1])
                if res is not None:
                    start_addr = res
            if len(parts) >= 3:
                try:
                    length = int(parts[2])
                except ValueError:
                    pass
            end_addr = min(start_addr + length - 1, 0xFFFF)
            try:
                data = self.bridge.read_memory(start_addr, end_addr)
                try:
                    regs = self.bridge.get_registers()
                    pc = regs.get("PC")
                except Exception:
                    pc = None
                lines = self.heatmap.render_grid(start_addr, data, pc)
                print(f"--- HEATMAP MEMORIA (${start_addr:04X}-${end_addr:04X}) ---")
                for line in lines:
                    print(line)
            except Exception as e:
                print(f"Errore lettura memoria per heatmap: {e}")
        else:
            print(f"Comando heatmap '{subcmd}' sconosciuto. Usa: on, off, reset, show [indirizzo_inizio] [lunghezza]")

    def do_rewind(self, arg: str) -> None:
        """
        Torna indietro nel tempo della timeline.
        Sintassi: rewind [passi]
        """
        if not self.timeline.enabled:
            print("Timeline disabilitata. Abilitala con 'timeline_status enable'.")
            return
        steps = 1
        if arg:
            try:
                steps = int(arg)
            except ValueError:
                print("Errore: specifica un numero valido di passi.")
                return

        state = self.timeline.rewind(steps)
        if not state:
            print("Nessun punto temporale a cui ritornare.")
            return

        # Ripristina lo stato nell'emulatore
        try:
            self.bridge.write_memory(0, state["ram"])
            self.bridge.write_registers(state["registers"])
            print(f"Timeline: riavvolto a index {self.timeline.current_index}/{len(self.timeline.snapshots)-1}")
            regs = state["registers"]
            print(f"PC corrente: ${regs.get('PC'):04X} A=${regs.get('A'):02X}")
        except Exception as e:
            print(f"Errore durante il ripristino dello stato: {e}")

    def do_forward(self, arg: str) -> None:
        """
        Avanza nel tempo della timeline (se precedentemente riavvolto).
        Sintassi: forward [passi]
        """
        if not self.timeline.enabled:
            print("Timeline disabilitata.")
            return
        steps = 1
        if arg:
            try:
                steps = int(arg)
            except ValueError:
                print("Errore: specifica un numero valido di passi.")
                return

        state = self.timeline.forward(steps)
        if not state:
            print("Nessun punto temporale futuro.")
            return

        # Ripristina lo stato nell'emulatore
        try:
            self.bridge.write_memory(0, state["ram"])
            self.bridge.write_registers(state["registers"])
            print(f"Timeline: avanzato a index {self.timeline.current_index}/{len(self.timeline.snapshots)-1}")
            regs = state["registers"]
            print(f"PC corrente: ${regs.get('PC'):04X} A=${regs.get('A'):02X}")
        except Exception as e:
            print(f"Errore durante il ripristino dello stato: {e}")

    def do_backstep(self, arg: str) -> None:
        """Alias per tornare indietro di esattamente 1 passo di istruzione."""
        self.do_rewind("1")

    def do_timeline_status(self, arg: str) -> None:
        """
        Mostra lo stato o controlla la timeline.
        Sintassi:
          timeline_status
          timeline_status [enable|disable|reset]
        """
        cmd = arg.strip().lower()
        if cmd == "enable":
            self.timeline.enabled = True
            print("Timeline abilitata.")
            try:
                ram = self.bridge.read_memory(0, 0xFFFF)
                regs = self.bridge.get_registers()
                if len(ram) == 65536 and regs:
                    self.timeline.record_state(ram, regs)
            except Exception:
                pass
        elif cmd == "disable":
            self.timeline.enabled = False
            print("Timeline disabilitata.")
        elif cmd == "reset":
            self.timeline.reset()
            print("Timeline resettata.")
        elif not cmd:
            info = self.timeline.status()
            print("--- STATO TIMELINE ---")
            print(f"  Abilitata: {'SI' if info['enabled'] else 'NO'}")
            print(f"  Snapshot totali: {info['total_snapshots']} / {info['max_snapshots']}")
            print(f"  Indice corrente: {info['current_index']}")
        else:
            print("Comando non riconosciuto. Usa: timeline_status [enable|disable|reset]")
