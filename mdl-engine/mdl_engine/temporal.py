"""Temporal layer (learning-curve memo, sections 2, 5, 6): is the frontier moving?

Four tools, all small and auditable:
  record_count_test   distribution-free test of 'World B' (static F, more sampling)
  simulate_static_null Monte-Carlo version with an explicit exponential upper tail
  poisson_changepoint exact Bayesian single changepoint in the record-event rate
  gate_backtest / calibrate_window  the pivot gate's firing history and false-fire rate
"""
from __future__ import annotations
import math
import numpy as np
from scipy import stats
from scipy.special import gammaln


# ---------------------------------------------------------------- series utils
def frontier(events):
    """events: [(decimal_year, efficiency)] -> running-max records only, sorted."""
    out, best = [], -math.inf
    for t, e in sorted(events):
        if e > best:
            out.append((t, e))
            best = e
    return out


def increments(events):
    f = frontier(events)
    return [(f[i][0], round(f[i][1] - f[i - 1][1], 3)) for i in range(1, len(f))]


def drift_rate(events, t0, t1):
    """Least-squares slope (abs. points / yr) of frontier records in [t0, t1],
    plus the simple endpoint rate. With <4 points this is a description, not an estimate."""
    f = [(t, e) for t, e in frontier(events) if t0 <= t <= t1]
    if len(f) < 2:
        return None
    t = np.array([x[0] for x in f]); e = np.array([x[1] for x in f])
    slope = float(np.polyfit(t, e, 1)[0]) if len(f) >= 3 else None
    return {"n_records": len(f), "ols_slope_pts_per_yr": None if slope is None else round(slope, 2),
            "endpoint_rate_pts_per_yr": round(float((e[-1] - e[0]) / (t[-1] - t[0])), 2)}


# ------------------------------------------------- World B: distribution-free
def record_count_test(k_records: int, attempt_ratio: float) -> dict:
    """P(at least k new records) when an i.i.d. static distribution is sampled
    until cumulative attempts grow by `attempt_ratio` (= N_after / N_before).

    For i.i.d. continuous draws the chance that draw j is a record is 1/j, whatever
    the distribution. So the number of new records between N0 and N1 draws is
    approximately Poisson with mean ln(N1/N0). No tail shape assumed.
    """
    mu = math.log(attempt_ratio)
    p = float(stats.poisson.sf(k_records - 1, mu))
    return {"k_records": k_records, "attempt_ratio": attempt_ratio,
            "expected_records": round(mu, 2), "p_value": p}


def ratio_needed(k_records: int, p: float = 0.05) -> float:
    """Smallest cumulative-attempt multiplication at which seeing >= k records
    under a static distribution stops being surprising at level p."""
    lo, hi = 1.0, 1e12
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if record_count_test(k_records, mid)["p_value"] < p:
            lo = mid
        else:
            hi = mid
    return hi


def simulate_static_null(r0: float, target: float, n_before: int, n_after: int,
                         tail_scale: float, n_sim: int = 20000, seed: int = 0) -> dict:
    """Static F with exponential upper tail (scale = tail_scale, in abs. points).

    The standing record r0 is the max of n_before draws, so its exceedance
    probability p0 is Beta(1, n_before). Each later draw beats the current record
    R with probability p0*exp(-(R - r0)/tail_scale)
    and overshoots by Exp(tail_scale) (memorylessness).
    Returns P(frontier >= target after n_after further draws) and the mean number
    of new records.
    """
    rng = np.random.default_rng(seed)
    reached = 0
    counts = np.zeros(n_sim, dtype=int)
    for s in range(n_sim):
        # exceedance probability of the max of n_before draws is Beta(1, n_before)
        p0 = rng.beta(1.0, n_before)
        rec, left, k = r0, n_after, 0
        while left > 0:
            p = p0 * math.exp(-(rec - r0) / tail_scale)
            wait = rng.geometric(p) if p > 1e-15 else left + 1
            if wait > left:
                break
            left -= wait
            rec += rng.exponential(tail_scale)
            k += 1
        counts[s] = k
        reached += rec >= target
    return {"p_reach_target": reached / n_sim, "mean_new_records": float(counts.mean()),
            "tail_scale": tail_scale, "attempt_ratio": (n_before + n_after) / n_before}


