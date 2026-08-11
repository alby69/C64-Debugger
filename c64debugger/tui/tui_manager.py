import os
import re
import sys
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("C64TUI")

def highlight_6502_assembly(line: str) -> str:
    """
    Applica evidenziazione della sintassi ANSI 6502 ad una riga di disassembly.
    """
    if ";" in line:
        code_part, comment_part = line.split(";", 1)
        comment_highlighted = f"\033[90m;{comment_part}\033[0m"
    else:
        code_part = line
        comment_highlighted = ""

    # Lista opcode standard 6502
    opcodes = ["LDA", "LDX", "LDY", "STA", "STX", "STY", "JSR", "JMP", "RTS", "RTI",
               "CMP", "CPX", "CPY", "BEQ", "BNE", "BCS", "BCC", "BVS", "BVC", "BPL",
               "BMI", "INC", "DEC", "INX", "DEX", "INY", "DEY", "CLC", "SEC", "CLI",
               "SEI", "PHA", "PLA", "PHP", "PLP", "TAX", "TXA", "TAY", "TYA", "TSX",
               "TXS", "NOP", "ORA", "AND", "EOR", "ADC", "SBC", "LSR", "ASL", "ROL", "ROR", "BIT"]

    # Evidenzia gli opcode (giallo/arancione)
    for op in opcodes:
        code_part = re.sub(rf"\b({op})\b", r"\033[93m\1\033[0m", code_part, flags=re.IGNORECASE)

    # Evidenzia indirizzi esadecimali (magenta)
    code_part = re.sub(r"(\$[0-9a-fA-F]+)\b", r"\033[95m\1\033[0m", code_part)
    code_part = re.sub(r"\b(0x[0-9a-fA-F]+)\b", r"\033[95m\1\033[0m", code_part)

    # Evidenzia immediati (cyan)
    code_part = re.sub(r"(#[0-9a-fA-F\$]+)\b", r"\033[96m\1\033[0m", code_part)
    code_part = re.sub(r"(#%[01]+)\b", r"\033[96m\1\033[0m", code_part)

    # Evidenzia registri A, X, Y (rosso)
    code_part = re.sub(r"\b([A|X|Y])\b", r"\033[91m\1\033[0m", code_part)
    code_part = re.sub(r",\s*([X|Y|x|y])\b", r",\033[91m\1\033[0m", code_part)

    return code_part + comment_highlighted


