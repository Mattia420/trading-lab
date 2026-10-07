"""Strategie: dati i prezzi e il portafoglio, restituiscono i pesi obiettivo e il motivo.

Restituiscono None quando oggi non c'è niente da decidere.
"""
import pandas as pd


def fixed_weights(cfg, prices, pf, today):
    """Pesi fissi: ribilancia al primo giorno o quando un peso esce dalla banda."""
    target = cfg["weights"]
    if not pf.positions and pf.cash > 0:
        return target, "Primo investimento: compro i pesi obiettivo."
    value = pf.value(prices.loc[today])
    drift = {t: pf.qty(t) * prices.loc[today, t] / value - w for t, w in target.items()}
    worst = max(drift, key=lambda t: abs(drift[t]))
    if abs(drift[worst]) * 100 > cfg["drift_pp"]:
        return target, (f"{worst} pesa {100 * (target[worst] + drift[worst]):.1f}% invece di "
                        f"{100 * target[worst]:.0f}% (banda ±{cfg['drift_pp']} punti): ribilancio.")
    return None, (f"Pesi dentro la banda (scarto massimo {100 * drift[worst]:+.1f} punti su {worst}): "
                  "nessuna operazione.")


def trend(cfg, prices, pf, today):
    """Sopra la media mobile di N fine-mese: asset. Sotto: difensivo. Decide una volta al mese
    (run.py segna il mese come deciso solo se la giornata non è stata bloccata)."""
    month = today.strftime("%Y-%m")
    if pf.meta.get("last_signal_month") == month:
        return None, "Segnale già valutato questo mese: si ricontrolla il primo giorno del prossimo."
    prev_month_end = today.replace(day=1) - pd.Timedelta(days=1)
    closes = prices[cfg["asset"]].loc[:prev_month_end].resample("ME").last().dropna()
    n = cfg["sma_months"]
    if len(closes) < n:
        return None, f"Servono almeno {n} chiusure mensili di {cfg['asset']}: ne ho {len(closes)}."
    last, sma = closes.iloc[-1], closes.iloc[-n:].mean()
    if last > sma:
        why = (f"{cfg['asset']} a fine {closes.index[-1]:%m/%Y} vale {last:.2f}, sopra la media a "
               f"{n} mesi ({sma:.2f}): trend positivo, sto sull'azionario.")
        return {cfg["asset"]: 1.0}, why
    why = (f"{cfg['asset']} a fine {closes.index[-1]:%m/%Y} vale {last:.2f}, sotto la media a "
           f"{n} mesi ({sma:.2f}): trend negativo, passo su {cfg['defensive']}.")
    return {cfg["defensive"]: 1.0}, why


def trend_multi(cfg, prices, pf, today):
    """Faber a più asset: ogni asset pesa 1/N ed è tenuto solo se a fine mese è sopra la sua
    media a N mesi, altrimenti quella quota va sul difensivo ("CASH" = resta liquidità, nessun ordine).

    Opzioni per ridurre gli ordini (e quindi i costi):
    - band_pct: si entra solo se il prezzo supera la media di almeno band_pct%, si esce solo se
      scende sotto di almeno band_pct% (ignora i falsi segnali vicino alla media);
    - months: mesi in cui si decide (es. [1, 4, 7, 10] = una volta a trimestre); il primo giro
      decide sempre."""
    month = today.strftime("%Y-%m")
    if pf.meta.get("last_signal_month") == month:
        return None, "Segnale già valutato questo mese: si ricontrolla il primo giorno del prossimo."
    state = pf.meta.get("in_trend")
    if state is not None and "months" in cfg and today.month not in cfg["months"]:
        return None, f"Decisione solo nei mesi {cfg['months']}: questo mese non si opera."
    prev_month_end = today.replace(day=1) - pd.Timedelta(days=1)
    n, share, band = cfg["sma_months"], 1 / len(cfg["assets"]), cfg.get("band_pct", 0) / 100
    target, parts, new_state = {}, [], {}
    for a in cfg["assets"]:
        closes = prices[a].loc[:prev_month_end].resample("ME").last().dropna()
        if len(closes) < n:
            return None, f"Servono almeno {n} chiusure mensili di {a}: ne ho {len(closes)}."
        last, sma = closes.iloc[-1], closes.iloc[-n:].mean()
        was_in = None if state is None else state.get(a)
        if was_in is None:
            is_in = last > sma
        elif was_in:
            is_in = last >= sma * (1 - band)
        else:
            is_in = last > sma * (1 + band)
        new_state[a] = bool(is_in)
        dest = a if is_in else cfg["defensive"]
        target[dest] = target.get(dest, 0) + share
        gap = (last / sma - 1) * 100
        parts.append(f"{a} {'dentro' if is_in else 'fuori'} ({gap:+.1f}% dalla media)")
    pf.meta["in_trend"] = new_state
    rule = f", banda ±{band * 100:.0f}%" if band else ""
    return target, f"Fine {prev_month_end:%m/%Y}{rule}: " + "; ".join(parts) + "."


STRATEGIES = {"fixed_weights": fixed_weights, "trend": trend, "trend_multi": trend_multi}
