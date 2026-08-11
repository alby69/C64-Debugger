# C64-Debugger — Roadmap di Sviluppo

**Progetto**: C64-Debugger (modulo di C64-Intelligence-SDK)
**Linguaggio**: Python 3.10+
**Licenza**: GPL v3
**Ultimo aggiornamento**: 2026-08-11

---

## Visione

C64-Debugger si propone di diventare il debugger Python più avanzato per Commodore 64, combinando:

- Controllo remoto nativo dell'emulatore VICE
- Analisi intelligente dei crash e dei comportamenti anomali tramite LLM
- Un'esperienza di debugging moderna, accessibile da CLI, TUI, API e IDE

---

## Stato Attuale (v0.2.0) ✅ COMPLETATA

| Componente | Stato | Note |
|------------|-------|------|
| VICERemoteMonitorBridge | ✅ Implementato | Connessione stabile con retry ed exponential backoff |
| VICEMonitorProtocol | ✅ Implementato | Protocollo parsing astratto e isolato |
| C64DebuggerCore | ✅ Implementato | Breakpoint, watchpoint, crash dump analysis |
| C64DebuggerAgentHelper | ✅ Implementato | Helper per integrazione LLM (stub base) |
| Test suite | ✅ Completata | Copertura ≥85% con mock server e test integrazione |
| Configuration | ✅ Completata | Supporto `config.yaml` / `config.json` |
| Packaging | ✅ Completato | `setup.py` per installazione editabile |
| Documentazione | ✅ Completata | Contributing guide, esempi d'uso, roadmap |

---

## Fase 2 — Core Avanzato (v0.3.0) 🚧 IN SVILUPPO

**Target**: 6 settimane | **Priorità**: Alta | **ETA**: ~7 settimane totali

### 2.1 Disassembly & Introspezione

| # | Task | Stato | Note |
|---|------|-------|------|
| 2.1.1 | Parser disassembly VICE in oggetti `Instruction` | 🔲 | Addr, bytes, mnemonic, operand, addressing mode |
| 2.1.2 | Stack trace 6502 (analisi pagina $0100-$01FF) | 🔲 | Ricostruzione call stack via RTS tracking |
| 2.1.3 | Memory map viewer con annotazioni | 🔲 | CODE/DATA/STACK/SCREEN/VIC/SID/CIA |
| 2.1.4 | Profiler base (conteggio cicli per funzione) | 🔲 | Basato su breakpoint trace |

### 2.2 Breakpoint & Watchpoint Avanzati

| # | Task | Stato | Note |
|---|------|-------|------|
| 2.2.1 | Breakpoint condizionati | 🔲 | `break $C000 if A == #$FF` |
| 2.2.2 | Breakpoint accesso I/O | 🔲 | Intercettazione CIA/VIC/SID |
| 2.2.3 | Watchpoint con maschera range | 🔲 | `watch $C000-$CFFF` |
| 2.2.4 | Hit count | 🔲 | Attivazione dopo N occorrenze |

### 2.3 CLI Interattiva

| # | Task | Stato | Note |
|---|------|-------|------|
| 2.3.1 | Shell REPL (`c64debugger`) | 🔲 | Comandi stile GDB |
| 2.3.2 | Comandi base: break, step, continue, info, x | 🔲 | |
| 2.3.3 | Auto-completamento tab | 🔲 | Indirizzi, comandi, simboli |
| 2.3.4 | History persistente | 🔲 | `~/.c64debugger_history` |

---

## Fase 3 — Intelligenza Artificiale (v0.4.0) 📋 PIANIFICATA

**Target**: 8 settimane | **Priorità**: Alta | **ETA**: ~15 settimane totali

### 3.1 Agent LLM — Base

