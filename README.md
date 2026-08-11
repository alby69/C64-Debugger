# C64 Debugger (Sottomodulo di C64-Intelligence-SDK)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Tests](https://img.shields.io/badge/tests-≥85%25-success)]()
[![Version](https://img.shields.io/badge/version-0.5.0-orange)]()

Modulo **C64-Debugger** per l'ecosistema **C64-Intelligence-SDK**.
Debugger Python avanzato per Commodore 64 con controllo remoto VICE, analisi AI e interfaccia moderna.

## Funzionalità Principali

### v0.5.0 (Corrente — In Sviluppo / Fase 4)
1. **Supporto Simboli & Label** (`symbols/`):
   - Parser automatico e robusto di file simboli generati da **ACME**, **KickAssembler**, **TMPx** e altri assemblatori.
   - Mappatura bidirezionale (nome simbolo $\leftrightarrow$ indirizzo di memoria).
   - Risoluzione dei simboli in tutti i comandi REPL (`break`, `watch`, `x`, ecc.) in modo da poter ispezionare codice con label al posto di costanti numeriche.
   - Comando `load_symbols <filepath>` per caricare le label dinamicamente.
   - Autocompletamento via Tab delle label nei comandi REPL.

2. **Snapshot & Sessioni** (`session.py`):
   - Salvataggio e caricamento dello stato completo della sessione di debug (breakpoint, condizioni, hit count, watchpoint, intervalli, path dei simboli caricati) in formato `.c64dbg` (JSON).
   - Salvataggio e caricamento di snapshot completi della memoria RAM del Commodore 64 (file binari `.bin`) in tempo reale direttamente tramite il bridge.
   - Comandi REPL dedicati: `save_session`, `load_session`, `save_snapshot`, `load_snapshot`.

3. **Text User Interface (TUI Dashboard)** (`tui/`):
   - Una dashboard TUI interattiva visualizzabile con il comando `tui`.
   - Layout multi-pannello a pieno schermo che disegna lo stato aggiornato di registri, flag della CPU 6502 (NV-BDIZC), disassembly, istruzione corrente, e porzione di memoria/sorgente con puntatori interattivi.
   - Evidenziazione sintassi ANSI 6502 intelligente (`highlight_6502_assembly`) per opcodi, immediati, indirizzi, registri e commenti.

4. **Integrazione AI Agent (Fase 3 - v0.4.0)**:
   - Integrazione multi-provider LLM (OpenAI, Anthropic, Gemini, Ollama, C64-LLM) con urllib sincrono integrato.
   - Diagnosi crash automatica ed analisi intelligente del call stack (Stack Overflow/Underflow, cicli infiniti, RTS non bilanciati).
   - Prompt engineering strutturato per suggerimenti di fix in assembly 6502 o BASIC.

### v0.3.0 (Precedente — Stabile)
1. **VICERemoteMonitorBridge** (`vice_bridge.py`):
   - Connessione e controllo remoto monitor VICE (`x64sc`)
   - Avvio headless VICE con limiti cicli clock
   - Lettura/scrittura diretta RAM e registri MOS 6502
   - Gestione breakpoint e stepping istruzioni
   - Retry connessione con exponential backoff

2. **C64DebuggerCore & C64DebuggerAgentHelper** (`debugger_core.py`):
   - Gestione avanzata breakpoint/watchpoint
   - Breakpoint condizionati (es: `break $C000 if A == 0xFF`)
   - Watchpoint su intervalli/range (es: `watch $C000-$CFFF`)
   - Breakpoint con hit count (attivazione dopo N occorrenze)
   - Intercettazione accessi I/O per i chip VIC/SID/CIA

3. **Introspezione & Profiling** (`disasm/`):
   - Disassembly strutturato e navigabile (`disassembler.py`)
   - Stack trace 6502 con RTS tracking (`stack.py`)
   - Mappa della memoria con annotazioni delle regioni del C64 (`memory_map.py`)
   - Profiler delle prestazioni per conteggio esecuzioni (hits) e cicli CPU (`profiler.py`)

4. **CLI REPL Interattiva** (`cli/`):
   - Shell interattiva completa (`c64debugger`) con comandi GDB-style
   - Auto-completamento avanzato con tab
   - Cronologia/history persistente salvata in `~/.c64debugger_history`

## Installazione

```bash
# Modalità editabile (sviluppo)
pip install -e .

# Avvio della CLI REPL
c64debugger --vice-host localhost --vice-port 6510
```

## Shell REPL Interattiva — Comandi Principali

All'interno della REPL `c64debugger` sono disponibili i seguenti comandi:

- **`break <addr|symbol>` / `b <addr|symbol>`**: Imposta un breakpoint su indirizzo o label.
  - Esempio semplice: `break $C000` o `break start_label`
  - Esempio condizionato: `break $C000 if A == 0xFF`
  - Esempio hit count: `break $C000 hit 5` (si ferma solo alla 5a occorrenza)
- **`watch <addr|symbol>`**: Imposta un watchpoint di memoria.
- **`watch_range <start|symbol> <end|symbol>`**: Imposta un watchpoint su un intervallo di memoria.
- **`step` / `s`**: Esegue un singolo step (istruzione successiva) e mostra i registri CPU.
- **`continue` / `c` / `g`**: Riprende l'esecuzione normale dell'emulatore.
- **`info <registers|break|memory|profiler|symbols>`**: Mostra informazioni sullo stato:
  - `info registers`: Mostra i registri correnti della CPU.
  - `info break`: Mostra i breakpoint configurati.
  - `info memory`: Mostra la mappa complessiva della memoria del C64.
  - `info profiler`: Mostra le statistiche raccolte dal profiler.
  - `info symbols`: Mostra i simboli/label caricati in memoria.
- **`x <start_addr|symbol> [end_addr_or_length]`**: Esamina la memoria con annotazioni delle regioni C64.
  - Esempio: `x $C000 16` o `x my_data 16`
- **`load_symbols <filepath>`**: Carica un file di label ACME/KickAssembler/TMPx.
- **`save_session <filepath>` / `load_session <filepath>`**: Salva/carica lo stato del debugger (.c64dbg).
- **`save_snapshot <filepath>` / `load_snapshot <filepath>`**: Salva/carica dump di RAM completi (.bin).
- **`tui`**: Avvia l'interfaccia utente grafica interattiva a pieno schermo (TUI Dashboard).
- **`profile <start|stop|reset|report>`**: Controlla il profiler delle prestazioni.
- **`quit` / `exit`**: Esci dal debugger.

## Esempi d'Uso
Vedi directory `examples/`:
- `breakpoint_conditional.py` — breakpoint con condizione su registro A
- `memory_dump.py` — dump memoria con annotazioni
- `stepping.py` — esecuzione passo-passo con stack trace
- `ai_diagnose.py` — analisi crash con LLM (v0.4.0+)

## Architettura
```plain
c64_debugger/
├── vice_bridge.py          # Connessione socket VICE
├── vice_protocol.py        # Parser protocollo monitor
├── debugger_core.py        # Logica breakpoint/watchpoint/crash/I/O
├── disasm/                 # Disassembly, stack trace, memory map & profiler (v0.3.0)
├── cli/                    # REPL interattiva (v0.3.0)
├── tui/                    # Text User Interface (v0.5.0)
├── llm/                    # Provider AI & prompt (v0.4.0)
├── symbols/                # Parser label & source map (v0.5.0)
├── plugin/                 # API estensioni (v0.6.0)
├── dap/                    # Debug Adapter Protocol (v0.6.0)
├── session.py              # Gestione sessioni e snapshot (v0.5.0)
└── cache/                  # Caching memoria (v1.0.0)
```

## Contributing
Vedi `CONTRIBUTING.md`. Convenzioni commit: Conventional Commits.

## Roadmap
Vedi `ROADMAP.md` per il piano di implementazione completo con task granulari e timeline.

## License
GPL v3 — vedi `LICENSE`.
