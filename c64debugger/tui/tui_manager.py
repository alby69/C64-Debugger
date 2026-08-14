import os
import re
import sys
import logging
from typing import Dict, Any, List, Optional
from c64debugger.hw_state import VICState, SIDState, CIAState
from c64debugger.heatmap import MemoryHeatmap
from c64debugger.reverse import TimelineEngine

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

    def __init__(self, bridge: Any, core: Any, heatmap: Optional[MemoryHeatmap] = None, timeline: Optional[TimelineEngine] = None) -> None:
        self.bridge = bridge
        self.core = core
        self.heatmap = heatmap if heatmap is not None else MemoryHeatmap()
        self.timeline = timeline if timeline is not None else TimelineEngine()
        self.running = False
        self.view_mode = "default"  # "default", "hw_state", "heatmap", "timeline"

    def draw_dashboard(self) -> str:
        """
        Genera una stringa contenente la dashboard testuale in base al view_mode selezionato.
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
        output.append(f"\033[97m C64 DEBUGGER TUI v0.7.0 \033[0;92m[CONNESSO] \033[0m| Host: {self.bridge.host}:{self.bridge.port}")
        output.append("\033[94m================================================================================\033[0m")
        output.append(f" PC: \033[95m${pc:04X}\033[0m   A: \033[96m${a:02X}\033[0m   X: \033[96m${x:02X}\033[0m   Y: \033[96m${y:02X}\033[0m   SP: \033[95m${sp:02X}\033[0m   Flags: {flags_str}")
        output.append("\033[94m--------------------------------------------------------------------------------\033[0m")

        if self.view_mode == "default":
            # Sezione disassembly
            output.append("\033[1;33m[DISASSEMBLY / ISTRUZIONI VICINE]\033[0m")
            try:
                mem_bytes = self.bridge.read_memory(pc, min(pc + 15, 0xFFFF))
                idx = 0
                while idx < len(mem_bytes) and idx < 10:
                    addr = pc + idx
                    b = mem_bytes[idx]
                    is_current = " \033[92m--->\033[0m" if addr == pc else "     "

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
                from c64debugger.disasm.memory_map import C64MemoryMap
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

        elif self.view_mode == "hw_state":
            output.append("\033[1;33m[STATO CHIP HARDWARE (VIC-II / SID / CIA)]\033[0m")
            try:
                # VIC-II
                vic_data = self.bridge.read_memory(0xD000, 0xD02E)
                vic = VICState(vic_data)
                v_info = vic.to_dict()
                output.append(f" \033[1;35m[VIC-II]\033[0m Raster Line: {v_info['raster_line']} (Bad Line: {'SI' if v_info['bad_line'] else 'NO'})")
                output.append(f"          Screen Enabled: {v_info['screen_on']} | Bitmap Mode: {v_info['bitmap_mode']} | Multicolor: {v_info['multicolor_mode']}")
                output.append(f"          Colors: Border={v_info['border_color']}, Bg={v_info['background_color']} | Row/Col: {v_info['row_select']}/{v_info['column_select']}")
                output.append(f"          Matrix Offset: ${v_info['screen_matrix_base_offset']:04X} | Charset: ${v_info['charset_base_offset']:04X}")

                # SID
                sid_data = self.bridge.read_memory(0xD400, 0xD41C)
                sid = SIDState(sid_data)
                s_info = sid.to_dict()
                output.append(f" \033[1;35m[SID]\033[0m    Volume: {s_info['volume']} | Cutoff: {s_info['cutoff_freq']} | Resonance: {s_info['resonance']}")
                for voice in s_info["voices"]:
                    output.append(f"          Voice {voice['voice_index']}: {voice['frequency_hz']} Hz (Note: {voice['note']}) | Wave: {voice['waveform']} | Gate: {voice['gate']}")

                # CIA1
                cia1_data = self.bridge.read_memory(0xDC00, 0xDC0F)
                cia1 = CIAState(cia1_data, "CIA1")
                c1_info = cia1.to_dict()
                output.append(f" \033[1;35m[CIA1]\033[0m   Timer A: {c1_info['timer_a']} ({'ON' if c1_info['timer_a_active'] else 'OFF'}) | Timer B: {c1_info['timer_b']} ({'ON' if c1_info['timer_b_active'] else 'OFF'})")
                output.append(f"          TOD: {c1_info['tod']} (PM: {c1_info['tod_pm']}) | Port A: ${c1_info['port_a']:02X} | Port B: ${c1_info['port_b']:02X}")
            except Exception as e:
                output.append(f"  Errore lettura stato hardware: {e}")

        elif self.view_mode == "heatmap":
            output.append("\033[1;33m[MEMORY HEATMAP - DETTAGLIO ACCESSI (64x32)]\033[0m")
            if not self.heatmap.enabled:
                output.append("\n  \033[91m[Heatmap Disabilitata] - Scrivi 'heatmap' per abilitarla.\033[0m")
            else:
                try:
                    start_addr = pc & 0xF800
                    mem_bytes = self.bridge.read_memory(start_addr, start_addr + 2047)
                    lines = self.heatmap.render_heatmap_2d(start_addr, mem_bytes, pc)
                    output.extend(lines)
                except Exception as e:
                    output.append(f"  Errore rendering heatmap: {e}")

        elif self.view_mode == "timeline":
            output.append("\033[1;33m[REVERSE DEBUGGING - TIMELINE STATUS]\033[0m")
            if not self.timeline.enabled:
                output.append("\n  \033[91m[Timeline Disabilitata] - Scrivi 'timeline' per abilitarla.\033[0m")
            else:
                info = self.timeline.status()
                total = info["total_snapshots"]
                curr = info["current_index"]
                output.append(f"  Stato: Abilitata")
                output.append(f"  Snapshot Registrati: {total} / {info['max_snapshots']}")
                output.append(f"  Indice Corrente: {curr}")

                # Visual progress bar of timeline position
                if total > 0:
                    bar_len = 40
                    pos = int((curr / (total - 1)) * bar_len) if total > 1 else 0
                    bar = "[" + "=" * pos + "*" + "=" * (bar_len - pos - 1) + "]"
                    output.append(f"  Posizione: {bar} ({curr + 1}/{total})")
                else:
                    output.append("  Nessuno snapshot registrato. Fai dei passi ('step') per iniziare la registrazione.")

        output.append("\033[94m--------------------------------------------------------------------------------\033[0m")
        output.append(" Menu: [d] Default | [s] HW States | [h] Heatmap | [t] Timeline")
        output.append(" Comandi TUI: 'step' | 'rewind' | 'forward' | 'exit' (o Premi Invio per aggiornare)")
        output.append("\033[94m================================================================================\033[0m")

        return "\n".join(output)

    def run(self) -> None:
        """
        Avvia la visualizzazione interattiva della dashboard.
        """
        self.running = True

        while self.running:
            print(self.draw_dashboard())
            try:
                inp = input("\n(tui) ").strip().lower()
                if inp in ("exit", "quit", "q"):
                    self.running = False
                elif inp in ("d", "default"):
                    self.view_mode = "default"
                elif inp in ("s", "hw", "hw_state"):
                    self.view_mode = "hw_state"
                elif inp in ("h", "heatmap"):
                    self.view_mode = "heatmap"
                    self.heatmap.enabled = True
                elif inp in ("t", "timeline"):
                    self.view_mode = "timeline"
                    self.timeline.enabled = True
                elif inp == "step":
                    # Esegue lo step dall'interfaccia TUI
                    regs = self.bridge.step_instruction()
                    pc = regs.get("PC", 0)
                    if self.heatmap.enabled:
                        self.heatmap.record_access(pc, 'X')
                    if self.timeline.enabled:
                        try:
                            ram = self.bridge.read_memory(0, 0xFFFF)
                            if len(ram) == 65536:
                                self.timeline.record_state(ram, regs)
                        except Exception:
                            pass
                elif inp == "rewind":
                    if self.timeline.enabled:
                        state = self.timeline.rewind(1)
                        if state:
                            self.bridge.write_memory(0, state["ram"])
                            self.bridge.write_registers(state["registers"])
                elif inp == "forward":
                    if self.timeline.enabled:
                        state = self.timeline.forward(1)
                        if state:
                            self.bridge.write_memory(0, state["ram"])
                            self.bridge.write_registers(state["registers"])
            except (KeyboardInterrupt, EOFError):
                self.running = False
                print()
