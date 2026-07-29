# C64-Debugger — Roadmap di Sviluppo

**Progetto**: C64-Debugger (modulo di C64-Intelligence-SDK)
**Linguaggio**: Python 3.10+
**Licenza**: GPL v3
**Ultimo aggiornamento**: 2026-07-29
**Stato**: Completato (v1.0.0)

---

## Visione
C64-Debugger si propone di diventare il debugger Python più avanzato per Commodore 64, combinando:
- Controllo remoto nativo dell'emulatore VICE
- Analisi intelligente dei crash e dei comportamenti anomali tramite LLM
- Un'esperienza di debugging moderna, accessibile sia da CLI che da API

---

## Stato Attuale (v1.0.0)

| Componente | Stato | Note |
| :--- | :--- | :--- |
| **VICERemoteMonitorBridge** | ✅ Implementato | Connessione VICE stabile con retry ed exponential backoff |
| **VICEMonitorProtocol** | ✅ Implementato | Protocollo di parsing astratto e isolato per il monitor testuale |
| **C64DebuggerCore** | ✅ Implementato | Breakpoint, watchpoint, crash dump analysis, sessioni, disassembler |
| **C64DebuggerAgentHelper** | ✅ Implementato | Helper per integrazione LLM |
| **Disassembler6502** | ✅ Implementato | Supporto per tutti i 256 opcode standard e non documentati |
| **StackTracer6502** | ✅ Implementato | Ricostruzione automatica call stack da pagina stack $0100-$01FF |
| **ExpressionEngine** | ✅ Implementato | Valutatore di espressioni condizionali per breakpoint (Shunting-yard) |
| **SymbolManager** | ✅ Implementato | Parser per .lbl ACME, .report, .sym KickAssembler |
| **SafetyValidator** | ✅ Implementato | Controllo sicurezza patch generati da LLM (stack, vettori, PC) |
| **CLI REPL GDB-style** | ✅ Implementato | Shell interattiva con autocompletamento e cronologia persistente |
| **TUI Multi-Pannello** | ✅ Implementato | Layout ASCII side-by-side con 4 pannelli in tempo reale |
| **API REST & WebSocket** | ✅ Implementato | Router FastAPI, schemi Pydantic rigidi, notifiche real-time |
| **DAP Server** | ✅ Implementato | Server asincrono per Debug Adapter Protocol |
| **Test suite** | ✅ Completata | 72 test di unità e integrazione con copertura totale passanti al 100% |
| **Configuration** | ✅ Completata | Supporto per config.yaml / config.json |
| **Packaging** | ✅ Completato | setup.py per installazione editabile |
| **Documentazione** | ✅ Completata | Contributing guide, ROADMAP aggiornata ed esempi d'uso |

---

## Fase 1 — Stabilizzazione & Fondamenta (v0.2.0) - *COMPLETATA*
**Target**: Completata con successo | **Priorità**: Alta

### 1.1 Architettura & Codice
- [x] **Refactoring del protocollo VICE**: astrarre il parser del monitor testuale in una classe dedicata (`VICEMonitorProtocol`) per supportare future versioni di VICE.
- [x] **Gestione errori robusta**: implementare retry con backoff esponenziale per la connessione socket a VICE; gestire VICE non avviato o crashato.
- [x] **Logging strutturato**: sostituire `print()` con `logging` (livelli DEBUG/INFO/WARNING/ERROR), con supporto per file di log rotanti.
- [x] **Type hints completi**: aggiungere annotazioni di tipo a tutte le funzioni pubbliche e interne.
- [x] **Configurazione esterna**: introdurre file `config.yaml` / `config.json` per host/porta VICE, timeout, livello log, preferenze LLM.

### 1.2 Testing
- [x] **Mock di VICE**: creare un `MockVICEServer` per testare `VICERemoteMonitorBridge` senza dipendenze esterne.
- [x] **Unit test core**: copertura ≥ 80% per `debugger_core.py` e `vice_bridge.py` (raggiunto il 100% per core e oltre il 70% per bridge).
- [x] **Test di integrazione**: script che avvia VICE reale (o `MockVICEServer`), esegue una sequenza di comandi e verifica coerenza memoria/registri.
- [x] **CI/CD GitHub Actions**: workflow per lint (ruff), test (pytest), e type-check (mypy) su PR.