| # | Task | Stato | Note |
|---|------|-------|------|
| 3.1.1 | Provider Manager (OpenAI, Anthropic, Ollama, Gemini) | 🔲 | Astrazione `LLMProvider` |
| 3.1.2 | Configurazione provider in `config.yaml` | 🔲 | api_key, model, temperature, max_tokens |
| 3.1.3 | Prompt engineering 6502/C64 | 🔲 | System prompt specializzati |
| 3.1.4 | Context Window Optimizer | 🔲 | Invio solo contesto rilevante |

### 3.2 Agent LLM — Analisi Avanzata

| # | Task | Stato | Note |
|---|------|-------|------|
| 3.2.1 | Diagnosi crash automatica | 🔲 | Stack corruption, race IRQ, buffer overflow |
| 3.2.2 | Analisi cicli infiniti | 🔲 | Pattern ricorsivi/loop senza uscita |
| 3.2.3 | Suggerimento fix 6502 | 🔲 | Patch generative con metadati |
| 3.2.4 | Confronto snapshot diff | 🔲 | Analisi LLM differenze stati |

### 3.3 Auto-riparazione (Experimental)

| # | Task | Stato | Note |
|---|------|-------|------|
| 3.3.1 | Modifica memoria guidata | 🔲 | LLM suggerisce valori RAM |
| 3.3.2 | Patch assembly generativa | 🔲 | Snippet 6502 per bypass bug |
| 3.3.3 | Valutazione sicurezza patch | 🔲 | Verifica aree critiche protette |

---

## Fase 4 — Interfaccia Utente & Tooling (v0.5.0) 📋 PIANIFICATA

**Target**: 8 settimane | **Priorità**: Media | **ETA**: ~23 settimane totali

### 4.1 TUI (Text User Interface)

| # | Task | Stato | Note |
|---|------|-------|------|
| 4.1.1 | Layout multi-pannello (textual) | 🔲 | Registri, disassembly, memoria, stack |
| 4.1.2 | Highlight sintassi 6502 | 🔲 | Opcode, immediati, indirizzi, label |
| 4.1.3 | Navigazione memoria interattiva | 🔲 | Scroll con annotazioni |
| 4.1.4 | Breakpoint visivi | 🔲 | Indicatori ●/○ nel disassembly |

### 4.2 Supporto Simboli & Debug Info

| # | Task | Stato | Note |
|---|------|-------|------|
| 4.2.1 | Parser file `.lbl` (ACME, KickAssembler, TMPx) | 🔲 | Mappa indirizzi → nomi |
| 4.2.2 | Source-level debugging | 🔲 | Mappatura sorgente ↔ macchina |
| 4.2.3 | Watch su simboli | 🔲 | `watch myLabel` |

### 4.3 Snapshot & Sessioni

| # | Task | Stato | Note |
|---|------|-------|------|
| 4.3.1 | Salvataggio sessione `.c64dbg` | 🔲 | Breakpoint, watch, config, layout |
| 4.3.2 | Caricamento sessione | 🔲 | Ripristino automatico |
| 4.3.3 | Snapshot RAM completo | 🔲 | Save/load stato memoria |

---

## Fase 5 — Ecosistema & Estensibilità (v0.6.0) 📋 PIANIFICATA

**Target**: 8 settimane | **Priorità**: Media | **ETA**: ~31 settimana totali

### 5.1 Plugin System

| # | Task | Stato | Note |
|---|------|-------|------|
| 5.1.1 | Architettura a plugin | 🔲 | API registrazione comandi/viste/analizzatori |
| 5.1.2 | Hook lifecycle | 🔲 | pre/post breakpoint, step, crash |
| 5.1.3 | Repository plugin | 🔲 | Docs sviluppo terze parti |

### 5.2 Integrazione IDE

| # | Task | Stato | Note |
|---|------|-------|------|
| 5.2.1 | VS Code Extension | 🔲 | Backend per debugging in VS Code |
| 5.2.2 | Protocollo DAP | 🔲 | Implementazione parziale Debug Adapter Protocol |

### 5.3 Batch & Scripting

| # | Task | Stato | Note |
|---|------|-------|------|
| 5.3.1 | Scripting Python | 🔲 | Decoratore `@c64_script` |
| 5.3.2 | Batch mode | 🔲 | `c64debugger --batch script.py` |

