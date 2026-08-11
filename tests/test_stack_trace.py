import pytest
from c64debugger.disasm import StackFrame, reconstruct_stack_trace

def test_stack_frame_string_representation():
    frame = StackFrame(
        stack_address=0x01FC,
        raw_bytes=bytes([0x02, 0xC0]),
        return_address=0xC003
    )
    assert str(frame) == "$01FC: Return to $C003 (Bytes: 02C0)"


def test_empty_stack():
    # An empty stack has SP pointing to 0xFF, meaning no active frames
    stack_data = bytearray(256)
    frames = reconstruct_stack_trace(bytes(stack_data), 0xFF)
    assert len(frames) == 0


def test_single_subroutine_call():
    # Supponiamo JSR a $C000 da un'istruzione a $C100
    # L'indirizzo di ritorno sarebbe $C103. Il valore memorizzato su stack è return_addr - 1 = $C102 (Low=$02, High=$C1)
    # Lo SP iniziale era $FD. Dopo il JSR, SP = $FB.
    # I byte sono scritti a SP+1 ($FC) e SP+2 ($FD).
    stack_data = bytearray(256)
    stack_data[0xFC] = 0x02
    stack_data[0xFD] = 0xC1

    frames = reconstruct_stack_trace(bytes(stack_data), 0xFB)
    assert len(frames) == 1
    assert frames[0].stack_address == 0x01FC
    assert frames[0].return_address == 0xC103
    assert frames[0].raw_bytes == b"\x02\xc1"


def test_multiple_nested_calls():
    # Tre chiamate annidate:
    # 1. JSR da $C100 (ritorno $C103, scrive $C102 a $01FD-$01FE) -> SP passa da $FF a $FD
    # 2. JSR da $C200 (ritorno $C203, scrive $C202 a $01FB-$01FC) -> SP passa da $FD a $FB
    # 3. JSR da $C300 (ritorno $C303, scrive $C302 a $01F9-$01FA) -> SP passa da $FB a $F9
    stack_data = bytearray(256)

    # Primo frame ($01FD-$01FE)
    stack_data[0xFD] = 0x02
    stack_data[0xFE] = 0xC1

    # Secondo frame ($01FB-$01FC)
    stack_data[0xFB] = 0x02
    stack_data[0xFC] = 0xC2

    # Terzo frame ($01F9-$01FA)
    stack_data[0xF9] = 0x02
    stack_data[0xFA] = 0xC3

    frames = reconstruct_stack_trace(bytes(stack_data), 0xF8)
    assert len(frames) == 3

    # L'ordine deve essere dal più recente al più vecchio (SP più basso a SP più alto)
    assert frames[0].stack_address == 0x01F9
    assert frames[0].return_address == 0xC303

    assert frames[1].stack_address == 0x01FB
    assert frames[1].return_address == 0xC203

    assert frames[2].stack_address == 0x01FD
    assert frames[2].return_address == 0xC103


def test_single_byte_pushes_on_stack():
    # Caso con push a singolo byte (es: PHA/PHP) intermezzati
    # JSR da $C100 -> Ritorno $C103, scrive $C102 a $01FD-$01FE, SP diventa $FD
    # PHA -> Scrive un byte (es: $55) a $01FC, SP diventa $FC
    # JSR da $C200 -> Ritorno $C203, scrive $C202 a $01FA-$01FB, SP diventa $FA
    stack_data = bytearray(256)

    # Primo JSR ($01FD-$01FE)
    stack_data[0xFD] = 0x02
    stack_data[0xFE] = 0xC1

    # PHA ($01FC)
    stack_data[0xFC] = 0x55

    # Secondo JSR ($01FA-$01FB)
    stack_data[0xFA] = 0x02
    stack_data[0xFB] = 0xC2

    frames = reconstruct_stack_trace(bytes(stack_data), 0xF9)
    assert len(frames) == 2

    # Primo frame rilevato (più recente)
    assert frames[0].stack_address == 0x01FA
    assert frames[0].return_address == 0xC203

    # Secondo frame rilevato
    assert frames[1].stack_address == 0x01FD
    assert frames[1].return_address == 0xC103


def test_full_memory_jsr_validation():
    # Test che l'opzione full_memory escluda indirizzi non preceduti da JSR (opcode $20)
    # Impostiamo una finta memoria C64 di 64KB
    memory = bytearray(65536)

    # All'indirizzo $C100 c'è un JSR ($20) a qualche subroutine, che ritorna a $C103
    # Quindi a $C100 (return_addr - 3) scriviamo 0x20
    memory[0xC100] = 0x20

    # Abbiamo anche un altro frame candidato sul finto stack che punta a $D003.
    # Ma a $D000 NON c'è un JSR, scriviamo NOP ($EA) per simulare un falso positivo
    memory[0xD000] = 0xEA

    stack_data = bytearray(256)

    # Frame 1: Ritorno $C103 (scrive $C102 a $01FD-$01FE)
    stack_data[0xFD] = 0x02
    stack_data[0xFE] = 0xC1

    # Frame 2: Ritorno $D003 (scrive $D002 a $01FB-$01FC)
    stack_data[0xFB] = 0x02
    stack_data[0xFC] = 0xD0

    # Chiamiamo con full_memory fornito
    frames = reconstruct_stack_trace(bytes(stack_data), 0xFA, full_memory=bytes(memory))

    # Solo Frame 1 deve essere valido, Frame 2 viene scartato perché non preceduto da JSR ($20)
    assert len(frames) == 1
    assert frames[0].return_address == 0xC103


def test_corrupted_or_invalid_inputs():
    # Test che l'input non sia di lunghezza errata
    with pytest.raises(ValueError):
        reconstruct_stack_trace(b"\x00\x00", 0xFD)
