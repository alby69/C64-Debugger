import os
import pytest
from unittest.mock import MagicMock
from c64debugger.cli.repl import C64DebuggerREPL

def test_repl_symbol_integration(tmp_path):
    mock_bridge = MagicMock()
    mock_bridge.read_memory.return_value = bytes([0xEA, 0xEA, 0x60])

    repl = C64DebuggerREPL(mock_bridge=mock_bridge)

    # 1. Define and load symbols
    symbols_file = tmp_path / "symbols.lbl"
    symbols_file.write_text("my_start = $C000\nmy_loop = $C002", encoding="utf-8")

    # Command to load symbols
    repl.onecmd(f"load_symbols {symbols_file}")
    assert repl.symbol_manager.get_address("my_start") == 0xC000
    assert repl.symbol_manager.get_address("my_loop") == 0xC002

    # 2. Set breakpoint using a symbol
    repl.onecmd("break my_start")
    assert 0xC000 in repl.core.breakpoints
    mock_bridge.set_breakpoint.assert_called_with(0xC000)

    # 3. Examine memory using a symbol
    repl.onecmd("x my_start 3")
    mock_bridge.read_memory.assert_called_with(0xC000, 0xC002)

    # 4. Set watchpoint using a symbol
    repl.onecmd("watch my_loop")
    assert 0xC002 in repl.core.watchpoints

    # 5. Autocomplete suggestions for symbols
    comp_b = repl.complete_break("my_", "break my_", 6, 9)
    assert "my_start" in comp_b
    assert "my_loop" in comp_b

    comp_x = repl.complete_x("my_s", "x my_s", 2, 6)
    assert comp_x == ["my_start"]

def test_repl_session_and_snapshot_commands(tmp_path):
    mock_bridge = MagicMock()
    mock_bridge.read_memory.return_value = bytes([0x12, 0x34, 0x56])

    repl = C64DebuggerREPL(mock_bridge=mock_bridge)

    # Configure some breakpoint and symbols in REPL
    repl.symbol_manager.add_symbol("test_addr", 0xC000)
    repl.onecmd("break test_addr")

    session_file = tmp_path / "session.c64dbg"
    snapshot_file = tmp_path / "snapshot.bin"

    # Save session command
    repl.onecmd(f"save_session {session_file}")
    assert os.path.exists(session_file)

    # Clear current breakpoints in core
    repl.core.breakpoints.clear()
    assert 0xC000 not in repl.core.breakpoints

    # Load session command
    mock_bridge.reset_mock()
    repl.onecmd(f"load_session {session_file}")
    assert 0xC000 in repl.core.breakpoints
    mock_bridge.set_breakpoint.assert_called_with(0xC000)

    # Save snapshot command
    repl.onecmd(f"save_snapshot {snapshot_file}")
    assert os.path.exists(snapshot_file)
    mock_bridge.read_memory.assert_called()

    # Load snapshot command
    mock_bridge.reset_mock()
    repl.onecmd(f"load_snapshot {snapshot_file}")
    mock_bridge.write_memory.assert_called_with(0x0000, bytes([0x12, 0x34, 0x56]))
