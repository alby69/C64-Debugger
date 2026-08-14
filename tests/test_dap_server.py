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

    # 6. Test Hardware Scopes
    req_scopes = {"command": "scopes", "seq": 15}
    res_scopes, evs = server._process_request(req_scopes, 6)
    assert res_scopes["success"] is True
    scopes = res_scopes["body"]["scopes"]
    assert len(scopes) == 5
    assert any(s["name"] == "VIC-II State" and s["variablesReference"] == 2000 for s in scopes)
    assert any(s["name"] == "SID State" and s["variablesReference"] == 3000 for s in scopes)
    assert any(s["name"] == "CIA1 State" and s["variablesReference"] == 4001 for s in scopes)
    assert any(s["name"] == "CIA2 State" and s["variablesReference"] == 4002 for s in scopes)

    # 7. Test Hardware Variables (VIC-II)
    req_vic_vars = {"command": "variables", "seq": 16, "arguments": {"variablesReference": 2000}}
    res_vic_vars, evs = server._process_request(req_vic_vars, 7)
    assert res_vic_vars["success"] is True
    assert any(v["name"] == "screen_on" for v in res_vic_vars["body"]["variables"])

    # 8. Test Hardware Variables (SID)
    req_sid_vars = {"command": "variables", "seq": 17, "arguments": {"variablesReference": 3000}}
    res_sid_vars, evs = server._process_request(req_sid_vars, 8)
    assert res_sid_vars["success"] is True
    assert any(v["name"] == "volume" for v in res_sid_vars["body"]["variables"])

    # 9. Test Hardware Variables (CIA1 & CIA2)
    req_cia1_vars = {"command": "variables", "seq": 18, "arguments": {"variablesReference": 4001}}
    res_cia1_vars, evs = server._process_request(req_cia1_vars, 9)
    assert res_cia1_vars["success"] is True
    assert any(v["name"] == "timer_a" for v in res_cia1_vars["body"]["variables"])

    req_cia2_vars = {"command": "variables", "seq": 19, "arguments": {"variablesReference": 4002}}
    res_cia2_vars, evs = server._process_request(req_cia2_vars, 10)
    assert res_cia2_vars["success"] is True
    assert any(v["name"] == "timer_b" for v in res_cia2_vars["body"]["variables"])


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
