import pytest
from c64debugger.disasm import Instruction, VICEDisassemblerParser

def test_instruction_string_representation():
    instr = Instruction(
        address=0xC000,
        bytes_data=bytes([0xA9, 0x01]),
        mnemonic="LDA",
        operand="#$01",
        addressing_mode="Immediate",
        raw_line=".c000  a9 01         LDA #$01"
    )
    assert str(instr) == "$C000: LDA #$01 (Immediate)"

    instr_implied = Instruction(
        address=0xC002,
        bytes_data=bytes([0xEA]),
        mnemonic="NOP",
        operand="",
        addressing_mode="Implied",
        raw_line=".c002  ea            NOP"
    )
    assert str(instr_implied) == "$C002: NOP (Implied)"


def test_parse_standard_instructions():
    # Immediate
    line_imm = ".c000  a9 01         LDA #$01"
    instr = VICEDisassemblerParser.parse_line(line_imm)
    assert instr is not None
    assert instr.address == 0xC000
    assert instr.bytes_data == b"\xa9\x01"
    assert instr.mnemonic == "LDA"
    assert instr.operand == "#$01"
    assert instr.addressing_mode == "Immediate"

    # Absolute
    line_abs = ".c123  ad 34 12      LDA $1234"
    instr = VICEDisassemblerParser.parse_line(line_abs)
    assert instr is not None
    assert instr.address == 0xC123
    assert instr.bytes_data == b"\xad\x34\x12"
    assert instr.mnemonic == "LDA"
    assert instr.operand == "$1234"
    assert instr.addressing_mode == "Absolute"

    # Implied / Accumulator
    line_imp = ".c010  0a            ASL A"
    instr = VICEDisassemblerParser.parse_line(line_imp)
    assert instr is not None
    assert instr.address == 0xC010
    assert instr.bytes_data == b"\x0a"
    assert instr.mnemonic == "ASL"
    assert instr.operand == "A"
    assert instr.addressing_mode == "Accumulator"

    # Indirect Indexed
    line_ind_y = ".c020  b1 12         LDA ($12),Y"
    instr = VICEDisassemblerParser.parse_line(line_ind_y)
    assert instr is not None
    assert instr.address == 0xC020
    assert instr.bytes_data == b"\xb1\x12"
    assert instr.mnemonic == "LDA"
    assert instr.operand == "($12),Y"
    assert instr.addressing_mode == "Indirect Indexed"


def test_parse_comments_in_line():
    line_comment = ".c000  a9 01         LDA #$01       ; Set register A to 1"
    instr = VICEDisassemblerParser.parse_line(line_comment)
    assert instr is not None
    assert instr.operand == "#$01"


def test_parse_disassembly_block():
    block = """
.c000  a9 01         LDA #$01
.c002  8d 00 04      STA $0400
.c005  60            RTS
"""
    instructions = VICEDisassemblerParser.parse_disassembly(block)
    assert len(instructions) == 3
    assert instructions[0].mnemonic == "LDA"
    assert instructions[1].mnemonic == "STA"
    assert instructions[2].mnemonic == "RTS"


def test_invalid_lines():
    assert VICEDisassemblerParser.parse_line("") is None
    assert VICEDisassemblerParser.parse_line("This is not disassembly") is None
    # Invalid hex bytes
    assert VICEDisassemblerParser.parse_line(".c000  zz 01         LDA #$01") is None


def test_addressing_modes():
    # Relative
    assert VICEDisassemblerParser.determine_addressing_mode("BNE", "$c000") == "Relative"
    # Zero Page vs Absolute
    assert VICEDisassemblerParser.determine_addressing_mode("LDA", "$12") == "Zero Page"
    assert VICEDisassemblerParser.determine_addressing_mode("LDA", "$12,X") == "Zero Page,X"
    assert VICEDisassemblerParser.determine_addressing_mode("LDX", "$12,Y") == "Zero Page,Y"
    assert VICEDisassemblerParser.determine_addressing_mode("LDA", "$1234") == "Absolute"
    assert VICEDisassemblerParser.determine_addressing_mode("LDA", "$1234,X") == "Absolute,X"
    assert VICEDisassemblerParser.determine_addressing_mode("LDX", "$1234,Y") == "Absolute,Y"

    # Indirect / Indexed Indirect
    assert VICEDisassemblerParser.determine_addressing_mode("JMP", "($1234)") == "Indirect"
    assert VICEDisassemblerParser.determine_addressing_mode("LDA", "($12,X)") == "Indexed Indirect"

    # Implied fallback
    assert VICEDisassemblerParser.determine_addressing_mode("ASL", "") == "Implied"
    assert VICEDisassemblerParser.determine_addressing_mode("NOP", "") == "Implied"
