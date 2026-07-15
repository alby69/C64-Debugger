import unittest
from unittest.mock import MagicMock, patch
import socket
from c64debugger.vice_bridge import VICERemoteMonitorBridge

class TestVICERemoteMonitorBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = VICERemoteMonitorBridge(host="127.0.0.1", port=6510)

    @patch("subprocess.Popen")
    def test_start_vice_headless(self, mock_popen):
        # Test success
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        success = self.bridge.start_vice_headless(limit_cycles=1000)
        self.assertTrue(success)
        mock_popen.assert_called()

    @patch("socket.socket")
    def test_connect_success(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recv.return_value = b"Welcome to VICE monitor"

        success, msg = self.bridge.connect()
        self.assertTrue(success)
        self.assertIn("Connesso", msg)

    @patch("socket.socket")
    def test_connect_failure(self, mock_socket_class):
        mock_socket_class.side_effect = Exception("Connection refused")
        success, msg = self.bridge.connect()
        self.assertFalse(success)
        self.assertIn("Impossibile connettersi", msg)

    def test_send_command_not_connected(self):
        res = self.bridge.send_command("r")
        self.assertEqual(res, "Nessuna connessione attiva.")

    @patch("socket.socket")
    def test_send_command_success(self, mock_socket_class):
        mock_socket = MagicMock()
        self.bridge.socket = mock_socket

        # We mock socket.recv to simulate reading back from VICE until finding prompt
        # First call: timeout on clearing buffer (or we can raise socket.timeout inside setUp)
        # To simplify, we'll configure recv side_effects:
        # First when flushing we can raise socket.timeout
        # Then when receiving command output, return data containing prompt
        mock_socket.recv.side_effect = [socket.timeout, b"A=00 X=00 Y=00\n(C64)"]

        res = self.bridge.send_command("r")
        self.assertIn("A=00", res)
        self.assertIn("(C64)", res)

    @patch("c64debugger.vice_bridge.VICERemoteMonitorBridge.send_command")
    def test_get_registers(self, mock_send_command):
        # Sample output from VICE monitor for command 'r'
        mock_send_command.return_value = ".c000 01 02 03 f6 2f 37 00101010"
        regs = self.bridge.get_registers()
        self.assertEqual(regs["PC"], 0xC000)
        self.assertEqual(regs["A"], 1)
        self.assertEqual(regs["X"], 2)
        self.assertEqual(regs["Y"], 3)
        self.assertEqual(regs["SP"], 0xF6)

    @patch("c64debugger.vice_bridge.VICERemoteMonitorBridge.send_command")
    def test_read_memory(self, mock_send_command):
        mock_send_command.return_value = ".c000 00 01 02 03 04 05 06 07  ........"
        data = self.bridge.read_memory(0xC000, 0xC007)
        self.assertEqual(data, b"\x00\x01\x02\x03\x04\x05\x06\x07")

if __name__ == "__main__":
    unittest.main()
