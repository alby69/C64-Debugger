import os
import pytest
from c64debugger.symbols.symbol_manager import C64SymbolManager

def test_symbol_manager_basic():
    mgr = C64SymbolManager()
    assert mgr.get_address("start") is None
    assert mgr.get_symbols(0xC000) == []

    mgr.add_symbol("start", 0xC000)
    assert mgr.get_address("start") == 0xC000
    assert mgr.get_symbols(0xC000) == ["start"]

    mgr.add_symbol("init", 0xC000)
    assert mgr.get_address("init") == 0xC000
    # Both names should be associated with the address
    assert sorted(mgr.get_symbols(0xC000)) == ["init", "start"]

    assert mgr.all_symbols() == {"start": 0xC000, "init": 0xC000}

    mgr.clear()
    assert mgr.get_address("start") is None
    assert mgr.get_symbols(0xC000) == []
    assert mgr.all_symbols() == {}

def test_acme_format_parsing(tmp_path):
    # Test ACME standard format and al format
    lbl_content = """
    ; ACME label file
    start_label = $C000
    al C:d020 .border_color
    al $C100 .play_routine
    """
    lbl_file = tmp_path / "acme.lbl"
    lbl_file.write_text(lbl_content, encoding="utf-8")

    mgr = C64SymbolManager()
    count = mgr.load_from_file(str(lbl_file))
    assert count == 3
    assert mgr.get_address("start_label") == 0xC000
    assert mgr.get_address("border_color") == 0xD020
    assert mgr.get_address("play_routine") == 0xC100

def test_kick_assembler_format_parsing(tmp_path):
    # Test KickAssembler format
    lbl_content = """
    // KickAssembler symbol file
    .label main_loop=$c000
    .label sprite_data=12288
    .label vector_flag = $10
    """
    lbl_file = tmp_path / "kick.vs"
    lbl_file.write_text(lbl_content, encoding="utf-8")

    mgr = C64SymbolManager()
    count = mgr.load_from_file(str(lbl_file))
    assert count == 3
    assert mgr.get_address("main_loop") == 0xC000
    assert mgr.get_address("sprite_data") == 12288  # 0x3000
    assert mgr.get_address("vector_flag") == 0x0010

def test_tmpx_format_parsing(tmp_path):
    # Test TMPx format (columns separation) and generic equals
    lbl_content = """
    ; TMPx format labels
    start_point $C000
    data_block 49152
    simple_var = $02
    """
    lbl_file = tmp_path / "tmpx.lbl"
    lbl_file.write_text(lbl_content, encoding="utf-8")

    mgr = C64SymbolManager()
    count = mgr.load_from_file(str(lbl_file))
    assert count == 3
    assert mgr.get_address("start_point") == 0xC000
    assert mgr.get_address("data_block") == 0xC000
    assert mgr.get_address("simple_var") == 0x0002

def test_load_non_existent_file():
    mgr = C64SymbolManager()
    with pytest.raises(FileNotFoundError):
        mgr.load_from_file("non_existent_file_xyz_123.lbl")
