import argparse
import sys
from c64debugger.cli.repl import C64DebuggerREPL

def main() -> None:
    parser = argparse.ArgumentParser(
        description="C64 Debugger - Shell interattiva collegata a VICE remote monitor."
    )
    parser.add_argument(
        "--vice-host",
        type=str,
        default="127.0.0.1",
        help="Indirizzo IP dell'host su cui gira l'emulatore VICE (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--vice-port",
        type=int,
        default=6510,
        help="Porta del monitor remoto di VICE (default: 6510)"
    )
    parser.add_argument(
        "--autostart",
        type=str,
        help="Percorso di un file .PRG da caricare automaticamente all'avvio dell'emulatore"
    )

    args = parser.parse_args()

    # Se c'è una PRG da avviare, potremmo tentare l'avvio headless del bridge,
    # altrimenti assumiamo che VICE sia già in esecuzione e proviamo a connetterci.
    repl = C64DebuggerREPL(host=args.vice_host, port=args.vice_port)

    if args.autostart:
        print(f"Tentativo di avvio headless di VICE con il file '{args.autostart}'...")
        success = repl.bridge.start_vice_headless(prg_path=args.autostart, limit_cycles=0)
        if not success:
            print("Errore: impossibile avviare VICE. Assicurati che 'x64sc' sia nel PATH.")
            sys.exit(1)

    print(f"Tentativo di connessione a VICE su {args.vice_host}:{args.vice_port}...")
    success, msg = repl.bridge.connect()
    if not success:
        print(f"Connessione fallita: {msg}")
        print("Assicurati che VICE sia in esecuzione con il monitor remoto abilitato (-monitorport o -binarymonitor).")
        sys.exit(1)

    try:
        repl.cmdloop()
    except KeyboardInterrupt:
        print("\nInterruzione da tastiera rilevata. Uscita.")
        repl.bridge.disconnect()

if __name__ == "__main__":
    main()
