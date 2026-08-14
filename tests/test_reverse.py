from c64debugger.reverse.timeline_engine import TimelineEngine

def test_timeline_basic():
    engine = TimelineEngine(max_snapshots=5)
    assert engine.enabled is False

    ram = b"\xa9\x01" + b"\x00" * 65534
    regs = {"PC": 0xC000, "A": 1, "X": 0, "Y": 0, "SP": 0xFD}

    # Recording when disabled does nothing
    engine.record_state(ram, regs)
    assert len(engine.snapshots) == 0

    engine.enabled = True
    # Record 3 states
    engine.record_state(ram, regs)
    regs2 = regs.copy()
    regs2["PC"] = 0xC002
    regs2["A"] = 2
    engine.record_state(ram, regs2)
    regs3 = regs.copy()
    regs3["PC"] = 0xC003
    regs3["A"] = 3
    engine.record_state(ram, regs3)

    assert len(engine.snapshots) == 3
    assert engine.current_index == 2

    # Rewind
    state = engine.rewind(1)
    assert state is not None
    assert state["registers"]["PC"] == 0xC002
    assert engine.current_index == 1

    # Rewind more
    state = engine.rewind(1)
    assert state["registers"]["PC"] == 0xC000
    assert engine.current_index == 0

    # Cannot rewind beyond 0
    state = engine.rewind(1)
    assert state["registers"]["PC"] == 0xC000
    assert engine.current_index == 0

    # Forward
    state = engine.forward(1)
    assert state["registers"]["PC"] == 0xC002
    assert engine.current_index == 1

    # Record new state from middle (clears future alternative path)
    regs4 = regs.copy()
    regs4["PC"] = 0xC005
    engine.record_state(ram, regs4)
    assert len(engine.snapshots) == 3  # state 3 is replaced by state 4
    assert engine.current_index == 2
    assert engine.snapshots[2]["registers"]["PC"] == 0xC005


def test_timeline_ring_buffer():
    engine = TimelineEngine(max_snapshots=3)
    engine.enabled = True
    ram = b"\x00" * 65536
    regs = {"PC": 0xC000}

    for i in range(5):
        regs_copy = regs.copy()
        regs_copy["PC"] = 0xC000 + i
        engine.record_state(ram, regs_copy)

    assert len(engine.snapshots) == 3
    # Check that older states (PC=C000, C001) were popped out
    assert engine.snapshots[0]["registers"]["PC"] == 0xC002
    assert engine.snapshots[1]["registers"]["PC"] == 0xC003
    assert engine.snapshots[2]["registers"]["PC"] == 0xC004
