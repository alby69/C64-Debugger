import unittest
from unittest.mock import MagicMock, patch
from c64debugger.debugger_core import C64DebuggerCore, C64DebuggerAgentHelper

class TestC64DebuggerCore(unittest.TestCase):
    def setUp(self):
        self.core = C64DebuggerCore()

    def test_breakpoints(self):
        self.core.add_breakpoint(0xC000)
        self.assertIn(0xC000, self.core.breakpoints)

        self.core.remove_breakpoint(0xC000)
        self.assertNotIn(0xC000, self.core.breakpoints)

    def test_watchpoints(self):
        self.core.add_watchpoint(0x0400)
        self.assertIn(0x0400, self.core.watchpoints)

    def test_init_simulator_no_validator(self):
        # By default c64validator may not be installed in the test environment,
        # so init_simulator should handle ImportError gracefully.
        self.core.init_simulator(b"\xea\xea", start_addr=0xC000)
        self.assertIsNone(self.core.simulation_adapter)

    def test_step_into_no_simulator(self):
        success, msg = self.core.step_into()
        self.assertFalse(success)
        self.assertEqual(msg, "Simulatore non inizializzato.")

    @patch("socket.socket")
    def test_connect_to_vice_success(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        success, msg = self.core.connect_to_vice()
        self.assertTrue(success)
        self.assertEqual(msg, "Connesso!")

    @patch("socket.socket")
    def test_connect_to_vice_failure(self, mock_socket_class):
        mock_socket_class.side_effect = Exception("Connection error")

        success, msg = self.core.connect_to_vice()
        self.assertFalse(success)
        self.assertIn("Impossibile connettersi a VICE", msg)


class TestC64DebuggerAgentHelper(unittest.TestCase):
    def test_analyze_crash_stack_overflow(self):
        # Stack Pointer out of bounds (0x0100 - 0x01FF page 1 bounds)
        registers = {"PC": 0xC000, "SP": 0x105}
        history = []
        report = C64DebuggerAgentHelper.analyze_crash_dump(registers, history)
        self.assertEqual(report["error_type"], "Stack Overflow/Underflow")

    def test_analyze_crash_infinite_loop(self):
        # PC remaining constant across last steps
        registers = {"PC": 0xC000, "SP": 0xFD}
        history = [{"PC": 0xC000}, {"PC": 0xC000}, {"PC": 0xC000}]
        report = C64DebuggerAgentHelper.analyze_crash_dump(registers, history)
        self.assertEqual(report["error_type"], "Infinite Self-Loop")

    def test_analyze_crash_invalid_rts(self):
        # Empty stack trace upon RTS execution
        registers = {"PC": 0xC000, "SP": 0xFD}
        history = [{"PC": 0xC001}, {"PC": 0xC002}]
        report = C64DebuggerAgentHelper.analyze_crash_dump(registers, history, stack_trace=[])
        self.assertEqual(report["error_type"], "Invalid RTS execution")

    def test_analyze_crash_default(self):
        registers = {"PC": 0xC000, "SP": 0xFD, "A": 0, "X": 0, "Y": 0}
        history = [{"PC": 0xC001}, {"PC": 0xC002}]
        report = C64DebuggerAgentHelper.analyze_crash_dump(registers, history, stack_trace=None)
        self.assertEqual(report["error_type"], "Unknown")
        self.assertIn("Crash rilevato", report["explanation"])

if __name__ == "__main__":
    unittest.main()
