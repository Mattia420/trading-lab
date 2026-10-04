"""Validazione delle strategie: i tre cancelli da superare prima di usare soldi veri.

    python validate.py            # scrive VALIDAZIONE.md

1. Niente sbirciate al futuro: il segnale del mese t diventa posizione solo nel mese t+1
   (shift(1)); un test con un "segnale oracolo" verifica che il motore non lasci passare il futuro.
2. Sharpe sgonfiato (Bailey e López de Prado, 2014): il migliore di N tentativi deve battere
   quello che si otterrebbe per caso provando N strategie a vuoto.
3. Walk-forward: si sceglie il parametro solo sul passato, si opera sul futuro, si avanza.

Le tasse qui sono escluse (la domanda è: c'è un vantaggio reale?). Costi e tasse completi
sono in backtest.py.
"""
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np
import pandas as pd

from backtest import load_prices

N = NormalDist()
EULER = 0.5772156649


@dataclass
class Config:
    fee_bps: float = 25.0       # 5 € su un ordine da ~2.000 €
    slippage_bps: float = 10.0  # differenza denaro-lettera degli ETF su Borsa Italiana
    periods_per_year: int = 12  # dati mensili


# --- 1. Motore --------------------------------------------------------------------------

def backtest(rets: pd.DataFrame, weights: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """rets: rendimenti mensili semplici. weights: pesi decisi CON i dati di fine mese t.
    Il peso deciso a fine mese t si applica al rendimento del mese t+1."""
    position = weights.reindex(columns=rets.columns, fill_value=0).shift(1).fillna(0)
    gross = (position * rets).sum(axis=1)
    turnover = position.diff().abs().sum(axis=1).fillna(position.abs().sum(axis=1))
    costs = turnover * (cfg.fee_bps + cfg.slippage_bps) / 1e4
    net = gross - costs
    return pd.DataFrame({"gross": gross, "costs": costs, "net": net, "turnover": turnover})


def metrics(net: pd.Series, cfg: Config) -> dict:
    r = net.dropna()
    ppy = cfg.periods_per_year
    equity = (1 + r).cumprod()
    dd = equity / equity.cummax() - 1
    under = (dd < 0).astype(int)
    longest = under.groupby((under != under.shift()).cumsum()).sum().max()
    ann_ret = equity.iloc[-1] ** (ppy / len(r)) - 1
    vol = r.std() * np.sqrt(ppy)
    return {"rendimento_annuo": ann_ret, "volatilita": vol,
            "sharpe": r.mean() / r.std() * np.sqrt(ppy) if r.std() > 0 else 0.0,
            "max_drawdown": dd.min(), "mesi_sott_acqua": int(longest), "mesi": len(r)}


# --- Strategie: pesi decisi a fine mese con i soli dati disponibili a fine mese -----------

def const(px, w):
    return pd.DataFrame({t: v for t, v in w.items()}, index=px.index)


def trend_sma(px, asset, defensive, months, share=1.0):
    above = px[asset] > px[asset].rolling(months).mean()
    w = pd.DataFrame(0.0, index=px.index, columns=[asset, defensive])
    w[asset] = np.where(above, share, 0.0)
    w[defensive] = np.where(above, 0.0, share)
    w[w.index < px[asset].rolling(months).mean().first_valid_index()] = 0.0
    return w


def dual_momentum(px):
    r12 = px[["SPY", "EFA"]] / px[["SPY", "EFA"]].shift(12) - 1
    best = r12.fillna(-np.inf).idxmax(axis=1)
    w = pd.DataFrame(0.0, index=px.index, columns=["SPY", "EFA", "IEF"])
    for t in ("SPY", "EFA"):
        w[t] = ((best == t) & (r12.max(axis=1) > 0)).astype(float)
    w["IEF"] = (r12.max(axis=1) <= 0).astype(float)
    w[r12.max(axis=1).isna()] = 0.0
    return w


def all_trials(px):
    """Tutte le varianti provate finora in questo progetto, comprese quelle scartate.
    Contarle tutte è obbligatorio: ogni tentativo aumenta la probabilità di un vincitore per caso."""
    trend_world = trend_sma(px, "SPY", "CASH", 10, 0.6).add(trend_sma(px, "EFA", "CASH", 10, 0.4), fill_value=0)
    return {
        "Azionario 60/40 USA-mondo (compra e tieni)": (const(px, {"SPY": .6, "EFA": .4}), None),
        "Bilanciato azioni-bond-oro (compra e tieni)": (const(px, {"SPY": .4, "EFA": .2, "IEF": .25, "GLD": .15}), None),
        "Trend 10 mesi azionario mondo": (trend_world, "Azionario 60/40 USA-mondo (compra e tieni)"),
        "Dual momentum": (dual_momentum(px), "Azionario 60/40 USA-mondo (compra e tieni)"),
        "Borsa USA (compra e tieni)": (const(px, {"SPY": 1.0}), None),
        "Trend 10 mesi USA, sotto in liquidità": (trend_sma(px, "SPY", "CASH", 10), "Borsa USA (compra e tieni)"),
        "Trend 10 mesi USA, sotto ETF inverso": (trend_sma(px, "SPY", "SH", 10), "Borsa USA (compra e tieni)"),
        "Banche italiane (compra e tieni)": (const(px, {"ISP.MI": .5, "UCG.MI": .5}), None),
    }


# --- 2. Sharpe sgonfiato -------------------------------------------------------------------

def expected_max_z(n_trials):
    return (1 - EULER) * N.inv_cdf(1 - 1 / n_trials) + EULER * N.inv_cdf(1 - 1 / (n_trials * np.e))


def deflated_sharpe(r: pd.Series, trial_sharpes: list) -> dict:
    """Bailey e López de Prado (2014). Tutto in unità per periodo (mensili), NON annualizzate:
    la soglia è il massimo atteso tra N strategie senza vantaggio, scalato per la dispersione
    reale degli Sharpe provati."""
    r = r.dropna()
    sr = r.mean() / r.std()
    t = len(r)
    skew = ((r - r.mean()) ** 3).mean() / r.std(ddof=0) ** 3
    kurt = ((r - r.mean()) ** 4).mean() / r.std(ddof=0) ** 4
    n = len(trial_sharpes)
    sr0 = np.std(trial_sharpes, ddof=1) * expected_max_z(n) if n > 1 else 0.0
    denom = np.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2)
    dsr = N.cdf((sr - sr0) * np.sqrt(t - 1) / denom)
    return {"dsr": dsr, "soglia_sharpe_annuo": sr0 * np.sqrt(12), "sharpe_annuo": sr * np.sqrt(12)}


