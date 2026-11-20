"""Campaign strategies: the OVAT control arm and the loop (noise-aware batch BO).

Both arms start from the literature recipe, use the same furnace (shared
trajectory per run, four slots) and are scored the same way: the true QFLS of
the recipe each arm would hand to an anchor device after N runs.

OVAT is written as a competent human campaign, not a straw man: it replicates
every trajectory level four times, uses all four slots for sample-level
variables (two levels x two replicates), line-searches in the improving
direction, and halves its step after each full pass.
"""
from __future__ import annotations

import math
import warnings

import numpy as np
from scipy.stats import norm

from .space import Cat, P0_SPACE

warnings.filterwarnings("ignore", module="sklearn")


def _mean_valid(obs):
    v = [o.qfls for o in obs if not o.failed]
    return (float(np.mean(v)), len(v)) if v else (-math.inf, 0)


# --------------------------------------------------------------------------- OVAT
class OVAT:
    """One-variable-at-a-time control arm.

    careful=True (the control C1 should pre-register)
        pools every observation of the current recipe; accepts a change only
        if its mean beats the pooled incumbent by more than one standard error
        of the difference; re-measures the incumbent every ``remeasure_every``
        runs, the same replicate overhead the loop carries.
    careful=False ("greedy", kept to show the failure mode)
        accepts any candidate whose four-film mean beats the last accepted
        mean. Its incumbent estimate is a noisy maximum, so it ratchets upward
        on noise and later rejects real gains.
    """
    ORDER = ["anneal_c", "anneal_min", "se_mg", "na_mM", "li_mM", "ramp_c_per_min",
             "cool_c_per_min", "cu_ratio", "inter_hold_min", "inter_hold_c", "li_layer"]

    def __init__(self, start: dict, space=P0_SPACE, step: float = 0.25, shrink: float = 0.5,
                 careful: bool = True, z: float = 1.0, remeasure_every: int = 5):
        self.space, self.cur, self.step0, self.shrink = space, dict(start), step, shrink
        self.careful, self.z, self.every = careful, z, remeasure_every
        self.name = "ovat" if careful else "ovat-greedy"
        self.est = -math.inf
        self._gen = None
        self._pool = {}            # recipe key -> list of observed QFLS
        self._resid = []           # within-recipe deviations, for the pooled SD

    @staticmethod
    def _key(x):
        return tuple(sorted((k, round(v, 9) if isinstance(v, float) else v) for k, v in x.items()))

    def _record(self, obs):
        for o in obs:
            if not o.failed:
                self._pool.setdefault(self._key(o.x), []).append(o.qfls)

    def _sd(self):
        devs = []
        for v in self._pool.values():
            if len(v) >= 2:
                m = np.mean(v)
                devs += [(x - m) ** 2 * len(v) / (len(v) - 1) for x in v]
        return math.sqrt(np.mean(devs)) if devs else 0.02

    def _cur_est(self):
        v = self._pool.get(self._key(self.cur), [])
        return (float(np.mean(v)), len(v)) if v else (-math.inf, 0)

    def _better(self, x, m, n):
        """Should candidate x (mean m over n films) replace the incumbent?"""
        if not n:
            return False
        if not self.careful:
            return m > self.est
        mc, nc = self._cur_est()
        if nc == 0:
            return True
        se = self._sd() * math.sqrt(1.0 / n + 1.0 / nc)
        return m - mc > self.z * se

    def _accept(self, x, m):
        self.cur = dict(x)
        self.est = m if not self.careful else self._cur_est()[0]

    def _shift(self, x, name, du):
        p = self.space[name]
        u = p.to_unit(x[name]) + du
        if u < -1e-9 or u > 1 + 1e-9:
            return None
        y = dict(x)
        y[name] = p.from_unit(u)
        return y

    def _run(self, lab, traj, recs):
        obs = lab.furnace_run(traj, recs, "ovat")
        self._record(obs)
        return obs

    def _maybe_remeasure(self, lab):
        if self.careful and lab.n_runs % self.every == self.every - 1:
            sp = self.space
            self._run(lab, sp.trajectory(self.cur), [sp.recipe(self.cur)] * lab.slots)
            self.est = self._cur_est()[0]
            return True
        return False

    def _plan(self, lab):
        sp = self.space
        obs = self._run(lab, sp.trajectory(self.cur), [sp.recipe(self.cur)] * lab.slots)
        self.est, _ = _mean_valid(obs)
        yield
        step = self.step0
        while True:
            for name in self.ORDER:
                if self._maybe_remeasure(lab):
                    yield
                p = sp[name]
                if isinstance(p, Cat):
                    others = [c for c in p.choices if c != self.cur[name]]
                    recs = []
                    for c in others:
                        r = sp.recipe(self.cur)
                        r[name] = c
                        recs += [r, dict(r)]
                    obs = self._run(lab, sp.trajectory(self.cur), recs[:lab.slots])
                    yield
                    scored = []
                    for c in others:
                        m, n = _mean_valid([o for o in obs if o.x[name] == c])
                        scored.append((m, n, c))
                    m, n, c = max(scored)
                    y = dict(self.cur)
                    y[name] = c
                    if self._better(y, m, n):
                        self._accept(y, m)
                    continue
                if p.level == "sample":
                    cands = [y for y in (self._shift(self.cur, name, -step),
                                         self._shift(self.cur, name, +step)) if y]
                    recs = []
                    for y in cands:
                        recs += [sp.recipe(y), sp.recipe(y)]
                    obs = self._run(lab, sp.trajectory(self.cur), recs[:lab.slots])
                    yield
                    scored = []
                    for y in cands:
                        m, n = _mean_valid([o for o in obs if o.x[name] == y[name]])
                        scored.append((m, n, y))
                    m, n, y = max(scored, key=lambda t: t[0])
                    if self._better(y, m, n):
                        self._accept(y, m)
                    continue
                # run-level: one replicated run per level, then one more step if it moved
                moved_dir = 0
                for d in (-1, +1):
                    y = self._shift(self.cur, name, d * step)
                    if y is None:
                        continue
                    obs = self._run(lab, sp.trajectory(y), [sp.recipe(y)] * lab.slots)
                    yield
                    m, n = _mean_valid(obs)
                    if self._better(y, m, n):
                        self._accept(y, m)
                        moved_dir = d
                        break
                if moved_dir:
                    y = self._shift(self.cur, name, moved_dir * step)
                    if y is not None:
                        obs = self._run(lab, sp.trajectory(y), [sp.recipe(y)] * lab.slots)
                        yield
                        m, n = _mean_valid(obs)
                        if self._better(y, m, n):
                            self._accept(y, m)
            step *= self.shrink

    def step(self, lab):
        if self._gen is None:
            self._gen = self._plan(lab)
        next(self._gen)

    def recommend(self, lab):
        return dict(self.cur), (self._cur_est()[0] if self.careful else self.est)


