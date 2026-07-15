# C64 Debugger (Sottomodulo di C64-Intelligence-SDK)

Questo repository contiene il modulo **C64-Debugger** per l'ecosistema **C64-Intelligence-SDK**.
Fornisce strumenti di debugging a basso livello, esecuzione passo-passo, emulazione e simulazione per Commodore 64.

## Funzionalità Principali

1. **VICERemoteMonitorBridge (`vice_bridge.py`)**:
   - Connessione e controllo remoto per il monitor dell'emulatore VICE (`x64sc`).
   - Avvio headless di VICE con limiti sui cicli di clock.
   - Lettura e scrittura diretta della memoria RAM e dei registri del processore MOS 6502.
   - Gestione di breakpoint e stepping delle istruzioni.

2. **C64DebuggerCore & C64DebuggerAgentHelper (`debugger_core.py`)**:
   - Gestione avanzata di breakpoint e watchpoint.
   - Analisi intelligente dei crash dump (rilevazione di Stack Overflow/Underflow, cicli infiniti ricorsivi ed esecuzioni RTS non valide).
   - Helper agentico integrabile con LLM per l'auto-riparazione del codice.

## Installazione

Per installare il package in modalità editabile:
```bash
pip install -e .
```
