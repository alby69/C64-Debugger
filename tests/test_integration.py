import unittest
import time
from tests.mock_vice_server import MockVICEServer
from c64debugger.vice_bridge import VICERemoteMonitorBridge

class TestIntegrationVICEBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = MockVICEServer(host="127.0.0.1", port=6520)
        cls.server.start()
        # Give mock server a tiny bit to start up
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()

    def setUp(self) -> None:
        self.bridge = VICERemoteMonitorBridge(host="127.0.0.1", port=6520)

    def tearDown(self) -> None:
        self.bridge.disconnect()

    def test_connect_and_commands(self) -> None:
        # Test connection with retries
        success, msg = self.bridge.connect(max_retries=2)
        self.assertTrue(success)
        self.assertIn("Connesso con successo", msg)

        # Test read default registers
        regs = self.bridge.get_registers()
        self.assertEqual(regs["PC"], 0xC000)
        self.assertEqual(regs["A"], 0x00)
        self.assertEqual(regs["X"], 0x00)
        self.assertEqual(regs["Y"], 0x00)
        self.assertEqual(regs["SP"], 0xFD)

        # Test write memory
        success_write = self.bridge.write_memory(0xC000, b"\xa9\xff\x8d\x00\x04")
        self.assertTrue(success_write)

        # Test read memory
        mem_data = self.bridge.read_memory(0xC000, 0xC004)
        self.assertEqual(mem_data, b"\xa9\xff\x8d\x00\x04")

        # Test breakpoint
        success_bp = self.bridge.set_breakpoint(0xC000)
        self.assertTrue(success_bp)

        # Test step instruction
        step_regs = self.bridge.step_instruction()
        self.assertEqual(step_regs["PC"], 0xC001)

        # Test resume & stop
        self.bridge.resume_execution()
        self.bridge.stop_execution()
