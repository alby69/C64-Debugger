import os
import pytest
from c64debugger.sourcemap import KickAssDbgParser

def test_kickass_dbg_parser_basic(tmp_path):
    dbg_content = """<?xml version="1.0" encoding="UTF-8"?>
    <debuginfo>
        <sources>
            <source id="0" filepath="main.asm" filename="main.asm" />
            <source id="1" filepath="utils.asm" filename="utils.asm" />
        </sources>
        <sourceinfo>
            <line fileid="0" line="10" startaddress="$C000" endaddress="$C002" />
            <line fileid="0" line="11" startaddress="49155" endaddress="49156" />
            <line fileid="1" line="42" startadd="$1000" endadd="$1005" />
        </sourceinfo>
        <labels>
            <label name="init" address="$C000" />
            <label name="loop" address="49155" />
        </labels>
    </debuginfo>
    """
    dbg_file = tmp_path / "test.dbg"
    dbg_file.write_text(dbg_content, encoding="utf-8")

    parser = KickAssDbgParser()
    success = parser.load_dbg(str(dbg_file))
    assert success is True
    assert parser.loaded_filepath == str(dbg_file)

    res1 = parser.get_source_line(0xC001)
    assert res1 is not None
    filepath, line_num = res1
    assert filepath == "main.asm"
    assert line_num == 10

    res2 = parser.get_source_line(49156)
    assert res2 == ("main.asm", 11)

    res3 = parser.get_source_line(0x1003)
    assert res3 == ("utils.asm", 42)

    assert parser.get_address_for_line("main.asm", 10) == 0xC000
    assert parser.get_address_for_line("main.asm", 11) == 0xC003
    assert parser.get_address_for_line("utils.asm", 42) == 0x1000

    assert parser.labels["init"] == 0xC000
    assert parser.labels["loop"] == 0xC003

    with pytest.raises(FileNotFoundError):
        parser.load_dbg("non_existent_dbg_file.dbg")
