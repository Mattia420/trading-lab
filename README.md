# trading-lab

Laboratorio personale per un bot di investimento **a regole**, costruito per fasi:

1. **Backtest** (questa fase): `python backtest.py` confronta strategie su 20 anni di dati, in euro,
   con commissioni, tasse italiane (26%) e bollo. Risultati commentati in `RISULTATI.md`.
2. **Paper trading**: il bot gira su un conto demo e scrive un resoconto giornaliero.
3. **Soldi veri, pochi**: il bot *propone* gli ordini, il proprietario li approva uno per uno.

Regole di sicurezza che valgono in ogni fase:
- Le decisioni le prendono regole scritte e testate, non l'AI. L'AI controlla, spiega e segnala anomalie.
- I limiti di rischio sono nel codice e non si possono scavalcare.
- Credenziali del broker solo in variabili d'ambiente, mai nel repository.
