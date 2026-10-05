# Validazione delle strategie

Dati mensili 01/2006 - 08/2026, in euro. Costi: 25 punti base di commissione + 10 di slippage per ogni euro scambiato. Tasse escluse (sono in `backtest.py`).

**Tentativi contati: 8** (tutte le varianti provate in questo progetto, comprese quelle scartate).

## Risultati e Sharpe sgonfiato

Per chi fa timing la domanda giusta non è "guadagna?" ma "guadagna più del semplice compra e tieni?": lo Sharpe sgonfiato è calcolato sulla differenza col suo riferimento.

| Strategia | Rendimento annuo | Calo max | Sharpe | Confronto | Sharpe sgonfiato | Cancello 2 |
|---|---|---|---|---|---|---|
| Azionario 60/40 USA-mondo (compra e tieni) | +9,3% | -48,8% | 0.74 | assoluto | 0.95 | ✅ |
| Bilanciato azioni-bond-oro (compra e tieni) | +8,7% | -22,1% | 0.99 | assoluto | 1.00 | ✅ |
| Trend 10 mesi azionario mondo | +8,3% | -19,7% | 0.93 | vs Azionario 60/40 USA-mondo | 0.01 | ❌ |
| Dual momentum | +8,7% | -21,1% | 0.73 | vs Azionario 60/40 USA-mondo | 0.03 | ❌ |
| Borsa USA (compra e tieni) | +11,3% | -46,8% | 0.83 | assoluto | 0.98 | ✅ |
| Trend 10 mesi USA, sotto in liquidità | +9,3% | -24,5% | 0.89 | vs Borsa USA | 0.00 | ❌ |
| Trend 10 mesi USA, sotto ETF inverso | +6,0% | -37,4% | 0.43 | vs Borsa USA | 0.00 | ❌ |
| Banche italiane (compra e tieni) | +4,7% | -86,6% | 0.31 | assoluto | 0.42 | ❌ |

Lo Sharpe sgonfiato è la probabilità che il vantaggio sia reale e non fortuna dopo 8 tentativi: serve almeno 0,95. Con 8 tentativi, uno Sharpe annuo di circa 0.35 si otterrebbe anche per puro caso.

## Walk-forward: la media mobile scelta solo sul passato

Per ogni anno dal 2011: si sceglie la media mobile migliore (6, 8, 10 o 12 mesi) guardando solo i 5 anni precedenti, la si usa per i 12 mesi successivi, poi si ripete.

| Strategia | Anni meglio / pari / peggio del compra e tieni | Anno peggiore vs compra e tieni | Totale fuori campione vs compra e tieni |
|---|---|---|---|
| Trend USA, sotto in liquidità | 0 / 3 / 12 | -15,8% | -53,3% |
| Trend USA, sotto ETF inverso | 0 / 3 / 12 | -26,1% | -76,5% |

Parametri scelti anno per anno (ultima strategia): 2011: 10, 2012: 10, 2013: 12, 2014: 6, 2015: 12, 2016: 8, 2017: 12, 2018: 10, 2019: 10, 2020: 10, 2021: 10, 2022: 10, 2023: 10, 2024: 10, 2025: 10.
Se il parametro "migliore" cambia spesso, non c'è un valore stabile: è rumore.
Cancello 3 superato solo se gli anni migliori sono più dei peggiori E il totale fuori campione è positivo: Trend USA, sotto in liquidità ❌, Trend USA, sotto ETF inverso ❌.

## Per fase di mercato (rendimento medio mensile)

| Strategia | Rialzo | Laterale | Ribasso |
|---|---|---|---|
| Azionario 60/40 USA-mondo (compra e tieni) | +0,8% | +1,0% | +0,0% |
| Bilanciato azioni-bond-oro (compra e tieni) | +0,7% | +0,9% | +0,3% |
| Trend 10 mesi azionario mondo | +0,8% | +0,7% | +0,2% |
| Dual momentum | +0,7% | +0,9% | +0,4% |
| Borsa USA (compra e tieni) | +1,0% | +1,2% | +0,1% |
| Trend 10 mesi USA, sotto in liquidità | +1,0% | +0,8% | +0,0% |
| Trend 10 mesi USA, sotto ETF inverso | +0,9% | +0,5% | -0,2% |
| Banche italiane (compra e tieni) | +1,5% | +0,3% | +0,2% |

Mesi per fase: rialzo 129, laterale 93, ribasso 25. Il campione contiene sia rialzi sia ribassi (2008, 2011, 2020, 2022).

## Verdetto

Una strategia può usare soldi veri solo se supera tutti e tre i cancelli (1: nessuna sbirciata al futuro, verificato dai test; 2: Sharpe sgonfiato ≥ 0,95; 3: walk-forward). Per le strategie di timing il confronto è con il compra e tieni.

- ✅ Azionario 60/40 USA-mondo (compra e tieni)
- ✅ Bilanciato azioni-bond-oro (compra e tieni)
- ❌ Trend 10 mesi azionario mondo
- ❌ Dual momentum
- ✅ Borsa USA (compra e tieni)
- ❌ Trend 10 mesi USA, sotto in liquidità
- ❌ Trend 10 mesi USA, sotto ETF inverso
- ❌ Banche italiane (compra e tieni)