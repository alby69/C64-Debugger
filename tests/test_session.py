import os
import pytest
from unittest.mock import MagicMock
from c64debugger.debugger_core import C64DebuggerCore
from c64debugger.session import C64SessionManager, C64SnapshotManager

def test_session_save_load(tmp_path):
    core = C64DebuggerCore()

    # Configure initial core state
    core.add_breakpoint(0xC000)
    core.add_conditional_breakpoint(0xC010, "A == 0xFF")
    core.add_hit_count_breakpoint(0xC020, 5)
    core.add_watchpoint(0x1000)
    core.add_watchpoint_range(0x2000, 0x20FF)
    core.add_io_breakpoint("VIC")

    session_file = tmp_path / "test_session.c64dbg"
    symbols_path = "/path/to/my_symbols.lbl"

    # Save session
    success = C64SessionManager.save_session(str(session_file), core, symbols_path)
    assert success
    assert os.path.exists(session_file)

    # Create new blank core and restore
    new_core = C64DebuggerCore()
    data = C64SessionManager.load_session(str(session_file), new_core)

    # Verify restored state
    assert data["version"] == "0.5.0"
    assert data["loaded_symbols_path"] == symbols_path

    assert 0xC000 in new_core.breakpoints
    assert 0xC010 in new_core.breakpoints
    assert new_core.breakpoint_conditions[0xC010] == "A == 0xFF"

    assert 0xC020 in new_core.breakpoints
    assert new_core.hit_count_limits[0xC020] == 5

    assert 0x1000 in new_core.watchpoints
    assert (0x2000, 0x20FF) in new_core.watchpoint_ranges
    assert "VIC" in new_core.io_breakpoints
    assert new_core.io_breakpoints["VIC"] == (0xD000, 0xD3FF)

def test_snapshot_save_load(tmp_path):
    mock_bridge = MagicMock()
    mock_bridge.read_memory.return_value = bytes([0x11, 0x22, 0x33, 0x44])

    snapshot_file = tmp_path / "test_ram.bin"

    # Save snapshot
    success = C64SnapshotManager.save_ram_snapshot(str(snapshot_file), mock_bridge, start_addr=0xC000, end_addr=0xC003)
    assert success
    assert os.path.exists(snapshot_file)
    mock_bridge.read_memory.assert_called_with(0xC000, 0xC003)

    # Check contents
    with open(snapshot_file, "rb") as f:
        content = f.read()
    assert content == bytes([0x11, 0x22, 0x33, 0x44])

    # Load snapshot
    mock_bridge.reset_mock()
    success = C64SnapshotManager.load_ram_snapshot(str(snapshot_file), mock_bridge, start_addr=0xC000)
    assert success
    mock_bridge.write_memory.assert_called_with(0xC000, bytes([0x11, 0x22, 0x33, 0x44]))