class C64DebuggerTUI:
    """
    Rappresenta una Text User Interface (TUI) interattiva stile dashboard
    per mostrare lo stato del Commodore 64 (registri, disassembly, memoria, stack).
    """

    def __init__(self, bridge: Any, core: Any) -> None:
        self.bridge = bridge
        self.core = core
        self.running = False

    def draw_dashboard(self) -> str:
        """
        Genera una stringa contenente l'intera dashboard testuale.
        """
        try:
            regs = self.bridge.get_registers()
        except Exception:
            regs = {}

        if not regs or "PC" not in regs:
            return (
                "\033[2J\033[H"
                "==================================================\n"
                "           C64 DEBUGGER - DASHBOARD TUI           \n"
                "==================================================\n\n"
                " \033[91m[STATO: DISCONNESSO / ERRORE DI COMUNICAZIONE]\033[0m\n\n"
                " Assicurati che l'emulatore VICE sia connesso."
            )

        pc = regs.get("PC", 0)
        a = regs.get("A", 0)
        x = regs.get("X", 0)
        y = regs.get("Y", 0)
        sp = regs.get("SP", 0xFD)
        sr = regs.get("SR", 0x30)

        # Costruisce la visualizzazione dei Flag SR (NV-BDIZC)
        flags_str = ""
        flags_labels = [("N", 7), ("V", 6), ("-", 5), ("B", 4), ("D", 3), ("I", 2), ("Z", 1), ("C", 0)]
        for label, bit in flags_labels:
            if sr & (1 << bit):
                flags_str += f"\033[92m{label}\033[0m "
            else:
                flags_str += f"\033[90m{label}\033[0m "

        # Layout intestazione e registri
        output = []
        output.append("\033[2J\033[H")  # Pulisce schermo e posiziona cursore in alto a sinistra
        output.append("\033[94m================================================================================\033[0m")
        output.append(f"\033[97m C64 DEBUGGER TUI v0.5.0 \033[0;92m[CONNESSO] \033[0m| Host: {self.bridge.host}:{self.bridge.port}")
        output.append("\033[94m================================================================================\033[0m")
        output.append(f" PC: \033[95m${pc:04X}\033[0m   A: \033[96m${a:02X}\033[0m   X: \033[96m${x:02X}\033[0m   Y: \033[96m${y:02X}\033[0m   SP: \033[95m${sp:02X}\033[0m   Flags: {flags_str}")
        output.append("\033[94m--------------------------------------------------------------------------------\033[0m")

        # Sezione disassembly (disassembly simulato o letto dal PC corrente)
        output.append("\033[1;33m[DISASSEMBLY / ISTRUZIONI VICINE]\033[0m")
        try:
            # Leggi 16 byte intorno a PC
            mem_bytes = self.bridge.read_memory(pc, min(pc + 15, 0xFFFF))
            # Semplice disassembly demo
            idx = 0
            while idx < len(mem_bytes) and idx < 10:
                addr = pc + idx
                b = mem_bytes[idx]
                is_current = " \033[92m--->\033[0m" if addr == pc else "     "

                # Semplice mock disasm per la demo
                if b == 0xA9:
                    dis = f"LDA #${mem_bytes[idx+1]:02X}" if idx + 1 < len(mem_bytes) else "LDA #??"
                    bytes_str = f"A9 {mem_bytes[idx+1]:02X}" if idx + 1 < len(mem_bytes) else "A9"
                    step = 2
                elif b == 0xAD:
                    dis = f"LDA ${mem_bytes[idx+2]:02X}{mem_bytes[idx+1]:02X}" if idx + 2 < len(mem_bytes) else "LDA $????"
                    bytes_str = f"AD {mem_bytes[idx+1]:02X} {mem_bytes[idx+2]:02X}" if idx + 2 < len(mem_bytes) else "AD"
                    step = 3
                elif b == 0xEA:
                    dis = "NOP"
                    bytes_str = "EA"
                    step = 1
                elif b == 0x60:
                    dis = "RTS"
                    bytes_str = "60"
                    step = 1
                else:
                    dis = f"HEX ${b:02X}"
                    bytes_str = f"{b:02X}"
                    step = 1

                line = f"{is_current} \033[95m${addr:04X}\033[0m: {bytes_str:<8} {dis}"
                output.append(highlight_6502_assembly(line))
                idx += step
        except Exception as e:
            output.append(f"  Errore lettura disassembly: {e}")

        output.append("\033[94m--------------------------------------------------------------------------------\033[0m")
        output.append("\033[1;33m[MEMORIA CORRENTE - AREA CODICE/DATI]\033[0m")
        try:
            # Mostra 32 byte della memoria a partire da PC o $C000
            start_mem = pc & 0xFFF0
            mem_bytes = self.bridge.read_memory(start_mem, start_mem + 31)
            for row in range(2):
                addr_row = start_mem + row * 16
                row_bytes = mem_bytes[row * 16 : (row + 1) * 16]
                hex_vals = " ".join(f"{b:02X}" for b in row_bytes)
                ascii_vals = "".join(chr(b) if 32 <= b <= 126 else "." for b in row_bytes)
                output.append(f"  \033[95m${addr_row:04X}\033[0m:  {hex_vals:<47}  \033[92m|{ascii_vals}|\033[0m")
        except Exception as e:
            output.append(f"  Errore lettura memoria: {e}")

        output.append("\033[94m--------------------------------------------------------------------------------\033[0m")
        output.append(" Premi [Invio] per aggiornare, o scrivi 'exit' per tornare alla REPL CLI.")
        output.append("\033[94m================================================================================\033[0m")

        return "\n".join(output)

    def run(self) -> None:
        """
        Avvia la visualizzazione interattiva della dashboard.
        """
        self.running = True
        import sys

        while self.running:
            print(self.draw_dashboard())
            try:
                inp = input("\n(tui) ").strip().lower()
                if inp in ("exit", "quit", "q"):
                    self.running = False
            except (KeyboardInterrupt, EOFError):
                self.running = False
                print()
