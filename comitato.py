"""Prepara il dossier per il comitato di controllo (agenti Rischio e Trader).

    python comitato.py            # scrive comitato/AAAA-MM-GG-dossier.md

Il dossier contiene solo fatti presi dai file del progetto: regole, stato dei portafogli,
ordini proposti dal bot e costi. Gli agenti (agenti/rischio.md, agenti/trader.md) lo leggono
e scrivono comitato/AAAA-MM-GG-decisioni.md. Nessun ordine viene eseguito.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
CFG = json.loads((ROOT / "bot" / "config.json").read_text())


def eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def section(name, pcfg):
    path = ROOT / "state" / f"{name}.json"
    lines = [f"## Portafoglio `{name}`", "", f"- Descrizione: {pcfg['description']}"]
    if not path.exists():
        return "\n".join(lines + ["- Stato: NON ANCORA AVVIATO (nessun file in state/).", ""])
    s = json.loads(path.read_text())
    h = s["history"]
    value, capital = h[-1]["value"], s["meta"]["capital"]
    peak = max([x["value"] for x in h] + [capital])
    commission = pcfg.get("commission_eur", CFG["commission_eur"])
    days = max(1, len(h))
    lines += [f"- Ultimo giorno elaborato: {h[-1]['date']} (giorni di storia: {days})",
              f"- Capitale iniziale: {eur(capital)} | Valore: {eur(value)} ({(value / capital - 1) * 100:+.2f}%)",
              f"- Calo dal massimo: {(value / peak - 1) * 100:+.2f}% (massimo {eur(peak)})",
              f"- Liquidità: {eur(s['cash'])}",
              f"- Costi finora: commissioni {eur(s['totals']['commissioni'])} "
              f"({s['totals']['commissioni'] / capital * 100:.2f}% del capitale), tasse {eur(s['totals']['tasse'])}, "
              f"bollo {eur(s['totals']['bollo'])}; ordini totali {len(s['trades'])}",
              f"- Commissione per ordine di questo portafoglio: {eur(commission)}; quote frazionate: "
              f"{'sì' if pcfg.get('fractional') else 'no'}",
              f"- Bloccato: {s['meta'].get('halted', 'no')}"]
    if s["positions"]:
        lines += ["", "| Posizione | Quote | Prezzo medio |", "|---|---|---|"]
        lines += [f"| {t} | {p['qty']:g} | {eur(p['cost'])} |" for t, p in s["positions"].items()]
    pending = s["meta"].get("pending", [])
    lines += ["", f"**Ordini proposti dal bot, da eseguire all'apertura successiva: {len(pending)}**"]
    for p in pending:
        lines.append(f"- {p['side']} {p['qty']:g} {p['ticker']} (deciso il {p['decided']}): {p['reason']}")
    last5 = s["trades"][-5:]
    if last5:
        lines += ["", "Ultimi ordini eseguiti:"] + [
            f"- {t['date']}: {t['side']} {t['qty']:g} {t['ticker']} a {eur(t['price'])} "
            f"(importo {eur(t['qty'] * t['price'])}, commissione {eur(commission)} = "
            f"{commission / max(t['qty'] * t['price'], 0.01) * 100:.1f}% dell'ordine)" for t in last5]
    return "\n".join(lines + [""])


def main():
    today = date.today().isoformat()
    parts = [f"# Dossier del comitato — {today}", "",
             "Fonte: file del repository. Solo fatti; nessuna valutazione.", "",
             "## Regole di rischio in vigore", "", (ROOT / "regole" / "regole-rischio.md").read_text(), ""]
    parts += [section(n, p) for n, p in CFG["portfolios"].items()]
    out = ROOT / "comitato" / f"{today}-dossier.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(parts))
    print(out)


if __name__ == "__main__":
    main()
