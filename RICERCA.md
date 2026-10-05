# Ricerca: cosa funziona davvero sui mercati (ottobre 2026)

Obiettivo: trovare metodi con prove solide, adatti a un piccolo investitore italiano, solo al rialzo,
su ETF. Ogni idea testabile è passata dai tre cancelli (`validate.py`, `ipotesi.py`, `ipotesi_giro2.py`).

## 1. Il quadro generale: perché la maggior parte dei metodi non funziona

| Prova | Cosa dice | Fonte |
|---|---|---|
| 97 "anomalie" pubblicate | Rendono il 26% in meno fuori campione e il **58% in meno dopo la pubblicazione** | McLean e Pontiff, *Journal of Finance* 2016 ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623)) |
| 452 anomalie ritestate | Il **65% non si replica**; con la soglia per test multipli fallisce l'82% | Hou, Xue e Zhang, *Review of Financial Studies* 2020 ([ResearchGate](https://www.researchgate.net/publication/345507035_Replicating_Anomalies)) |
| 316 fattori pubblicati | Una nuova scoperta deve superare un t-statistico di 3, non di 2: molti risultati sono fortuna | Harvey, Liu e Zhu, *Review of Financial Studies* 2016 ([Duke](https://people.duke.edu/~charvey/Research/Published_Papers/P118_and_the_cross.PDF)) |
| Fondi attivi in Europa | A 10 anni il **94–98%** dei fondi azionari globali fa peggio dell'indice | SPIVA Europe 2025 ([S&P](https://www.spglobal.com/spdji/en/spiva/article/spiva-europe-mid-year-2025)) |
| Day trader a Taiwan, 1992–2006 | **Meno dell'1%** guadagna in modo prevedibile al netto dei costi | Barber, Lee, Liu e Odean ([Berkeley](https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/Day%20Trade%20040330.pdf)) |
| 66.465 famiglie, 1991–1996 | Chi opera di più guadagna l'11,4% l'anno contro il 17,9% del mercato | Barber e Odean, *Journal of Finance* 2000 ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=219228)) |
| CFD in Europa | Dal **74 all'89%** dei conti retail perde soldi | ESMA ([decisione](https://www.esma.europa.eu/node/84933)) |
| Analisi tecnica | 56 studi su 95 positivi, ma con data snooping e costi sottostimati; sulle azioni i profitti spariscono dalla fine degli anni '80 | Park e Irwin, *Journal of Economic Surveys* 2007 ([Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-6419.2007.00519.x)) |

## 2. Metodi con le prove più solide, e cosa è successo quando li abbiamo testati

| Metodo | Prove pubblicate | Nostro test (euro, costi veri, contro il riferimento) | Verdetto |
|---|---|---|---|
| **Portafoglio diversificato compra e tieni** | Base di tutta la teoria del portafoglio; batte il 94–98% dei gestori (SPIVA) | Bilanciato: 8,7% l'anno lordo, calo max -22% | ✅ **Usato** |
| Trend following (media mobile) | Un secolo di prove, positivo in 8 delle 10 crisi peggiori (Hurst, Ooi e Pedersen 2017, [AQR](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing)) | Riduce i cali ma rende meno; walk-forward 0 anni vinti su 15 contro il compra e tieni | ❌ |
| Trend multi-asset di Faber (5 asset) | Fuori campione 2006–2012: 4,8% contro 3,5% ([Faber](https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf)) | 6,3% contro 8,8% del bilanciato; calo max -10% contro -22% | ❌ (ma rischio dimezzato) |
| Fattori: momentum, qualità, bassa volatilità, value | Premi storici documentati, ma ciclici e ridotti dopo la pubblicazione | ETF UCITS mondiali 2015–2026: 10,2% contro 10,7% dell'azionario mondo | ❌ |
| "Sell in May" / effetto Halloween | Presente in 89 paesi su 114, anche fuori campione ([Jacobsen e Zhang](https://www.sciencedirect.com/science/article/abs/pii/S0261560620302242)) | 6,7% contro 8,7% del bilanciato; 8 anni migliori, 12 peggiori | ❌ |
| Rotazione tra mercati (momentum) | Momentum tra asset class documentato | 7,8% contro 8,7% | ❌ |
| Freno di volatilità | La volatilità si raggruppa | 6,0% con calo max -11% | ❌ (ma rischio dimezzato) |
| Effetto fine mese | Documentato | Guadagno lordo 2,3% l'anno, mangiato dai costi | ❌ |
| Dual momentum (Antonacci) | Libro e studi 2012–2014 | Non supera lo Sharpe sgonfiato | ❌ |
| Rischio bilanciato senza leva | Teoria della leva vincolata | 7,6% con calo max -10% | ❌ (ma rischio dimezzato) |

Tentativi contati in totale: **23**. Dettagli in `VALIDAZIONE.md`, `IPOTESI.md` e `IPOTESI_2.md`.

## 3. Metodi scartati senza test (per motivi di principio)

- **Dividendi come "reddito gratis"**: il prezzo scende dell'importo del dividendo. È un errore di
  ragionamento documentato da Hartzmark e Solomon ([Chicago Booth](https://www.chicagobooth.edu/review/dividends-are-not-free-money-though-lots-investors-seem-think-they-are)).
  In Italia, in più, il dividendo si tassa subito.
- **Day trading, CFD, leva, opzioni**: le statistiche al punto 1 bastano.
- **Strategie a breve termine sulle cripto** (come gli esempi del video): sono incompatibili con il "rischiare poco".
- **Segnali, corsi e bot "AI" a pagamento**: CONSOB ha oscurato oltre 200 siti abusivi nel 2026.

## 4. Da tenere d'occhio (non ancora testabile con i nostri dati)

- **Managed futures** (trend following su decine di mercati futures, anche al ribasso, dentro un fondo
  regolato): è il modo serio di avere "guadagni anche quando la borsa scende" come diversificazione.
  Esiste in versione UCITS su Borsa Italiana (es. iMGP DBi Managed Futures, quotato da marzo 2025,
  TER 0,75%, [scheda](https://www.imgp.com/imgp-dbi-managed-futures-fund/)). La storia europea è troppo breve
  per i nostri tre cancelli: da rivalutare quando ci saranno dati sufficienti.

## 5. Conclusioni pratiche

1. **Il vantaggio per un piccolo investitore non viene dal timing ma dai costi, dalla diversificazione e dalla costanza.**
2. **Costi:** con 5 € a ordine, un piccolo capitale perde in commissioni più di quanto il mercato renda in mesi.
   Directa offre centinaia di ETF senza commissioni (da verificare se sono inclusi quelli del bilanciato);
   Trade Republic e Scalable Capital offrono PAC gratuiti da 1 € con quote frazionate e regime amministrato
   (Trade Republic da gennaio 2025, Scalable dal 1° settembre 2026).
3. **Versare una cifra fissa ogni mese**: investire tutto subito batte il versamento graduale circa 2 volte
   su 3 (Vanguard, 1926–2015), ma per chi investe dallo stipendio il PAC è il metodo naturale e senza costi.
4. **Le varianti "a rischio dimezzato"** (Faber 5 asset, freno di volatilità, rischio bilanciato) non battono il
   bilanciato sul rendimento, ma hanno avuto cali massimi intorno al -10%. Sono un'opzione per chi
   vuole meno oscillazioni accettando di guadagnare meno.
