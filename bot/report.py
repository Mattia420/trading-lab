"""Diario giornaliero (journal/AAAA-MM-GG.md) e riepilogo sempre aggiornato (STATO.md)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x):
    return f"{x:+.2f}%".replace(".", ",")


def portfolio_section(pf, log, row, names):
    value = pf.value(row)
    capital = pf.meta["capital"]
    prev = pf.history[-2]["value"] if len(pf.history) > 1 else capital
    peak = pf.peak()
    lines = [f"## {log['name']}", f"_{log['description']}_", "",
             f"- **Valore:** {eur(value)} (oggi {pct((value / prev - 1) * 100)}, "
             f"dall'inizio {pct((value / capital - 1) * 100)}, dal massimo {pct((value / peak - 1) * 100)})",
             f"- **Liquidità:** {eur(pf.cash)}",
             f"- **Decisione:** {log.get('decision', '-')}"]
    for n in log["notes"]:
        lines.append(f"- {n}")
    for key, title in (("executed", "Eseguiti oggi all'apertura (ordini decisi ieri sera)"),
                       ("orders", "Decisi stasera, da eseguire domani all'apertura (prezzo stimato)")):
        if log[key]:
            lines += ["", f"**{title}**", "", "| Ordine | Strumento | Quote | Prezzo | Importo |",
                      "|---|---|---|---|---|"]
            for o in log[key]:
                side = "Compra" if o.side == "BUY" else "Vendi"
                lines.append(f"| {side} | {o.ticker} ({names.get(o.ticker, '')}) | {o.qty:g} | "
                             f"{eur(o.price)} | {eur(o.amount)} |")
    for o, why in log["rejected"]:
        lines.append(f"- ⚠️ Ordine scartato dai controlli di rischio: {o.side} {o.qty} {o.ticker} ({why})")
    if pf.positions:
        lines += ["", "| Posizione | Quote | Prezzo medio | Prezzo oggi | Valore | Guadagno |",
                  "|---|---|---|---|---|---|"]
        for t, p in pf.positions.items():
            v = p["qty"] * row[t]
            lines.append(f"| {t} | {p['qty']:g} | {eur(p['cost'])} | {eur(row[t])} | {eur(v)} | "
                         f"{pct((row[t] / p['cost'] - 1) * 100)} |")
    tot = pf.totals
    lines += ["", f"Costi finora: commissioni {eur(tot['commissioni'])}, tasse {eur(tot['tasse'])}, "
                  f"bollo {eur(tot['bollo'])}. Ordini totali: {len(pf.trades)}.", ""]
    return "\n".join(lines)


def write_reports(results, row, today, cfg, problems, save=True):
    names = cfg["names"]
    head = [f"# Diario del bot — {today:%d/%m/%Y}", "",
            f"Modalità: **{cfg['mode']}** (soldi finti, prezzi veri di chiusura). "
            f"Commissione {eur(cfg['commission_eur'])} a ordine, slippage {cfg['slippage_bps']} punti base, "
            f"tasse {cfg['tax_rate']:.0%} sulle plusvalenze. Gli ordini decisi la sera si eseguono "
            "all'apertura del giorno dopo.", ""]
    if problems:
        head += ["> ⚠️ **Anomalie sui dati, nessun ordine eseguito:**"] + [f"> - {p}" for p in problems] + [""]
    summary = ["| Portafoglio | Valore | Dall'inizio | Ordini |", "|---|---|---|---|"]
    for pf, _ in results:
        v = pf.value(row)
        summary.append(f"| {pf.name} | {eur(v)} | {pct((v / pf.meta['capital'] - 1) * 100)} | {len(pf.trades)} |")
    body = [portfolio_section(pf, log, row, names) for pf, log in results]
    text = "\n".join(head + summary + [""] + body)
    if save:
        (ROOT / "journal").mkdir(exist_ok=True)
        (ROOT / "journal" / f"{today:%Y-%m-%d}.md").write_text(text)
        (ROOT / "STATO.md").write_text(text.replace("# Diario del bot", "# Stato del bot", 1))
    return text
