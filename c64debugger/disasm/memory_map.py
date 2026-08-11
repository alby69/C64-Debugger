from typing import List, Dict, Tuple

class C64MemoryMap:
    """
    Gestore e visualizzatore della mappa di memoria del Commodore 64.
    Mappa gli indirizzi da $0000 a $FFFF nelle rispettive aree hardware/software.
    """

    REGIONS: List[Tuple[int, int, str, str]] = [
        (0x0000, 0x0001, "6510 I/O", "DDR e Register I/O della CPU 6510"),
        (0x0002, 0x00FF, "Zero Page", "RAM ad accesso rapido per variabili di sistema e puntatori"),
        (0x0100, 0x01FF, "Stack", "Stack di sistema della CPU 6502"),
        (0x0200, 0x03FF, "System RAM", "Vettori di sistema, buffer di input e aree KERNAL/BASIC"),
        (0x0400, 0x07FF, "Screen Memory", "Memoria video dei caratteri (default $0400)"),
        (0x0800, 0x9FFF, "BASIC RAM", "Area per i programmi BASIC dell'utente"),
        (0xA000, 0xBFFF, "BASIC ROM / RAM", "ROM dell'interprete BASIC o RAM sottostante"),
        (0xC000, 0xCFFF, "User RAM", "RAM libera per l'utente, tipicamente usata per codice Assembly"),
        (0xD000, 0xD3FF, "VIC-II I/O", "Registri del chip video VIC-II"),
        (0xD400, 0xD7FF, "SID I/O", "Registri del chip audio/sintetizzatore SID"),
        (0xD800, 0xDBFF, "Color RAM", "RAM dei colori dei caratteri a video"),
        (0xDC00, 0xDCFF, "CIA 1 I/O", "Complex Interface Adapter 1 (Tastiera, Joystick 2, IRQ)"),
        (0xDD00, 0xDDFF, "CIA 2 I/O", "Complex Interface Adapter 2 (Porta seriale, User Port, NMI)"),
        (0xDE00, 0xDFFF, "I/O Expansion", "Area per cartucce di espansione hardware"),
        (0xE000, 0xFFFF, "KERNAL ROM / RAM", "ROM del sistema operativo KERNAL o RAM sottostante")
    ]

    @classmethod
    def get_region_info(cls, address: int) -> Dict[str, str]:
        """
        Ritorna le informazioni sulla regione di memoria per un dato indirizzo.
        """
        address &= 0xFFFF
        for start, end, name, desc in cls.REGIONS:
            if start <= address <= end:
                return {
                    "name": name,
                    "description": desc,
                    "range": f"${start:04X}-${end:04X}"
                }
        return {
            "name": "Unknown",
            "description": "Area di memoria non mappata",
            "range": "????-????"
        }

    @classmethod
    def format_memory_with_annotations(cls, start_addr: int, data: bytes, bytes_per_line: int = 8) -> List[str]:
        """
        Formatta un blocco di byte con indirizzi esadecimali, rappresentazione ASCII e annotazioni della regione di memoria.
        """
        lines = []
        curr_addr = start_addr & 0xFFFF

        for i in range(0, len(data), bytes_per_line):
            chunk = data[i:i+bytes_per_line]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            # Allineamento visivo se l'ultimo chunk è incompleto
            if len(chunk) < bytes_per_line:
                hex_part = hex_part.ljust(bytes_per_line * 3 - 1)

            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            if len(chunk) < bytes_per_line:
                ascii_part = ascii_part.ljust(bytes_per_line)

            region_info = cls.get_region_info(curr_addr)
            region_name = region_info["name"]

            line = f"${curr_addr:04X}:  {hex_part}  |{ascii_part}|  [{region_name}]"
            lines.append(line)
            curr_addr = (curr_addr + len(chunk)) & 0xFFFF

        return lines
