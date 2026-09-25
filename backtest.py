"""Backtest mensile di strategie a regole, in euro, con costi e tasse italiane.

Uso:
    python backtest.py                  # scarica i dati (se mancano) e stampa i risultati
    python backtest.py --capitale 2000 --commissione 5

Ipotesi (volutamente prudenti, vedi RISULTATI.md):
- ETF USA con storia lunga usati come "controfigure" degli ETF UCITS quotati a Milano,
  convertiti in euro con il cambio EUR/USD del giorno.
- Liquidità al 0% (conservativo: dal 2023 un ETF monetario in euro ha reso ~3% l'anno).
- Tasse: 26% sulla plusvalenza a ogni vendita. Sugli ETF le minusvalenze NON compensano
  le plusvalenze (le plusvalenze da ETF sono redditi di capitale, le minus redditi diversi).
  Sulle azioni le minus compensano plus future (scadenza a 4 anni ignorata).
- Imposta di bollo 0,2% annuo sul valore dei titoli.
- Commissione fissa per ordine; quote frazionarie ammesse (semplificazione).
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data" / "prices.csv"
TICKERS = ["SPY", "EFA", "IEF", "GLD", "SHY", "SH", "EURUSD=X", "ISP.MI", "UCG.MI"]
USD = {"SPY", "EFA", "IEF", "GLD", "SHY", "SH"}
STOCKS = {"ISP.MI", "UCG.MI"}  # redditi diversi: minus compensabili
TAX = 0.26
BOLLO = 0.002


def load_prices(start="2004-12-01"):
    if not DATA.exists():
        import yfinance as yf
        DATA.parent.mkdir(exist_ok=True)
        yf.download(TICKERS, start="2000-01-01", auto_adjust=True, progress=False)["Close"].to_csv(DATA)
    px = pd.read_csv(DATA, index_col=0, parse_dates=True)
    fx = px["EURUSD=X"].ffill()
    for t in USD:
        px[t] = px[t] / fx
    px = px.drop(columns=[c for c in px.columns if c not in TICKERS or c == "EURUSD=X"])
    m = px.ffill().resample("ME").last().loc[start:]
    m["CASH"] = 1.0
    return m


# --- Strategie: ricevono lo storico mensile fino al mese t, restituiscono i pesi obiettivo ---

def bh_azioni(h):
    return {"SPY": 0.6, "EFA": 0.4}


def bh_bilanciato(h):
    return {"SPY": 0.4, "EFA": 0.2, "IEF": 0.25, "GLD": 0.15}


def trend_10m(h):
    """Ogni fetta azionaria resta investita solo se il prezzo è sopra la media di 10 mesi."""
    w = {}
    for t, share in (("SPY", 0.6), ("EFA", 0.4)):
        above = h[t].iloc[-1] > h[t].iloc[-10:].mean()
        w[t if above else "CASH"] = w.get(t if above else "CASH", 0) + share
    return w


def dual_momentum(h):
    """Antonacci: l'azionario migliore a 12 mesi se batte la liquidità, altrimenti obbligazioni."""
    r = {t: h[t].iloc[-1] / h[t].iloc[-13] - 1 for t in ("SPY", "EFA")}
    best = max(r, key=r.get)
    return {best: 1.0} if r[best] > 0 else {"IEF": 1.0}


def spy_bh(h):
    return {"SPY": 1.0}


def trend_long_cash(h):
    """Borsa USA sopra la media di 10 mesi: investito. Sotto: liquidità."""
    return {"SPY": 1.0} if h["SPY"].iloc[-1] > h["SPY"].iloc[-10:].mean() else {"CASH": 1.0}


def trend_long_short(h):
    """Come sopra, ma sotto la media compra l'ETF inverso: guadagna quando la borsa scende."""
    return {"SPY": 1.0} if h["SPY"].iloc[-1] > h["SPY"].iloc[-10:].mean() else {"SH": 1.0}


def banche_bh(h):
    return {"ISP.MI": 0.5, "UCG.MI": 0.5}


STRATEGIE = {
    "Compra e tieni azionario (60 USA / 40 resto mondo)": (bh_azioni, "annuale"),
    "Compra e tieni bilanciato (azioni, bond, oro)": (bh_bilanciato, "annuale"),
    "Trend: azioni solo sopra media 10 mesi": (trend_10m, "mensile"),
    "Dual momentum (Antonacci)": (dual_momentum, "mensile"),
    "Borsa USA: compra e tieni": (spy_bh, "annuale"),
    "Borsa USA: trend, sotto la media in liquidità": (trend_long_cash, "mensile"),
    "Borsa USA: trend, sotto la media ETF inverso (short)": (trend_long_short, "mensile"),
    "Riferimento: banche italiane (Intesa + UniCredit)": (banche_bh, "annuale"),
}


