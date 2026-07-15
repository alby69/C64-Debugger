import re
from typing import Dict, Any, Union

class VICEMonitorProtocol:
    """
    Parser and formatter class for the VICE remote text monitor protocol.
    Provides standard tools to parse response messages and format commands.
    """

    @staticmethod
    def parse_registers(response: str) -> Dict[str, Union[int, str]]:
        """
        Parses the register display command ('r') output from the VICE monitor.
        Returns a dictionary with PC, A, X, Y, SP and optional Status Flags.
        """
        registers: Dict[str, Union[int, str]] = {
            "PC": 0,
            "A": 0,
            "X": 0,
            "Y": 0,
            "SP": 0,
            "Flags": ""
        }

        # Try to match the standard columns structure: ADDR A  X  Y  SP
        # Example: .c000 00 00 00 f6 2f 37 00101010
        match = re.search(
            r'\.([0-9a-fA-F]{4})\s+([0-9a-fA-F]{2})\s+([0-9a-fA-F]{2})\s+([0-9a-fA-F]{2})\s+([0-9a-fA-F]{2})',
            response
        )
        if match:
            registers["PC"] = int(match.group(1), 16)
            registers["A"] = int(match.group(2), 16)
            registers["X"] = int(match.group(3), 16)
            registers["Y"] = int(match.group(4), 16)
            registers["SP"] = int(match.group(5), 16)
        else:
            # Fallback parsing line by line for explicit key=value pairs, e.g. "PC=c000" or similar
            for line in response.splitlines():
                if "PC=" in line or "A=" in line:
                    for part in line.split():
                        if "=" in part:
                            parts = part.split("=")
                            if len(parts) == 2:
                                k, v = parts
                                try:
                                    registers[k] = int(v.replace("$", ""), 16)
                                except ValueError:
                                    registers[k] = v
        return registers

    @staticmethod
    def parse_memory(response: str) -> bytes:
        """
        Parses memory dump ('m') output from the VICE monitor.
        Returns a bytes object of the read memory.
        """
        byte_list = []
        for line in response.splitlines():
            line = line.strip()
            if line.startswith(".") or line.startswith(">"):
                parts = line.split()
                if len(parts) > 1:
                    for part in parts[1:]:
                        # If we hit the ASCII representation (e.g. "........") or any non-hex part
                        if len(part) != 2 or not all(c in "0123456789abcdefABCDEF" for c in part):
                            break
                        byte_list.append(int(part, 16))
        return bytes(byte_list)

    @staticmethod
    def format_write_memory(addr: int, data: bytes) -> str:
        """
        Formats the write memory command ('>') for VICE monitor.
        """
        bytes_str = " ".join(f"{b:02x}" for b in data)
        return f"> {addr:04x} {bytes_str}"

    @staticmethod
    def format_breakpoint(addr: int) -> str:
        """
        Formats the set breakpoint command ('break') for VICE monitor.
        """
        return f"break {addr:04x}"

    @staticmethod
    def format_read_memory(start_addr: int, end_addr: int) -> str:
        """
        Formats the read memory command ('m') for VICE monitor.
        """
        return f"m {start_addr:04x} {end_addr:04x}"
