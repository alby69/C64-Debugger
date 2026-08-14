import pytest
from unittest.mock import MagicMock
from c64debugger.cli.repl import C64DebuggerREPL

def test_repl_hardware_state_commands():
    mock_bridge = MagicMock()
    mock_bridge.read_memory.side_effect = lambda start, end: bytes([0] * (end - start + 1))

    repl = C64DebuggerREPL(mock_bridge=mock_bridge)

    # Test vic_state
    repl.onecmd("vic_state")
    mock_bridge.read_memory.assert_any_call(0xD000, 0xD02E)

    # Test sid_state
    repl.onecmd("sid_state")
    mock_bridge.read_memory.assert_any_call(0xD400, 0xD41C)

    # Test cia_state
    repl.onecmd("cia_state")
    mock_bridge.read_memory.assert_any_call(0xDC00, 0xDC0F)
    mock_bridge.read_memory.assert_any_call(0xDD00, 0xDD0F)

def test_repl_heatmap_commands():
    mock_bridge = MagicMock()
    mock_bridge.read_memory.return_value = bytes([0] * 256)
    mock_bridge.get_registers.return_value = {"PC": 0xC000}

    repl = C64DebuggerREPL(mock_bridge=mock_bridge)

    # Check default status
    repl.onecmd("heatmap")
    assert not repl.heatmap.enabled

    # Turn on
    repl.onecmd("heatmap on")
    assert repl.heatmap.enabled

    # Turn off
    repl.onecmd("heatmap off")
    assert not repl.heatmap.enabled

    # Show
    repl.onecmd("heatmap show $C000 256")
    mock_bridge.read_memory.assert_any_call(0xC000, 0xC0FF)

    # Reset
    repl.onecmd("heatmap reset")

def test_repl_timeline_commands():
    mock_bridge = MagicMock()
    mock_bridge.read_memory.return_value = bytes([0] * 65536)
    mock_bridge.get_registers.return_value = {"PC": 0xC000, "A": 1}

    repl = C64DebuggerREPL(mock_bridge=mock_bridge)

    # Check default status
    repl.onecmd("timeline_status")
    assert not repl.timeline.enabled

    # Enable
    repl.onecmd("timeline_status enable")
    assert repl.timeline.enabled
    assert len(repl.timeline.snapshots) == 1

    # Step to record states
    mock_bridge.step_instruction.return_value = {"PC": 0xC001, "A": 2}
    repl.onecmd("step")
    assert len(repl.timeline.snapshots) == 2

    # Rewind
    repl.onecmd("rewind")
    assert repl.timeline.current_index == 0
    mock_bridge.write_memory.assert_called()
    mock_bridge.write_registers.assert_called_with({"PC": 0xC000, "A": 1})

    # Forward
    repl.onecmd("forward")
    assert repl.timeline.current_index == 1

    # Backstep
    repl.onecmd("backstep")
    assert repl.timeline.current_index == 0

    # Disable
    repl.onecmd("timeline_status disable")
    assert not repl.timeline.enabled

    # Reset
    repl.onecmd("timeline_status reset")
    assert len(repl.timeline.snapshots) == 0
