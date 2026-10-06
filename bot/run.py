"""Giro giornaliero del bot (dopo la chiusura di Borsa Italiana).

    python -m bot.run                 # usa i prezzi di oggi da Yahoo Finance
    python -m bot.run --dry-run       # mostra cosa farebbe senza salvare niente

Per ogni portafoglio: controlla i dati, controlla i limiti di rischio, chiede alla strategia
i pesi obiettivo, filtra gli ordini, li esegue sul conto simulato e scrive il diario in journal/.
"""
import argparse
import json
import math
from pathlib import Path

import pandas as pd

from . import risk
from .portfolio import Order, Portfolio, floor4
from .report import write_reports
from .strategies import STRATEGIES

ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).resolve().parent / "config.json"


def load_prices(tickers, years=2):
    """Chiusure e aperture giornaliere (rettificate per i dividendi)."""
    import yfinance as yf
    df = yf.download(tickers, period=f"{years}y", auto_adjust=True, progress=False)
    close = df["Close"][tickers].dropna(how="all")
    return close, df["Open"][tickers].reindex(close.index)


def fill_pending(pf, opens, cfg, today, log):
    """Esegue all'apertura di oggi gli ordini decisi ieri sera, con slippage:
    chi compra paga un po' di più, chi vende incassa un po' di meno."""
    slip = cfg["slippage_bps"] / 1e4
    pending = sorted(pf.meta.pop("pending", []), key=lambda o: o["side"] != "SELL")
    for p in pending:
        price = opens.get(p["ticker"])
        if price is None or pd.isna(price):
            log["notes"].append(f"Ordine annullato, manca il prezzo di apertura: {p['side']} {p['qty']} {p['ticker']}.")
            continue
        price *= (1 + slip) if p["side"] == "BUY" else (1 - slip)
        qty = p["qty"]
        if p["side"] == "BUY":
            room = (pf.cash - cfg["commission_eur"]) / price
            qty = min(qty, floor4(room) if cfg.get("fractional") else math.floor(room))
        else:
            qty = min(qty, pf.qty(p["ticker"]))
        if qty <= 0:
            log["notes"].append(f"Ordine annullato, contanti o quote insufficienti all'apertura: "
                                f"{p['side']} {p['qty']} {p['ticker']}.")
            continue
        o = Order(p["ticker"], p["side"], qty, float(price), p["reason"])
        pf.execute(o, cfg["commission_eur"], cfg["tax_rate"], str(today.date()))
        log["executed"].append(o)


def run_portfolio(name, pcfg, cfg, prices, opens, today, market_problems):
    # costi e regole di esecuzione propri del portafoglio (broker diverso), se indicati
    cfg = {**cfg, **{k: pcfg[k] for k in ("commission_eur", "slippage_bps", "min_order_eur", "fractional") if k in pcfg}}
    path = ROOT / "state" / f"{name}.json"
    pf = Portfolio.load(path, name, pcfg["capital_eur"])
    row = prices.loc[today]
    log = {"name": name, "description": pcfg["description"], "orders": [], "executed": [],
           "rejected": [], "notes": []}

    if pf.history and pf.history[-1]["date"] == str(today.date()):
        log["notes"].append("Giornata già elaborata: nessuna nuova azione.")
        return pf, path, log, False

    last_year = pf.meta.get("last_run", str(today.date()))[:4]
    if int(last_year) < today.year:
        securities = pf.value(row) - pf.cash
        bollo = securities * cfg["bollo_rate"]
        pf.cash -= bollo
        pf.totals["bollo"] += bollo
        log["notes"].append(f"Nuovo anno: addebitata imposta di bollo di {bollo:.2f} €.")

    value = pf.value(row)
    rules = {**cfg["risk"], **pcfg.get("risk", {})}  # limiti propri del portafoglio, se più stretti
    blocked, why = risk.check_portfolio(pf, value, rules)
    if market_problems:
        blocked, why = True, "Dati di mercato non affidabili: " + " ".join(market_problems)

    if blocked:
        log["decision"] = "BLOCCATO: " + why
        for p in pf.meta.pop("pending", []):
            log["notes"].append(f"Ordine di ieri annullato per il blocco: {p['side']} {p['qty']} {p['ticker']}.")
    else:
        fill_pending(pf, opens.loc[today], cfg, today, log)
        target, reason = STRATEGIES[pcfg["strategy"]](pcfg, prices, pf, today)
        log["decision"] = reason
        if target is not None:
            orders = pf.plan(target, row, cfg["commission_eur"], cfg["min_order_eur"], cfg.get("fractional", False))
            for o in orders:
                o.reason = reason
            ok, rejected = risk.filter_orders(orders, pf, row, rules, cfg["commission_eur"])
            # si decide dopo la chiusura: il prezzo di chiusura non è più disponibile,
            # gli ordini partono domani all'apertura
            pf.meta["pending"] = [{"ticker": o.ticker, "side": o.side, "qty": o.qty,
                                   "reason": o.reason, "decided": str(today.date())} for o in ok]
            log["orders"] = ok
            log["rejected"] = rejected
            if not orders:
                log["notes"].append("Nessun ordine utile: il portafoglio è già il più vicino possibile all'obiettivo.")
            if pcfg["strategy"].startswith("trend"):
                pf.meta["last_signal_month"] = today.strftime("%Y-%m")

    pf.history.append({"date": str(today.date()), "value": round(pf.value(row), 2)})
    pf.meta["last_run"] = str(today.date())
    return pf, path, log, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text())
    tickers = sorted({t for p in cfg["portfolios"].values()
                      for t in (list(p.get("weights", {})) + p.get("assets", []) + [p.get("asset"), p.get("defensive")]) if t})
    raw, opens = load_prices(tickers)
    today = raw.index[-1]
    problems = risk.check_market(raw, today, tickers, cfg["risk"], pd.Timestamp.now())
    prices = raw.ffill()

    results, any_changed = [], False
    for name, pcfg in cfg["portfolios"].items():
        pf, path, log, changed = run_portfolio(name, pcfg, cfg, prices, opens, today, problems)
        results.append((pf, log))
        any_changed |= changed
        if changed and not args.dry_run:
            pf.save(path)

    text = write_reports(results, prices.loc[today], today, cfg, problems,
                         save=any_changed and not args.dry_run)
    print(text)


if __name__ == "__main__":
    main()