# --------------------------------------------------------------------------- GP-BO
class GPBO:
    """Batch Bayesian optimization for a shared-trajectory furnace.

    noise_aware=True  (the loop as the v2 map specifies it)
        learned noise term; first run replicates the literature recipe; every
        ``confirm_every``-th run re-runs the incumbent trajectory with two
        replicate slots; recommendation = best lower confidence bound among
        observed recipes.
    noise_aware=False (ablation)
        noise fixed near zero; recommendation = best single observation.

    Failed films are not imputed into the regression model (that created false
    cliffs and drove length scales to their bounds in early tests). A separate
    GP classifier estimates the probability that a film survives, and the
    acquisition is expected improvement times that probability.

    trust_region=True is a TuRBO-style ablation. On this surface it shrank too
    early and underperformed global expected improvement, so it is off by default.
    """

    def __init__(self, start: dict, rng, space=P0_SPACE, noise_aware: bool = True,
                 n_init: int = 6, confirm_every: int = 5, n_cand: int = 1000,
                 n_local: int = 300, kappa_rec: float = 1.0, trust_region: bool = False,
                 tr_init: float = 0.4, tr_min: float = 0.05, tr_max: float = 0.8):
        self.space, self.start, self.rng = space, dict(start), rng
        self.aware, self.n_init, self.every, self.n_cand = noise_aware, n_init, confirm_every, n_cand
        self.n_local, self.kappa_rec = n_local, kappa_rec
        self.tr, self.L, self.tr_min, self.tr_max = trust_region, tr_init, tr_min, tr_max
        self._succ = self._fail = 0
        self._last_best = None
        self.name = ("loop" if noise_aware else "bo-naive") + ("-tr" if trust_region else "")
        self.gp = None
        self._kernel = None
        self._init_trajs = None

    # ---- data
    def _xy(self, lab):
        hist = lab.history
        X = self.space.encode_many([o.x for o in hist])
        y = np.array([o.qfls for o in hist]) * 1000.0
        ok = ~np.isnan(y)
        return X, y, ok

    def _new_gp(self, kernel=None, optimize=True, n_restarts=1):
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
        if kernel is None:
            d = self.space.dim
            white = (WhiteKernel(0.1, (1e-4, 2.0)) if self.aware
                     else WhiteKernel(1e-6, "fixed"))
            kernel = (ConstantKernel(1.0, (1e-2, 1e2))
                      * Matern(np.full(d, 0.5), (0.03, 30.0), nu=2.5) + white)
        return GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                        optimizer="fmin_l_bfgs_b" if optimize else None,
                                        n_restarts_optimizer=n_restarts if optimize else 0,
                                        random_state=int(self.rng.integers(1 << 30)))

    def _fit(self, lab, optimize: bool = True):
        """Regression GP on successful films; failure model fitted separately."""
        Xall, yall, ok = self._xy(lab)
        X, y = Xall[ok], yall[ok]
        optimize = optimize or self._kernel is None
        gp = self._new_gp(self._kernel, optimize=optimize, n_restarts=1 if len(y) < 60 else 0)
        gp.fit(X, y)
        self._kernel = gp.kernel_
        self.gp, self._X, self._y = gp, X, y
        self._ok = np.ones(len(y), bool)
        self._n_hist = len(yall)
        self.clf = None
        if optimize and (~ok).sum() >= 3 and ok.sum() >= 3:
            from sklearn.gaussian_process import GaussianProcessClassifier
            from sklearn.gaussian_process.kernels import ConstantKernel, RBF
            clf = GaussianProcessClassifier(ConstantKernel(1.0, (1e-2, 1e2))
                                            * RBF(np.full(self.space.dim, 0.5), (0.05, 30.0)),
                                            random_state=0)
            clf.fit(Xall, ok.astype(int))
            self.clf = clf
        elif not optimize:
            self.clf = getattr(self, "_clf_prev", None)
        self._clf_prev = self.clf
        return gp

    def _p_ok(self, X):
        if self.clf is None:
            return np.ones(len(X))
        return self.clf.predict_proba(X)[:, 1]

    def _latent(self, gp, X):
        mu, sd = gp.predict(X, return_std=True)
        noise = gp.kernel_.k2.noise_level * float(np.atleast_1d(gp._y_train_std)[0]) ** 2
        var = np.maximum(sd ** 2 - noise, 1e-10)
        return mu, np.sqrt(var)

    def _incumbent(self):
        if self.aware:
            mu, _ = self._latent(self.gp, self._X[self._ok])
            return float(mu.max())
        return float(self._y[self._ok].max())

    def _ei(self, gp, X, best):
        """Expected improvement times probability that the film survives."""
        mu, sd = self._latent(gp, X)
        imp = mu - best
        z = imp / sd
        return (imp * norm.cdf(z) + sd * norm.pdf(z)) * self._p_ok(X)

    # ---- candidates
    def _tr_candidates(self, center: dict, n: int):
        sp, rng = self.space, self.rng
        reals = [p for p in sp.params if not isinstance(p, Cat)]
        p_pert = min(1.0, 4.0 / len(reals))
        xs = []
        for _ in range(n):
            x = dict(center)
            mask = rng.random(len(reals)) < p_pert
            if not mask.any():
                mask[rng.integers(len(reals))] = True
            for p, m in zip(reals, mask):
                if m:
                    x[p.name] = p.from_unit(p.to_unit(center[p.name]) + self.L * (rng.random() - 0.5))
            for p in sp.params:
                if isinstance(p, Cat) and rng.random() < 0.1:
                    x[p.name] = p.choices[rng.integers(len(p.choices))]
            xs.append(x)
        return xs

    def _update_tr(self, lab):
        """Expand after repeated success, shrink after repeated failure (TuRBO-style)."""
        best = self._incumbent()
        if self._last_best is not None:
            if best > self._last_best + 1.0:          # 1 mV improvement of the incumbent
                self._succ, self._fail = self._succ + 1, 0
            else:
                self._succ, self._fail = 0, self._fail + 1
            if self._succ >= 2:
                self.L, self._succ = min(self.tr_max, self.L * 2.0), 0
            if self._fail >= 3:
                self.L, self._fail = max(self.tr_min, self.L / 2.0), 0
        self._last_best = best

    def _candidates(self, lab):
        sp, rng = self.space, self.rng
        if self.tr:
            rec, _ = self.recommend(lab)
            return self._tr_candidates(rec, 3000) + sp.sample(rng, 200)
        xs = sp.sample(rng, self.n_cand)
        hist = [o for o in lab.history if not o.failed]
        if hist and self.gp is not None:
            mu, _ = self._latent(self.gp, sp.encode_many([o.x for o in hist]))
            for i in np.argsort(mu)[-3:]:
                for sc in (0.03, 0.08, 0.2):
                    xs += [sp.perturb(hist[i].x, rng, sc) for _ in range(self.n_local)]
        return xs

    def _fill_slots(self, lab, traj, first: list[dict], n_slots: int, best: float):
        """Kriging-believer completion of a run whose trajectory is fixed."""
        sp, rng = self.space, self.rng
        chosen = list(first)
        X, y = self._X.copy(), self._y.copy()
        for x in chosen:
            X = np.vstack([X, sp.encode(x)])
            y = np.append(y, self.gp.predict(sp.encode(x)[None])[0])
        while len(chosen) < n_slots:
            gp = self._new_gp(self._kernel, optimize=False)
            gp.fit(X, y)
            cands = sp.sample(rng, 300, level="sample", base=traj)
            for x in chosen:
                cands += [sp.perturb(x, rng, 0.1, level="sample") for _ in range(100)]
            ei = self._ei(gp, sp.encode_many(cands), best)
            x = cands[int(np.argmax(ei))]
            chosen.append(x)
            X = np.vstack([X, sp.encode(x)])
            y = np.append(y, gp.predict(sp.encode(x)[None])[0])
        return [sp.recipe(x) for x in chosen]

    # ---- protocol
    def step(self, lab):
        sp, rng, r = self.space, self.rng, lab.n_runs
        if r == 0:
            if self.aware:
                recs = [sp.recipe(self.start)] * lab.slots
            else:
                recs = [sp.recipe(self.start)] + [sp.recipe(x) for x in
                                                 sp.sample(rng, lab.slots - 1, level="sample", base=self.start)]
            lab.furnace_run(sp.trajectory(self.start), recs, "init")
            return
        if r < self.n_init:
            if self._init_trajs is None:
                self._init_trajs = sp.lhs_runs(rng, self.n_init - 1)
                if self.tr:   # prior knowledge: start the design around the literature recipe
                    c = sp.trajectory(self.start)
                    for t in self._init_trajs:
                        for k in t:
                            p = sp[k]
                            u = p.to_unit(c[k]) + self.L * (p.to_unit(t[k]) - 0.5)
                            t[k] = p.from_unit(u)
            traj = self._init_trajs[r - 1]
            recs = [sp.recipe(x) for x in sp.sample(rng, lab.slots, level="sample", base=traj)]
            lab.furnace_run(traj, recs, "init")
            return
        self._fit(lab)
        best = self._incumbent()
        if self.tr:
            self._update_tr(lab)
        confirm = self.aware and (r - self.n_init) % self.every == self.every - 1
        if confirm:
            rec, _ = self.recommend(lab)
            traj = sp.trajectory(rec)
            recs = self._fill_slots(lab, traj, [rec, dict(rec)], lab.slots, best)
            lab.furnace_run(traj, recs, "confirm")
            return
        cands = self._candidates(lab)
        ei = self._ei(self.gp, sp.encode_many(cands), best)
        x1 = cands[int(np.argmax(ei))]
        traj = sp.trajectory(x1)
        recs = self._fill_slots(lab, traj, [x1], lab.slots, best)
        lab.furnace_run(traj, recs, "bo")

    def recommend(self, lab):
        hist = [o for o in lab.history if not o.failed]
        if not hist:
            return dict(self.start), math.nan
        if self.aware and lab.n_runs >= self.n_init:
            if self.gp is None or self._n_hist != len(lab.history):
                self._fit(lab, optimize=False)
            mu, sd = self._latent(self.gp, self.space.encode_many([o.x for o in hist]))
            i = int(np.argmax(mu - self.kappa_rec * sd))     # conservative: lower confidence bound
            return dict(hist[i].x), float(mu[i]) / 1000.0
        if self.aware:
            # before the model exists: the replicated literature recipe
            m, _ = _mean_valid([o for o in hist if o.run == 0])
            return dict(self.start), m
        i = int(np.argmax([o.qfls for o in hist]))
        return dict(hist[i].x), hist[i].qfls


