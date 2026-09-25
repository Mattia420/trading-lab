# Risultati del backtest (settembre 2026)

Capitale iniziale 2.000 €, 5 € a ordine, tasse al 26%, bollo 0,2%. "Netto finale" = quanto resta
dopo aver venduto tutto e pagato le tasse. Tabelle complete in `output.md`.

## Cosa dicono i numeri
- **Nessuna strategia dà guadagno alto con rischio basso.** Chi rende di più ha anche i cali peggiori.
- **Le banche italiane non sono "basso rischio"**: -86% di calo massimo (2007-2012), -6,6% l'anno nel
  2006-2015, poi +15% l'anno dal 2016. Guadagno reale, ma solo per chi ha resistito a perdere quasi tutto.
- **Il timing (trend, dual momentum) ha protetto nelle crisi del 2008 e del 2011**, ma dal 2016 ha reso
  la metà del compra e tieni, perché esce ed entra nei momenti sbagliati dopo cali brevi (2018, 2020, 2022).
  Ogni uscita fa anche pagare tasse, e sugli ETF le perdite non compensano i guadagni.
- **Il bilanciato (azioni + obbligazioni + oro) ha avuto un calo massimo simile al timing (-23%) con un
  rendimento migliore e meno ordini.** La riduzione del rischio l'ha data la diversificazione, non il timing.

## Proposta per la fase 2 (paper trading)
Bot che gestisce il portafoglio bilanciato: ribilancia una volta l'anno o quando un peso esce di oltre
5 punti, con un "freno" di trend opzionale da confrontare in paper trading.

## Limiti di questa simulazione
- ETF americani con storia lunga usati come controfigure degli ETF UCITS di Milano (convertiti in euro).
- Liquidità allo 0% (prudente per le strategie di timing).
- Quote frazionarie; commissioni da verificare sul foglio costi del broker scelto.
- Il passato non garantisce il futuro: 20 anni sono un solo "percorso" possibile del mercato.
