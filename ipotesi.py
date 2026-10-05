"""Giro di ipotesi solo al rialzo, con il metodo dei cinque ruoli e dei tre cancelli.

    python ipotesi.py            # scrive IPOTESI.md

Domanda unica per ogni ipotesi: batte il portafoglio bilanciato (il sistema che ha già
superato i cancelli) dopo costi e slippage, in modo distinguibile dalla fortuna?

Ogni parametro è fissato PRIMA di guardare i risultati (valore "a priori"); il walk-forward
prova anche i valori vicini, sceglie solo sul passato e viene contato tra i tentativi.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import DATA, USD
from validate import Config, backtest, const, deflated_sharpe, load_prices, metrics, pct, trend_sma, dual_momentum

ASSETS = ["SPY", "EFA", "IEF", "GLD"]
BILANCIATO = {"SPY": .4, "EFA": .2, "IEF": .25, "GLD": .15}
EVAL_FROM = "2006-01-31"


def load_daily():
    px = pd.read_csv(DATA, index_col=0, parse_dates=True)
    fx = px["EURUSD=X"].ffill()
    for t in USD:
        px[t] = px[t] / fx
    d = px[ASSETS].ffill().loc["2004-12-01":].dropna()
    d["CASH"] = 1.0
    return d


def to_monthly(daily_net):
    return (1 + daily_net).resample("ME").prod() - 1


# --- Le ipotesi. Ciascuna restituisce i pesi decisi a fine periodo con i soli dati noti allora ---

def rotation(px, lookback=6, top=2):
    """H1 Rotazione tra mercati. Meccanismo: gli investitori reagiscono in ritardo alle notizie
    e seguono la massa, quindi i mercati forti restano forti per qualche mese. Dall'altra parte
    c'è chi vende i vincenti troppo presto e tiene i perdenti (effetto disposizione).
    Regola: ogni mese i `top` mercati con il miglior rendimento a `lookback` mesi, a pesi uguali;
    se il rendimento è negativo, quella quota va in liquidità."""
    r = px[ASSETS] / px[ASSETS].shift(lookback) - 1
    w = pd.DataFrame(0.0, index=px.index, columns=ASSETS + ["CASH"])
    for d, row in r.dropna().iterrows():
        for t in row.nlargest(top).index:
            w.loc[d, t if row[t] > 0 else "CASH"] += 1 / top
    return w


def vol_target(daily, monthly_idx, target=0.08, window=63):
    """H2 Bilanciato con freno di volatilità. Meccanismo: la volatilità si raggruppa (giorni
    agitati seguono giorni agitati) e nei periodi agitati il rendimento per unità di rischio è
    più basso. Chi è costretto a vendere nel panico (margini, fondi con limiti di rischio) è
    dall'altra parte. Regola: a fine mese si stima la volatilità del bilanciato sugli ultimi
    `window` giorni; se supera `target`, si riduce l'esposizione in proporzione e il resto va
    in liquidità. Mai leva."""
    w_bal = pd.Series(BILANCIATO)
    port = (daily[ASSETS].pct_change() * w_bal).sum(axis=1)
    vol = port.rolling(window).std() * np.sqrt(252)
    scale = (target / vol).clip(upper=1.0).resample("ME").last().reindex(monthly_idx)
    w = pd.DataFrame({t: w_bal[t] * scale for t in ASSETS})
    w["CASH"] = 1 - scale
    return w.fillna(0)


def turn_of_month(daily, days=3):
    """H3 Effetto fine mese. Meccanismo: a cavallo del cambio mese entrano in borsa stipendi,
    versamenti automatici e flussi dei fondi pensione; dall'altra parte c'è chi deve vendere
    a fine mese per esigenze di cassa. Regola: borsa USA dall'ultimo giorno del mese ai primi
    `days` giorni del mese dopo, liquidità negli altri giorni. Il calendario è noto in anticipo:
    non è una sbirciata al futuro."""
    idx = daily.index
    month = pd.Series(idx.to_period("M"), index=idx)
    pos_in_month = month.groupby(month).cumcount()
    last_day = month != month.shift(-1)
    hold = last_day | (pos_in_month < days)       # giorni in cui si vuole essere investiti
    signal = hold.shift(-1).fillna(False)        # deciso il giorno prima (il motore sfasa di 1)
    w = pd.DataFrame({"SPY": signal.astype(float)}, index=idx)
    w["CASH"] = 1 - w["SPY"]
    return w


def risk_parity(px, months=12):
    """H4 Rischio bilanciato. Meccanismo: molti investitori non possono usare la leva e per
    cercare rendimento comprano troppi asset rischiosi, rendendo quelli a basso rischio
    relativamente più convenienti. Regola: ogni mese pesi inversamente proporzionali alla
    volatilità degli ultimi `months` mesi. Senza leva (quindi il vantaggio teorico è ridotto)."""
    vol = px[ASSETS].pct_change().rolling(months).std()
    inv = 1 / vol
    return inv.div(inv.sum(axis=1), axis=0).fillna(0)


# --- Walk-forward su serie già calcolate (i segnali usano solo il passato) ---------------

def walk_forward(series: dict, bench: pd.Series, train=60, test=12):
    """Ogni anno sceglie il parametro con lo Sharpe migliore sui 5 anni precedenti e lo usa
    per i 12 mesi successivi. Restituisce i risultati anno per anno contro il bilanciato."""
    df = pd.DataFrame(series).loc[EVAL_FROM:].dropna()
    b = bench.reindex(df.index)
    rows = []
    i = 0
    while i + train + test <= len(df):
        tr, te = df.iloc[i:i + train], df.iloc[i + train:i + train + test]
        best = (tr.mean() / tr.std()).idxmax()
        rows.append({"inizio": te.index[0], "parametro": best,
                     "strategia": (1 + te[best]).prod() - 1,
                     "bilanciato": (1 + b.loc[te.index]).prod() - 1})
        i += test
    return pd.DataFrame(rows)


def build(cfg):
    """Calcola tutte le varianti del primo giro. Restituisce dati, riferimento, ipotesi e tentativi."""
    px = load_prices().loc["2005-01-31":]
    rets = px.pct_change().fillna(0)
    rets["CASH"] = 0.0
    daily = load_daily()
    drets = daily.pct_change().fillna(0)
    dcfg = Config(periods_per_year=252)

    def monthly_run(w):
        return backtest(rets, w, cfg)["net"]

    def daily_run(w):
        return to_monthly(backtest(drets, w, dcfg)["net"]).reindex(px.index).fillna(0)

    bench = monthly_run(const(px, BILANCIATO))

    # ipotesi: (descrizione, valore a priori, griglia per il walk-forward)
    hyp = {
        "H1 Rotazione tra mercati (6 mesi, i 2 migliori)":
            (6, {p: monthly_run(rotation(px, p)) for p in (3, 6, 9, 12)}, "mesi"),
        "H2 Bilanciato con freno di volatilità (8%)":
            (0.08, {p: monthly_run(vol_target(daily, px.index, p)) for p in (0.06, 0.08, 0.10)}, "vol. obiettivo"),
        "H3 Effetto fine mese (3 giorni)":
            (3, {p: daily_run(turn_of_month(daily, p)) for p in (2, 3, 4)}, "giorni"),
        "H4 Rischio bilanciato (12 mesi)":
            (12, {p: monthly_run(risk_parity(px, p)) for p in (6, 12)}, "mesi"),
    }

    # conteggio onesto: gli 8 tentativi già fatti + ogni variante delle nuove ipotesi
    old = [const(px, {"SPY": .6, "EFA": .4}), const(px, BILANCIATO),
           trend_sma(px, "SPY", "CASH", 10, .6).add(trend_sma(px, "EFA", "CASH", 10, .4), fill_value=0),
           dual_momentum(px), const(px, {"SPY": 1.0}), trend_sma(px, "SPY", "CASH", 10),
           trend_sma(px, "SPY", "SH", 10), const(px, {"ISP.MI": .5, "UCG.MI": .5})]
    excess_all = [monthly_run(w).loc[EVAL_FROM:] - bench.loc[EVAL_FROM:] for w in old]
    excess_all += [s.loc[EVAL_FROM:] - bench.loc[EVAL_FROM:] for _, grid, _ in hyp.values() for s in grid.values()]
    trial_sr = [e.mean() / e.std() for e in excess_all if e.std() > 0]
    n_trials = len(old) + sum(len(g) for _, g, _ in hyp.values())
    return px, bench, hyp, trial_sr, n_trials


def main():
    cfg = Config()
    px, bench, hyp, trial_sr, n_trials = build(cfg)

    mb = metrics(bench.loc[EVAL_FROM:], cfg)
    out = ["# Giro di ipotesi solo al rialzo", "",
           f"Dati mensili 01/2006 - {px.index[-1]:%m/%Y} in euro, costi {cfg.fee_bps:.0f} + slippage "
           f"{cfg.slippage_bps:.0f} punti base per ogni euro scambiato, tasse escluse.",
           f"**Riferimento da battere: il bilanciato** ({pct(mb['rendimento_annuo'])} l'anno, calo max "
           f"{pct(mb['max_drawdown'])}, Sharpe {mb['sharpe']:.2f}).", "",
           f"**Tentativi contati: {n_trials}** (gli 8 precedenti più ogni variante provata qui).", "",
           "## Risultati con il parametro fissato a priori", "",
           "| Ipotesi | Rendimento annuo | Calo max | Sharpe | Sharpe sgonfiato vs bilanciato | Cancello 2 |",
           "|---|---|---|---|---|---|"]
    verdict = {}
    for name, (prior, grid, _) in hyp.items():
        s = grid[prior].loc[EVAL_FROM:]
        m = metrics(s, cfg)
        d = deflated_sharpe(s - bench.loc[EVAL_FROM:], trial_sr)
        verdict[name] = [d["dsr"] > 0.95]
        out.append(f"| {name} | {pct(m['rendimento_annuo'])} | {pct(m['max_drawdown'])} | {m['sharpe']:.2f} | "
                   f"{d['dsr']:.2f} | {'✅' if verdict[name][0] else '❌'} |")

    out += ["", "## Walk-forward contro il bilanciato", "",
            "Ogni anno dal 2011 si sceglie il parametro solo sui 5 anni precedenti e lo si usa per l'anno dopo.", "",
            "| Ipotesi | Anni meglio / peggio del bilanciato | Anno peggiore vs bilanciato | Totale fuori campione vs bilanciato | Parametri scelti | Cancello 3 |",
            "|---|---|---|---|---|---|"]
    for name, (prior, grid, unit) in hyp.items():
        wf = walk_forward(grid, bench)
        diff = wf["strategia"] - wf["bilanciato"]
        tot = (1 + wf["strategia"]).prod() / (1 + wf["bilanciato"]).prod() - 1
        wins, losses = int((diff > 0.001).sum()), int((diff < -0.001).sum())
        ok = wins > losses and tot > 0
        verdict[name].append(ok)
        picks = ", ".join(str(p) for p in wf["parametro"].value_counts().index[:3])
        out.append(f"| {name} | {wins} / {losses} | {pct(diff.min())} | {pct(tot)} | {picks} ({unit}) | {'✅' if ok else '❌'} |")

    out += ["", "## Verdetto", "",
            "Passa in paper trading solo un'ipotesi che supera **entrambi** i cancelli statistici "
            "(il cancello 1, nessuna sbirciata al futuro, è garantito dal motore e dai test).", ""]
    for name, (g2, g3) in verdict.items():
        out.append(f"- {'✅ PASSA' if g2 and g3 else '❌ SCARTATA'}: {name} "
                   f"(Sharpe sgonfiato {'ok' if g2 else 'no'}, walk-forward {'ok' if g3 else 'no'})")
    text = "\n".join(out) + "\n"
    Path("IPOTESI.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
