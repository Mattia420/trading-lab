# Risultati del backtest (aggiornati il 04/10/2026)

> **Correzione del 04/10/2026.** La revisione critica (`CRITICA.md`) ha trovato una sbirciata al futuro:
> si decideva e si comprava alla stessa chiusura mensile. Ora si decide con il mese prima e si esegue
> al prezzo del mese dopo, e i numeri qui sotto sono quelli corretti. Le strategie di timing sono
> peggiorate, il compra e tieni è rimasto praticamente uguale. La validazione completa (Sharpe sgonfiato,
> walk-forward, fasi di mercato) è in `VALIDAZIONE.md`.

Capitale iniziale 2.000 €, 5 € a ordine, tasse al 26%, bollo 0,2%. "Netto finale" = quanto resta
dopo aver venduto tutto e pagato le tasse. Tabelle complete in `output.md`.

## Cosa dicono i numeri
- **Nessuna strategia dà guadagno alto con rischio basso.** Chi rende di più ha anche i cali peggiori.
- **Le banche italiane non sono "basso rischio"**: -86% di calo massimo (2007-2012), -6,6% l'anno nel
  2006-2015, poi +15% l'anno dal 2016. Guadagno reale, ma solo per chi ha resistito a perdere quasi tutto.
- **Il timing ha ridotto i cali** (trend azionario mondo: -27% contro -49% del compra e tieni), ma dal 2016
  ha reso molto meno (3,8% contro 10,0% l'anno) perché esce ed entra nei momenti sbagliati: vende dopo cali
  brevi e ricompra quando i prezzi sono già risaliti. Il dual momentum ha tenuto meglio (6,8% l'anno, -23%),
  ma non supera il test dello Sharpe sgonfiato (`VALIDAZIONE.md`).
  Ogni uscita fa anche pagare tasse, e sugli ETF le perdite non compensano i guadagni.
- **Il bilanciato (azioni + obbligazioni + oro) ha avuto un calo massimo simile o migliore del timing (-23%)
  con un rendimento più alto (6,7% l'anno contro 4,2% del trend) e meno ordini.** La riduzione del rischio l'ha data la diversificazione, non il timing.

## Proposta per la fase 2 (paper trading)
Bot che gestisce il portafoglio bilanciato: ribilancia una volta l'anno o quando un peso esce di oltre
5 punti, con un "freno" di trend opzionale da confrontare in paper trading.

## Limiti di questa simulazione
- ETF americani con storia lunga usati come controfigure degli ETF UCITS di Milano (convertiti in euro).
- Liquidità allo 0% (prudente per le strategie di timing).
- Quote frazionarie; commissioni da verificare sul foglio costi del broker scelto.
- Il passato non garantisce il futuro: 20 anni sono un solo "percorso" possibile del mercato.

## Test aggiuntivo: guadagnare anche quando la borsa scende (ETF inverso)
Stessa regola di trend sulla borsa USA: sopra la media di 10 mesi investiti, sotto si compra un ETF
inverso (che sale quando la borsa scende). Netto finale da 2.000 €:

| | 2006 - 08/2026 | 2006-2015 | 2016 - 08/2026 |
|---|---|---|---|
| Compra e tieni | 13.835 € (9,9%/anno, calo max -47%) | 6,4%/anno | 12,5%/anno |
| Trend, sotto la media in liquidità | 5.339 € (4,9%/anno, -28%) | 5,1%/anno | 5,1%/anno |
| Trend, sotto la media ETF inverso | 2.517 € (1,1%/anno, -51%) | 4,9%/anno | -2,2%/anno |

Andare "short" ha peggiorato tutto: il segnale arriva quando il calo è già in parte avvenuto, spesso
la borsa rimbalza subito dopo e la posizione inversa perde. Gli ETF inversi reali a ribilanciamento
giornaliero perdono valore anche nei mercati che oscillano senza direzione.
