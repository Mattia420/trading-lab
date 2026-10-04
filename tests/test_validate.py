import numpy as np
import pandas as pd

from validate import Config, backtest, deflated_sharpe, metrics


def random_returns(n=240, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2006-01-31", periods=n, freq="ME")
    return pd.DataFrame({"A": rng.normal(0.005, 0.04, n), "CASH": 0.0}, index=idx)


def test_engine_does_not_let_the_future_leak():
    """Segnale "oracolo": investito nei mesi in cui A sale. Se il motore non sfasasse il segnale
    di un mese, guadagnerebbe sempre; sfasato, non deve avere alcun vantaggio."""
    rets = random_returns()
    cheat = pd.DataFrame({"A": (rets["A"] > 0).astype(float)}, index=rets.index)
    cfg = Config(fee_bps=0, slippage_bps=0)
    unshifted_sharpe = metrics((cheat["A"] * rets["A"]), cfg)["sharpe"]
    engine_sharpe = metrics(backtest(rets, cheat, cfg)["net"], cfg)["sharpe"]
    assert unshifted_sharpe > 2
    assert engine_sharpe < 1


def test_costs_are_charged_on_turnover():
    rets = random_returns(24)
    flip = pd.DataFrame({"A": [1.0, 0.0] * 12}, index=rets.index)
    bt = backtest(rets, flip, Config(fee_bps=10, slippage_bps=5))
    assert bt["costs"].iloc[2:].round(6).eq(0.0015).all()


def test_deflated_sharpe_rejects_best_of_many_noise_strategies():
    rets = [random_returns(seed=s)["A"] - 0.005 for s in range(50)]  # nessun vantaggio vero
    srs = [r.mean() / r.std() for r in rets]
    best = rets[int(np.argmax(srs))]
    assert deflated_sharpe(best, srs)["dsr"] < 0.95
