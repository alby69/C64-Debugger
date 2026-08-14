import struct
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("C64WatchManager")

class WatchManager:
    """
    Manages watches on memory addresses or symbolic labels, formatting their values
    according to requested display types (hex8, hex16, hex32, s8, u8, s16, u16, s32, u32, text).
    """

    VALID_FORMATS = {"hex8", "hex16", "hex32", "s8", "u8", "s16", "u16", "s32", "u32", "text"}

    def __init__(self) -> None:
        self.watches: Dict[str, str] = {}  # name_or_address -> format_str

    def clear(self) -> None:
        """Removes all watches."""
        self.watches.clear()

    def add_watch(self, name_or_address: str, format_str: str = "hex8") -> bool:
        """
        Adds a watch for a name or address with the specified format.
        """
        name_or_address = name_or_address.strip()
        format_str = format_str.strip().lower()

        if format_str not in self.VALID_FORMATS:
            logger.warning(f"Invalid watch format '{format_str}', falling back to 'hex8'.")
            format_str = "hex8"

        self.watches[name_or_address] = format_str
        return True

    def remove_watch(self, name_or_address: str) -> bool:
        """
        Removes a watch. Returns True if found and removed.
        """
        name_or_address = name_or_address.strip()
        if name_or_address in self.watches:
            del self.watches[name_or_address]
            return True
        return False

    def list_watches(self) -> Dict[str, str]:
        """Returns the dictionary of currently configured watches."""
        return self.watches.copy()

    def evaluate_watches(self, bridge: Any, symbol_resolver_fn: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Reads memory from the bridge and evaluates the watched locations.
        """
        results = []
        for name_or_addr, fmt in self.watches.items():
            addr: Optional[int] = None
            if symbol_resolver_fn:
                addr = symbol_resolver_fn(name_or_addr)

            if addr is None:
                try:
                    if name_or_addr.startswith("$"):
                        addr = int(name_or_addr[1:], 16)
                    elif name_or_addr.lower().startswith("0x"):
                        addr = int(name_or_addr, 16)
                    else:
                        addr = int(name_or_addr)
                except ValueError:
                    results.append({
                        "name": name_or_addr,
                        "format": fmt,
                        "address": None,
                        "value": "Unresolved symbol"
                    })
                    continue

            addr &= 0xFFFF

            length = 1
            if fmt in {"hex16", "s16", "u16"}:
                length = 2
            elif fmt in {"hex32", "s32", "u32"}:
                length = 4
            elif fmt == "text":
                length = 16

            try:
                mem_data = bridge.read_memory(addr, min(addr + length - 1, 0xFFFF))
                if not mem_data:
                    val_str = "Error reading memory"
                else:
                    val_str = self.format_value(mem_data, fmt)
            except Exception as e:
                val_str = f"Error: {e}"

            results.append({
                "name": name_or_addr,
                "format": fmt,
                "address": addr,
                "value": val_str
            })

        return results

    def format_value(self, data: bytes, fmt: str) -> str:
        """Formats the read bytes according to the format specifier."""
        try:
            if fmt == "hex8":
                val = data[0] if data else 0
                return f"${val:02X}"
            elif fmt == "hex16":
                val = struct.unpack("<H", data[:2].ljust(2, b'\x00'))[0]
                return f"${val:04X}"
            elif fmt == "hex32":
                val = struct.unpack("<I", data[:4].ljust(4, b'\x00'))[0]
                return f"${val:08X}"
            elif fmt == "u8":
                val = data[0] if data else 0
                return str(val)
            elif fmt == "s8":
                val = struct.unpack("<b", data[:1])[0] if data else 0
                return str(val)
            elif fmt == "u16":
                val = struct.unpack("<H", data[:2].ljust(2, b'\x00'))[0]
                return str(val)
            elif fmt == "s16":
                val = struct.unpack("<h", data[:2].ljust(2, b'\x00'))[0]
                return str(val)
            elif fmt == "u32":
                val = struct.unpack("<I", data[:4].ljust(4, b'\x00'))[0]
                return str(val)
            elif fmt == "s32":
                val = struct.unpack("<i", data[:4].ljust(4, b'\x00'))[0]
                return str(val)
            elif fmt == "text":
                text_bytes = bytearray()
                for b in data:
                    if b == 0:
                        break
                    text_bytes.append(b)
                return text_bytes.decode("ascii", errors="replace")
        except Exception as e:
            return f"Formatting error ({e})"

        return "???"

    def save_to_session(self) -> List[Dict[str, str]]:
        """Serializes current watches into a JSON-compatible format."""
        return [{"name": name, "format": fmt} for name, fmt in self.watches.items()]

    def load_from_session(self, watches_data: List[Dict[str, str]]) -> None:
        """Restores watches from serialized data."""
        self.clear()
        if not isinstance(watches_data, list):
            return
        for item in watches_data:
            if isinstance(item, dict) and "name" in item:
                self.add_watch(item["name"], item.get("format", "hex8"))
