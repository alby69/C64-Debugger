import unittest
import os
import json
from c64debugger.config import C64DebuggerConfig

class TestC64DebuggerConfig(unittest.TestCase):
    def test_default_config(self):
        config = C64DebuggerConfig()
        self.assertEqual(config.vice_host, "127.0.0.1")
        self.assertEqual(config.vice_port, 6510)
        self.assertEqual(config.vice_timeout, 2.0)
        self.assertEqual(config.log_level, "INFO")
        self.assertIsNone(config.log_file)
        self.assertEqual(config.llm_provider, "openai")
        self.assertEqual(config.llm_model, "gpt-4")
        self.assertEqual(config.llm_temperature, 0.2)
        self.assertEqual(config.llm_max_tokens, 1000)

    def test_load_from_json(self):
        test_file = "test_config_temp.json"
        config_data = {
            "vice": {
                "host": "192.168.1.100",
                "port": 6511,
                "timeout": 5.5
            },
            "llm": {
                "provider": "anthropic",
                "model": "claude-3-opus-20240229"
            }
        }
        with open(test_file, "w") as f:
            json.dump(config_data, f)

        try:
            config = C64DebuggerConfig.load_from_file(test_file)
            self.assertEqual(config.vice_host, "192.168.1.100")
            self.assertEqual(config.vice_port, 6511)
            self.assertEqual(config.vice_timeout, 5.5)
            self.assertEqual(config.llm_provider, "anthropic")
            self.assertEqual(config.llm_model, "claude-3-opus-20240229")
            # Should fall back to default for omitted fields
            self.assertEqual(config.llm_temperature, 0.2)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_load_from_non_existent(self):
        config = C64DebuggerConfig.load_from_file("non_existent_file.json")
        self.assertEqual(config.vice_host, "127.0.0.1")