def run(prices, strat, freq, capitale, commissione, start, end):
    p = prices.loc[:end]
    dates = p.loc[start:end].index
    qty, cost = {}, {}
    cash, loss_bank = capitale, 0.0
    taxes = fees = bollo = 0.0
    trades = 0
    values = []

    def sell(t, q, price):
        nonlocal cash, loss_bank, taxes, fees, trades
        gain = q * (price - cost[t])
        cash += q * price - commissione
        fees += commissione
        trades += 1
        qty[t] -= q
        if gain > 0:
            if t in STOCKS:
                used = min(loss_bank, gain)
                loss_bank -= used
                gain -= used
            tax = gain * TAX
            cash -= tax
            taxes += tax
        elif t in STOCKS:
            loss_bank -= gain

    for i, d in enumerate(dates):
        row = p.loc[d]
        hist = p.loc[:d]
        value = cash + sum(q * row[t] for t, q in qty.items())
        rebalance = i == 0 or freq == "mensile" or d.month == 1
        if rebalance:
            target = {t: w for t, w in strat(hist).items() if t != "CASH"}
            # vendite prima degli acquisti
            for t in list(qty):
                if qty[t] <= 1e-9:
                    continue
                if t not in target:
                    sell(t, qty[t], row[t])
                else:
                    excess = qty[t] - target[t] * value / row[t]
                    if excess * row[t] > max(50, 0.02 * value):
                        sell(t, excess, row[t])
            value = cash + sum(q * row[t] for t, q in qty.items())
            for t, w in target.items():
                have = qty.get(t, 0)
                buy = w * value / row[t] - have
                amount = min(buy * row[t], cash - commissione)
                if amount > max(50, 0.02 * value):
                    q = amount / row[t]
                    cost[t] = (cost.get(t, 0) * have + amount) / (have + q)
                    qty[t] = have + q
                    cash -= amount + commissione
                    fees += commissione
                    trades += 1
        if d.month == 12:
            b = BOLLO * sum(q * row[t] for t, q in qty.items())
            cash -= b
            bollo += b
        values.append(cash + sum(q * row[t] for t, q in qty.items()))

    # liquidazione finale: quanto ti resta in tasca
    last = p.loc[dates[-1]]
    for t in list(qty):
        if qty[t] > 1e-9:
            sell(t, qty[t], last[t])
    curve = pd.Series(values, index=dates)
    return curve, dict(netto=cash, tasse=taxes, commissioni=fees, bollo=bollo, ordini=trades)


def stats(curve, res, capitale):
    years = (curve.index[-1] - curve.index[0]).days / 365.25
    rets = curve.pct_change().dropna()
    dd = (curve / curve.cummax() - 1).min()
    yearly = curve.resample("YE").last().pct_change().dropna()
    return {
        "Netto finale €": round(res["netto"]),
        "Rendimento annuo netto": f"{(res['netto'] / capitale) ** (1 / years) - 1:.1%}",
        "Peggior calo (max drawdown)": f"{dd:.0%}",
        "Volatilità annua": f"{rets.std() * np.sqrt(12):.0%}",
        "Anno peggiore": f"{yearly.min():.0%}",
        "Ordini": res["ordini"],
        "Tasse €": round(res["tasse"]),
        "Commissioni + bollo €": round(res["commissioni"] + res["bollo"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capitale", type=float, default=2000)
    ap.add_argument("--commissione", type=float, default=5)
    args = ap.parse_args()
    prices = load_prices()
    periods = [("2006-01-31", prices.index[-1], "Intero periodo"),
               ("2006-01-31", "2015-12-31", "2006-2015"),
               ("2016-01-31", prices.index[-1], "2016-oggi")]
    for start, end, label in periods:
        rows = {}
        for name, (f, freq) in STRATEGIE.items():
            curve, res = run(prices, f, freq, args.capitale, args.commissione, start, end)
            rows[name] = stats(curve, res, args.capitale)
        end_s = pd.Timestamp(end).strftime("%m/%Y")
        print(f"\n## {label} (01/{start[:4]} - {end_s}), capitale {args.capitale:.0f} €, "
              f"commissione {args.commissione:.0f} € a ordine\n")
        print(pd.DataFrame(rows).T.to_markdown())


if __name__ == "__main__":
    main()
