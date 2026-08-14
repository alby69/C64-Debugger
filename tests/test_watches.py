import struct
from unittest.mock import MagicMock
from c64debugger.watches import WatchManager
from c64debugger.debugger_core import C64DebuggerCore
from c64debugger.session import C64SessionManager

def test_watch_manager_operations():
    mgr = WatchManager()
    assert len(mgr.list_watches()) == 0

    mgr.add_watch("my_var", "u16")
    assert mgr.list_watches() == {"my_var": "u16"}

    mgr.add_watch("other", "invalid_format")
    assert mgr.list_watches()["other"] == "hex8"

    removed = mgr.remove_watch("my_var")
    assert removed is True
    assert "my_var" not in mgr.list_watches()

    removed_not_found = mgr.remove_watch("non_existent")
    assert removed_not_found is False

    mgr.clear()
    assert len(mgr.list_watches()) == 0

def test_watch_formatting():
    mgr = WatchManager()

    assert mgr.format_value(bytes([0xAB]), "hex8") == "$AB"
    assert mgr.format_value(bytes([0x34, 0x12]), "hex16") == "$1234"
    assert mgr.format_value(bytes([0x78, 0x56, 0x34, 0x12]), "hex32") == "$12345678"

    assert mgr.format_value(bytes([128]), "u8") == "128"
    assert mgr.format_value(bytes([0x80]), "s8") == "-128"

    assert mgr.format_value(bytes([0x00, 0x80]), "u16") == "32768"
    assert mgr.format_value(bytes([0x00, 0x80]), "s16") == "-32768"

    assert mgr.format_value(bytes([0x00, 0x00, 0x00, 0x80]), "u32") == "2147483648"
    assert mgr.format_value(bytes([0x00, 0x00, 0x00, 0x80]), "s32") == "-2147483648"

    assert mgr.format_value(b"Hello\x00World", "text") == "Hello"

def test_watch_evaluation():
    mock_bridge = MagicMock()
    mock_bridge.read_memory.return_value = bytes([0x10, 0x20, 0x30, 0x40])

    mgr = WatchManager()
    mgr.add_watch("$C000", "hex16")
    mgr.add_watch("my_symbol", "text")

    resolver = lambda name: 0xC100 if name == "my_symbol" else None

    results = mgr.evaluate_watches(mock_bridge, symbol_resolver_fn=resolver)
    assert len(results) == 2

    r0 = results[0]
    assert r0["name"] == "$C000"
    assert r0["address"] == 0xC000
    assert r0["value"] == "$2010"

    r1 = results[1]
    assert r1["name"] == "my_symbol"
    assert r1["address"] == 0xC100
    assert r1["value"] == "\x10\x20\x30\x40"

def test_session_saving_loading_with_watches(tmp_path):
    core = C64DebuggerCore()
    mgr = WatchManager()
    core.watch_manager = mgr

    mgr.add_watch("test_lbl", "s16")
    mgr.add_watch("$02", "hex8")

    session_file = tmp_path / "session_with_watches.c64dbg"
    success = C64SessionManager.save_session(str(session_file), core)
    assert success is True

    new_core = C64DebuggerCore()
    new_mgr = WatchManager()
    new_core.watch_manager = new_mgr

    C64SessionManager.load_session(str(session_file), new_core)
    assert new_mgr.list_watches() == {
        "test_lbl": "s16",
        "$02": "hex8"
    }
