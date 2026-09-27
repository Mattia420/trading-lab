"""Controlli di rischio. Sono regole fisse nel codice: nessuna strategia le può scavalcare.

check_market() blocca tutto se i dati non sono affidabili.
check_portfolio() blocca un portafoglio se perde troppo.
filter_orders() scarta gli ordini fuori dalle regole.
"""
from pathlib import Path

import pandas as pd

STOP_FILE = Path(__file__).resolve().parent.parent / "STOP"


def check_market(prices, today, tickers, rules, now):
    """Restituisce l'elenco dei problemi sui dati; lista vuota = si può operare."""
    problems = []
    if STOP_FILE.exists():
        problems.append("File STOP presente: il proprietario ha fermato il bot.")
    age = (now.normalize() - today).days
    if age > rules["max_data_age_days"]:
        problems.append(f"Ultimo prezzo del {today:%d/%m/%Y}, vecchio di {age} giorni.")
    for t in tickers:
        s = prices[t].dropna()
        if s.empty or s.index[-1] != today:
            problems.append(f"{t}: manca il prezzo di chiusura del {today:%d/%m/%Y}.")
            continue
        if len(s) > 1:
            jump = abs(s.iloc[-1] / s.iloc[-2] - 1) * 100
            if jump > rules["max_price_jump_pct"]:
                problems.append(f"{t}: variazione di {jump:.0f}% in un giorno, sospetto errore nei dati.")
    return problems


def check_portfolio(pf, value, rules):
    """Restituisce (bloccato, motivo). Il blocco per drawdown resta finché il proprietario non lo toglie."""
    if pf.meta.get("halted"):
        return True, f"Bloccato dal {pf.meta['halted']}: serve l'intervento del proprietario."
    if pf.history:
        prev = pf.history[-1]["value"]
        loss = (1 - value / prev) * 100
        if loss > rules["max_daily_loss_pct"]:
            return True, f"Perdita di {loss:.1f}% oggi (limite {rules['max_daily_loss_pct']}%): niente ordini oggi."
    dd = (1 - value / pf.peak()) * 100
    if dd > rules["max_drawdown_pct"]:
        pf.meta["halted"] = pd.Timestamp.now().strftime("%Y-%m-%d")
        return True, (f"Calo dal massimo di {dd:.1f}% (limite {rules['max_drawdown_pct']}%): "
                      "portafoglio bloccato finché il proprietario non decide.")
    return False, ""


def filter_orders(orders, pf, row, rules, commission):
    """Scarta ordini non ammessi. Restituisce (accettati, scartati con motivo)."""
    ok, rejected = [], []
    cash = pf.cash
    for o in orders:
        why = None
        if o.ticker not in rules["allowed_tickers"]:
            why = "strumento non in elenco"
        elif len(ok) >= rules["max_orders_per_day"]:
            why = "troppi ordini oggi"
        elif o.side == "SELL" and o.qty > pf.qty(o.ticker):
            why = "vendita allo scoperto non ammessa"
        elif o.side == "BUY" and o.amount + commission > cash + 1e-6:
            why = "contanti insufficienti (niente leva)"
        if why:
            rejected.append((o, why))
            continue
        cash += (o.amount - commission) if o.side == "SELL" else -(o.amount + commission)
        ok.append(o)
    return ok, rejected
