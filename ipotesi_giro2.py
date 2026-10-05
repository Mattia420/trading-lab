"""Secondo giro di ipotesi: le idee con le prove pubblicate più solide trovate nella ricerca.

    python ipotesi_giro2.py        # scrive IPOTESI_2.md

H5 "Sell in May" (Bouman e Jacobsen 2002; Jacobsen e Zhang, 114 paesi)
H6 Fattori azionari via ETF UCITS (momentum, qualità, bassa volatilità, value)
H7 Trend multi-asset di Faber a 5 asset (2007, verificato fuori campione dall'autore)

Stesso motore, stessi costi, tentativi contati insieme ai 20 del primo giro.
Nessuna di queste ipotesi ha parametri da scegliere: il walk-forward diventa un confronto
anno per anno contro il riferimento (nessun dato futuro viene usato per decidere).
"""
from pathlib import Path

import numpy as np
import pandas as pd

from ipotesi import BILANCIATO, EVAL_FROM, build
from validate import Config, backtest, const, deflated_sharpe, load_prices, metrics, pct, trend_sma

EXTRA = Path(__file__).parent / "data" / "extra.csv"
EXTRA_TICKERS = ["VNQ", "DBC", "IWMO.MI", "IWQU.MI", "MVOL.MI", "IWVL.MI", "SWDA.MI", "EURUSD=X"]
FACTORS = ["IWMO.MI", "IWQU.MI", "MVOL.MI", "IWVL.MI"]


def load_extra(index):
    if not EXTRA.exists():
        import yfinance as yf
        yf.download(EXTRA_TICKERS, start="2000-01-01", auto_adjust=True, progress=False)["Close"].to_csv(EXTRA)
    px = pd.read_csv(EXTRA, index_col=0, parse_dates=True).ffill()
    for t in ("VNQ", "DBC"):
        px[t] = px[t] / px["EURUSD=X"]
    m = px.drop(columns="EURUSD=X").resample("ME").last()
    return m.reindex(index)


def halloween(px):
    """Azioni (60 USA / 40 resto del mondo) da novembre ad aprile, obbligazioni da maggio a ottobre.
    Meccanismo proposto: meno attenzione e liquidità nei mesi estivi. Debole: gli stessi autori
    ammettono di non avere una spiegazione convincente, motivo in più per pretendere prove forti."""
    winter = px.index.month.isin([10, 11, 12, 1, 2, 3])  # deciso a fine mese per il mese successivo
    w = pd.DataFrame(0.0, index=px.index, columns=["SPY", "EFA", "IEF"])
    w.loc[winter, "SPY"], w.loc[winter, "EFA"] = 0.6, 0.4
    w.loc[~winter, "IEF"] = 1.0
    return w


def factors(px):
    """Pesi uguali su quattro ETF fattoriali mondiali. Meccanismo: premi per rischi che molti
    non vogliono portare (value), errori di comportamento (momentum), vincoli alla leva (bassa
    volatilità), prezzi che sottovalutano la redditività stabile (qualità)."""
    return const(px, {t: 0.25 for t in FACTORS})


def gtaa5(px):
    """Faber: 5 asset al 20%, ciascuno solo se sopra la media di 10 mesi, altrimenti liquidità."""
    w = pd.DataFrame(0.0, index=px.index, columns=["SPY", "EFA", "IEF", "VNQ", "DBC", "CASH"])
    for t in ("SPY", "EFA", "IEF", "VNQ", "DBC"):
        part = trend_sma(px, t, "CASH", 10, 0.2)
        w[t] += part[t]
        w["CASH"] += part["CASH"]
    return w


def yearly(net, ref, start):
    """Confronto anno per anno (anni solari completi) contro il riferimento."""
    a = (1 + net.loc[start:]).groupby(net.loc[start:].index.year).prod() - 1
    b = (1 + ref.loc[start:]).groupby(ref.loc[start:].index.year).prod() - 1
    full = [y for y in a.index if (net.loc[str(y)].index.size == 12)]
    d = (a - b).loc[full]
    tot = (1 + a.loc[full]).prod() / (1 + b.loc[full]).prod() - 1
    return int((d > 0.001).sum()), int((d < -0.001).sum()), d.min(), tot


def main():
    cfg = Config()
    px = load_prices().loc["2005-01-31":]
    px = px.join(load_extra(px.index))
    rets = px.pct_change().fillna(0)
    rets["CASH"] = 0.0

    def run(w):
        return backtest(rets, w, cfg)["net"]

    bal = run(const(px, BILANCIATO))
    world = run(const(px, {"SWDA.MI": 1.0}))
    f_start = px["IWVL.MI"].first_valid_index() + pd.offsets.MonthEnd(2)
    hyp = {
        "H5 Sell in May (azioni nov-apr, obbligazioni mag-ott)": (run(halloween(px)), bal, "bilanciato", EVAL_FROM),
        "H6 Fattori mondiali (momentum, qualità, bassa vol., value)": (run(factors(px)), world, "azionario mondo (SWDA)", f_start),
        "H7 Trend multi-asset di Faber (5 asset)": (run(gtaa5(px)), bal, "bilanciato", "2007-02-28"),
    }

    # conteggio onesto: tutti i tentativi del primo giro più questi
    _, _, _, first_sr, first_n = build(cfg)
    n_trials = first_n + len(hyp)
    excess = [(s - r).loc[st:] for s, r, _, st in hyp.values()]
    srs_all = first_sr + [e.mean() / e.std() for e in excess]

    out = ["# Secondo giro di ipotesi: le idee con più prove pubblicate", "",
           f"Dati mensili in euro fino a {px.index[-1]:%m/%Y}; costi {cfg.fee_bps:.0f} + slippage "
           f"{cfg.slippage_bps:.0f} punti base per euro scambiato; tasse escluse.",
           f"**Tentativi contati in totale: {n_trials}** ({first_n} precedenti + {len(hyp)}).", "",
           "| Ipotesi | Periodo | Rendimento annuo | Calo max | Sharpe | Riferimento | Rif. rendimento | Rif. calo max | Sharpe sgonfiato | Anni meglio / peggio | Totale vs rif. | Verdetto |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (name, (s, ref, refname, st)), e in zip(hyp.items(), excess):
        m, mr = metrics(s.loc[st:], cfg), metrics(ref.loc[st:], cfg)
        d = deflated_sharpe(e, srs_all)
        wins, losses, worst, tot = yearly(s, ref, st)
        ok = d["dsr"] > 0.95 and wins > losses and tot > 0
        out.append(f"| {name} | {pd.Timestamp(st):%Y}-{px.index[-1]:%Y} | {pct(m['rendimento_annuo'])} | "
                   f"{pct(m['max_drawdown'])} | {m['sharpe']:.2f} | {refname} | {pct(mr['rendimento_annuo'])} | "
                   f"{pct(mr['max_drawdown'])} | {d['dsr']:.2f} | {wins} / {losses} | {pct(tot)} | "
                   f"{'✅ PASSA' if ok else '❌ SCARTATA'} |")
    out += ["", "Lo Sharpe sgonfiato è calcolato sulla differenza col riferimento: risponde alla domanda "
                "\"fa meglio del riferimento, oltre la fortuna?\". Serve almeno 0,95.", ""]
    text = "\n".join(out) + "\n"
    Path("IPOTESI_2.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
