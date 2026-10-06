"""Portafoglio simulato: contanti, posizioni a quote intere, costo medio, tasse italiane."""
import json
import math
from dataclasses import dataclass, field
from pathlib import Path


def floor4(x):
    """Arrotonda per difetto a 4 decimali (le quote frazionate dei broker)."""
    return math.floor(x * 10000) / 10000


@dataclass
class Order:
    ticker: str
    side: str  # "BUY" o "SELL"
    qty: float  # intera per i conti normali, frazionata per i PAC
    price: float
    reason: str = ""

    @property
    def amount(self):
        return self.qty * self.price


@dataclass
class Portfolio:
    name: str
    cash: float
    positions: dict = field(default_factory=dict)  # ticker -> {"qty": int, "cost": float}
    history: list = field(default_factory=list)    # [{"date", "value"}]
    trades: list = field(default_factory=list)
    totals: dict = field(default_factory=lambda: {"commissioni": 0.0, "tasse": 0.0, "bollo": 0.0,
                                                  "minus_non_compensabili": 0.0})
    meta: dict = field(default_factory=dict)

    # --- persistenza ---
    @classmethod
    def load(cls, path: Path, name: str, capital: float):
        if path.exists():
            return cls(**json.loads(path.read_text()))
        return cls(name=name, cash=capital, meta={"capital": capital})

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.__dict__, indent=1, default=str))

    # --- valori ---
    def qty(self, t):
        return self.positions.get(t, {}).get("qty", 0)

    def value(self, row):
        return self.cash + sum(p["qty"] * row[t] for t, p in self.positions.items())

    def peak(self):
        return max([h["value"] for h in self.history] + [self.meta.get("capital", 0)])

    # --- ordini ---
    def plan(self, target, row, commission, min_order, fractional=False):
        """Ordini a quote intere per avvicinarsi il più possibile ai pesi obiettivo.

        Parte arrotondando per difetto, poi aggiunge una quota alla volta allo strumento più
        sottopesato finché i contanti bastano e l'aggiunta riduce lo scarto dal peso obiettivo.
        Prima le vendite, poi gli acquisti."""
        value = self.value(row)
        if fractional:
            # quote frazionate (PAC dei broker online): si arriva al peso esatto, tolte le commissioni
            investable = value - commission * (len(target) + len(self.positions))
            want = {t: floor4(w * investable / row[t]) for t, w in target.items()}
        else:
            want = {t: math.floor(w * value / row[t]) for t, w in target.items()}
        budget = value - sum(q * row[t] for t, q in want.items()) - commission * (len(target) + len(self.positions))
        while not fractional:
            gap = {t: target[t] * value - want[t] * row[t] for t in target}
            options = [t for t in target if row[t] <= budget and abs(gap[t] - row[t]) < abs(gap[t])]
            if not options:
                break
            t = max(options, key=lambda t: gap[t])
            want[t] += 1
            budget -= row[t]

        orders = []
        for t in list(self.positions):
            excess = round(self.qty(t) - want.get(t, 0), 4)
            if excess > 0 and (want.get(t, 0) == 0 or excess * row[t] >= min_order):
                orders.append(Order(t, "SELL", excess, float(row[t])))
        cash = self.cash + sum(o.amount - commission for o in orders)
        for t in sorted(target, key=lambda t: -target[t]):
            room = (cash - commission) / row[t]
            buy = min(round(want[t] - self.qty(t), 4), floor4(room) if fractional else math.floor(room))
            if buy > 0 and buy * row[t] >= min_order:
                orders.append(Order(t, "BUY", buy, float(row[t])))
                cash -= buy * row[t] + commission
        return orders

    def execute(self, o: Order, commission, tax_rate, date):
        """Esecuzione simulata al prezzo di chiusura. Tasse 26% sulle plusvalenze realizzate;
        sugli ETF le minusvalenze non compensano le plusvalenze (redditi di natura diversa)."""
        tax = 0.0
        if o.side == "BUY":
            p = self.positions.setdefault(o.ticker, {"qty": 0, "cost": 0.0})
            p["cost"] = (p["cost"] * p["qty"] + o.amount) / (p["qty"] + o.qty)
            p["qty"] += o.qty
            self.cash -= o.amount + commission
        else:
            p = self.positions[o.ticker]
            gain = o.qty * (o.price - p["cost"])
            if gain > 0:
                tax = gain * tax_rate
            else:
                self.totals["minus_non_compensabili"] -= gain
            p["qty"] = round(p["qty"] - o.qty, 6)
            if p["qty"] <= 1e-6:
                del self.positions[o.ticker]
            self.cash += o.amount - commission - tax
        self.totals["commissioni"] += commission
        self.totals["tasse"] += tax
        self.trades.append({"date": date, "ticker": o.ticker, "side": o.side, "qty": o.qty,
                            "price": round(o.price, 4), "tax": round(tax, 2), "reason": o.reason})
        if self.cash < -1e-6:
            raise RuntimeError(f"{self.name}: contanti negativi dopo {o}")
