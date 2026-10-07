import pandas as pd
import pytest

from bot import risk
from bot.portfolio import Order, Portfolio
from bot.strategies import fixed_weights, trend

RULES = {"allowed_tickers": ["A", "B", "C"], "max_orders_per_day": 6, "max_daily_loss_pct": 5,
         "max_drawdown_pct": 30, "max_price_jump_pct": 15, "max_data_age_days": 4}


def new_pf(cash=2000):
    return Portfolio(name="t", cash=cash, meta={"capital": cash})


def test_plan_never_spends_more_than_cash():
    pf = new_pf()
    row = pd.Series({"A": 128.9, "B": 104.4, "C": 361.3})
    orders = pf.plan({"A": 0.6, "B": 0.25, "C": 0.15}, row, commission=5, min_order=100)
    for o in orders:
        pf.execute(o, 5, 0.26, "2026-01-01")
    assert pf.cash >= 0
    assert {o.ticker for o in orders} == {"A", "B", "C"}  # anche lo strumento caro viene comprato


def test_sell_with_gain_pays_tax_and_loss_is_recorded():
    pf = new_pf()
    pf.execute(Order("A", "BUY", 10, 100), 5, 0.26, "d")
    pf.execute(Order("A", "SELL", 5, 120), 5, 0.26, "d")
    assert pf.totals["tasse"] == pytest.approx(5 * 20 * 0.26)
    pf.execute(Order("A", "SELL", 5, 90), 5, 0.26, "d")
    assert pf.totals["minus_non_compensabili"] == pytest.approx(50)
    assert pf.positions == {}


def test_filter_rejects_unknown_ticker_short_selling_and_leverage():
    pf = new_pf(cash=500)
    row = pd.Series({"A": 100.0, "X": 10.0})
    ok, rejected = risk.filter_orders(
        [Order("X", "BUY", 1, 10), Order("A", "SELL", 1, 100), Order("A", "BUY", 10, 100)],
        pf, row, RULES, commission=5)
    assert ok == []
    assert [why for _, why in rejected] == ["strumento non in elenco", "vendita allo scoperto non ammessa",
                                             "contanti insufficienti (niente leva)"]


def test_drawdown_halts_until_owner_intervenes():
    pf = new_pf()
    pf.history = [{"date": "d1", "value": 2000}, {"date": "d2", "value": 1450}]
    blocked, _ = risk.check_portfolio(pf, 1380, RULES)
    assert blocked and pf.meta["halted"]
    blocked, why = risk.check_portfolio(pf, 2500, RULES)
    assert blocked and "proprietario" in why


def test_daily_loss_blocks_orders():
    pf = new_pf()
    pf.history = [{"date": "d1", "value": 2000}]
    blocked, why = risk.check_portfolio(pf, 1880, RULES)
    assert blocked and "oggi" in why


def test_market_check_flags_jump_and_missing_price():
    idx = pd.bdate_range("2026-09-01", periods=5)
    prices = pd.DataFrame({"A": [100, 101, 102, 103, 130], "B": [50, 50, 50, 50, None]}, index=idx)
    problems = risk.check_market(prices, idx[-1], ["A", "B"], RULES, idx[-1])
    assert any("A: variazione" in p for p in problems)
    assert any("B: manca" in p for p in problems)


def test_trend_uses_only_completed_months_and_decides_once():
    idx = pd.bdate_range("2025-01-01", "2026-09-25")
    up = pd.Series(range(len(idx)), index=idx, dtype=float) + 100
    prices = pd.DataFrame({"A": up, "C": 1.0}, index=idx)
    cfg = {"asset": "A", "defensive": "C", "sma_months": 10}
    pf = new_pf()
    target, why = trend(cfg, prices, pf, idx[-1])
    assert target == {"A": 1.0} and "08/2026" in why
    pf.meta["last_signal_month"] = "2026-09"
    assert trend(cfg, prices, pf, idx[-1])[0] is None


def test_fixed_weights_holds_inside_band():
    row = pd.DataFrame({"A": [100.0], "B": [100.0]}, index=[pd.Timestamp("2026-09-25")])
    pf = new_pf(cash=0)
    pf.positions = {"A": {"qty": 6, "cost": 100}, "B": {"qty": 4, "cost": 100}}
    cfg = {"weights": {"A": 0.62, "B": 0.38}, "drift_pp": 5}
    assert fixed_weights(cfg, row, pf, row.index[0])[0] is None


