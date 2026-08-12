import json
import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from c64debugger.debugger_core import C64DebuggerCore

logger = logging.getLogger("C64SessionManager")

class C64SessionManager:
    """
    Gestisce il salvataggio e il caricamento delle sessioni di debugging (.c64dbg).
    Permette di persistere e ripristinare breakpoint, watchpoint, condizioni, ecc.
    """

    @staticmethod
    def save_session(filepath: str, core: C64DebuggerCore, loaded_symbols_path: Optional[str] = None) -> bool:
        """
        Salva lo stato corrente del debugger in un file JSON (.c64dbg).
        """
        try:
            # Converti set e dizionari con chiavi intere in liste/stringhe serializzabili in JSON
            session_data = {
                "version": "0.5.0",
                "breakpoints": list(core.breakpoints),
                "breakpoint_conditions": {str(k): v for k, v in core.breakpoint_conditions.items()},
                "hit_count_limits": {str(k): v for k, v in core.hit_count_limits.items()},
                "hit_counts": {str(k): v for k, v in core.hit_counts.items()},
                "watchpoints": list(core.watchpoints.keys()),
                "watchpoint_ranges": core.watchpoint_ranges,
                "io_breakpoints": core.io_breakpoints,
                "loaded_symbols_path": loaded_symbols_path
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=4)
            logger.info(f"Sessione di debug salvata con successo in '{filepath}'")
            return True
        except Exception as e:
            logger.error(f"Errore durante il salvataggio della sessione in '{filepath}': {e}")
            raise

    @staticmethod
    def load_session(filepath: str, core: C64DebuggerCore) -> Dict[str, Any]:
        """
        Carica e ripristina una sessione di debug da un file JSON (.c64dbg).
        Ritorna il dizionario completo con i dati caricati (inclusi i simboli).
        """
        if not os.path.exists(filepath):
            logger.error(f"File sessione non trovato: {filepath}")
            raise FileNotFoundError(f"File sessione non trovato: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Svuota lo stato precedente e ripristina
            core.breakpoints = set(data.get("breakpoints", []))
            core.breakpoint_conditions = {int(k): v for k, v in data.get("breakpoint_conditions", {}).items()}
            core.hit_count_limits = {int(k): v for k, v in data.get("hit_count_limits", {}).items()}
            core.hit_counts = {int(k): v for k, v in data.get("hit_counts", {}).items()}

            core.watchpoints = {int(addr): None for addr in data.get("watchpoints", [])}

            # Watchpoint ranges
            raw_ranges = data.get("watchpoint_ranges", [])
            core.watchpoint_ranges = [tuple(r) if isinstance(r, list) else r for r in raw_ranges]

            # IO breakpoints
            raw_io = data.get("io_breakpoints", {})
            core.io_breakpoints = {k: tuple(v) if isinstance(v, list) else v for k, v in raw_io.items()}

            logger.info(f"Sessione di debug caricata e ripristinata da '{filepath}'")
            return data
        except Exception as e:
            logger.error(f"Errore durante il caricamento della sessione da '{filepath}': {e}")
            raise


class C64SnapshotManager:
    """
    Gestisce il salvataggio e caricamento dei dump completi di RAM (snapshots) dal/al Commodore 64.
    """

    @staticmethod
    def save_ram_snapshot(filepath: str, bridge: Any, start_addr: int = 0x0000, end_addr: int = 0xFFFF) -> bool:
        """
        Scarica il blocco di memoria dall'emulatore tramite il bridge e lo salva in un file binario.
        """
        try:
            logger.info(f"Salvataggio snapshot RAM (${start_addr:04X}-${end_addr:04X}) in corso...")
            # Legge la memoria dal bridge
            ram_data = bridge.read_memory(start_addr, end_addr)
            if not ram_data:
                raise ValueError("Nessun dato letto dalla memoria del C64")

            # Salva in un file binario
            with open(filepath, "wb") as f:
                f.write(ram_data)

            logger.info(f"Snapshot RAM (${start_addr:04X}-${end_addr:04X}) salvato in '{filepath}'")
            return True
        except Exception as e:
            logger.error(f"Errore durante il salvataggio dello snapshot RAM: {e}")
            raise

    @staticmethod
    def load_ram_snapshot(filepath: str, bridge: Any, start_addr: int = 0x0000) -> bool:
        """
        Carica un file binario e scrive i suoi byte nella RAM del C64 a partire da start_addr.
        """
        if not os.path.exists(filepath):
            logger.error(f"File snapshot RAM non trovato: {filepath}")
            raise FileNotFoundError(f"File snapshot RAM non trovato: {filepath}")

        try:
            logger.info(f"Caricamento snapshot RAM da '{filepath}' in corso...")
            with open(filepath, "rb") as f:
                ram_data = f.read()

            if not ram_data:
                raise ValueError("Il file snapshot RAM è vuoto.")

            # Scrive la memoria tramite il bridge
            bridge.write_memory(start_addr, ram_data)
            logger.info(f"Snapshot RAM ({len(ram_data)} byte) caricato in memoria a partire da ${start_addr:04X}")
            return True
        except Exception as e:
            logger.error(f"Errore durante il caricamento dello snapshot RAM: {e}")
            raise
