from dataclasses import dataclass
from typing import List, Optional

@dataclass
class StackFrame:
    """
    Rappresentazione di un record di attivazione (frame di stack) 6502.
    """
    stack_address: int  # Indirizzo in pagina 1 (es. $01FC)
    raw_bytes: bytes    # I 2 byte letti dallo stack (low, high)
    return_address: int # L'indirizzo di ritorno ricostruito (raw_val + 1)

    def __str__(self) -> str:
        return f"${self.stack_address:04X}: Return to ${self.return_address:04X} (Bytes: {self.raw_bytes.hex().upper()})"


def reconstruct_stack_trace(
    stack_page_bytes: bytes,
    sp: int,
    full_memory: Optional[bytes] = None,
    min_valid_address: int = 0x0800
) -> List[StackFrame]:
    """
    Analizza i byte della pagina 1 dello stack ($0100 - $01FF) e ricostruisce i possibili indirizzi di ritorno.

    Args:
        stack_page_bytes: Array di 256 byte corrispondenti alla pagina 1 ($0100-$01FF).
        sp: Valore attuale dello Stack Pointer (0x00 - 0xFF).
        full_memory: Opzionale. Se fornito, verifica se l'istruzione precedente all'indirizzo di ritorno
                     è effettivamente un JSR (opcode $20) per eliminare i falsi positivi.
        min_valid_address: Indirizzo minimo accettabile come valido indirizzo di ritorno (default $0800 per C64).

    Returns:
        Lista di StackFrame ordinati dal frame più recente (SP più basso) a quello più vecchio.
    """
    if len(stack_page_bytes) != 256:
        raise ValueError("L'array dei byte dello stack deve essere esattamente di 256 byte.")

    frames = []

    # Lo stack pointer punta alla prossima cella libera.
    # Gli elementi attivi sono quindi da sp + 1 fino a 0xFF.
    curr = (sp + 1) & 0xFF

    while curr < 0xFF:
        low_byte = stack_page_bytes[curr]
        high_byte = stack_page_bytes[curr + 1]

        # L'indirizzo memorizzato sullo stack da JSR è PC - 1.
        # Quindi l'indirizzo di ritorno effettivo è (high << 8 | low) + 1.
        raw_addr = (high_byte << 8) | low_byte
        return_addr = (raw_addr + 1) & 0xFFFF

        # 1. Verifica JSR se full_memory è disponibile
        is_valid = False
        if return_addr >= min_valid_address:
            if full_memory is not None:
                # L'istruzione JSR ha lunghezza 3 byte, quindi l'opcode JSR ($20) si trova a return_addr - 3
                jsr_op_addr = return_addr - 3
                if 0 <= jsr_op_addr < len(full_memory):
                    is_valid = (full_memory[jsr_op_addr] == 0x20)
            else:
                # Heuristic fallback based on address range
                is_valid = True

        if is_valid:
            frames.append(StackFrame(
                stack_address=0x0100 + curr,
                raw_bytes=bytes([low_byte, high_byte]),
                return_address=return_addr
            ))
            # Avanziamo di 2 byte per questo frame JSR
            curr += 2
        else:
            # Se non sembra un indirizzo di ritorno valido, potrebbe essere un PHA/PHP di un singolo byte,
            # avanziamo solo di 1 per riallinearci eventualmente su coppie JSR successive
            curr += 1

    return frames
