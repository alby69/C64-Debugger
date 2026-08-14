import json
import socket
import threading
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("C64DAPServer")

class C64DAPServer:
    """
    A lightweight, compliant Debug Adapter Protocol (DAP) server for C64-Debugger.
    Enables IDE (like VS Code) integration.
    """
    def __init__(self, host: str, port: int, core: Any, bridge: Any) -> None:
        self.host = host
        self.port = port
        self.core = core
        self.bridge = bridge
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.client_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        logger.info(f"DAP Server listening on {self.host}:{self.port}")

        self.client_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.client_thread.start()

    def stop(self) -> None:
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        logger.info("DAP Server stopped")

    def _accept_loop(self) -> None:
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                logger.info(f"DAP Client connected from {addr}")
                self._handle_client(conn)
            except Exception as e:
                if self.running:
                    logger.debug(f"Accept error: {e}")
                break

    def _handle_client(self, conn: socket.socket) -> None:
        buffer = b""
        seq = 1
        try:
            while self.running:
                data = conn.recv(4096)
                if not data:
                    break
                buffer += data
                while b"Content-Length:" in buffer and b"\r\n\r\n" in buffer:
                    try:
                        header_idx = buffer.index(b"Content-Length:")
                        body_start = buffer.index(b"\r\n\r\n", header_idx) + 4
                        header_line = buffer[header_idx:body_start].decode("utf-8")
                        content_len = int(header_line.split("\r\n")[0].split(":")[1].strip())

                        if len(buffer) < body_start + content_len:
                            # Wait for more data
                            break

                        request_data = buffer[body_start : body_start + content_len].decode("utf-8")
                        buffer = buffer[body_start + content_len :]

                        request = json.loads(request_data)
                        logger.debug(f"DAP Request received: {request}")

                        response, events = self._process_request(request, seq)
                        seq += 1

                        if response:
                            self._send_message(conn, response)
                        for ev in events:
                            self._send_message(conn, ev)

                    except ValueError:
                        break
        except Exception as e:
            logger.exception(f"Error handling DAP client: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass
            logger.info("DAP Client disconnected")

    def _send_message(self, conn: socket.socket, msg: Dict[str, Any]) -> None:
        body = json.dumps(msg)
        body_bytes = body.encode("utf-8")
        header = f"Content-Length: {len(body_bytes)}\r\n\r\n"
        conn.sendall(header.encode("utf-8") + body_bytes)
        logger.debug(f"DAP Message sent: {msg}")

    def _process_request(self, req: Dict[str, Any], seq: int) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        command = req.get("command")
        req_seq = req.get("seq", 0)
        args = req.get("arguments", {})

        response: Dict[str, Any] = {
            "seq": seq,
            "type": "response",
            "request_seq": req_seq,
            "command": command,
            "success": True
        }
        events: List[Dict[str, Any]] = []

        if command == "initialize":
            response["body"] = {
                "supportsConfigurationDoneRequest": True,
                "supportsStepInTargetsRequest": False,
                "supportsEvaluateForHovers": False
            }
        elif command in ("launch", "attach"):
            # Connect to the VICE emulator
            success, msg = self.bridge.connect()
            response["success"] = success
            if not success:
                response["message"] = msg
            else:
                events.append({
                    "seq": seq + 1,
                    "type": "event",
                    "event": "initialized"
                })
        elif command == "setBreakpoints":
            # Clear old breakpoints
            self.core.breakpoints.clear()
            breakpoints_arg = args.get("breakpoints", [])
            response_breakpoints = []

            for bp in breakpoints_arg:
                line = bp.get("line")
                # Map line to address or use the line direct as mock address if no map
                addr = line  # In real assembly map, line is translated to address
                self.core.add_breakpoint(addr)
                self.bridge.set_breakpoint(addr)
                response_breakpoints.append({
                    "verified": True,
                    "line": line,
                    "id": addr
                })
            response["body"] = {"breakpoints": response_breakpoints}
        elif command == "configurationDone":
            # Complete configuration and send a stopped or continued event
            events.append({
                "seq": seq + 1,
                "type": "event",
                "event": "stopped",
                "body": {
                    "reason": "entry",
                    "threadId": 1
                }
            })
        elif command == "threads":
            response["body"] = {
                "threads": [{"id": 1, "name": "C64 CPU (MOS 6502)"}]
            }
        elif command == "stackTrace":
            # Retrieve registers and use the stack tracer
            try:
                regs = self.bridge.get_registers()
                sp = regs.get("SP", 0xFD)
                # Call stack analysis on page 1 ($0100-$01FF)
                from c64debugger.disasm.stack import reconstruct_stack_trace
                # We can mock/read memory of page 1
                stack_mem = self.bridge.read_memory(0x0100, 0x01FF)
                frames = reconstruct_stack_trace(stack_mem, sp)

                stack_frames = []
                # Always add current frame
                stack_frames.append({
                    "id": 0,
                    "name": f"PC: ${regs.get('PC', 0):04X}",
                    "line": regs.get("PC", 0),
                    "column": 0
                })
                for i, frame in enumerate(frames):
                    stack_frames.append({
                        "id": i + 1,
                        "name": f"Subroutine via RTS tracing",
                        "line": frame.return_address,
                        "column": 0
                    })
                response["body"] = {"stackFrames": stack_frames, "totalFrames": len(stack_frames)}
            except Exception as e:
                logger.exception(f"Error in stackTrace processing: {e}")
                response["body"] = {
                    "stackFrames": [{"id": 0, "name": f"PC: ${regs.get('PC', 0):04X}", "line": regs.get("PC", 0)}],
                    "totalFrames": 1
                }
        elif command == "scopes":
            response["body"] = {
                "scopes": [
                    {
                        "name": "Registers",
                        "variablesReference": 1000,
                        "expensive": False
                    },
                    {
                        "name": "VIC-II State",
                        "variablesReference": 2000,
                        "expensive": False
                    },
                    {
                        "name": "SID State",
                        "variablesReference": 3000,
                        "expensive": False
                    },
                    {
                        "name": "CIA1 State",
                        "variablesReference": 4001,
                        "expensive": False
                    },
                    {
                        "name": "CIA2 State",
                        "variablesReference": 4002,
                        "expensive": False
                    }
                ]
            }
        elif command == "variables":
            ref = args.get("variablesReference", 0)
            vars_list = []
            if ref == 1000:
                try:
                    regs = self.bridge.get_registers()
                    for k, v in regs.items():
                        vars_list.append({
                            "name": k,
                            "value": f"${v:04X}" if k == "PC" else f"${v:02X}",
                            "variablesReference": 0
                        })
                except Exception:
                    pass
            elif ref == 2000:
                try:
                    from c64debugger.hw_state.vic_state import VICState
                    vic_data = self.bridge.read_memory(0xD000, 0xD02E)
                    vic = VICState(vic_data)
                    info = vic.to_dict()
                    for k, v in info.items():
                        if isinstance(v, list):
                            val_str = ", ".join(str(x) for x in v)
                        elif isinstance(v, int) and "offset" in k:
                            val_str = f"${v:04X}"
                        else:
                            val_str = str(v)
                        vars_list.append({
                            "name": k,
                            "value": val_str,
                            "variablesReference": 0
                        })
                except Exception:
                    pass
            elif ref == 3000:
                try:
                    from c64debugger.hw_state.sid_state import SIDState
                    sid_data = self.bridge.read_memory(0xD400, 0xD41C)
                    sid = SIDState(sid_data)
                    info = sid.to_dict()
                    for k, v in info.items():
                        if k == "voices":
                            for voice in v:
                                v_idx = voice["voice_index"]
                                for vk, vv in voice.items():
                                    if vk != "voice_index":
                                        vars_list.append({
                                            "name": f"voice_{v_idx}_{vk}",
                                            "value": str(vv),
                                            "variablesReference": 0
                                        })
                        else:
                            vars_list.append({
                                "name": k,
                                "value": str(v),
                                "variablesReference": 0
                            })
                except Exception:
                    pass
            elif ref == 4001:
                try:
                    from c64debugger.hw_state.cia_state import CIAState
                    cia_data = self.bridge.read_memory(0xDC00, 0xDC0F)
                    cia = CIAState(cia_data, "CIA1")
                    info = cia.to_dict()
                    for k, v in info.items():
                        vars_list.append({
                            "name": k,
                            "value": str(v),
                            "variablesReference": 0
                        })
                except Exception:
                    pass
            elif ref == 4002:
                try:
                    from c64debugger.hw_state.cia_state import CIAState
                    cia_data = self.bridge.read_memory(0xDD00, 0xDD0F)
                    cia = CIAState(cia_data, "CIA2")
                    info = cia.to_dict()
                    for k, v in info.items():
                        vars_list.append({
                            "name": k,
                            "value": str(v),
                            "variablesReference": 0
                        })
                except Exception:
                    pass
            response["body"] = {"variables": vars_list}
        elif command in ("next", "stepIn"):
            self.bridge.step_instruction()
            events.append({
                "seq": seq + 1,
                "type": "event",
                "event": "stopped",
                "body": {
                    "reason": "step",
                    "threadId": 1
                }
            })
        elif command == "continue":
            self.bridge.resume_execution()
            response["body"] = {"allThreadsContinued": True}
        elif command == "disconnect":
            self.bridge.disconnect()
        else:
            response["success"] = False
            response["message"] = f"Command '{command}' not implemented"

        return response, events
