import json
import socket
import time
import pytest
from unittest.mock import MagicMock
from c64debugger.dap.dap_server import C64DAPServer
from c64debugger.debugger_core import C64DebuggerCore

def test_dap_request_processing():
    mock_core = C64DebuggerCore()
    mock_bridge = MagicMock()
    mock_bridge.connect.return_value = (True, "Connected")
    mock_bridge.get_registers.return_value = {"PC": 0xC000, "SP": 0xFD, "A": 0xFF}
    mock_bridge.read_memory.return_value = bytes([0] * 256)

    server = C64DAPServer("127.0.0.1", 12345, mock_core, mock_bridge)

    # 1. Test "initialize"
    req_init = {"command": "initialize", "seq": 10}
    res, evs = server._process_request(req_init, 1)
    assert res["success"] is True
    assert res["command"] == "initialize"
    assert res["body"]["supportsConfigurationDoneRequest"] is True

    # 2. Test "launch"
    req_launch = {"command": "launch", "seq": 11}
    res, evs = server._process_request(req_launch, 2)
    assert res["success"] is True
    assert len(evs) == 1
    assert evs[0]["event"] == "initialized"

    # 3. Test "setBreakpoints"
    req_bp = {
        "command": "setBreakpoints",
        "seq": 12,
        "arguments": {
            "breakpoints": [
                {"line": 0xC000},
                {"line": 0xC010}
            ]
        }
    }
    res, evs = server._process_request(req_bp, 3)
    assert res["success"] is True
    assert 0xC000 in mock_core.breakpoints
    assert 0xC010 in mock_core.breakpoints
    assert len(res["body"]["breakpoints"]) == 2

    # 4. Test "stackTrace"
    req_stack = {"command": "stackTrace", "seq": 13}
    res, evs = server._process_request(req_stack, 4)
    assert res["success"] is True
    assert res["body"]["totalFrames"] > 0
    assert res["body"]["stackFrames"][0]["line"] == 0xC000

    # 5. Test "variables"
    req_vars = {"command": "variables", "seq": 14, "arguments": {"variablesReference": 1000}}
    res, evs = server._process_request(req_vars, 5)
    assert res["success"] is True
    assert any(v["name"] == "A" and v["value"] == "$FF" for v in res["body"]["variables"])


def test_dap_socket_integration():
    # Find a free port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    mock_core = C64DebuggerCore()
    mock_bridge = MagicMock()
    mock_bridge.connect.return_value = (True, "Connected")

    server = C64DAPServer("127.0.0.1", port, mock_core, mock_bridge)
    server.start()

    # Wait a moment for server to start listening
    time.sleep(0.1)

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", port))

        # Send initialize request
        req = {"command": "initialize", "seq": 1, "type": "request"}
        body = json.dumps(req)
        body_bytes = body.encode("utf-8")
        packet = f"Content-Length: {len(body_bytes)}\r\n\r\n{body}"
        client.sendall(packet.encode("utf-8"))

        # Read response
        response_data = client.recv(1024)
        assert b"Content-Length:" in response_data
        assert b"initialize" in response_data
        assert b"supportsConfigurationDoneRequest" in response_data

        client.close()
    finally:
        server.stop()
