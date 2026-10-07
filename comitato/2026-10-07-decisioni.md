# Decisioni del comitato — 07/10/2026

Fonte unica: `comitato/2026-10-07-dossier.md` (dati del giro del 06/10) e `regole/regole-rischio.md`.
Agenti: `agenti/rischio.md`, `agenti/trader.md`, regole comuni `agenti/comune.md`.
Nessun ordine reale viene eseguito. Gli ordini dei portafogli simulati partono da soli all'apertura.

---

## RAPPORTO RISCHIO — reale_100 — 07/10/2026

1. **CONTROLLO REGOLE**
   | Regola | Valore | Rispettata? | Come lo so |
   |---|---|---|---|
   | Capitale reale | 100 € | sì | dossier: "Capitale iniziale: 100,00 €" |
   | Strumenti ammessi | SWDA.MI, SEGA.MI, SGLD.MI | sì | tutti in `allowed_tickers` |
   | Commissione massima per ordine | 1% | sì | dossier: "Commissione per ordine di questo portafoglio: 0,00 €" |
   | Costi annui massimi | 1,5% | sì (stima 0% di commissioni; bollo 0,2%) | dossier e regole |
   | Niente leva / scoperto | — | sì | solo acquisti, contanti 100 € |
2. **COSTI** — 3 ordini da circa 60,00 €, 25,00 € e 15,00 € (quote proposte × prezzi del 06/10); commissione 0 € = 0%.
3. **RISCHIO** — calo dal massimo 0%; pesi 60/25/15 come da regola; nessuna concentrazione oltre l'obiettivo.
4. **VERDETTO** — PIANO COMPLETO dal punto di vista delle regole. Restano informazioni mancanti
   (vedi decisione) che non dipendono dal bot.

## DECISIONE DEL COMITATO — reale_100 — 07/10/2026

1. **DECISIONE:** ASPETTA
2. **MOTIVI**
   - Il piano rispetta tutte le regole di costo e rischio (rapporto rischio, punti 1–3).
   - Il broker non è ancora scelto: il dossier dice "SPECCHIO DEL CONTO REALE (da attivare)".
   - Non è verificato che i tre ETF siano disponibili nel PAC gratuito del broker scelto (regola "commissione massima 1%": vale solo se il PAC è davvero gratuito).
3. **DISACCORDI** — nessuno tra bot, regole e rapporto rischio.
4. **INFORMAZIONI MANCANTI**
   - Broker scelto (Trade Republic o Scalable Capital) e conto aperto.
   - Disponibilità nel PAC di SWDA, SEGA, SGLD o di equivalenti; se cambiano, va aggiornato `bot/config.json`.
   - Conferma che il PAC si può eseguire una sola volta senza costi.
5. **PROSSIMO PASSO PER MATTIA** — aprire il conto e controllare che i tre ETF siano nel piano di accumulo gratuito.

---

## RAPPORTO RISCHIO — operativo_100 (simulato) — 07/10/2026

1. **CONTROLLO REGOLE**
   | Regola | Valore | Rispettata? | Come lo so |
   |---|---|---|---|
   | Strumenti ammessi | XEON, XSPX, EXUS, CMOD | sì | tutti in `allowed_tickers` |
   | Commissione massima per ordine (soldi veri) | 1% | **no** | 1,00 € su ordini da circa 19 € (5,2%) e 38 € (2,6%) |
   | Costi annui massimi (soldi veri) | 1,5% | **no** (stima) | 4 ordini solo per entrare = 4% del capitale; nel backtest ~17 ordini l'anno |
   | Ordini al mese | max 10 | sì | 4 ordini |
   | Blocco a -15% | — | non scattato | dossier: "Calo dal massimo: +0.00%" |
2. **COSTI** — 4 ordini, 4,00 € di commissioni = 4% del capitale all'ingresso.
3. **RISCHIO** — 40% sul monetario (SEGA e IWDP sotto la media, dossier); il resto diviso su 3 mercati.
4. **VERDETTO** — RIFIUTATO per i soldi veri (costi oltre i limiti). Come simulazione è conforme.

## DECISIONE DEL COMITATO — operativo_100 (simulato) — 07/10/2026

1. **DECISIONE:** RIFIUTO per i soldi veri. La simulazione prosegue come esercizio.
2. **MOTIVI**
   - Commissione per ordine dal 2,6% al 5,2%, contro un limite dell'1% (rapporto rischio, punto 1).
   - Costi d'ingresso pari al 4% del capitale (rapporto rischio, punto 2).
   - Le regole richiedono 3 mesi di simulazione dal vivo prima dei soldi veri; ne ha 1 giorno (dossier: "giorni di storia: 1").
3. **DISACCORDI** — nessuno sui fatti. Il bot propone gli ordini perché è una simulazione; le regole li vietano solo con soldi veri.
4. **INFORMAZIONI MANCANTI** — un broker con commissioni zero sugli ordini singoli per questi ETF; capitale reale sufficiente perché 1 € pesi meno dell'1% (ordini da almeno 100 €, cioè circa 500 € di capitale su 5 asset).
5. **PROSSIMO PASSO PER MATTIA** — decidere se applicare la versione a costi ridotti proposta il 06/10 (uscita in liquidità, banda del 3%, decisione trimestrale).

---

## Portafogli senza ordini proposti

| Portafoglio | Decisione | Motivo (dal diario del 06/10) |
|---|---|---|
| bilanciato (2.000 €, simulato) | APPROVO l'assenza di ordini | "Pesi dentro la banda (scarto massimo -4.1 punti su SEGA.MI)", sotto il limite di 5 |
| trend_liquidita (simulato) | APPROVO l'assenza di ordini | "Segnale già valutato questo mese" |
| trend_short (simulato) | APPROVO l'assenza di ordini | "Segnale già valutato questo mese" |

## Anomalie dei dati
- Il 05/10/2026 manca nei dati della fonte (Yahoo Finance): il bot non ha operato quel giorno, come previsto
  dalle regole. Nessun effetto sui portafogli.
