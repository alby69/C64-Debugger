import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("C64XRefDatabase")

class XRefDatabase:
    """
    Manages a cross-reference database of memory accesses.
    Tracks which instructions (PC) read (R), write (W), or execute (X) specific memory cells.
    """

    def __init__(self) -> None:
        self.accesses: Dict[int, List[Dict[str, Any]]] = {}  # address -> list of accesses
        self._counter = 0

    def clear(self) -> None:
        """Clears all tracked cross-references."""
        self.accesses.clear()
        self._counter = 0

    def record_access(self, address: int, pc: int, access_type: str) -> None:
        """
        Records an access of type 'R' (Read), 'W' (Write) or 'X' (Execute)
        at the specified address by the instruction at pc.
        """
        address &= 0xFFFF
        pc &= 0xFFFF
        access_type = access_type.upper()

        if access_type not in {"R", "W", "X"}:
            logger.warning(f"Invalid access type: {access_type}")
            return

        if address not in self.accesses:
            self.accesses[address] = []

        existing = self.accesses[address]
        if existing:
            last = existing[-1]
            if last["pc"] == pc and last["type"] == access_type:
                return

        self._counter += 1
        existing.append({
            "pc": pc,
            "type": access_type,
            "timestamp": self._counter
        })

    def get_references(self, address: int) -> List[Dict[str, Any]]:
        """
        Returns all recorded accesses for a given memory address.
        Each access is represented as: {"pc": pc, "type": type, "timestamp": timestamp}
        """
        return self.accesses.get(address & 0xFFFF, []).copy()
