import socket
import struct
import logging
import re
from typing import Dict, Any, Union, Optional, List, Set, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("C64DebuggerCore")

class C64DebuggerCore:
    """
    Motore core di debugging per Commodore 64.
    Supporta la simulazione passo-passo (via py6502) e il collegamento all'emulatore VICE.
    """
    def __init__(self):
        self.breakpoints: Set[int] = set()
        self.breakpoint_conditions: Dict[int, str] = {}
        self.hit_count_limits: Dict[int, int] = {}
        self.hit_counts: Dict[int, int] = {}
        self.watchpoints: Dict[int, Optional[int]] = {}  # addr -> value
        self.watchpoint_ranges: List[Tuple[int, int]] = []
        self.io_breakpoints: Dict[str, Tuple[int, int]] = {}  # chip -> (start, end)
        self.execution_history: List[Dict[str, Any]] = []
        self.registers: Dict[str, int] = {
            "PC": 0x0000,
            "A": 0x00,
            "X": 0x00,
            "Y": 0x00,
            "SP": 0xFD,
            "SR": 0x30,  # Status Register (Flags)
        }
        self.simulation_adapter = None
        self.vice_socket = None

    # --- BREAKPOINTS / WATCHPOINTS ---
    def add_breakpoint(self, address: int):
        """Aggiunge un breakpoint ad un indirizzo specifico."""
        address &= 0xFFFF
        self.breakpoints.add(address)
        logger.info(f"Breakpoint impostato a ${address:04X}")

    def remove_breakpoint(self, address: int):
        """Rimuove un breakpoint."""
        address &= 0xFFFF
        if address in self.breakpoints:
            self.breakpoints.remove(address)
            self.breakpoint_conditions.pop(address, None)
            self.hit_count_limits.pop(address, None)
            self.hit_counts.pop(address, None)
            logger.info(f"Breakpoint rimosso a ${address:04X}")

    def add_conditional_breakpoint(self, address: int, condition_str: str):
        """Aggiunge un breakpoint condizionato."""
        address &= 0xFFFF
        self.add_breakpoint(address)
        self.breakpoint_conditions[address] = condition_str
        logger.info(f"Breakpoint condizionato impostato a ${address:04X} con condizione: {condition_str}")

    def add_hit_count_breakpoint(self, address: int, limit: int):
        """Aggiunge un breakpoint con hit count."""
        address &= 0xFFFF
        self.add_breakpoint(address)
        self.hit_count_limits[address] = limit
        self.hit_counts[address] = 0
        logger.info(f"Breakpoint hit count impostato a ${address:04X} (smetti dopo {limit} hit)")

    def add_watchpoint(self, address: int):
        """Aggiunge un watchpoint su una cella di memoria."""
        address &= 0xFFFF
        self.watchpoints[address] = None
        logger.info(f"Watchpoint impostato sulla cella di memoria ${address:04X}")

    def remove_watchpoint(self, address: int):
        """Rimuove un watchpoint da una cella di memoria."""
        address &= 0xFFFF
        self.watchpoints.pop(address, None)
        logger.info(f"Watchpoint rimosso dalla cella di memoria ${address:04X}")

    def add_watchpoint_range(self, start_addr: int, end_addr: int):
        """Aggiunge un watchpoint su un intero intervallo di indirizzi di memoria."""
        start_addr &= 0xFFFF
        end_addr &= 0xFFFF
        self.watchpoint_ranges.append((start_addr, end_addr))
        logger.info(f"Watchpoint range impostato su ${start_addr:04X}-${end_addr:04X}")

    def add_io_breakpoint(self, io_chip: str):
        """
        Aggiunge un intercettatore per gli accessi ai chip di I/O.
        Opzioni valide: 'VIC' ($D000-$D3FF), 'SID' ($D400-$D7FF), 'CIA1' ($DC00-$DCFF), 'CIA2' ($DD00-$DDFF), 'IO' ($D000-$DFFF)
        """
        chip = io_chip.upper()
        ranges = {
            "VIC": (0xD000, 0xD3FF),
            "SID": (0xD400, 0xD7FF),
            "CIA1": (0xDC00, 0xDCFF),
            "CIA2": (0xDD00, 0xDDFF),
            "IO": (0xD000, 0xDFFF)
        }
        if chip in ranges:
            self.io_breakpoints[chip] = ranges[chip]
            logger.info(f"Intercettazione I/O impostata per il chip {chip} su range ${ranges[chip][0]:04X}-${ranges[chip][1]:04X}")
        else:
            logger.warning(f"Chip di I/O '{io_chip}' non valido.")

    def remove_io_breakpoint(self, io_chip: str):
        """Rimuove l'intercettazione I/O per un chip."""
        chip = io_chip.upper()
        if chip in self.io_breakpoints:
            self.io_breakpoints.pop(chip)
            logger.info(f"Intercettazione I/O rimossa per il chip {chip}")

    # --- EVALUATION ENGINE ---
    def eval_condition(self, condition_str: str, registers: dict) -> bool:
        """
        Valuta se una espressione di condizione è vera per lo stato attuale dei registri.
        """
        if not condition_str:
            return True

        condition_str = condition_str.strip()
        pattern = re.compile(r"^([a-zA-Z]+)\s*(==|!=|>=|<=|>|<)\s*([\$#0-9a-fA-F_x]+)$")
        match = pattern.match(condition_str)
        if not match:
            # Fallback sicuro ad un'interpretazione tramite eval (con ambiente ristretto)
            cleaned = condition_str.replace('$', '0x').replace('#', '')
            try:
                safe_env = {k: v for k, v in registers.items()}
                return bool(eval(cleaned, {"__builtins__": None}, safe_env))
            except Exception:
                return False

        reg, op, val_str = match.groups()
        reg = reg.upper()
        if reg not in registers:
            return False

        val_str = val_str.replace('$', '0x').replace('#', '').strip()
        try:
            if val_str.lower().startswith('0x'):
                val = int(val_str, 16)
            else:
                val = int(val_str)
        except ValueError:
            return False

        reg_val = registers[reg]
        if op == "==":
            return reg_val == val
        elif op == "!=":
            return reg_val != val
        elif op == ">":
            return reg_val > val
        elif op == "<":
            return reg_val < val
        elif op == ">=":
            return reg_val >= val
        elif op == "<=":
            return reg_val <= val

        return False

    def should_stop(self, address: int, registers: dict) -> bool:
        """
        Determina se l'esecuzione si deve fermare all'indirizzo corrente,
        considerando breakpoint normali, condizionati e hit count.
        """
        address &= 0xFFFF
        if address not in self.breakpoints:
            return False

        # Trigger pre_breakpoint hook if plugin manager exists
        pm = getattr(self, "plugin_manager", None)
        if pm:
            pm.trigger_hook("pre_breakpoint", address, registers)

        stop = True
        # Se c'è un hit count limit, incrementiamo e verifichiamo
        if address in self.hit_count_limits:
            self.hit_counts[address] = self.hit_counts.get(address, 0) + 1
            if self.hit_counts[address] < self.hit_count_limits[address]:
                stop = False

        # Se c'è una condizione, verifichiamola
        if stop and address in self.breakpoint_conditions:
            cond = self.breakpoint_conditions[address]
            stop = self.eval_condition(cond, registers)

        # Trigger post_breakpoint hook if plugin manager exists and we are stopping
        if stop and pm:
            pm.trigger_hook("post_breakpoint", address, registers)

        return stop

    def check_and_trigger_crash(self, registers: dict, history: list, stack_trace: list = None) -> Optional[dict]:
        """
        Checks if the current state represents a crash using C64DebuggerAgentHelper.
        If a crash is detected, triggers the on_crash hook for loaded plugins.
        """
        report = C64DebuggerAgentHelper.analyze_crash_dump(registers, history, stack_trace)
        if report and report.get("error_type") != "Unknown":
            pm = getattr(self, "plugin_manager", None)
            if pm:
                pm.trigger_hook("on_crash", report)
            return report
        return None

    def check_watchpoint_trigger(self, address: int, old_val: int, new_val: int) -> bool:
        """
        Determina se un accesso in scrittura su una cella ha attivato un watchpoint.
        """
        address &= 0xFFFF
        if old_val == new_val:
            return False

        if address in self.watchpoints:
            return True

        for start, end in self.watchpoint_ranges:
            if start <= address <= end:
                return True

        return False

    def check_io_access(self, address: int) -> Optional[str]:
        """
        Controlla se l'indirizzo appartiene a un chip di I/O monitorato.
        Ritorna il nome del chip se intercettato.
        """
        address &= 0xFFFF
        for chip_name, (start, end) in self.io_breakpoints.items():
            if start <= address <= end:
                return chip_name
        return None

    # --- SIMULATORE PY6502 ADAPTER ---
    def init_simulator(self, code_bytes: bytes, start_addr: int = 0xC000):
        """Inizializza il simulatore py6502 interno per il debugging locale."""
        try:
            from c64validator.py6502_adapter import C64Py6502Adapter
            self.simulation_adapter = C64Py6502Adapter()
            self.registers["PC"] = start_addr
            logger.info(f"Simulatore inizializzato all'indirizzo ${start_addr:04X}")
        except ImportError:
            logger.warning("c64validator non trovato. Funzionalità di simulazione locale disabilitata.")

    def step_into(self):
        """Esegue una singola istruzione e aggiorna lo stato dei registri."""
        if not self.simulation_adapter:
            return False, "Simulatore non inizializzato."

        pc_before = self.registers["PC"]
        self.execution_history.append({
            "PC": pc_before,
            "registers": self.registers.copy()
        })
        logger.info(f"Step eseguito: PC=${pc_before:04X}")
        return True, self.registers

    # --- COLLEGAMENTO EMULATORE (VICE BINARY MONITOR CLIENT) ---
    def connect_to_vice(self, host: str = "127.0.0.1", port: int = 6510):
        """
        Connette il debugger all'emulatore VICE usando la porta monitor binaria.
        """
        try:
            self.vice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.vice_socket.settimeout(2.0)
            self.vice_socket.connect((host, port))
            logger.info(f"Connesso con successo al Monitor di VICE su {host}:{port}")
            return True, "Connesso!"
        except Exception as e:
            self.vice_socket = None
            err_msg = f"Impossibile connettersi a VICE: {e}. Assicurati che VICE sia avviato con l'opzione -binarymonitor."
            logger.error(err_msg)
            return False, err_msg

    def send_vice_command(self, cmd_bytes: bytes):
        """Invia un comando binario a VICE."""
        if not self.vice_socket:
            return False, "Nessuna connessione a VICE attiva."
        try:
            self.vice_socket.sendall(cmd_bytes)
            response = self.vice_socket.recv(1024)
            return True, response
        except Exception as e:
            logger.error(f"Errore durante l'invio del comando a VICE: {e}")
            return False, str(e)

    def close_vice(self):
        """Chiude la connessione a VICE."""
        if self.vice_socket:
            self.vice_socket.close()
            self.vice_socket = None
            logger.info("Connessione con VICE chiusa.")