def test_pending_orders_fill_next_open_with_slippage():
    from bot.run import fill_pending
    pf = new_pf(cash=1000)
    pf.meta["pending"] = [{"ticker": "A", "side": "BUY", "qty": 5, "reason": "r", "decided": "d"}]
    log = {"executed": [], "notes": []}
    cfg = {"slippage_bps": 10, "commission_eur": 5, "tax_rate": 0.26}
    fill_pending(pf, pd.Series({"A": 100.0}), cfg, pd.Timestamp("2026-10-05"), log)
    assert log["executed"][0].price == pytest.approx(100.1)  # paga lo slippage
    assert "pending" not in pf.meta and pf.qty("A") == 5


def test_pending_buy_is_reduced_when_open_gaps_up():
    from bot.run import fill_pending
    pf = new_pf(cash=505)
    pf.meta["pending"] = [{"ticker": "A", "side": "BUY", "qty": 5, "reason": "r", "decided": "d"}]
    log = {"executed": [], "notes": []}
    fill_pending(pf, pd.Series({"A": 120.0}), {"slippage_bps": 0, "commission_eur": 5, "tax_rate": 0.26},
                 pd.Timestamp("2026-10-05"), log)
    assert pf.qty("A") == 4 and pf.cash >= 0


def test_fractional_plan_reaches_weights_and_respects_commissions():
    pf = new_pf(cash=100)
    row = pd.Series({"A": 131.0, "B": 104.0, "C": 355.0})
    orders = pf.plan({"A": 0.6, "B": 0.25, "C": 0.15}, row, commission=1, min_order=5, fractional=True)
    for o in orders:
        pf.execute(o, 1, 0.26, "d")
    assert {o.ticker for o in orders} == {"A", "B", "C"}  # anche con 100 € si compra tutto
    assert 0 <= pf.cash < 1
    assert pf.qty("A") * 131 == pytest.approx(0.6 * 97, abs=0.02)


def test_trend_multi_splits_assets_and_uses_defensive():
    from bot.strategies import trend_multi
    idx = pd.bdate_range("2025-01-01", "2026-09-25")
    up = pd.Series(range(len(idx)), index=idx, dtype=float) + 100
    prices = pd.DataFrame({"A": up, "B": up[::-1].values, "D": 1.0}, index=idx)
    target, _ = trend_multi({"assets": ["A", "B"], "defensive": "D", "sma_months": 10}, prices, new_pf(), idx[-1])
    assert target == {"A": 0.5, "D": 0.5}


def _trend_prices(last_gap):
    """Prezzi piatti a 100 per un anno; l'ultima chiusura di settembre è 100 * (1 + last_gap)."""
    idx = pd.bdate_range("2025-07-01", "2026-10-06")
    s = pd.Series(100.0, index=idx)
    s.loc["2026-09-30"] = 100 * (1 + last_gap)
    return pd.DataFrame({"A": s})


def test_band_ignores_small_moves_and_cash_means_no_order():
    from bot.strategies import trend_multi
    cfg = {"assets": ["A"], "defensive": "CASH", "sma_months": 10, "band_pct": 3, "months": [1, 4, 7, 10]}
    pf = new_pf()
    pf.meta["in_trend"] = {"A": True}
    target, _ = trend_multi(cfg, _trend_prices(-0.01), pf, pd.Timestamp("2026-10-06"))
    assert target == {"A": 1.0}  # -1% dalla media: dentro la banda, resta investito
    pf.meta.pop("last_signal_month", None)
    target, _ = trend_multi(cfg, _trend_prices(-0.05), pf, pd.Timestamp("2026-10-06"))
    assert target == {"CASH": 1.0}  # -5%: esce, in liquidità


def test_quarterly_decision_skips_other_months():
    from bot.strategies import trend_multi
    cfg = {"assets": ["A"], "defensive": "CASH", "sma_months": 10, "months": [1, 4, 7, 10]}
    pf = new_pf()
    pf.meta["in_trend"] = {"A": True}
    target, why = trend_multi(cfg, _trend_prices(0.05), pf, pd.Timestamp("2026-11-03"))
    assert target is None and "mesi" in why
