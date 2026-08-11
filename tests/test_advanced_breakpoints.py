import pytest
from c64debugger.debugger_core import C64DebuggerCore

def test_conditional_breakpoints():
    core = C64DebuggerCore()
    # Adding a conditional breakpoint
    core.add_conditional_breakpoint(0xC000, "A == 0xFF")

    # Check execution
    regs = {"PC": 0xC000, "A": 0x00}
    assert not core.should_stop(0xC000, regs)

    regs = {"PC": 0xC000, "A": 0xFF}
    assert core.should_stop(0xC000, regs)

def test_complex_eval_conditions():
    core = C64DebuggerCore()
    regs = {"A": 0x10, "X": 0x20, "Y": 0x00}

    assert core.eval_condition("A == $10", regs)
    assert core.eval_condition("X >= 0x10", regs)
    assert core.eval_condition("Y == 0", regs)
    assert not core.eval_condition("A == 0", regs)

def test_hit_count_breakpoints():
    core = C64DebuggerCore()
    core.add_hit_count_breakpoint(0xC010, 3)

    regs = {"PC": 0xC010}

    # 1st hit -> do not stop
    assert not core.should_stop(0xC010, regs)
    # 2nd hit -> do not stop
    assert not core.should_stop(0xC010, regs)
    # 3rd hit -> stop!
    assert core.should_stop(0xC010, regs)
    # 4th hit -> stop! (or subsequent)
    assert core.should_stop(0xC010, regs)

def test_watchpoint_ranges():
    core = C64DebuggerCore()
    core.add_watchpoint_range(0x400, 0x7FF)

    # Watchpoint inside range triggered
    assert core.check_watchpoint_trigger(0x500, 0x11, 0x22)
    # Watchpoint outside range not triggered
    assert not core.check_watchpoint_trigger(0xC000, 0x11, 0x22)
    # No change -> not triggered
    assert not core.check_watchpoint_trigger(0x500, 0x11, 0x11)

def test_io_breakpoints():
    core = C64DebuggerCore()
    core.add_io_breakpoint("VIC")
    core.add_io_breakpoint("SID")

    assert core.check_io_access(0xD011) == "VIC"
    assert core.check_io_access(0xD400) == "SID"
    assert core.check_io_access(0xC000) is None

    core.remove_io_breakpoint("VIC")
    assert core.check_io_access(0xD011) is None
