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


class TestLLMIntegration(unittest.TestCase):
    def setUp(self):
        from c64debugger.config import C64DebuggerConfig
        self.config = C64DebuggerConfig()

    @patch("urllib.request.urlopen")
    def test_openai_provider(self, mock_urlopen):
        from c64debugger.config import C64DebuggerConfig
        from c64debugger.llm_client import C64DebuggerLLMClient

        # Configure for OpenAI
        config = C64DebuggerConfig({
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "test_openai_key"
            }
        })

        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"choices": [{"message": {"content": "OpenAI Test Response"}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = C64DebuggerLLMClient(config)
        res = client.call_llm("System", "User")
        self.assertEqual(res, "OpenAI Test Response")

        # Verify call arguments
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(req.headers["Authorization"], "Bearer test_openai_key")

    @patch("urllib.request.urlopen")
    def test_anthropic_provider(self, mock_urlopen):
        from c64debugger.config import C64DebuggerConfig
        from c64debugger.llm_client import C64DebuggerLLMClient

        config = C64DebuggerConfig({
            "llm": {
                "provider": "anthropic",
                "model": "claude-3",
                "api_key": "test_anthropic_key"
            }
        })

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"content": [{"text": "Anthropic Test Response"}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = C64DebuggerLLMClient(config)
        res = client.call_llm("System", "User")
        self.assertEqual(res, "Anthropic Test Response")

        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(req.headers["X-api-key"], "test_anthropic_key")

    @patch("urllib.request.urlopen")
    def test_gemini_provider(self, mock_urlopen):
        from c64debugger.config import C64DebuggerConfig
        from c64debugger.llm_client import C64DebuggerLLMClient

        config = C64DebuggerConfig({
            "llm": {
                "provider": "gemini",
                "model": "gemini-pro",
                "api_key": "test_gemini_key"
            }
        })

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"candidates": [{"content": {"parts": [{"text": "Gemini Test Response"}]}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = C64DebuggerLLMClient(config)
        res = client.call_llm("System", "User")
        self.assertEqual(res, "Gemini Test Response")

        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertIn("generativelanguage.googleapis.com", req.full_url)
        self.assertIn("test_gemini_key", req.full_url)

    @patch("urllib.request.urlopen")
    def test_ollama_provider(self, mock_urlopen):
        from c64debugger.config import C64DebuggerConfig
        from c64debugger.llm_client import C64DebuggerLLMClient

        config = C64DebuggerConfig({
            "llm": {
                "provider": "ollama",
                "model": "llama3",
                "ollama_url": "http://localhost:11434/api/chat"
            }
        })

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "Ollama Test Response"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = C64DebuggerLLMClient(config)
        res = client.call_llm("System", "User")
        self.assertEqual(res, "Ollama Test Response")

        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.full_url, "http://localhost:11434/api/chat")

    @patch("urllib.request.urlopen")
    def test_c64_llm_provider(self, mock_urlopen):
        from c64debugger.config import C64DebuggerConfig
        from c64debugger.llm_client import C64DebuggerLLMClient

        config = C64DebuggerConfig({
            "llm": {
                "provider": "c64-llm",
                "c64_llm_url": "http://localhost:7860/api/predict"
            }
        })

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"data": ["C64-LLM Gradio Test Response"]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = C64DebuggerLLMClient(config)
        res = client.call_llm("System", "User")
        self.assertEqual(res, "C64-LLM Gradio Test Response")

        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.full_url, "http://localhost:7860/api/predict")

    @patch("urllib.request.urlopen")
    def test_analyze_crash_dump_with_llm(self, mock_urlopen):
        from c64debugger.config import C64DebuggerConfig
        from c64debugger.debugger_core import C64DebuggerAgentHelper

        config = C64DebuggerConfig({
            "llm": {
                "provider": "openai",
                "api_key": "test"
            }
        })

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"choices": [{"message": {"content": "LLM Analysis Result"}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        registers = {"PC": 0xC000, "A": 0xFF, "X": 0x00, "Y": 0x12, "SP": 0xFD}
        history = [{"PC": 0xBFFF, "registers": registers}]
        stack_trace = [0x01, 0x02]

        res = C64DebuggerAgentHelper.analyze_crash_dump_with_llm(
            config, registers, history, stack_trace
        )
        self.assertEqual(res, "LLM Analysis Result")


if __name__ == "__main__":
    unittest.main()