# --------------------------------------------------------------------------- A8
class DeviceAwareGPBO(GPBO):
    """The loop with anchor devices in the objective (next-stage plan item A8).

    Two models instead of one:

    * the QFLS GP of the parent class, fed by every surviving film;
    * a gap GP for (film QFLS - device Voc), fed only by the films that were
      finished into anchor devices.

    Acquisition, incumbent and recommendation all use predicted device Voc,
    mu_q - mu_gap, with the two variances added. Before any anchors exist the
    gap is a constant prior, so the loop behaves like the QFLS loop shifted by
    that constant.

    Anchors cost no furnace runs: every ``anchor_every`` runs after the initial
    design, ``anchors_per_cycle`` existing films are finished into devices. The
    first cycle includes a literature-recipe film (the device baseline); each
    cycle includes the incumbent's film if one is available; the rest go to the
    promising films whose gap the model is least sure of.
    """

    def __init__(self, start: dict, rng, anchor_every: int = 5, anchors_per_cycle: int = 2,
                 gap_prior_mev: float = 25.0, gap_prior_sd_mev: float = 15.0, **kw):
        kw.setdefault("noise_aware", True)
        super().__init__(start, rng, **kw)
        self.name = "loop-dev"
        self.anchor_every, self.per_cycle = anchor_every, anchors_per_cycle
        self.g0, self.g0_sd = gap_prior_mev, gap_prior_sd_mev
        self.gap_gp, self._gap_kernel, self._n_gap = None, None, 0

    # ---- models
    def _fit(self, lab, optimize: bool = True):
        gp = super()._fit(lab, optimize)
        anchored = [o for o in lab.history if not o.failed and not math.isnan(o.device)]
        if len(anchored) >= 3 and (len(anchored) != self._n_gap or self.gap_gp is None):
            from sklearn.gaussian_process import GaussianProcessRegressor
            from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
            Xg = self.space.encode_many([o.x for o in anchored])
            yg = np.array([o.qfls - o.device for o in anchored]) * 1000.0
            kernel = self._gap_kernel or (ConstantKernel(1.0, (1e-2, 1e2))
                                          * Matern(np.full(self.space.dim, 1.0), (0.5, 30.0), nu=2.5)
                                          + WhiteKernel(0.1, (1e-3, 2.0)))
            g = GaussianProcessRegressor(kernel=kernel, normalize_y=True, n_restarts_optimizer=1,
                                         random_state=int(self.rng.integers(1 << 30)))
            g.fit(Xg, yg)
            self.gap_gp, self._gap_kernel, self._n_gap = g, g.kernel_, len(anchored)
        return gp

    def _gap(self, X):
        if self.gap_gp is None:
            return np.full(len(X), self.g0), np.full(len(X), self.g0_sd)
        return self._latent(self.gap_gp, X)

    def _dev(self, gp, X):
        mq, sq = self._latent(gp, X)
        mg, sg = self._gap(X)
        return mq - mg, np.sqrt(sq ** 2 + sg ** 2)

    # ---- device-based acquisition
    def _incumbent(self):
        mu, _ = self._dev(self.gp, self._X)
        return float(mu.max())

    def _ei(self, gp, X, best):
        mu, sd = self._dev(gp, X)
        imp = mu - best
        z = imp / sd
        return (imp * norm.cdf(z) + sd * norm.pdf(z)) * self._p_ok(X)

    def _candidates(self, lab):
        sp, rng = self.space, self.rng
        xs = sp.sample(rng, self.n_cand)
        hist = [o for o in lab.history if not o.failed]
        if hist and self.gp is not None:
            mu, _ = self._dev(self.gp, sp.encode_many([o.x for o in hist]))
            for i in np.argsort(mu)[-3:]:
                for sc in (0.03, 0.08, 0.2):
                    xs += [sp.perturb(hist[i].x, rng, sc) for _ in range(self.n_local)]
        return xs

    def recommend(self, lab):
        hist = [o for o in lab.history if not o.failed]
        if not hist:
            return dict(self.start), math.nan
        if lab.n_runs >= self.n_init:
            if self.gp is None or self._n_hist != len(lab.history):
                self._fit(lab, optimize=False)
            mu, sd = self._dev(self.gp, self.space.encode_many([o.x for o in hist]))
            i = int(np.argmax(mu - self.kappa_rec * sd))
            return dict(hist[i].x), float(mu[i]) / 1000.0
        m, _ = _mean_valid([o for o in hist if o.run == 0])
        return dict(self.start), m - self.g0 / 1000.0

    # ---- anchors
    def _anchor(self, lab):
        films = [o for o in lab.history if not o.failed and math.isnan(o.device)]
        if not films:
            return
        self._fit(lab, optimize=False)
        chosen = []
        if lab.n_devices == 0:
            lit = [o for o in films if o.run == 0]
            if lit:
                chosen.append(lit[0])
        rec, _ = self.recommend(lab)
        same = [o for o in films if o.x == rec and o not in chosen]
        if same and len(chosen) < self.per_cycle:
            chosen.append(same[-1])
        X = self.space.encode_many([o.x for o in films])
        mu_d, _ = self._dev(self.gp, X)
        _, sd_g = self._gap(X)
        promising = mu_d >= np.quantile(mu_d, 0.7)
        for i in np.argsort(-(sd_g + 1e-6 * mu_d) * promising):
            if len(chosen) >= self.per_cycle:
                break
            if promising[i] and films[i] not in chosen:
                chosen.append(films[i])
        for o in chosen:
            lab.make_device(o)
        self._fit(lab, optimize=False)

    def step(self, lab):
        super().step(lab)
        r = lab.n_runs
        if r >= self.n_init and (r - self.n_init) % self.anchor_every == 0:
            self._anchor(lab)