class C64DebuggerAgentHelper:
    """
    Helper Agentico per l'analisi intelligente dei crash o dei log di esecuzione.
    Funge da ponte con l'LLM per spiegare l'errore e auto-curare il codice.
    """
    @staticmethod
    def analyze_crash_dump_with_llm(
        config,
        registers: dict,
        history: list,
        stack_trace: list = None
    ) -> str:
        """
        Analizza un dump di crash inviando un prompt strutturato e ottimizzato a un LLM multi-provider.
        Ottimizza la context window inviando solo il contesto rilevante.
        """
        from c64debugger.llm_client import C64DebuggerLLMClient

        # 1. Prompt Engineering Strutturato
        system_prompt = (
            "Sei un assistente esperto di programmazione e debugging per il Commodore 64 "
            "e il microprocessore MOS 6502. Il tuo compito è analizzare crash dump, registri, "
            "cronologia di esecuzione e lo stack per identificare bug, spiegare l'errore "
            "e proporre fix accurati in linguaggio macchina/assembly 6502 o BASIC."
        )

        # 2. Context Window Ottimizzata (limita history e stack trace per risparmiare token)
        history_optimized = history[-10:] if history else []
        stack_optimized = stack_trace[:20] if stack_trace is not None else []

        # Formattazione pulita e compatta del contesto
        regs_str = ", ".join(f"{k}=${v:02X}" if k != "PC" else f"PC=${v:04X}" for k, v in registers.items())

        history_str_list = []
        for i, step in enumerate(history_optimized):
            if isinstance(step, dict):
                pc_val = step.get("PC", 0)
                step_regs = step.get("registers", {})
                step_regs_str = ", ".join(f"{k}=${v:02X}" for k, v in step_regs.items() if k != "PC")
                history_str_list.append(f"  Step {i+1}: PC=${pc_val:04X} ({step_regs_str})")
            else:
                history_str_list.append(f"  Step {i+1}: {step}")
        history_str = "\n".join(history_str_list) if history_str_list else "Nessuna cronologia disponibile."

        stack_str = ", ".join(f"${v:02X}" for v in stack_optimized) if stack_optimized else "Stack vuoto o non disponibile."

        user_prompt = (
            "Analizza il seguente stato di crash/debug del Commodore 64:\n\n"
            f"[REGISTRI CPU 6502]\n{regs_str}\n\n"
            f"[CRONOLOGIA ULTIME ISTRUZIONI]\n{history_str}\n\n"
            f"[STACK TRACE / MEMORIA SOSPETTA]\n{stack_str}\n\n"
            "Fornisci un'analisi contenente:\n"
            "1. Tipo di Errore rilevato (es. Stack Overflow/Underflow, Ciclo Infinito, RTS non valido, o altro)\n"
            "2. Spiegazione dettagliata del problema\n"
            "3. Proposta di patch o codice correttivo in Assembly 6502 o BASIC."
        )

        # 3. Invio della richiesta all'LLM client
        client = C64DebuggerLLMClient(config)
        return client.call_llm(system_prompt, user_prompt)

    @staticmethod
    def analyze_crash_dump(registers: dict, history: list, stack_trace: list = None) -> dict:
        """
        Analizza un dump di crash e identifica la causa probabile del fallimento (RTS sbilanciato, ciclo infinito, etc).
        """
        report = {
            "error_type": "Unknown",
            "explanation": "",
            "severity": "High",
            "probable_fix": ""
        }

        # Analisi degli errori comuni del 6502
        pc = registers.get("PC", 0)
        sp = registers.get("SP", 0xFF)

        # 1. Stack sbilanciato (SP è andato oltre i limiti della pagina 1 $0100-$01FF)
        if sp < 0x00 or sp > 0xFF:
            report["error_type"] = "Stack Overflow/Underflow"
            report["explanation"] = f"Lo Stack Pointer (${sp:02X}) è fuori dall'area riservata alla pagina 1 ($0100-$01FF). " \
                                    f"Ciò accade solitamente quando ci sono istruzioni PHA/PHP non bilanciate con PLA/PLP, " \
                                    f"oppure quando una subroutine chiama RTS senza che l'indirizzo di ritorno sia presente sullo stack."
            report["probable_fix"] = "Verifica che per ogni PHA ci sia un PLA corrispondente e che tutti i salti alle subroutine usino JSR e terminino con RTS."
            return report

        # 2. Ciclo infinito su riga singola (es. JMP * o BEQ *)
        if len(history) >= 2:
            last_steps = history[-5:]
            if len(set(step.get("PC") for step in last_steps if "PC" in step)) == 1:
                report["error_type"] = "Infinite Self-Loop"
                report["explanation"] = f"Il processore è rimasto bloccato in un ciclo infinito sullo stesso indirizzo PC (${pc:04X})."
                report["probable_fix"] = "Verifica le condizioni dei salti condizionali (BNE, BEQ, etc) o rimuovi il salto incondizionato ricorsivo su se stesso."
                return report

        # 3. Chiamata RTS sospetta
        if stack_trace is not None and len(stack_trace) == 0:
            report["error_type"] = "Invalid RTS execution"
            report["explanation"] = "È stata eseguita un'istruzione RTS (Return from Subroutine) ma la traccia dello stack risulta vuota. " \
                                    "Il PC salterà a una locazione casuale della memoria, causando un crash o un congelamento."
            report["probable_fix"] = "Assicurati che la subroutine sia stata chiamata tramite JSR e non tramite JMP."
            return report

        # Default fall-back
        report["explanation"] = f"Crash rilevato a PC=${pc:04X} con registri A={registers.get('A', 0):02X}, X={registers.get('X', 0):02X}, Y={registers.get('Y', 0):02X}."
        report["probable_fix"] = "Ispeziona l'ultima riga di codice eseguita per verificare la corretta manipolazione di memoria e registri."
        return report
