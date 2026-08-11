import pytest
from c64debugger.disasm.memory_map import C64MemoryMap

def test_get_region_info():
    info_zp = C64MemoryMap.get_region_info(0x0050)
    assert info_zp["name"] == "Zero Page"
    assert "RAM ad accesso rapido" in info_zp["description"]

    info_vic = C64MemoryMap.get_region_info(0xD011)
    assert info_vic["name"] == "VIC-II I/O"

    info_kernal = C64MemoryMap.get_region_info(0xF000)
    assert info_kernal["name"] == "KERNAL ROM / RAM"

def test_format_memory_with_annotations():
    data = bytes([0x01, 0x02, 0x03, 0x04])
    formatted = C64MemoryMap.format_memory_with_annotations(0xC000, data, bytes_per_line=4)
    assert len(formatted) == 1
    assert "$C000:" in formatted[0]
    assert "01 02 03 04" in formatted[0]
    assert "[User RAM]" in formatted[0]
