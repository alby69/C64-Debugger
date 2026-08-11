import pytest
from unittest.mock import MagicMock
from c64debugger.cli.repl import C64DebuggerREPL

def test_repl_commands():
    # Setup mock bridge
    mock_bridge = MagicMock()
    mock_bridge.step_instruction.return_value = {"PC": 0xC001, "A": 0xFF, "X": 0x00, "Y": 0x00, "SP": 0xFD}
    mock_bridge.get_registers.return_value = {"PC": 0xC000, "A": 0x00, "X": 0x12, "Y": 0x34, "SP": 0xFD}
    mock_bridge.read_memory.return_value = bytes([0xA9, 0x01, 0xEA])

    repl = C64DebuggerREPL(mock_bridge=mock_bridge)

    # Test break command (with conditional and hit count)
    repl.onecmd("break $C000")
    assert 0xC000 in repl.core.breakpoints
    mock_bridge.set_breakpoint.assert_called_with(0xC000)

    repl.onecmd("break $C002 if A == 0x50")
    assert 0xC002 in repl.core.breakpoints
    assert repl.core.breakpoint_conditions[0xC002] == "A == 0x50"

    repl.onecmd("break $C004 hit 3")
    assert 0xC004 in repl.core.breakpoints
    assert repl.core.hit_count_limits[0xC004] == 3

    # Test step command
    repl.onecmd("step")
    mock_bridge.step_instruction.assert_called_once()

    # Test continue command
    repl.onecmd("continue")
    mock_bridge.resume_execution.assert_called_once()

    # Test examine memory command
    repl.onecmd("x $C000 3")
    mock_bridge.read_memory.assert_called_with(0xC000, 0xC002)

    # Test profile commands
    repl.onecmd("profile start")
    assert repl.profiler.is_running
    repl.onecmd("profile stop")
    assert not repl.profiler.is_running

def test_repl_info_commands():
    mock_bridge = MagicMock()
    mock_bridge.get_registers.return_value = {"PC": 0xC000, "A": 0x00, "X": 0x12, "Y": 0x34, "SP": 0xFD}

    repl = C64DebuggerREPL(mock_bridge=mock_bridge)

    # Run info commands
    repl.onecmd("info registers")
    repl.onecmd("info break")
    repl.onecmd("info memory")
    repl.onecmd("info profiler")

    mock_bridge.get_registers.assert_called()

def test_repl_completions():
    mock_bridge = MagicMock()
    repl = C64DebuggerREPL(mock_bridge=mock_bridge)

    # Test completions
    comp_info = repl.complete_info("reg", "info reg", 5, 8)
    assert "registers" in comp_info

    comp_profile = repl.complete_profile("sta", "profile sta", 8, 11)
    assert "start" in comp_profile
