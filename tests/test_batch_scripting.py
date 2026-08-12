import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from c64debugger.plugin.plugin_manager import c64_script, _registered_scripts
from c64debugger.cli.main import main

def test_c64_script_decorator():
    _registered_scripts.clear()

    @c64_script
    def dummy_func(repl):
        pass

    assert dummy_func in _registered_scripts


def test_batch_mode_execution(tmp_path):
    # 1. Create a dummy batch script file
    batch_script_code = """
from c64debugger.plugin.plugin_manager import c64_script

@c64_script
def my_batch_job(repl):
    repl.core.add_breakpoint(0xD000)
"""
    batch_file = tmp_path / "my_script.py"
    batch_file.write_text(batch_script_code, encoding="utf-8")

    # 2. Patch main arguments and connections
    test_args = ["c64debugger", "--batch", str(batch_file)]

    with patch.object(sys, "argv", test_args), \
         patch("c64debugger.vice_bridge.VICERemoteMonitorBridge.connect", return_value=(True, "Connected")), \
         patch("c64debugger.vice_bridge.VICERemoteMonitorBridge.disconnect") as mock_disconnect, \
         pytest.raises(SystemExit) as exit_info:
        main()

    # Ensure it exited with 0 (success)
    assert exit_info.value.code == 0
    # The disconnect should have been called
    mock_disconnect.assert_called_once()
