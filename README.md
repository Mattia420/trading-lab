# trading-lab

Laboratorio personale per un bot di investimento **a regole** su ETF di Borsa Italiana, costruito per fasi:

1. **Backtest** ✅: `python backtest.py` confronta strategie su 20 anni di dati, in euro, con commissioni,
   tasse italiane e bollo. Risultati commentati in `RISULTATI.md`.
   **Validazione** ✅: `python validate.py` applica i tre cancelli (nessuna sbirciata al futuro, Sharpe
   sgonfiato per il numero di tentativi, walk-forward) e scrive `VALIDAZIONE.md`. La revisione critica
   del codice con le 8 domande è in `CRITICA.md`.
   **Giro di ipotesi** ✅: `python ipotesi.py` mette alla prova idee nuove solo al rialzo contro il
   bilanciato e scrive `IPOTESI.md`. Primo giro (05/10/2026): 4 ipotesi, tutte scartate.
   Secondo giro (`ipotesi_giro2.py` → `IPOTESI_2.md`): le 3 idee con più prove pubblicate, tutte scartate.
   La ricerca con le fonti è in `RICERCA.md`.
2. **Paper trading** ⏳ (in corso): il bot gira ogni giorno feriale dopo la chiusura, con soldi finti e prezzi veri.
3. **Soldi veri, pochi**: il bot *propone* gli ordini, il proprietario li approva uno per uno.

## Il bot in paper trading

Tre portafogli da 2.000 € (finti) girano in parallelo, per confrontarli sul campo:

| Portafoglio | Regola |
|---|---|
| `bilanciato` | 60% azioni mondo, 25% titoli di Stato euro, 15% oro; ribilancia se un peso si sposta di oltre 5 punti |
| `trend_liquidita` | S&P 500 sopra la media di 10 mesi, altrimenti monetario euro; decide a inizio mese |
| `trend_short` | S&P 500 sopra la media di 10 mesi, altrimenti ETF inverso; decide a inizio mese |

Dove guardare:
- **`STATO.md`**: la situazione aggiornata di tutti i portafogli.
- **`journal/`**: il diario di ogni giorno, con ogni decisione e il motivo.
- `state/`: lo stato dei conti simulati (non modificare a mano).

Come gira: `.github/workflows/paper.yml` lo avvia dal lunedì al venerdì alle 17:15 UTC, esegue i test,
fa il giro giornaliero e salva diario e stato con un commit. Si può avviare anche a mano da
*Actions → Bot paper trading → Run workflow*. In locale: `python -m bot.run --dry-run`.

## Controlli di rischio (`bot/risk.py`)

Regole fisse nel codice, che nessuna strategia può scavalcare:
- **Stop totale:** se nella cartella principale esiste un file `STOP`, il bot non fa niente.
- **Dati sospetti:** prezzo mancante, vecchio di oltre 4 giorni o salto di oltre il 15% in un giorno → nessun ordine.
- **Perdita giornaliera oltre il 5%** → nessun ordine quel giorno.
- **Calo dal massimo oltre il 30%** → portafoglio bloccato finché il proprietario non decide
  (per sbloccarlo: togliere `halted` da `state/<portafoglio>.json`).
- Solo strumenti in elenco, niente vendite allo scoperto, niente leva, massimo 6 ordini al giorno.

Simulazione: ordini decisi dopo la chiusura ed eseguiti all'apertura del giorno dopo con 10 punti base
di slippage, quote intere, 5 € a ordine, tasse al 26% sulle
plusvalenze (sugli ETF le minusvalenze non compensano), bollo 0,2% a inizio anno.

Credenziali del broker (fase 3): solo in variabili d'ambiente o segreti di GitHub, mai nel repository.

## Regola d'oro (dal metodo di validazione)

Nessuna strategia passa a soldi veri se non supera tutti e tre i cancelli di `validate.py`.
Ogni nuova idea si aggiunge in `all_trials()`, anche quelle scartate: il conteggio onesto dei tentativi
è ciò che rende affidabile lo Sharpe sgonfiato. Le condizioni di stop si decidono prima di partire
(`bot/config.json → risk`) e non si cambiano mentre si perde.
