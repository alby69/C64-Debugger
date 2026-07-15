# C64-Debugger — Roadmap di Sviluppo

**Progetto**: C64-Debugger (modulo di C64-Intelligence-SDK)
**Linguaggio**: Python 3.10+
**Licenza**: GPL v3
**Ultimo aggiornamento**: 2026-07-15

---

## Visione
C64-Debugger si propone di diventare il debugger Python più avanzato per Commodore 64, combinando:
- Controllo remoto nativo dell'emulatore VICE
- Analisi intelligente dei crash e dei comportamenti anomali tramite LLM
- Un'esperienza di debugging moderna, accessibile sia da CLI che da API

---

## Stato Attuale (v0.2.0)

| Componente | Stato | Note |
| :--- | :--- | :--- |
| **VICERemoteMonitorBridge** | ✅ Implementato | Connessione VICE stabile con retry ed exponential backoff |
| **VICEMonitorProtocol** | ✅ Implementato | Protocollo di parsing astratto e isolato per il monitor testuale |
| **C64DebuggerCore** | ✅ Implementato | Breakpoint, watchpoint, crash dump analysis |
| **C64DebuggerAgentHelper** | ✅ Implementato | Helper per integrazione LLM |
| **Test suite** | ✅ Completata | Copertura test ≥ 85% con mock server e test di integrazione |
| **Configuration** | ✅ Completata | Supporto per config.yaml / config.json |
| **Packaging** | ✅ Completato | setup.py per installazione editabile |
| **Documentazione** | ✅ Completata | Contributing guide, esempi d'uso e roadmap completa |

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

## Fase 2 — Funzionalità Core Avanzate (v0.3.0)
**Target**: 3-4 settimane | **Priorità**: Alta

### 2.1 Breakpoint & Watchpoint
- [ ] **Breakpoint condizionati**: supporto per condizioni su registri/memoria (es. `break $C000 if A == #$FF`).
- [ ] **Breakpoint su accesso I/O**: intercettare letture/scritture su porte CIA/VIC/SID.
- [ ] **Watchpoint con maschera**: monitorare range di memoria (es. tutta la pagina zero `$00-$FF`).
- [ ] **Hit count**: eseguire breakpoint solo dopo N occorrenze.

### 2.2 Analisi & Introspezione
- [ ] **Disassembly integrato**: parser del disassembly restituito da VICE in struttura dati navigabile (istruzione, operandi, indirizzo, bytes).
- [ ] **Stack trace 6502**: ricostruzione del call stack analizzando la pagina stack e i puntatori RTS.
- [ ] **Memory map viewer**: API per ottenere snapshot della memoria con annotazioni (codice, dati, stack, screen RAM).
- [ ] **Profiling base**: conteggio cicli per funzione/segmento di codice.

### 2.3 CLI Interattiva
- [ ] **Shell REPL**: comando `c64debugger` che avvia una shell interattiva con comandi stile GDB (`break`, `step`, `continue`, `info registers`, `x/16 $C000`).
- [ ] **Auto-completamento**: supporto tab-completion per indirizzi, simboli e comandi.
- [ ] **History persistente**: salvataggio cronologia comandi in `~/.c64debugger_history`.

---

## Fase 3 — Integrazione Intelligenza Artificiale (v0.4.0)
**Target**: 4-5 settimane | **Priorità**: Media-Alta

### 3.1 Agent LLM — Base
- [ ] **Prompt engineering strutturato**: template di system prompt specializzati per analisi 6502/C64.
- [ ] **Context window ottimizzata**: invio al LLM solo del contesto rilevante (registri, stack, istruzioni circostanti) per risparmiare token.
- [ ] **Supporto multi-provider**: OpenAI GPT-4, Anthropic Claude, Ollama (locale), Google Gemini.
- [ ] **Configurazione provider**: API key, modello, temperature, max_tokens via `config.yaml`.

### 3.2 Agent LLM — Analisi Avanzata
- [ ] **Diagnosi crash**: analisi automatica di crash dump con suggerimento di cause (stack corruption, race condition IRQ, buffer overflow).
- [ ] **Analisi cicli infiniti**: rilevamento pattern ricorsivi o loop senza uscita con spiegazione in linguaggio naturale.
- [ ] **Suggerimento fix**: proposta di patch 6502 per correggere bug rilevati.
- [ ] **Confronto snapshot**: diff tra due stati di memoria/registri con analisi LLM delle differenze.

### 3.3 Auto-riparazione (Experimental)
- [ ] **Modifica memoria guidata**: LLM suggerisce valori da scrivere in RAM per fixare stato corrotto.
- [ ] **Patch assembly generativa**: generazione di snippet 6502 per bypassare bug o aggiungere logging.
- [ ] **Valutazione sicurezza**: verifica che le patch proposte non corrompano aree critiche (stack, vettori IRQ/NMI).

