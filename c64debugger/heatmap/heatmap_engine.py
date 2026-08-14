import time
from typing import Dict, Any, List, Optional, Tuple

class MemoryHeatmap:
    """
    Tracciamento degli accessi in memoria (read/write/execute) con decadimento temporale.
    """
    def __init__(self, fade_duration: float = 5.0) -> None:
        self.fade_duration = fade_duration
        self.enabled = False
        self.access_types: List[Optional[str]] = [None] * 65536
        self.access_timestamps: List[float] = [0.0] * 65536
        self.color_mode = "RGB"  # "RGB" o "GRAYSCALE"

    def record_access(self, addr: int, access_type: str, timestamp: Optional[float] = None, value: Optional[int] = None, pm: Optional[Any] = None) -> None:
        if not self.enabled:
            return
        addr &= 0xFFFF
        t = timestamp or time.time()
        self.access_types[addr] = access_type
        self.access_timestamps[addr] = t

        if pm:
            # Trigger hook 'on_memory_access(addr, type, value)'
            pm.trigger_hook("on_memory_access", addr, access_type, value)

    def reset(self) -> None:
        self.access_types = [None] * 65536
        self.access_timestamps = [0.0] * 65536

    def get_color_for_value(self, val: int) -> str:
        """
        Associa un colore ANSI in base al valore del byte (0-255).
        """
        if self.color_mode == "RGB":
            if 0 <= val <= 85:
                return "\033[31m"      # Rosso
            elif 86 <= val <= 170:
                return "\033[32m"    # Verde
            else:
                return "\033[34m"     # Blu
        else:  # GRAYSCALE
            if val < 64:
                return "\033[90m"      # Grigio scuro
            elif val < 128:
                return "\033[37m"     # Grigio chiaro
            elif val < 192:
                return "\033[97m"     # Bianco
            else:
                return "\033[1;97m"   # Bianco grassetto

    def get_ansi_color(self, addr: int, val: int, current_pc: Optional[int] = None, current_time: Optional[float] = None) -> str:
        addr &= 0xFFFF
        now = current_time or time.time()

        if current_pc is not None and addr == current_pc:
            return "\033[1;97m"  # Bianco per PC corrente

        last_time = self.access_timestamps[addr]
        acc_type = self.access_types[addr]

        if acc_type and (now - last_time < self.fade_duration):
            if acc_type == 'X':
                return "\033[93m"  # Giallo per execute
            elif acc_type == 'W':
                return "\033[91m"  # Rosso per write
            elif acc_type == 'R':
                return "\033[94m"  # Blu per read

        return self.get_color_for_value(val)

    def render_grid(self, start_addr: int, data: bytes, current_pc: Optional[int] = None) -> List[str]:
        """
        Genera una visualizzazione a griglia 2D di una porzione di memoria con heatmap.
        """
        lines = []
        now = time.time()
        rows = len(data) // 16
        for r in range(rows):
            row_addr = start_addr + r * 16
            hex_parts = []
            for c in range(16):
                addr = row_addr + c
                val = data[r * 16 + c]
                color = self.get_ansi_color(addr, val, current_pc, now)
                hex_parts.append(f"{color}{val:02X}\033[0m")
            lines.append(f"  \033[95m${row_addr:04X}\033[0m:  " + " ".join(hex_parts))
        return lines

    def render_heatmap_2d(self, start_addr: int, data: bytes, current_pc: Optional[int] = None) -> List[str]:
        """
        Genera una visualizzazione a griglia compatta 2D (64 colonne) di una porzione di memoria con heatmap,
        utilizzando simboli a blocco singolo (es: '■').
        """
        lines = []
        now = time.time()
        cols = 64
        rows = len(data) // cols
        if len(data) % cols != 0:
            rows += 1

        for r in range(rows):
            row_addr = start_addr + r * cols
            cell_parts = []
            for c in range(cols):
                idx = r * cols + c
                if idx >= len(data):
                    break
                addr = row_addr + c
                val = data[idx]
                color = self.get_ansi_color(addr, val, current_pc, now)
                cell_parts.append(f"{color}■\033[0m")
            lines.append(f"  \033[95m${row_addr:04X}\033[0m: " + "".join(cell_parts))
        return lines
