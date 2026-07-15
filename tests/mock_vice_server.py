import socket
import threading
import time
from typing import Dict, List, Optional

class MockVICEServer:
    """
    A multi-threaded socket-based Mock VICE Server to test the VICERemoteMonitorBridge
    without real emulators or external dependencies.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 6510) -> None:
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.client_threads: List[threading.Thread] = []
        self.lock = threading.Lock()

        # Mocked state
        self.registers = {
            "PC": 0xC000,
            "A": 0x00,
            "X": 0x00,
            "Y": 0x00,
            "SP": 0xFD
        }
        self.memory = bytearray(65536)
        self.breakpoints: List[int] = []

    def start(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True

        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()

    def _accept_loop(self) -> None:
        while self.running:
            try:
                self.server_socket.settimeout(0.5)
                client_sock, addr = self.server_socket.accept()
                t = threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True)
                t.start()
                with self.lock:
                    self.client_threads.append(t)
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, client_sock: socket.socket) -> None:
        try:
            # Send initial welcome banner
            client_sock.sendall(b"Welcome to mock x64sc monitor!\n(C64) ")

            buffer = ""
            while self.running:
                client_sock.settimeout(0.5)
                try:
                    data = client_sock.recv(1024)
                    if not data:
                        break
                    buffer += data.decode("utf-8", errors="ignore")
                except socket.timeout:
                    continue
                except Exception:
                    break

                if "\n" in buffer:
                    lines = buffer.split("\n")
                    # Last element might be incomplete line
                    buffer = lines[-1]
                    for line in lines[:-1]:
                        line = line.strip()
                        if not line:
                            continue
                        response = self._process_command(line)
                        client_sock.sendall(response.encode("utf-8"))
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def _process_command(self, cmd_line: str) -> str:
        parts = cmd_line.split()
        if not parts:
            return "(C64) "

        cmd = parts[0].lower()

        with self.lock:
            if cmd == "r":
                # Returns standard registers layout: ADDR A  X  Y  SP
                # .c000 00 00 00 f6 2f 37 00101010
                # We format it exactly as parsed by VICEMonitorProtocol
                addr_hex = f"{self.registers['PC']:04x}"
                a_hex = f"{self.registers['A']:02x}"
                x_hex = f"{self.registers['X']:02x}"
                y_hex = f"{self.registers['Y']:02x}"
                sp_hex = f"{self.registers['SP']:02x}"
                return f".{addr_hex} {a_hex} {x_hex} {y_hex} {sp_hex} 2f 37 00101010\n(C64) "

            elif cmd == "m":
                if len(parts) >= 3:
                    try:
                        start = int(parts[1], 16)
                        end = int(parts[2], 16)
                    except ValueError:
                        return "Invalid address format.\n(C64) "

                    # VICE returns chunks of 8 or 16 bytes. Let's return bytes exactly as needed.
                    # line format: .c000 00 01 02 03 04 05 06 07  ........
                    # We will output in chunks of 8 bytes
                    output_lines = []
                    curr = start
                    while curr <= end:
                        chunk_end = min(curr + 7, end)
                        chunk_bytes = self.memory[curr:chunk_end + 1]
                        hex_str = " ".join(f"{b:02x}" for b in chunk_bytes)
                        # pad hex_str to align if fewer than 8 bytes (though VICE might have variable alignment)
                        ascii_rep = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk_bytes)
                        output_lines.append(f".{curr:04x} {hex_str}  {ascii_rep}")
                        curr += 8

                    return "\n".join(output_lines) + "\n(C64) "
                return "Invalid 'm' parameters.\n(C64) "

            elif cmd == ">":
                if len(parts) >= 3:
                    try:
                        addr = int(parts[1], 16)
                        bytes_to_write = [int(p, 16) for p in parts[2:]]
                    except ValueError:
                        return "Invalid memory write format.\n(C64) "

                    for idx, b in enumerate(bytes_to_write):
                        if 0 <= addr + idx < len(self.memory):
                            self.memory[addr + idx] = b
                    return "(C64) "
                return "Invalid '>' parameters.\n(C64) "

            elif cmd == "break":
                if len(parts) >= 2:
                    try:
                        addr = int(parts[1], 16)
                    except ValueError:
                        return "Invalid breakpoint address.\n(C64) "
                    self.breakpoints.append(addr)
                    return f"Breakpoint {len(self.breakpoints)} impostato a ${addr:04X}\n(C64) "
                return "Invalid 'break' parameters.\n(C64) "

            elif cmd == "bk":
                lines = [f"Breakpoint {idx+1}: ${addr:04X}" for idx, addr in enumerate(self.breakpoints)]
                return "\n".join(lines) + "\n(C64) "

            elif cmd == "z":
                # Simulate single step by moving PC forward by 1 (or 2/3, 1 is fine for mock)
                self.registers["PC"] = (self.registers["PC"] + 1) & 0xFFFF
                addr_hex = f"{self.registers['PC']:04x}"
                a_hex = f"{self.registers['A']:02x}"
                x_hex = f"{self.registers['X']:02x}"
                y_hex = f"{self.registers['Y']:02x}"
                sp_hex = f"{self.registers['SP']:02x}"
                return f".{addr_hex} {a_hex} {x_hex} {y_hex} {sp_hex} 2f 37 00101010\n(C64) "

            elif cmd in ("stop", "g"):
                return "(C64) "

            else:
                return f"Command not recognized: {cmd}\n(C64) "

    def stop(self) -> None:
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        # Wait for threads to close or terminate
        for t in self.client_threads:
            try:
                t.join(timeout=0.2)
            except Exception:
                pass
        self.client_threads.clear()
