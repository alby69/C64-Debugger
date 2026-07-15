import time
from c64debugger.vice_bridge import VICERemoteMonitorBridge
from tests.mock_vice_server import MockVICEServer

def main():
    print("Avvio del server Mock VICE...")
    server = MockVICEServer(host="127.0.0.1", port=6535)
    server.start()
    time.sleep(0.5)

    bridge = VICERemoteMonitorBridge(host="127.0.0.1", port=6535)
    success, msg = bridge.connect()
    if not success:
        print(f"Errore connessione: {msg}")
        server.stop()
        return

    # Let's say we want a conditional breakpoint: stop when A register becomes $FF
    print("\n--- EMULAZIONE BREAKPOINT CONDIZIONATO (A == $FF) ---")

    # We will step instructions and inspect register A
    server.registers["A"] = 0x00
    server.registers["PC"] = 0xC000

    # Let's write a sequence where A changes: $00 -> $50 -> $FF -> $10
    # We write those instructions or simply mock stepping where A increases
    # We can programmatically change server's state to simulate this during stepping

    steps = [0x00, 0x50, 0xFF, 0x10]

    for idx, a_val in enumerate(steps):
        # Programmatically simulate CPU step in the mock server for demonstration
        server.registers["A"] = a_val

        regs = bridge.step_instruction()
        print(f"Step {idx + 1}: PC=${regs['PC']:04X}, A=${regs['A']:02X}")

        if regs["A"] == 0xFF:
            print(f"[CONDIZIONE SODDISFATTA] Rilevato A == $FF a PC=${regs['PC']:04X}! Debugger interrotto.")
            break

    bridge.disconnect()
    server.stop()

if __name__ == "__main__":
    main()