# ------------------------------------------------------ Bayesian changepoint
def poisson_changepoint(years, counts, a: float = 1.0, b: float = 2.0) -> dict:
    """Exact posterior over a single changepoint in a Poisson rate.

    Rates before/after ~ Gamma(a, b) (prior mean a/b records/yr); uniform prior on
    the changepoint year tau (rate changes from year tau onward). Also returns the
    Bayes factor against the no-changepoint model.
    """
    years = list(years); c = np.asarray(counts, float); n = len(c)

    def logml(seg):
        s, m = seg.sum(), len(seg)
        return (a * math.log(b) - gammaln(a) + gammaln(a + s) - (a + s) * math.log(b + m)
                - gammaln(seg + 1).sum())

    lm = np.array([logml(c[:i]) + logml(c[i:]) for i in range(1, n)])
    post = np.exp(lm - lm.max()); post /= post.sum()
    log_bf = float(np.log(np.mean(np.exp(lm - lm.max()))) + lm.max() - logml(c))
    i = int(np.argmax(post))
    pre, pst = c[:i + 1], c[i + 1:]
    return {"posterior": {int(years[j + 1]): round(float(post[j]), 4) for j in range(n - 1)},
            "map_year": int(years[i + 1]), "map_prob": round(float(post[i]), 3),
            "log10_bayes_factor_vs_no_change": round(log_bf / math.log(10), 2),
            "rate_before": round(float((a + pre.sum()) / (b + len(pre))), 3),
            "rate_after": round(float((a + pst.sum()) / (b + len(pst))), 3)}


def annual_counts(events, y0: int, y1: int):
    f = frontier(events)
    years = list(range(y0, y1 + 1))
    return years, [sum(1 for t, _ in f if int(math.floor(t)) == y) for y in years]


# ------------------------------------------------------------------ the gate
def gate_backtest(events, window_yr: float, t_end: float, leading_alive=None) -> list:
    """Intervals during which the gate is fired.

    One-signal gate (v2 draft): fires once no new record for `window_yr`.
    Two-signal gate: pass `leading_alive(t) -> bool`; the gate fires only while
    silence has lasted `window_yr` AND the leading indicators are not alive.
    """
    f = frontier(events)
    fired = []
    for i, (t, _) in enumerate(f):
        nxt = f[i + 1][0] if i + 1 < len(f) else t_end
        start = t + window_yr
        if start < nxt:
            if leading_alive is None:
                fired.append((round(start, 2), round(nxt, 2)))
            else:
                grid = np.arange(start, nxt, 0.25)
                run = None
                for g in grid:
                    if not leading_alive(g):
                        run = run or g
                    elif run is not None:
                        fired.append((round(run, 2), round(float(g), 2))); run = None
                if run is not None:
                    fired.append((round(run, 2), round(nxt, 2)))
    return fired


def calibrate_window(windows=(2, 3, 4, 5), attempt_rates=(0.5, 1, 2, 4),
                     drift=0.25, shortfall_scale=1.0, horizon=9.0, incumbent_lead=1.0,
                     n_sim=4000, seed=1) -> dict:
    """False-fire probability of the SILENCE signal alone during latent progress.

    World: true capability rises `drift` points/yr (hidden). Certification-grade
    record attempts arrive Poisson(rate/yr); each lands at capability(t) minus an
    Exp(shortfall_scale) shortfall. A record needs to beat the standing one, which
    starts `incumbent_lead` points above capability (1.0 = an outlier incumbent, as
    IBM's hydrazine cell arguably was in 2014; 0.0 = incumbent sits at capability).
    Returns P(silence >= W at some point within `horizon` years).
    """
    rng = np.random.default_rng(seed)
    out = {}
    for lam in attempt_rates:
        longest = np.zeros(n_sim)
        for s in range(n_sim):
            n = rng.poisson(lam * horizon)
            ts = np.sort(rng.uniform(0, horizon, n))
            rec, last, gap = incumbent_lead, 0.0, 0.0
            for t in ts:
                x = drift * t - rng.exponential(shortfall_scale)
                if x > rec:
                    gap = max(gap, t - last); rec, last = x, t
            longest[s] = max(gap, horizon - last)
        out[lam] = {w: round(float((longest >= w).mean()), 3) for w in windows}
    return {"params": {"drift_pts_per_yr": drift, "shortfall_scale": shortfall_scale, "incumbent_lead": incumbent_lead,
                       "horizon_yr": horizon},
            "p_false_fire": out}
