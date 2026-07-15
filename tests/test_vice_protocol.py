import unittest
from c64debugger.vice_protocol import VICEMonitorProtocol

class TestVICEMonitorProtocol(unittest.TestCase):
    def test_parse_registers_standard(self):
        response = ".c000 01 02 03 f6 2f 37 00101010"
        regs = VICEMonitorProtocol.parse_registers(response)
        self.assertEqual(regs["PC"], 0xC000)
        self.assertEqual(regs["A"], 1)
        self.assertEqual(regs["X"], 2)
        self.assertEqual(regs["Y"], 3)
        self.assertEqual(regs["SP"], 0xF6)

    def test_parse_registers_fallback(self):
        response = "PC=c000 A=01 X=02 Y=03 SP=f6"
        regs = VICEMonitorProtocol.parse_registers(response)
        self.assertEqual(regs["PC"], 0xC000)
        self.assertEqual(regs["A"], 1)
        self.assertEqual(regs["X"], 2)
        self.assertEqual(regs["Y"], 3)
        self.assertEqual(regs["SP"], 0xF6)

    def test_parse_memory(self):
        response = ".c000 00 01 02 03 04 05 06 07  ........"
        data = VICEMonitorProtocol.parse_memory(response)
        self.assertEqual(data, b"\x00\x01\x02\x03\x04\x05\x06\x07")

    def test_format_write_memory(self):
        cmd = VICEMonitorProtocol.format_write_memory(0xC000, b"\xa9\xff")
        self.assertEqual(cmd, "> c000 a9 ff")

    def test_format_breakpoint(self):
        cmd = VICEMonitorProtocol.format_breakpoint(0xC000)
        self.assertEqual(cmd, "break c000")

    def test_format_read_memory(self):
        cmd = VICEMonitorProtocol.format_read_memory(0xC000, 0xC007)
        self.assertEqual(cmd, "m c000 c007")
