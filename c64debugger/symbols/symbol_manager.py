import os
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("C64SymbolManager")

def _parse_int_val(val_str: str) -> int:
    """
    Helper robusto per convertire una stringa numerica (esadecimale o decimale) in intero.
    Supporta prefissi como '$', '0x' o formati grezzi.
    """
    val_str = val_str.strip()
    if val_str.startswith("$"):
        return int(val_str[1:], 16)
    if val_str.lower().startswith("0x"):
        return int(val_str[2:], 16)
    if val_str.isdigit():
        return int(val_str, 10)
    try:
        return int(val_str, 16)
    except ValueError:
        return int(val_str, 10)

class C64SymbolManager:
    """
    Gestisce la mappatura bidirezionale dei simboli (label) per il Commodore 64.
    Supporta l'importazione di file di simboli generati da diversi assemblatori:
    - ACME (.lbl, .sym)
    - KickAssembler (.vs, .txt)
    - TMPx / altri assemblatori con formati standard a colonne o definizioni '='.
    """

    def __init__(self) -> None:
        self._name_to_addr: Dict[str, int] = {}
        self._addr_to_names: Dict[int, List[str]] = {}
        self.loaded_filepath: Optional[str] = None

    def clear(self) -> None:
        """Pulisce tutti i simboli correnti."""
        self._name_to_addr.clear()
        self._addr_to_names.clear()
        self.loaded_filepath = None

    def add_symbol(self, name: str, address: int) -> None:
        """Aggiunge un singolo simbolo con il relativo indirizzo (0x0000 - 0xFFFF)."""
        address &= 0xFFFF
        name = name.strip()
        if not name:
            return

        self._name_to_addr[name] = address
        if address not in self._addr_to_names:
            self._addr_to_names[address] = []
        if name not in self._addr_to_names[address]:
            self._addr_to_names[address].append(name)

    def get_address(self, name: str) -> Optional[int]:
        """Restituisce l'indirizzo associato ad un nome di simbolo."""
        return self._name_to_addr.get(name.strip())

    def get_symbols(self, address: int) -> List[str]:
        """Restituisce la lista di simboli associati ad un indirizzo."""
        return self._addr_to_names.get(address & 0xFFFF, [])

    def all_symbols(self) -> Dict[str, int]:
        """Restituisce tutti i simboli correnti (mappa nome -> indirizzo)."""
        return self._name_to_addr.copy()

    def load_from_file(self, filepath: str, file_format: Optional[str] = None) -> int:
        """
        Carica i simboli da un file. Riconosce automaticamente il formato o usa quello fornito.
        Ritorna il numero di simboli caricati con successo.
        """
        if not os.path.exists(filepath):
            logger.error(f"File dei simboli non trovato: {filepath}")
            raise FileNotFoundError(f"File dei simboli non trovato: {filepath}")

        self.clear()
        self.loaded_filepath = filepath
        count = 0

        # Pattern regex per riconoscere i diversi formati
        # 1. ACME standard / al format (es: al C:c000 .init o al $c000 label_name)
        re_al_format = re.compile(r"^\s*al\s+(?:C:|\$)?([0-9a-fA-F]+)\s+\.?([a-zA-Z_][a-zA-Z0-9_]*)")

        # 2. KickAssembler .label format (es: .label my_label=$c000 o .label other=49152)
        re_kick_label = re.compile(r"^\s*\.label\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*?)\s*$")

        # 3. Definizioni con '=' (es: my_label = $C000 o my_label = 49152)
        re_equals_definition = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*?)\s*$")

        # 4. TMPx / Formato a colonne (es: my_label $C000)
        re_columns_format = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+(.*?)\s*$")

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_strip = line.strip()
                    # Salta commenti e righe vuote
                    if not line_strip or line_strip.startswith(";") or line_strip.startswith("//"):
                        continue

                    # Prova ad applicare i vari regex matcher
                    # 1. ACME al
                    match = re_al_format.match(line_strip)
                    if match:
                        addr_str, name = match.groups()
                        self.add_symbol(name, _parse_int_val(addr_str))
                        count += 1
                        continue

                    # 2. KickAssembler .label
                    match = re_kick_label.match(line_strip)
                    if match:
                        name, addr_str = match.groups()
                        self.add_symbol(name, _parse_int_val(addr_str))
                        count += 1
                        continue

                    # 3. Definizioni '=' con hex o dec
                    match = re_equals_definition.match(line_strip)
                    if match:
                        name, addr_str = match.groups()
                        self.add_symbol(name, _parse_int_val(addr_str))
                        count += 1
                        continue

                    # 4. TMPx / Colonne
                    match = re_columns_format.match(line_strip)
                    if match:
                        name, addr_str = match.groups()
                        try:
                            self.add_symbol(name, _parse_int_val(addr_str))
                            count += 1
                        except ValueError:
                            pass
                        continue

            logger.info(f"Caricati {count} simboli da '{filepath}'")
            return count
        except Exception as e:
            logger.error(f"Errore durante la lettura del file dei simboli '{filepath}': {e}")
            raise