---

## Fase 6 — Performance & Affidabilità (v1.0.0) 📋 PIANIFICATA

**Target**: 8 settimane | **Priorità**: Media | **ETA**: ~39 settimane totali

### 6.1 Ottimizzazioni

| # | Task | Stato | Note |
|---|------|-------|------|
| 6.1.1 | Async I/O rewrite | 🔲 | `asyncio` per concorrenza TUI+LLM+VICE |
| 6.1.2 | Connessione persistente | 🔲 | Socket aperto con reconnect |
| 6.1.3 | Caching memoria | 🔲 | Cache lato Python con invalidazione |

### 6.2 Compatibilità

| # | Task | Stato | Note |
|---|------|-------|------|
| 6.2.1 | Multi-versione VICE | 🔲 | Test 3.6/3.7/3.8, gestione differenze |
| 6.2.2 | Cross-platform | 🔲 | Windows (WSL/native), macOS, Linux |
| 6.2.3 | Supporto altri emulatori | 🔲 | Esplorazione CCS64, Hoxs64 |

### 6.3 Release & Distribuzione

| # | Task | Stato | Note |
|---|------|-------|------|
| 6.3.1 | Package PyPI | 🔲 | `pip install c64-debugger` |
| 6.3.2 | Binary standalone | 🔲 | PyInstaller/pex |
| 6.3.3 | Changelog automatizzato | 🔲 | Da Conventional Commits |
| 6.3.4 | Documentazione GitHub Pages | 🔲 | Hosting completo |

---

## Miglioramenti Aggiuntivi (Backlog)

| # | Feature | Priorità | Fase Target |
|---|---------|----------|-------------|
| A1 | Parser formati C64 (PRG/D64/CRT) | Media | v0.5.x |
| A2 | BASIC V2 Decoder | Bassa | v0.6.x |
| A3 | Reverse Debugging (step backward) | Media | v0.7.0 |
| A4 | VIC-II/SID/CIA State Inspection | Media | v0.5.x |
| A5 | Memory Heatmap & Access Patterns | Bassa | v0.6.x |
| A6 | Collaborative Debugging (session sharing) | Bassa | v0.7.0 |
| A7 | Security Hardening (input validation, sandbox) | Alta | v0.3.x |

---

## Timeline Riassuntiva Aggiornata
```text
Settimane:  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40
|----Fase 1----|------Fase 2-------|--------Fase 3--------|--------Fase 4--------|--------Fase 5--------|--------Fase 6--------|
Stabilizzazione     Core Avanzato        AI Agent           UI & Tooling           Ecosistema            Performance/Release
✅ COMPLETATA      🚧 IN SVILUPPO      📋 PIANIFICATA      📋 PIANIFICATA         📋 PIANIFICATA         📋 PIANIFICATA
```

| Release | Milestone | ETA Cumulativa |
|---------|-----------|----------------|
| **v0.2.0** | Stabilizzazione, test, logging, config | ✅ Completata |
| **v0.3.0** | Breakpoint avanzati, disassembly, CLI REPL | ~7 settimane |
| **v0.4.0** | Integrazione LLM, auto-analisi, auto-fix | ~15 settimane |
| **v0.5.0** | TUI, simboli, snapshot sessioni | ~23 settimane |
| **v0.6.0** | Plugin, VS Code, DAP, scripting | ~31 settimane |
| **v1.0.0** | Performance, PyPI, documentazione | ~39 settimane |

---

## Metriche di Successo

- Copertura test ≥ 85% (target v1.0.0: ≥90%)
- Zero crash su test suite CI
- Tempo di risposta comandi VICE < 50ms (in locale)
- Supporto almeno 3 provider LLM (OpenAI, Anthropic, Ollama)
- Documentazione API completa
- ≥ 15 esempi d'uso funzionanti
- Installazione via `pip install c64-debugger` (v1.0.0)