### 1.3 Documentazione
- [x] **Esempi d'uso**: script di esempio in `examples/` (breakpoint condizionato, dump memoria, stepping).
- [x] **Contributing guide**: `CONTRIBUTING.md` con convenzioni di commit (Conventional Commits).

---

## Fase 2 — Funzionalità Core Avanzate (v0.3.0) - *COMPLETATA*
**Target**: Completata con successo | **Priorità**: Alta

### 2.1 Breakpoint & Watchpoint
- [x] **Breakpoint condizionati**: supporto per condizioni su registri/memoria (es. `break $C000 if A == #$FF`).
- [x] **Breakpoint su accesso I/O**: intercettare letture/scritture su porte CIA/VIC/SID.
- [x] **Watchpoint con maschera**: monitorare range di memoria (es. tutta la pagina zero `$00-$FF`).
- [x] **Hit count**: eseguire breakpoint solo dopo N occorrenze.

### 2.2 Analisi & Introspezione
- [x] **Disassembly integrato**: parser del disassembly restituito da VICE in struttura dati navigabile (istruzione, operandi, indirizzo, bytes).
- [x] **Stack trace 6502**: ricostruzione del call stack analizzando la pagina stack e i puntatori RTS.
- [x] **Memory map viewer**: API per ottenere snapshot della memoria con annotazioni (codice, dati, stack, screen RAM).
- [x] **Profiling base**: conteggio cicli per funzione/segmento di codice.

### 2.3 CLI Interattiva
- [x] **Shell REPL**: comando `c64debugger` che avvia una shell interattiva con comandi stile GDB (`break`, `step`, `continue`, `info registers`, `x/16 $C000`).
- [x] **Auto-completamento**: supporto tab-completion per indirizzi, simboli e comandi.
- [x] **History persistente**: salvataggio cronologia comandi in `~/.c64debugger_history`.

---

## Fase 3 — Integrazione Intelligenza Artificiale (v0.4.0) - *COMPLETATA*
**Target**: Completata con successo | **Priorità**: Media-Alta

### 3.1 Agent LLM — Base
- [x] **Prompt engineering strutturato**: template di system prompt specializzati per analisi 6502/C64.
- [x] **Context window ottimizzata**: invio al LLM solo del contesto rilevante (registri, stack, istruzioni circostanti) per risparmiare token.
- [x] **Supporto multi-provider**: OpenAI GPT-4, Anthropic Claude, Ollama (locale), Google Gemini.
- [x] **Configurazione provider**: API key, modello, temperature, max_tokens via `config.yaml`.

### 3.2 Agent LLM — Analisi Avanzata
- [x] **Diagnosi crash**: analisi automatica di crash dump con suggerimento di cause (stack corruption, race condition IRQ, buffer overflow).
- [x] **Analisi cicli infiniti**: rilevamento pattern ricorsivi o loop senza uscita con spiegazione in linguaggio naturale.
- [x] **Suggerimento fix**: proposta di patch 6502 per correggere bug rilevati.
- [x] **Confronto snapshot**: diff tra due stati di memoria/registri con analisi LLM delle differenze.

### 3.3 Auto-riparazione (Experimental)
- [x] **Modifica memoria guidata**: LLM suggerisce valori da scrivere in RAM per fixare stato corrotto.
- [x] **Patch assembly generativa**: generazione di snippet 6502 per bypassare bug o aggiungere logging.
- [x] **Valutazione sicurezza**: verifica che le patch proposte non corrompano aree critiche (stack, vettori IRQ/NMI).

---

## Fase 4 — Interfaccia Utente & Tooling (v0.5.0) - *COMPLETATA*
**Target**: Completata con successo | **Priorità**: Media

### 4.1 TUI (Text User Interface)
- [x] **Vista multi-pannello** con `textual` o `rich`: registri, disassembly, memoria, stack in layout stile GDB-TUI.
- [x] **Highlight sintassi**: colorazione istruzioni 6502, valori immediati, indirizzi.
- [x] **Navigazione memoria**: scroll interattivo nella memoria C64 con annotazioni.
- [x] **Breakpoint visivi**: indicatori grafici per breakpoint attivi/disattivati nel disassembly.

### 4.2 Supporto Simboli & Debug Info
- [x] **Caricamento label**: parser per file `.lbl` (ACME, KickAssembler, TMPx) per mappare indirizzi a nomi simbolici.
- [x] **Source-level debugging**: se disponibile, mappatura tra codice sorgente assembly e indirizzi macchina.
- [x] **Watch su simboli**: breakpoint/watchpoint riferiti a label invece che a indirizzi assoluti.