# --- 3. Walk-forward -----------------------------------------------------------------------

def walk_forward(px, rets, cfg, make_weights, grid, train=60, test=12):
    """Per ogni finestra: sceglie il parametro migliore (Sharpe) sui `train` mesi passati,
    lo applica ai `test` mesi successivi mai visti, poi avanza di `test` mesi."""
    folds, picks = [], []
    stitched = pd.DataFrame(np.nan, index=px.index, columns=rets.columns)
    i = 13  # servono 12 mesi di storia anche per le medie più lunghe
    while i + train + test <= len(px):
        tr = slice(i, i + train)
        scores = {p: metrics(backtest(rets.iloc[tr], make_weights(px, p).iloc[tr], cfg)["net"], cfg)["sharpe"]
                  for p in grid}
        best = max(scores, key=scores.get)
        # decisioni prese da fine ultimo mese di training a fine penultimo mese di test:
        # i pesi usano solo dati passati (medie mobili), il parametro solo il training
        dec = slice(i + train - 1, i + train + test - 1)
        w = make_weights(px, best).reindex(columns=rets.columns, fill_value=0)
        stitched.iloc[dec] = w.iloc[dec].values
        picks.append((rets.index[i + train], best, slice(i + train, i + train + test)))
        i += test
    net = backtest(rets, stitched.fillna(0), cfg)["net"]
    for start, best, te in picks:
        folds.append({"inizio": start.strftime("%m/%Y"), "parametro": best,
                      "rendimento": (1 + net.iloc[te]).prod() - 1})
    return pd.DataFrame(folds)


def regimes(px):
    """Fasi di mercato dall'azionario mondo: rialzo, ribasso, laterale (rendimento 12 mesi)."""
    world = 0.6 * px["SPY"] + 0.4 * px["EFA"] * (px["SPY"].iloc[0] / px["EFA"].iloc[0])
    r12 = world / world.shift(12) - 1
    return pd.cut(r12, [-np.inf, -0.05, 0.10, np.inf], labels=["ribasso", "laterale", "rialzo"])


# --- Rapporto ------------------------------------------------------------------------------

def pct(x):
    return f"{x:+.1%}".replace(".", ",")


