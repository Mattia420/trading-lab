"""Giro giornaliero del bot (dopo la chiusura di Borsa Italiana).

    python -m bot.run                 # usa i prezzi di oggi da Yahoo Finance
    python -m bot.run --dry-run       # mostra cosa farebbe senza salvare niente

Per ogni portafoglio: controlla i dati, controlla i limiti di rischio, chiede alla strategia
i pesi obiettivo, filtra gli ordini, li esegue sul conto simulato e scrive il diario in journal/.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from . import risk
from .portfolio import Portfolio
from .report import write_reports
from .strategies import STRATEGIES

ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).resolve().parent / "config.json"


def load_prices(tickers, years=2):
    import yfinance as yf
    df = yf.download(tickers, period=f"{years}y", auto_adjust=True, progress=False)["Close"]
    return df[tickers].dropna(how="all")


def run_portfolio(name, pcfg, cfg, prices, today, market_problems):
    path = ROOT / "state" / f"{name}.json"
    pf = Portfolio.load(path, name, pcfg["capital_eur"])
    row = prices.loc[today]
    log = {"name": name, "description": pcfg["description"], "orders": [], "rejected": [], "notes": []}

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
    blocked, why = risk.check_portfolio(pf, value, cfg["risk"])
    if market_problems:
        blocked, why = True, "Dati di mercato non affidabili: " + " ".join(market_problems)

    if blocked:
        log["decision"] = "BLOCCATO: " + why
    else:
        target, reason = STRATEGIES[pcfg["strategy"]](pcfg, prices, pf, today)
        log["decision"] = reason
        if target is not None:
            orders = pf.plan(target, row, cfg["commission_eur"], cfg["min_order_eur"])
            for o in orders:
                o.reason = reason
            ok, rejected = risk.filter_orders(orders, pf, row, cfg["risk"], cfg["commission_eur"])
            for o in ok:
                pf.execute(o, cfg["commission_eur"], cfg["tax_rate"], str(today.date()))
            log["orders"] = ok
            log["rejected"] = rejected
            if not orders:
                log["notes"].append("Nessun ordine utile: con quote intere questo è già il portafoglio più vicino all'obiettivo.")
            if pcfg["strategy"] == "trend":
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
                      for t in (list(p.get("weights", {})) + [p.get("asset"), p.get("defensive")]) if t})
    raw = load_prices(tickers)
    today = raw.index[-1]
    problems = risk.check_market(raw, today, tickers, cfg["risk"], pd.Timestamp.now())
    prices = raw.ffill()

    results, any_changed = [], False
    for name, pcfg in cfg["portfolios"].items():
        pf, path, log, changed = run_portfolio(name, pcfg, cfg, prices, today, problems)
        results.append((pf, log))
        any_changed |= changed
        if changed and not args.dry_run:
            pf.save(path)

    text = write_reports(results, prices.loc[today], today, cfg, problems,
                         save=any_changed and not args.dry_run)
    print(text)


if __name__ == "__main__":
    main()
