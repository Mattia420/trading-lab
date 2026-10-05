# Giro di ipotesi solo al rialzo

Dati mensili 01/2006 - 08/2026 in euro, costi 25 + slippage 10 punti base per ogni euro scambiato, tasse escluse.
**Riferimento da battere: il bilanciato** (+8,7% l'anno, calo max -22,1%, Sharpe 0.99).

**Tentativi contati: 20** (gli 8 precedenti più ogni variante provata qui).

## Risultati con il parametro fissato a priori

| Ipotesi | Rendimento annuo | Calo max | Sharpe | Sharpe sgonfiato vs bilanciato | Cancello 2 |
|---|---|---|---|---|---|
| H1 Rotazione tra mercati (6 mesi, i 2 migliori) | +7,8% | -18,4% | 0.76 | 0.00 | ❌ |
| H2 Bilanciato con freno di volatilità (8%) | +6,0% | -11,4% | 1.04 | 0.00 | ❌ |
| H3 Effetto fine mese (3 giorni) | -5,9% | -72,6% | -0.83 | 0.00 | ❌ |
| H4 Rischio bilanciato (12 mesi) | +7,6% | -10,3% | 0.97 | 0.00 | ❌ |

## Walk-forward contro il bilanciato

Ogni anno dal 2011 si sceglie il parametro solo sui 5 anni precedenti e lo si usa per l'anno dopo.

| Ipotesi | Anni meglio / peggio del bilanciato | Anno peggiore vs bilanciato | Totale fuori campione vs bilanciato | Parametri scelti | Cancello 3 |
|---|---|---|---|---|---|
| H1 Rotazione tra mercati (6 mesi, i 2 migliori) | 6 / 9 | -21,2% | -35,4% | 3, 9, 12 (mesi) | ❌ |
| H2 Bilanciato con freno di volatilità (8%) | 1 / 14 | -10,2% | -41,9% | 0.1, 0.06, 0.08 (vol. obiettivo) | ❌ |
| H3 Effetto fine mese (3 giorni) | 0 / 15 | -31,0% | -90,9% | 4, 3 (giorni) | ❌ |
| H4 Rischio bilanciato (12 mesi) | 2 / 11 | -7,9% | -28,5% | 6, 12 (mesi) | ❌ |

## Verdetto

Passa in paper trading solo un'ipotesi che supera **entrambi** i cancelli statistici (il cancello 1, nessuna sbirciata al futuro, è garantito dal motore e dai test).

- ❌ SCARTATA: H1 Rotazione tra mercati (6 mesi, i 2 migliori) (Sharpe sgonfiato no, walk-forward no)
- ❌ SCARTATA: H2 Bilanciato con freno di volatilità (8%) (Sharpe sgonfiato no, walk-forward no)
- ❌ SCARTATA: H3 Effetto fine mese (3 giorni) (Sharpe sgonfiato no, walk-forward no)
- ❌ SCARTATA: H4 Rischio bilanciato (12 mesi) (Sharpe sgonfiato no, walk-forward no)
