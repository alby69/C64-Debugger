import time
from c64debugger.vice_bridge import VICERemoteMonitorBridge, setup_logger
from tests.mock_vice_server import MockVICEServer

def main():
    # Setup structured logging
    setup_logger(log_file="examples_debug.log")

    print("Avvio del server Mock VICE...")
    server = MockVICEServer(host="127.0.0.1", port=6530)
    server.start()
    time.sleep(0.5)

    print("Connessione al bridge del monitor remoto di VICE...")
    bridge = VICERemoteMonitorBridge(host="127.0.0.1", port=6530)
    success, msg = bridge.connect(max_retries=3)
    if not success:
        print(f"Connessione fallita: {msg}")
        server.stop()
        return

    print("\n--- 1. LETTURA REGISTRI ---")
    regs = bridge.get_registers()
    print(f"Registri attuali: PC=${regs['PC']:04X}, A=${regs['A']:02X}, X=${regs['X']:02X}, Y=${regs['Y']:02X}, SP=${regs['SP']:02X}")

    print("\n--- 2. SCRITTURA E LETTURA MEMORIA (RAM) ---")
    # Scrive codice assembly in memoria a $C000 (LDA #$FF; STA $0400)
    code = b"\xa9\xff\x8d\x00\x04"
    bridge.write_memory(0xC000, code)
    print("Scritta sequenza di byte a $C000: LDA #$FF; STA $0400")

    # Rilegge i byte scritti
    mem = bridge.read_memory(0xC000, 0xC004)
    print(f"Letto da $C000: {mem.hex()}")

    print("\n--- 3. IMPOSTAZIONE BREAKPOINT ---")
    if bridge.set_breakpoint(0xC000):
        print("Breakpoint impostato con successo a $C000!")

    print("\n--- 4. STEPPING DI ISTRUZIONI ---")
    step_regs = bridge.step_instruction()
    print(f"Eseguito step 1. Nuovo PC: ${step_regs['PC']:04X}")

    print("\nDisconnessione...")
    bridge.disconnect()
    server.stop()
    print("Terminato con successo!")

if __name__ == "__main__":
    main()
