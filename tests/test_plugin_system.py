import os
import pytest
from unittest.mock import MagicMock
from c64debugger.plugin.plugin_manager import C64PluginManager, C64DebuggerPlugin
from c64debugger.cli.repl import C64DebuggerREPL

def test_plugin_lifecycle_and_hooks(tmp_path):
    # 1. Create a dummy plugin file
    plugin_code = """
from c64debugger.plugin.plugin_manager import C64DebuggerPlugin

class MyTestPlugin(C64DebuggerPlugin):
    name = "TestPlugin"
    description = "A plugin for testing"
    version = "1.2.3"

    def __init__(self):
        super().__init__()
        self.pre_step_called = False
        self.post_step_called = False
        self.pre_bp_called = False
        self.post_bp_called = False
        self.on_crash_called = False

    def on_plugin_load(self, manager):
        super().on_plugin_load(manager)
        # Register a custom command
        manager.register_command("test_cmd", self.test_command, "A test command help")

    def test_command(self, *args):
        self.cmd_args = args

    def pre_step(self, regs):
        self.pre_step_called = True

    def post_step(self, regs):
        self.post_step_called = True

    def pre_breakpoint(self, addr, regs):
        self.pre_bp_called = True

    def post_breakpoint(self, addr, regs):
        self.post_bp_called = True

    def on_crash(self, crash_report):
        self.on_crash_called = True
"""
    plugin_file = tmp_path / "test_plugin.py"
    plugin_file.write_text(plugin_code, encoding="utf-8")

    # 2. Setup mock bridge and core
    mock_bridge = MagicMock()
    mock_bridge.get_registers.return_value = {"PC": 0xC000, "SP": 0xFD, "A": 0, "X": 0, "Y": 0}
    mock_bridge.step_instruction.return_value = {"PC": 0xC001, "SP": 0xFD, "A": 0, "X": 0, "Y": 0}

    repl = C64DebuggerREPL(mock_bridge=mock_bridge)
    pm = repl.plugin_manager

    # 3. Load the plugin
    plugin = pm.load_plugin(str(plugin_file))
    assert plugin is not None
    assert plugin.name == "TestPlugin"
    assert plugin.description == "A plugin for testing"
    assert plugin.version == "1.2.3"

    # Verify custom command is registered on REPL
    assert hasattr(repl, "do_test_cmd")

    # 4. Invoke custom command via REPL
    repl.onecmd("test_cmd arg1 arg2")
    assert plugin.cmd_args == ("arg1", "arg2")

    # 5. Trigger Step and verify pre_step and post_step hooks are invoked
    repl.onecmd("step")
    assert plugin.pre_step_called is True
    assert plugin.post_step_called is True

    # 6. Trigger Breakpoint Evaluation and verify pre_breakpoint and post_breakpoint hooks
    repl.core.add_breakpoint(0xC000)
    # should_stop should trigger hooks
    stop = repl.core.should_stop(0xC000, {"PC": 0xC000, "SP": 0xFD})
    assert stop is True
    assert plugin.pre_bp_called is True
    assert plugin.post_bp_called is True

    # 7. Trigger Crash Check and verify on_crash hook
    # Loop on single instruction represents infinite loop/crash
    history = [{"PC": 0xC000}, {"PC": 0xC000}, {"PC": 0xC000}]
    repl.core.check_and_trigger_crash({"PC": 0xC000, "SP": 0xFD}, history)
    assert plugin.on_crash_called is True

    # 8. Unload plugin
    pm.unload_plugin("TestPlugin")
    assert not hasattr(repl, "do_test_cmd")
    assert "TestPlugin" not in pm.loaded_plugins
