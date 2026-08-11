import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class Instruction:
    """
    Rappresentazione strutturata di un'istruzione assembly 6502.
    """
    address: int
    bytes_data: bytes
    mnemonic: str
    operand: str
    addressing_mode: str
    raw_line: str

    def __str__(self) -> str:
        operand_part = f" {self.operand}" if self.operand else ""
        return f"${self.address:04X}: {self.mnemonic}{operand_part} ({self.addressing_mode})"


class VICEDisassemblerParser:
    """
    Parser per l'output di disassembly del monitor VICE.
    """

    # Regex per catturare: indirizzo, byte (1-3), mnemonic (3 caratteri o ???), operando (opzionale)
    # Esempio: .c000  a9 01         LDA #$01
    LINE_PATTERN = re.compile(
        r'^\.([0-9a-fA-F]{4})\s+((?:[0-9a-fA-F]{2}\s+){1,3}|(?:[0-9a-fA-F]{2}){1,3})\s*([a-zA-Z?*]{3})\s*(.*)$'
    )

    @staticmethod
    def determine_addressing_mode(mnemonic: str, operand: str) -> str:
        """
        Determina l'addressing mode del 6502 basandosi sul mnemonic e sull'operando.
        """
        mnemonic = mnemonic.upper()
        operand = operand.strip()

        # Se non c'è operando
        if not operand:
            if mnemonic in {"ASL", "LSR", "ROL", "ROR", "DEC", "INC"}:
                return "Implied" # o Accumulator, di default usiamo Implied se non esplicitato con 'A'
            return "Implied"

        if operand == "A" or operand == "a":
            return "Accumulator"

        # Immediato: #$01, #12, #$FF
        if operand.startswith("#"):
            return "Immediate"

        # Indiretto e sue varianti
        # ($12,X) -> Indexed Indirect
        # ($12),Y -> Indirect Indexed
        # ($1234) -> Indirect
        if operand.startswith("(") and operand.endswith(")"):
            inner = operand[1:-1].strip()
            if inner.upper().endswith(",X"):
                return "Indexed Indirect"
            return "Indirect"

        if operand.startswith("(") and operand.upper().endswith("),Y"):
            return "Indirect Indexed"

        # Relativo (istruzioni di branch come BNE, BEQ, BCC, etc.)
        if mnemonic in {"BPL", "BMI", "BVC", "BVS", "BCC", "BCS", "BNE", "BEQ"}:
            return "Relative"

        # Ora gestiamo Absolute vs Zero Page, anche indicizzati con ,X o ,Y
        has_x = operand.upper().endswith(",X")
        has_y = operand.upper().endswith(",Y")

        # Estraiamo l'eventuale valore esadecimale (es: $FF o $C000)
        hex_match = re.search(r'\$([0-9a-fA-F]+)', operand)
        if hex_match:
            hex_val = hex_match.group(1)
            is_zp = len(hex_val) <= 2
            if is_zp:
                if has_x:
                    return "Zero Page,X"
                if has_y:
                    return "Zero Page,Y"
                return "Zero Page"
            else:
                if has_x:
                    return "Absolute,X"
                if has_y:
                    return "Absolute,Y"
                return "Absolute"

        # Fallback nel caso in cui non ci sia il prefisso $ ma ci sia indicizzazione
        if has_x:
            return "Absolute,X"
        if has_y:
            return "Absolute,Y"

        return "Absolute"

    @classmethod
    def parse_line(cls, line: str) -> Optional[Instruction]:
        """
        Analizza una singola riga di disassembly VICE e restituisce un oggetto Instruction.
        Ritorna None se la riga non corrisponde al formato previsto.
        """
        line_clean = line.strip()
        match = cls.LINE_PATTERN.match(line_clean)
        if not match:
            # Proviamo una regex più tollerante per istruzioni speciali o sconosciute
            # ad es. se mancano byte o l'operando è strano
            fallback_pattern = re.compile(r'^\.([0-9a-fA-F]{4})\s+([0-9a-fA-F\s]+)\s+([a-zA-Z?*]{3})\s*(.*)$')
            match = fallback_pattern.match(line_clean)
            if not match:
                return None

        addr_str, bytes_str, mnemonic_str, operand_str = match.groups()

        # Pulizia dell'indirizzo
        address = int(addr_str, 16)

        # Pulizia e parsing dei byte macchina
        byte_parts = bytes_str.strip().split()
        if not byte_parts:
            # Se split vuoto, potrebbe essere una stringa di byte contigui (es: "a901")
            clean_bytes_str = bytes_str.replace(" ", "")
            byte_parts = [clean_bytes_str[i:i+2] for i in range(0, len(clean_bytes_str), 2)]

        try:
            bytes_data = bytes(int(b, 16) for b in byte_parts if b)
        except ValueError:
            return None

        mnemonic = mnemonic_str.strip()
        operand = operand_str.strip()

        # Se c'è un commento inline, separiamolo dall'operando
        if ";" in operand:
            operand, _ = operand.split(";", 1)
            operand = operand.strip()

        addressing_mode = cls.determine_addressing_mode(mnemonic, operand)

        return Instruction(
            address=address,
            bytes_data=bytes_data,
            mnemonic=mnemonic,
            operand=operand,
            addressing_mode=addressing_mode,
            raw_line=line
        )

    @classmethod
    def parse_disassembly(cls, response: str) -> List[Instruction]:
        """
        Analizza un blocco di testo multilinea di disassembly restituito da VICE.
        """
        instructions = []
        for line in response.splitlines():
            instr = cls.parse_line(line)
            if instr:
                instructions.append(instr)
        return instructions