---

## Fase 4 — Interfaccia Utente & Tooling (v0.5.0)
**Target**: 4-6 settimane | **Priorità**: Media

### 4.1 TUI (Text User Interface)
- [ ] **Vista multi-pannello** con `textual` o `rich`: registri, disassembly, memoria, stack in layout stile GDB-TUI.
- [ ] **Highlight sintassi**: colorazione istruzioni 6502, valori immediati, indirizzi.
- [ ] **Navigazione memoria**: scroll interattivo nella memoria C64 con annotazioni.
- [ ] **Breakpoint visivi**: indicatori grafici per breakpoint attivi/disattivati nel disassembly.

### 4.2 Supporto Simboli & Debug Info
- [ ] **Caricamento label**: parser per file `.lbl` (ACME, KickAssembler, TMPx) per mappare indirizzi a nomi simbolici.
- [ ] **Source-level debugging**: se disponibile, mappatura tra codice sorgente assembly e indirizzi macchina.
- [ ] **Watch su simboli**: breakpoint/watchpoint riferiti a label invece che a indirizzi assoluti.

### 4.3 Snapshot & Sessioni
- [ ] **Salvataggio sessione**: esportazione di tutti i breakpoint, watchpoint, e configurazioni in file `.c64dbg`.
- [ ] **Caricamento sessione**: ripristino automatico di una sessione di debug precedente.
- [ ] **Snapshot memoria**: salvataggio/ripristino di snapshot completi della RAM C64.

---

## Fase 5 — Ecosistema & Estensibilità (v0.6.0)
**Target**: 5-6 settimane | **Priorità**: Media

### 5.1 Plugin System
- [ ] **Architettura a plugin**: API per estensioni Python che possono registrare comandi, viste, e analizzatori.
- [ ] **Hook lifecycle**: punti di estensione (pre/post breakpoint, pre/post step, on crash).
- [ ] **Repository plugin**: documentazione per sviluppare e pubblicare plugin di terze parti.

### 5.2 Integrazione IDE
- [ ] **VS Code Extension**: estensione che utilizza C64-Debugger come backend per debugging dentro VS Code.
- [ ] **Protocollo DAP (Debug Adapter Protocol)**: implementazione parziale di DAP per compatibilità con più IDE.

### 5.3 Batch & Scripting
- [ ] **Scripting Python**: esecuzione di script Python personalizzati che interagiscono con il debugger.
- [ ] **Batch mode**: esecuzione non interattiva di script di debug (utile per CI/test automatici).

---

## Fase 6 — Performance & Affidabilità (v1.0.0)
**Target**: 6-8 settimane | **Priorità**: Bassa-Media

### 6.1 Ottimizzazioni
- [ ] **Connessione persistente**: mantenere socket aperto invece di riconnettersi ad ogni comando.
- [ ] **Caching memoria**: cache lato Python delle aree di memoria lette frequentemente con invalidazione su scrittura.
- [ ] **Async I/O**: riscrittura core con `asyncio` per supportare operazioni concorrenti (es. TUI + LLM + VICE).

### 6.2 Compatibilità
- [ ] **Supporto multi-versione VICE**: test con VICE 3.6, 3.7, 3.8 e gestione differenze protocollo.
- [ ] **Supporto altri emulatori**: esplorazione integrazione con CCS64, Hoxs64 (se protocollo disponibile).
- [ ] **Cross-platform**: test e fix per Windows (WSL/native), macOS, Linux.

### 6.3 Release & Distribuzione
- [ ] **Package PyPI**: pubblicazione su PyPI per `pip install c64-debugger`.
- [ ] **Binary standalone**: build con PyInstaller/pex per distribuzione senza Python.
- [ ] **Changelog automatizzato**: generazione da Conventional Commits.
- [ ] **Documentazione su GitHub Pages**: hosting della documentazione completa.

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

| Release | Milestone | ETA |
| :--- | :--- | :--- |
| **v0.2.0** | Stabilizzazione, test, logging, config | ~3 settimane (COMPLETATA) |
| **v0.3.0** | Breakpoint avanzati, disassembly, CLI REPL | ~7 settimane |
| **v0.4.0** | Integrazione LLM, auto-analisi, auto-fix | ~12 settimane |
| **v0.5.0** | TUI, simboli, snapshot sessioni | ~18 settimane |
| **v0.6.0** | Plugin, VS Code, DAP, scripting | ~24 settimane |
| **v1.0.0** | Performance, PyPI, documentazione | ~32 settimane |

---

## Metriche di Successo
- [x] Copertura test ≥ 85%
- [x] Zero crash su test suite CI
- [ ] Tempo di risposta comandi VICE < 50ms (in locale)
- [ ] Supporto almeno 2 provider LLM
- [ ] Documentazione API completa
- [x] ≥ 10 esempi d'uso funzionanti (nella suite e negli esempi)
