import pytest
from unittest.mock import MagicMock, patch
from c64debugger.xref import XRefDatabase
from c64debugger.cli.repl import C64DebuggerREPL

def test_xref_database_basic():
    db = XRefDatabase()

    db.record_access(0xC000, 0xC100, "R")
    db.record_access(0xC000, 0xC200, "W")
    db.record_access(0xC001, 0xC100, "X")

    refs_c000 = db.get_references(0xC000)
    assert len(refs_c000) == 2
    assert refs_c000[0]["pc"] == 0xC100
    assert refs_c000[0]["type"] == "R"
    assert refs_c000[1]["pc"] == 0xC200
    assert refs_c000[1]["type"] == "W"

    refs_c001 = db.get_references(0xC001)
    assert len(refs_c001) == 1
    assert refs_c001[0]["pc"] == 0xC100
    assert refs_c001[0]["type"] == "X"

    db.record_access(0xC001, 0xC100, "X")
    assert len(db.get_references(0xC001)) == 1

    db.clear()
    assert len(db.get_references(0xC000)) == 0

def test_repl_xref_tracking():
    mock_bridge = MagicMock()
    mock_bridge.step_instruction.return_value = {"PC": 0xC000, "A": 0, "X": 0, "Y": 0, "SP": 0xFD}
    mock_bridge.send_command.return_value = ".c000  ad 00 c1         LDA $C100"

    repl = C64DebuggerREPL(mock_bridge=mock_bridge)

    repl.onecmd("step")

    refs_execute = repl.xref_db.get_references(0xC000)
    assert len(refs_execute) >= 1
    assert refs_execute[0]["type"] == "X"

    refs_execute_1 = repl.xref_db.get_references(0xC001)
    assert len(refs_execute_1) >= 1
    assert refs_execute_1[0]["type"] == "X"

    refs_read = repl.xref_db.get_references(0xC100)
    assert len(refs_read) == 1
    assert refs_read[0]["type"] == "R"
    assert refs_read[0]["pc"] == 0xC000

    with patch("builtins.print") as mock_print:
        repl.onecmd("xref $C100")
        mock_print.assert_any_call("--- CROSS-REFERENCES PER $C100 ---")
