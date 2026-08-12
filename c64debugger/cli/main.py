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
    parser.add_argument(
        "--batch",
        type=str,
        help="Percorso di un file di script Python (.py) da eseguire in modalità batch"
    )
    parser.add_argument(
        "--dap-port",
        type=int,
        help="Porta su cui avviare il server DAP (Debug Adapter Protocol)"
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

    if args.dap_port:
        print(f"Avvio del server DAP (Debug Adapter Protocol) sulla porta {args.dap_port}...")
        from c64debugger.dap.dap_server import C64DAPServer
        import time
        dap_server = C64DAPServer(host="127.0.0.1", port=args.dap_port, core=repl.core, bridge=repl.bridge)
        dap_server.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nArresto del server DAP...")
            dap_server.stop()
            sys.exit(0)

    print(f"Tentativo di connessione a VICE su {args.vice_host}:{args.vice_port}...")
    success, msg = repl.bridge.connect()
    if not success:
        print(f"Connessione fallita: {msg}")
        print("Assicurati che VICE sia in esecuzione con il monitor remoto abilitato (-monitorport o -binarymonitor).")
        sys.exit(1)

    if args.batch:
        print(f"Esecuzione in modalità batch del file '{args.batch}'...")
        import os
        import importlib.util
        from c64debugger.plugin.plugin_manager import _registered_scripts

        if not os.path.exists(args.batch):
            print(f"Errore: file di script batch '{args.batch}' non trovato.")
            sys.exit(1)

        try:
            # Pulisci gli script precedentemente registrati
            _registered_scripts.clear()

            # Carica dinamicamente lo script
            spec = importlib.util.spec_from_file_location("c64dbg_batch_script", args.batch)
            if spec is None or spec.loader is None:
                print(f"Errore: impossibile caricare lo script '{args.batch}'.")
                sys.exit(1)

            module = importlib.util.module_from_spec(spec)
            sys.modules["c64dbg_batch_script"] = module
            spec.loader.exec_module(module)

            if not _registered_scripts:
                print("Avviso: nessun blocco decorato con '@c64_script' trovato nello script.")
            else:
                for func in _registered_scripts:
                    print(f"Esecuzione dello script: {func.__name__}...")
                    func(repl)
            print("Modalità batch completata con successo.")
            repl.bridge.disconnect()
            sys.exit(0)
        except Exception as e:
            print(f"Errore durante l'esecuzione del batch: {e}")
            repl.bridge.disconnect()
            sys.exit(1)

    try:
        repl.cmdloop()
    except KeyboardInterrupt:
        print("\nInterruzione da tastiera rilevata. Uscita.")
        repl.bridge.disconnect()

if __name__ == "__main__":
    main()