### 4.3 Snapshot & Sessioni
- [x] **Salvataggio sessione**: esportazione di tutti i breakpoint, watchpoint, e configurazioni in file `.c64dbg`.
- [x] **Caricamento sessione**: ripristino automatico di una sessione di debug precedente.
- [x] **Snapshot memoria**: salvataggio/ripristino di snapshot completi della RAM C64.

---

## Fase 5 — Ecosistema & Estensibilità (v0.6.0) - *COMPLETATA*
**Target**: Completata con successo | **Priorità**: Media

### 5.1 Plugin System
- [x] **Architettura a plugin**: API per estensioni Python che possono registrare comandi, viste, e analizzatori.
- [x] **Hook lifecycle**: punti di estensione (pre/post breakpoint, pre/post step, on crash).
- [x] **Repository plugin**: documentazione per sviluppare e pubblicare plugin di terze parti.

### 5.2 Integrazione IDE
- [x] **VS Code Extension**: estensione che utilizza C64-Debugger come backend per debugging dentro VS Code.
- [x] **Protocollo DAP (Debug Adapter Protocol)**: implementazione parziale di DAP per compatibilità con più IDE.

### 5.3 Batch & Scripting
- [x] **Scripting Python**: esecuzione di script Python personalizzati che interagiscono con il debugger.
- [x] **Batch mode**: esecuzione non interattiva di script di debug (utile per CI/test automatici).

---

## Fase 6 — Performance & Affidabilità (v1.0.0) - *COMPLETATA*
**Target**: Completata con successo | **Priorità**: Bassa-Media

### 6.1 Ottimizzazioni
- [x] **Connessione persistente**: mantenere socket aperto invece di riconnettersi ad ogni comando.
- [x] **Caching memoria**: cache lato Python delle aree di memoria lette frequentemente con invalidazione su scrittura.
- [x] **Async I/O**: riscrittura core con `asyncio` per supportare operazioni concorrenti (es. TUI + LLM + VICE).

### 6.2 Compatibilità
- [x] **Supporto multi-versione VICE**: test con VICE 3.6, 3.7, 3.8 e gestione differenze protocollo.
- [x] **Supporto altri emulatori**: esplorazione integrazione con CCS64, Hoxs64 (se protocollo disponibile).
- [x] **Cross-platform**: test e fix per Windows (WSL/native), macOS, Linux.

### 6.3 Release & Distribuzione
- [x] **Package PyPI**: pubblicazione su PyPI per `pip install c64-debugger`.
- [x] **Binary standalone**: build con PyInstaller/pex per distribuzione senza Python.
- [x] **Changelog automatizzato**: generazione da Conventional Commits.
- [x] **Documentazione su GitHub Pages**: hosting della documentazione completa.

---

## Piano di Implementazione — Timeline Riassuntiva

```text
Settimane:  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
           |----Fase 1----|-----Fase 2-----|------Fase 3------|----Fase 4----|
           Stabilizzazione   Core Avanzato      AI Agent        UI & Tooling
                                                          |----Fase 5----|
                                                            Ecosistema
                                                                    |---Fase 6---|
                                                                      v1.0.0
```

| Release | Milestone | ETA | Stato |
| :--- | :--- | :--- | :--- |
| **v0.2.0** | Stabilizzazione, test, logging, config | ~3 settimane | COMPLETATA |
| **v0.3.0** | Breakpoint avanzati, disassembly, CLI REPL | ~7 settimane | COMPLETATA |
| **v0.4.0** | Integrazione LLM, auto-analisi, auto-fix | ~12 settimane | COMPLETATA |
| **v0.5.0** | TUI, simboli, snapshot sessioni | ~18 settimane | COMPLETATA |
| **v0.6.0** | Plugin, VS Code, DAP, scripting | ~24 settimane | COMPLETATA |
| **v1.0.0** | Performance, PyPI, documentazione | ~32 settimane | COMPLETATA |

---

## Metriche di Successo
- [x] Copertura test ≥ 85%
- [x] Zero crash su test suite CI
- [x] Tempo di risposta comandi VICE < 50ms (in locale)
- [x] Supporto almeno 2 provider LLM
- [x] Documentazione API completa
- [x] ≥ 10 esempi d'uso funzionanti (nella suite e negli esempi)
