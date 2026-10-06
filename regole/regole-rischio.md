# Regole di rischio — Mattia — bozza scritta da Claude il 06/10/2026, da rivedere insieme

Queste regole valgono finché il proprietario non le cambia. Il bot e il comitato non possono
inventarle né modificarle. Ogni modifica si scrive qui, con data, prima di applicarla.

## Capitale
- Capitale reale previsto: **100 €**, versato una volta sola (nessun versamento mensile per ora).
- Capitale reale nel portafoglio passivo (`reale_100`): 100%. Nel portafoglio operativo: **0 €**
  (resta simulato finché non soddisfa le condizioni sotto).

## Strumenti
- Ammessi: solo ETF/ETC UCITS quotati su Borsa Italiana elencati in `bot/config.json → risk.allowed_tickers`.
- Vietati: azioni singole, criptovalute, CFD, opzioni, certificati, leva, vendite allo scoperto,
  ETF a leva o inversi con soldi veri (l'ETF inverso resta solo nel test simulato `trend_short`).

## Costi
- Commissione massima accettabile per un ordine reale: **1% dell'importo dell'ordine**.
- Costi totali previsti in un anno (commissioni + bollo): **massimo 1,5% del capitale**.
  Se una strategia li supera, il comitato la RIFIUTA per i soldi veri, qualunque sia il rendimento.

## Perdite
- Portafoglio passivo: nessuna vendita per paura. Se scende più del **20% dal massimo**, il comitato
  dice ASPETTA e si fa una revisione insieme (non una vendita automatica). Orizzonte: 5 anni.
- Portafoglio operativo (simulato): blocco automatico se scende più del **15% dal massimo**.
- Limiti tecnici del bot (perdita giornaliera, calo massimo, dati sospetti): `bot/config.json → risk`.

## Operazioni
- Portafoglio passivo: ribilanciamento solo se un peso si sposta di oltre **10 punti**, al massimo
  **una volta l'anno**.
- Portafoglio operativo: decide una volta al mese, al massimo **10 ordini al mese**.

## Quando una strategia può passare a soldi veri
Tutte e tre le condizioni:
1. supera i tre cancelli di `validate.py` (nessuna sbirciata al futuro, Sharpe sgonfiato, walk-forward);
2. almeno **3 mesi** di simulazione dal vivo senza anomalie;
3. costi entro i limiti sopra **con il capitale reale disponibile**.

## Approvazione umana
Ogni ordine reale va approvato e registrato da **Mattia** nel diario (`comitato/`) prima di essere
eseguito. Il bot e Claude non eseguono mai ordini reali. APPROVO del comitato significa solo
"il piano è completo e rispetta le regole", non "compra".

## Prossima revisione di queste regole
Entro il **6/11/2026**, oppure prima di qualunque versamento.
