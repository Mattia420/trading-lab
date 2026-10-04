# Revisione critica: gli 8 modi in cui un backtest mente

Revisione fatta il 04/10/2026 con la lista delle 8 domande, sul codice **prima** delle correzioni
(commit `2c77563`). Per ogni punto: PRESENTE o ASSENTE, la riga citata, e cosa è stato fatto.

## A. `backtest.py` (simulazione storica)

**1. Sbirciata al futuro (il segnale è sfasato prima di diventare posizione?): PRESENTE**
```
130:        row = p.loc[d]
131:        hist = p.loc[:d]
135:            target = {t: w for t, w in strat(hist).items() if t != "CASH"}
```
La decisione usa la chiusura del mese `d` ed esegue allo stesso prezzo `row = p.loc[d]`.
→ **Corretto:** `hist = p.loc[:d].iloc[:-1]`, quindi si decide con il mese prima e si esegue al prezzo di questo mese.
Effetto: il trend con l'ETF inverso passa da 3,4% a 1,1% l'anno sui 20 anni.

**2. Sopravvivenza (ci sono titoli poi falliti o tolti dal listino?): PRESENTE (solo nel riferimento banche)**
```
24:TICKERS = ["SPY", "EFA", "IEF", "GLD", "SHY", "SH", "EURUSD=X", "ISP.MI", "UCG.MI"]
```
Intesa e UniCredit sono state scelte sapendo che esistono ancora oggi. Nel 2006 un investitore poteva
scegliere anche altre banche quotate: Banca Etruria è stata messa in risoluzione nel 2015, Carige ha quasi
azzerato i suoi azionisti e MPS è stata salvata dallo Stato.
Le banche restano solo come riferimento e non vanno mai considerate un risultato ottenibile.
Gli ETF su indici non hanno questo problema: l'indice sostituisce da solo le aziende che escono.

**3. Indicatori che "ridisegnano" il passato (medie centrate, resample incompleto): PRESENTE**
```
41:    m = px.ffill().resample("ME").last().loc[start:]
```
L'ultimo mese, ancora in corso, veniva trattato come una chiusura mensile vera.
→ **Corretto:** il mese incompleto viene scartato. Le medie mobili guardano solo indietro
(`iloc[-10:].mean()`), quindi qui il problema non c'è.

**4. Costi (commissioni E slippage sui volumi scambiati?): PRESENTE**
```
114:        cash += q * price - commissione
```
C'è la commissione ma non lo slippage. → **Corretto in `validate.py`:** 25 punti base di commissione
più 10 di slippage per ogni euro scambiato.

**5. Prezzo di esecuzione (si compra a un prezzo che non è mai stato disponibile?): PRESENTE**
È lo stesso problema del punto 1: si compra alla chiusura usata per decidere, ma quella
chiusura si conosce solo quando non si può più comprare a quel prezzo. → Corretto come al punto 1.

**6. Parametri (quanti, e scelti guardando tutti i dati?): ATTENZIONE**
```
60:        above = h[t].iloc[-1] > h[t].iloc[-10:].mean()
67:    r = {t: h[t].iloc[-1] / h[t].iloc[-13] - 1 for t in ("SPY", "EFA")}
```
I parametri sono 4: media a 10 mesi, momentum a 12 mesi, pesi 60/40 e 40/20/25/15, ribilanciamento annuale.
Non li ho ottimizzati sui nostri dati, li ho presi dalla letteratura (Faber 2007, Antonacci 2012).
Però quei valori sono diventati famosi proprio perché avevano funzionato in passato, quindi una
parte di adattamento ai dati c'è comunque. → Contati **8 tentativi** nello Sharpe sgonfiato, e il
walk-forward sceglie la media solo sul passato (`validate.py`).

**7. Campione (contiene sia mercati in rialzo sia in ribasso?): ASSENTE (il campione va bene)**
Il periodo va da 01/2006 a 08/2026 e comprende 2008, 2011, 2020 e 2022. In `validate.py` i risultati sono
divisi per fase di mercato: 129 mesi di rialzo, 93 laterali e 25 di ribasso.

**8. Allineamento dei dati (stesso fuso orario e stessa ora di chiusura?): PRESENTE (lieve)**
```
39:        px[t] = px[t] / fx
```
Gli ETF USA chiudono alle 22:00 ora italiana, mentre il cambio EUR/USD di Yahoo chiude a un orario diverso.
Su dati mensili lo scarto è trascurabile. Nel bot il problema non c'è: tutti gli ETF sono quotati su Borsa Italiana.

## B. Il bot (`bot/`)

**1. Sbirciata al futuro: ASSENTE**
```
30:    closes = prices[cfg["asset"]].loc[:prev_month_end].resample("ME").last().dropna()
```
Il trend usa solo le chiusure dei mesi già finiti.

**5. Prezzo di esecuzione: PRESENTE**
```
run.py 64:                pf.execute(o, cfg["commission_eur"], cfg["tax_rate"], str(today.date()))
portfolio.py 81:                orders.append(Order(t, "BUY", buy, float(row[t])))
```
Il bot gira dopo la chiusura ma eseguiva gli ordini al prezzo di chiusura, che a quel punto non è più disponibile.
→ **Corretto:** gli ordini decisi la sera si eseguono all'**apertura del giorno dopo**, con 10 punti base
di slippage. Se il prezzo d'apertura è salito e i contanti non bastano, le quote vengono ridotte.
Gli ordini già eseguiti tra il 25/09 e il 02/10 restano come sono stati registrati.

**4. Costi: PRESENTE → corretto** (slippage aggiunto, `config.json → slippage_bps`).

**7. Campione: PRESENTE (inevitabile)**: il paper trading è iniziato il 25/09/2026 in un mercato in rialzo.
Per giudicarlo servono mesi e almeno una fase di ribasso.

**2, 3, 6, 8:** come nel backtest. Gli strumenti sono ETF quotati su Borsa Italiana, con parametri fissati
in `config.json` prima di partire.

## C. Errori nel codice del video

Il video stesso dice "All code is illustrative", ed è così:
- **`deflated_sharpe`** mescola le unità di misura: confronta lo Sharpe annualizzato con il massimo atteso
  di normali standard e poi moltiplica per `sqrt(n_obs)` giornaliero. Il risultato diventa un interruttore
  0/1 invece di una probabilità: con 80 tentativi risponde PASS solo se lo Sharpe annuo supera circa 2,4,
  qualunque sia la lunghezza dei dati e la dispersione reale dei tentativi. La formula originale
  (Bailey e López de Prado, 2014) usa lo Sharpe per periodo e scala la soglia per la dispersione degli Sharpe
  provati. In `validate.py` c'è la versione corretta.
- **`periods_per_year = 365`** vale per le cripto, che si scambiano tutti i giorni. Per gli ETF servono 252 giorni o 12 mesi.
- **`position_size` con lo stop-loss** è pensata per singole operazioni con stop. Le nostre strategie sono
  allocazioni di portafoglio senza leva: il loro equivalente sono i limiti in `bot/risk.py`.
