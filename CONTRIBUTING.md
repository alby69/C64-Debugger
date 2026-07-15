# Contributing to C64-Debugger

Grazie per voler contribuire a **C64-Debugger**! Per garantire uno sviluppo coordinato, di qualità ed efficiente, segui le linee guida descritte in questo documento.

## Modello di Branching

Il progetto utilizza una versione adattata di Git Flow:
- **`main`**: contiene solo codice stabile e pronto per il rilascio in produzione (es. v0.2.0, v1.0.0). Questa branch è protetta.
- **`develop`**: branch di integrazione principale per lo sviluppo di nuove funzionalità della versione corrente.
- **`feat/nome-feature`**: branch dedicate allo sviluppo di nuove funzionalità o miglioramenti (es. `feat/vice-protocol-refactor`). Create a partire da `develop` e integrate nuovamente tramite Pull Request.
- **`bugfix/nome-bug`**: branch dedicate alla risoluzione di problemi riscontrati su `develop`.

## Convenzioni sui Commit (Conventional Commits)

Per consentire la generazione automatica del Changelog, tutti i messaggi di commit devono seguire lo standard **Conventional Commits 1.0.0**:

```
<tipo>(<ambito>): <descrizione breve>

[corpo del messaggio dettagliato, se necessario]

[riferimenti a issue, es: Closes #12]
```

### Tipi di Commit Ammessi:
- **`feat`**: Nuova funzionalità (es. `feat(vice): add exponential backoff retry to connect`)
- **`fix`**: Correzione di un bug (es. `fix(core): handle stack overflow check correctly`)
- **`docs`**: Modifiche alla documentazione (es. `docs: add contributing guide`)
- **`style`**: Modifiche di formattazione o stile che non cambiano la logica del codice (es. spazi, type hints)
- **`refactor`**: Ristrutturazione del codice senza aggiungere nuove feature o correggere bug (es. `refactor(protocol): abstract vice monitor parsing`)
- **`test`**: Aggiunta o correzione di test (es. `test: add mock vice server tests`)
- **`chore`**: Aggiornamenti minori relativi a build tool o dipendenze.

## Requisiti per le Pull Request (PR)

Ogni Pull Request verso `develop` o `main` deve rispettare i seguenti requisiti prima di poter essere integrata:
1. **Test passanti**: Tutta la test suite deve passare senza errori (`PYTHONPATH=. pytest`).
2. **Copertura dei Test**: La copertura complessiva dei test per le modifiche introdotte deve essere pari o superiore all'**85%** (e ad almeno l'80% per i moduli core).
3. **Type hints**: Il nuovo codice deve essere completamente tipizzato e passare i controlli di tipo (`mypy`).
4. **Documentazione aggiornata**: Le modifiche pubbliche devono essere documentate (es. docstrings e guide).
5. **Review obbligatoria**: Almeno un manutentore del progetto deve approvare i cambiamenti.
