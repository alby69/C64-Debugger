# C64 Debugger (Sottomodulo di C64-Intelligence-SDK)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Tests](https://img.shields.io/badge/tests-≥85%25-success)]()
[![Version](https://img.shields.io/badge/version-0.2.0-orange)]()

Modulo **C64-Debugger** per l'ecosistema **C64-Intelligence-SDK**.
Debugger Python avanzato per Commodore 64 con controllo remoto VICE, analisi AI e interfaccia moderna.

## Funzionalità Principali

### v0.2.0 (Corrente — Stabile)
1. **VICERemoteMonitorBridge** (`vice_bridge.py`):
   - Connessione e controllo remoto monitor VICE (`x64sc`)
   - Avvio headless VICE con limiti cicli clock
   - Lettura/scrittura diretta RAM e registri MOS 6502
   - Gestione breakpoint e stepping istruzioni
   - Retry connessione con exponential backoff

2. **C64DebuggerCore & C64DebuggerAgentHelper** (`debugger_core.py`):
   - Gestione avanzata breakpoint/watchpoint
   - Analisi intelligente crash dump (Stack Overflow/Underflow, cicli infiniti, RTS non validi)
   - Helper agentico integrabile con LLM per auto-riparazione codice

3. **Infrastructure**:
   - Protocollo monitor testuale astratto (`VICEMonitorProtocol`)
   - Configurazione esterna (`config.yaml` / `config.json`)
   - Logging strutturato con rotazione
   - Type hints completi
   - Test suite ≥85% copertura (mock server + integrazione)

### v0.3.0 (In Sviluppo)
- Disassembly strutturato e navigabile
- Stack trace 6502
- Breakpoint condizionati e watchpoint con maschera
- CLI REPL interattiva stile GDB
- Auto-completamento e history persistente

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

# CLI (da v0.3.0)
c64debugger --vice-host localhost --vice-port 6510
```

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
├── debugger_core.py        # Logica breakpoint/watchpoint/crash
├── disasm/                 # Disassembly & stack trace (v0.3.0)
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