def main():
    cfg = Config()
    px = load_prices().loc["2005-01-31":]
    rets = px.pct_change().fillna(0)
    rets["CASH"] = 0.0
    eval_from = "2006-01-31"
    trials = all_trials(px)
    runs = {name: backtest(rets, w, cfg).loc[eval_from:] for name, (w, _) in trials.items()}
    trial_sr = [r["net"].mean() / r["net"].std() for r in runs.values()]

    out = ["# Validazione delle strategie", "",
           f"Dati mensili {runs[next(iter(runs))].index[0]:%m/%Y} - {px.index[-1]:%m/%Y}, in euro. "
           f"Costi: {cfg.fee_bps:.0f} punti base di commissione + {cfg.slippage_bps:.0f} di slippage "
           "per ogni euro scambiato. Tasse escluse (sono in `backtest.py`).", "",
           f"**Tentativi contati: {len(trials)}** (tutte le varianti provate in questo progetto, "
           "comprese quelle scartate).", "",
           "## Risultati e Sharpe sgonfiato", "",
           "Per chi fa timing la domanda giusta non è \"guadagna?\" ma \"guadagna più del semplice "
           "compra e tieni?\": lo Sharpe sgonfiato è calcolato sulla differenza col suo riferimento.", "",
           "| Strategia | Rendimento annuo | Calo max | Sharpe | Confronto | Sharpe sgonfiato | Cancello 2 |",
           "|---|---|---|---|---|---|---|"]
    gate2 = {}
    for name, (w, bench) in trials.items():
        m = metrics(runs[name]["net"], cfg)
        if bench:
            excess = runs[name]["net"] - runs[bench]["net"]
            d = deflated_sharpe(excess, trial_sr)
            what = f"vs {bench.split(' (')[0]}"
        else:
            d = deflated_sharpe(runs[name]["net"], trial_sr)
            what = "assoluto"
        gate2[name] = d["dsr"] > 0.95
        out.append(f"| {name} | {pct(m['rendimento_annuo'])} | {pct(m['max_drawdown'])} | "
                   f"{m['sharpe']:.2f} | {what} | {d['dsr']:.2f} | {'✅' if gate2[name] else '❌'} |")
    soglia = deflated_sharpe(runs[next(iter(runs))]["net"], trial_sr)["soglia_sharpe_annuo"]
    out += ["", f"Lo Sharpe sgonfiato è la probabilità che il vantaggio sia reale e non fortuna dopo "
                f"{len(trials)} tentativi: serve almeno 0,95. Con {len(trials)} tentativi, uno Sharpe annuo di "
                f"circa {soglia:.2f} si otterrebbe anche per puro caso.", ""]

    # walk-forward sul parametro della media mobile
    out += ["## Walk-forward: la media mobile scelta solo sul passato", "",
            "Per ogni anno dal 2011: si sceglie la media mobile migliore (6, 8, 10 o 12 mesi) guardando "
            "solo i 5 anni precedenti, la si usa per i 12 mesi successivi, poi si ripete.", "",
            "| Strategia | Anni meglio / pari / peggio del compra e tieni | Anno peggiore vs compra e tieni | Totale fuori campione vs compra e tieni |",
            "|---|---|---|---|"]
    bh = backtest(rets, const(px, {"SPY": 1.0}), cfg)["net"]
    gate3 = {}
    for name, defensive in (("Trend USA, sotto in liquidità", "CASH"), ("Trend USA, sotto ETF inverso", "SH")):
        wf = walk_forward(px, rets, cfg, lambda p, m, d=defensive: trend_sma(p, "SPY", d, m), [6, 8, 10, 12])
        bh_f = [(1 + bh.loc[pd.Timestamp(f"{f[3:]}-{f[:2]}-01"):].iloc[:12]).prod() - 1 for f in wf["inizio"]]
        diff = wf["rendimento"].values - np.array(bh_f)
        tot = (1 + wf["rendimento"]).prod() / np.prod(1 + np.array(bh_f)) - 1
        wins, ties = int((diff > 0.001).sum()), int((abs(diff) <= 0.001).sum())
        gate3[name] = wins > len(diff) - wins - ties and tot > 0
        out.append(f"| {name} | {wins} / {ties} / {len(diff) - wins - ties} | {pct(diff.min())} | {pct(tot)} |")
        wf_detail = wf.assign(compra_e_tieni=bh_f)
    out += ["", "Parametri scelti anno per anno (ultima strategia): " +
            ", ".join(f"{r.inizio[3:]}: {r.parametro}" for r in wf_detail.itertuples()) + ".",
            "Se il parametro \"migliore\" cambia spesso, non c'è un valore stabile: è rumore.",
            "Cancello 3 superato solo se gli anni migliori sono più dei peggiori E il totale fuori campione è positivo: "
            + ", ".join(f"{k} {'✅' if v else '❌'}" for k, v in gate3.items()) + ".", ""]

    # regimi
    reg = regimes(px).loc[eval_from:]
    out += ["## Per fase di mercato (rendimento medio mensile)", "",
            "| Strategia | Rialzo | Laterale | Ribasso |", "|---|---|---|---|"]
    for name in trials:
        n = runs[name]["net"]
        by = n.groupby(reg.shift(1).reindex(n.index), observed=False).mean()
        out.append(f"| {name} | " + " | ".join(pct(by.get(k, np.nan)) for k in ("rialzo", "laterale", "ribasso")) + " |")
    counts = reg.shift(1).value_counts()
    out += ["", f"Mesi per fase: rialzo {counts.get('rialzo', 0)}, laterale {counts.get('laterale', 0)}, "
                f"ribasso {counts.get('ribasso', 0)}. Il campione contiene sia rialzi sia ribassi (2008, 2011, 2020, 2022).", ""]

    out += ["## Verdetto", "",
            "Una strategia può usare soldi veri solo se supera tutti e tre i cancelli "
            "(1: nessuna sbirciata al futuro, verificato dai test; 2: Sharpe sgonfiato ≥ 0,95; "
            "3: walk-forward). Per le strategie di timing il confronto è con il compra e tieni.", ""]
    for name, (w, bench) in trials.items():
        ok = gate2[name] and gate3.get(name.replace("Trend 10 mesi USA", "Trend USA"), True)
        out.append(f"- {'✅' if ok else '❌'} {name}")
    text = "\n".join(out)
    open("VALIDAZIONE.md", "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
