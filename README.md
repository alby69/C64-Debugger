# C64 Debugger (Sottomodulo di C64-Intelligence-SDK)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Tests](https://img.shields.io/badge/tests-≥85%25-success)]()
[![Version](https://img.shields.io/badge/version-0.3.0-orange)]()

Modulo **C64-Debugger** per l'ecosistema **C64-Intelligence-SDK**.
Debugger Python avanzato per Commodore 64 con controllo remoto VICE, analisi AI e interfaccia moderna.

## Funzionalità Principali

### v0.3.0 (Corrente — Stabile)
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
   - Analisi intelligente crash dump (Stack Overflow/Underflow, cicli infiniti, RTS non validi)
   - Helper agentico integrabile con LLM per auto-riparazione codice

3. **Introspezione & Profiling** (`disasm/`):
   - Disassembly strutturato e navigabile (`disassembler.py`)
   - Stack trace 6502 con RTS tracking (`stack.py`)
   - Mappa della memoria con annotazioni delle regioni del C64 (`memory_map.py`)
   - Profiler delle prestazioni per conteggio esecuzioni (hits) e cicli CPU (`profiler.py`)

4. **CLI REPL Interattiva** (`cli/`):
   - Shell interattiva completa (`c64debugger`) con comandi GDB-style
   - Auto-completamento avanzato con tab
   - Cronologia/history persistente salvata in `~/.c64debugger_history`

5. **Infrastructure**:
   - Protocollo monitor testuale astratto (`VICEMonitorProtocol`)
   - Configurazione esterna (`config.yaml` / `config.json`)
   - Logging strutturato con rotazione
   - Type hints completi
   - Test suite ≥85% copertura (mock server + integrazione)

### v0.4.0 (Pianificato)
- Integrazione multi-provider LLM (OpenAI, Anthropic, Ollama, Gemini)
- Diagnosi crash automatica e spiegazione in linguaggio naturale
- Suggerimento patch 6502 generative
- Auto-riparazione guidata con valutazione sicurezza

### v0.5.0 (Pianificato)
- TUI multi-pannello con `textual` (registri, disassembly, memoria, stack)
- Supporto simboli (`.lbl` ACME/KickAssembler/TMPx)
- Source-level debugging
- Snapshot e sessioni persistenti (`.c64dbg`)

### v1.0.0 (Target)
- Async I/O, connessione persistente, caching memoria
- Plugin system, VS Code extension, DAP protocol
- Distribuzione PyPI e binary standalone
- Documentazione completa su GitHub Pages

## Installazione

```bash
# Modalità editabile (sviluppo)
pip install -e .

# Avvio della CLI REPL
c64debugger --vice-host localhost --vice-port 6510
```

## Shell REPL Interattiva — Comandi Principali

All'interno della REPL `c64debugger` sono disponibili i seguenti comandi:

- **`break <addr>` / `b <addr>`**: Imposta un breakpoint.
  - Esempio semplice: `break $C000`
  - Esempio condizionato: `break $C000 if A == 0xFF`
  - Esempio hit count: `break $C000 hit 5` (si ferma solo alla 5a occorrenza)
- **`step` / `s`**: Esegue un singolo step (istruzione successiva) e mostra i registri CPU.
- **`continue` / `c` / `g`**: Riprende l'esecuzione normale dell'emulatore.
- **`info <registers|break|memory|profiler>`**: Mostra informazioni sullo stato:
  - `info registers`: Mostra i registri correnti della CPU.
  - `info break`: Mostra i breakpoint configurati.
  - `info memory`: Mostra la mappa complessiva della memoria del C64.
  - `info profiler`: Mostra le statistiche raccolte dal profiler.
- **`x <start_addr> [end_addr_or_length]`**: Esamina la memoria con annotazioni delle regioni C64.
  - Esempio: `x $C000 16` (mostra 16 byte a partire da $C000).
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
├── session.py              # Gestione sessioni (v0.5.0)
└── cache/                  # Caching memoria (v1.0.0)
```

## Contributing
Vedi `CONTRIBUTING.md`. Convenzioni commit: Conventional Commits.

## Roadmap
Vedi `ROADMAP.md` per il piano di implementazione completo con task granulari e timeline.

## License
GPL v3 — vedi `LICENSE`.
