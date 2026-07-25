# OMI v1.3 — Implementation Specification

**Companion to OMI v1.3 Core. Normative.**

**Pass A skeleton, July 2026**

> **Status.** This document holds everything executable: procedures, estimators, thresholds, numbers, and reporting requirements. The Core document holds everything falsifiable. Every Core claim with a procedure points here; Appendix D of Core is the index.
>
> **Section order follows the Core pointer index, not pedagogical order.** A specification is indexed, not read linearly. For a first reading, §9 (conformance) states what an implementation must deliver; §12 (architecture) states what it must be built from; the rest are the procedures those two require.
>
> **Requirement language.** **MUST** — required for conformance at the stated level. **SHOULD** — expected unless justified in the implementation report. **MAY** — permitted.
>
> Sections marked **[Pass B]** require derivation and demonstration; **[Pass C]** require synthesis and numbers. Neither is present in this skeleton.

---

## 1. State selection in practice

*Serves Core §2.2. **Depends on §3** — the variance term is the observability spectrum propagated to the readout, so §3 must be read first.*

### 1.1 The three terms

For a candidate state description \(\mathcal{S}\) and declared target \(\rho\),

\[
\mathbb{E}\big[\|\hat\rho - \rho\|^2\big] \;=\; \underbrace{\mathrm{Bias}^2(\mathcal{S})}_{\S 1.2} \;+\; \underbrace{\mathrm{Var}_{\text{est}}(\mathcal{S})}_{\S 1.3} \;+\; \underbrace{\mathrm{Err}_{\text{learn}}(\mathcal{S})}_{\S 1.4} \;+\; \text{irreducible}.
\]

Each term has an estimator already defined elsewhere in this specification. The content of §1 is their assembly and the stopping rule.

### 1.2 Bias: the sufficiency deficit

From matched-history pairs (§8): specimens \(A, B\) matched on the candidate description, driven by different histories, then subjected to identical subsequent driving \(u\).

The naive statistic \(\mathbb{E}[(\rho_A - \rho_B)^2]\) confounds three things: genuine insufficiency, measurement and aleatoric noise, and **imperfect matching**. Matching is performed on measurable proxies, never on \(s\) itself, so residual mismatch in the matched components inflates the statistic. Correct by decomposition:

\[
\boxed{\;\delta^2(\mathcal{S}) \;=\; \mathbb{E}\big[(\rho_A-\rho_B)^2\big] \;-\; 2\sigma^2_{\text{rep}} \;-\; \sum_j \Big(\tfrac{\partial \rho}{\partial s_j}\Big)^{\!2}\, \mathbb{E}\big[(s_{A,j}-s_{B,j})^2\big]\;}
\]

clamped at zero, where \(\sigma^2_{\text{rep}}\) is the within-condition repeat variance (matched history, matched driving) and the sum runs over components on which matching was attempted. The factor 2 arises because the difference of two independent draws has twice the variance of one.

> **Requirement.** An implementation reporting a sufficiency deficit MUST report all three terms separately. A raw response gap is not a sufficiency deficit, and reporting it as one systematically over-states insufficiency.

Under the null of sufficiency, \(\hat\delta^2\) is a scaled \(\chi^2\) with degrees of freedom set by pair count; §8 gives the power calculation.

**Chain-level bias.** \(\delta\) is a per-segment quantity. Over a chain it accumulates with the same amplification structure as learning error (§2.6):

\[
\mathrm{Bias}(\mathcal{S}) \;\le\; \sum_k \delta_k(\mathcal{S}) \prod_{j>k} L_j ,
\]

so segment-level deficits upstream of an erasure are suppressed by that erasure's contraction. **A large deficit in a segment followed by a complete erasure is not a reason to enlarge the state.** This is the single most common source of wasted state augmentation.

### 1.3 Variance: the danger scores of §3

\[
\mathrm{Var}_{\text{est}}(\mathcal{S}) \;=\; \operatorname{tr}\big(W S_k P_k S_k^{*}\big) \;=\; \sum_i \mathcal{D}_i ,
\]

exactly the sum of danger scores from §3.3. Enlarging \(\mathcal{S}\) adds directions; each added direction contributes \(\mathcal{D}_i\), which is small only if the component is either well observed or without influence. **A component that is influential and unobservable makes the model worse, not better** — it converts model bias into estimation variance without reducing terminal error.

This is the precise sense in which Axiom S has a price, and it is why §3 is a prerequisite rather than a companion.

### 1.4 Learning error

Not predictable a priori; measured. Train candidate models on each \(\mathcal{S}\) at **matched data budget** and read \(\mathrm{Err}_{\text{learn}}\) from the rollout-length curve (§9.2) at the chain length of interest.

The relevant cost driver is *effective* dimension, not nominal. A component that is a smooth function of existing components adds little (intrinsic dimension unchanged); a genuinely new degree of freedom adds substantially. Estimate effective dimension by the latent width required to reconstruct the augmented state to fixed fidelity, and report it alongside nominal dimension.

### 1.5 The augmentation loop

```
Input:  declared target set P, tolerance τ (from §7.3), candidate pool Z
Init:   S ← minimal state (resolved fields only)

repeat
  1. Run sufficiency test on S              → δ(S), divergence fingerprint   [§8]
  2. If Bias(S) ≤ τ_bias: STOP — sufficient at tolerance
  3. Read candidate z* from the divergence fingerprint                       [§1.6]
  4. Compute ΔVar_est from the Gramian for S ∪ {z*}                          [§3]
  5. Compute ΔErr_learn at matched data budget                               [§1.4]
  6. Accept z* iff  Δ(Bias²) > ΔVar_est + ΔErr_learn
  7. If no candidate in Z passes: interior optimum reached → §1.7
until accepted set is empty
```

### 1.6 Reading the missing variable from the divergence fingerprint

Step 3 is the step that makes the loop constructive rather than a search. The *pattern* of divergence across a probe set of subsequent drivings fingerprints the missing component:

| Divergence appears under | Implicated component |
|---|---|
| reversed or non-proportional driving only | directional / kinematic variable |
| thermal driving only, with Arrhenius scaling | thermally activated population, sub-resolution |
| scaling with subsequent accumulated driving | damage or nucleation-site population |
| only near an interface or free surface | \(\Gamma\), not a bulk variable |
| only at long times or under load reversal after hold | unresolved clustering or relaxation state |
| under changed boundary constraint at equal local driving | \(\nu\), the nonlocal slot |

> **Design requirement on §8.** The probe set of subsequent drivings MUST be chosen to *discriminate* between candidate components, not merely to detect divergence. A campaign that establishes insufficiency without identifying its direction has spent its budget for a fraction of its value.

### 1.7 Interior optimum with residual deficit: a diagnostic trichotomy

Step 7 is not a single outcome. Identify which term blocks:

| Blocking term | Meaning | Action |
|---|---|---|
| \(\mathrm{Var}_{\text{est}}\) | the needed component exists but cannot be identified | **buy sensing** — §3.4 gives the placement and the expected return |
| \(\mathrm{Err}_{\text{learn}}\) | the state is right, the operator is undertrained | **buy data or simulation** — §2.6 gives the allocation |
| \(\mathrm{Bias}\), no candidate in \(Z\) | no bounded augmentation removes the deficit | **falsification event** — Core §6.1, criterion 1 |

Only the third is a refutation. Conflating the three is how a framework acquires an undeserved reputation for failure, and an implementation MUST report which term blocks before declaring any of them.

### 1.8 Requirements

- Target readout set MUST be declared before selection begins; selection MUST be re-run if it changes.
- The three terms MUST be reported separately at each accepted augmentation, so the trajectory of the loop is auditable.
- Deficits suppressed by a downstream erasure MUST NOT be used to justify augmentation (§1.2).
- **[Pass D]** Worked demonstration exhibiting an interior optimum. `[REQUIRES: one chain with matched-history pair data and an instrumented sensor suite]`

---

## 2. Operator learning: architecture, constraints, stability

*Serves Core §3.9. Carries v1.2 §§4.1–4.3 and extends them.*

### 2.1 Approximation class and its caveats

Neural operators supply the approximation class: DeepONet branch–trunk decompositions for general function-to-function maps; Fourier and multi-resolution neural operators for field-to-field maps on grids; graph-based operators for unstructured structures. Known approximation results MUST be cited with their caveats — universality holds, but bounds on network size are not immune to the curse of dimensionality, and reported empirical rates typically reflect low intrinsic dimension of the data rather than genuine dimension-independence.

There is **no general result on composition**. Composition stability is an empirical property, measured per chain by the protocols below, and an implementation MUST NOT claim it as inherited from single-operator approximation theory.

### 2.2 Hard structural constraints

**Hard constraints beat soft penalties, and this matters most for inverse design.** A penalty enforces physics *where the training data live*; an optimiser searching for an optimal route will find precisely the regions where enforcement is weak. Structural constraints that cannot be violated by construction are therefore worth substantial architectural inconvenience.

- **Symmetry.** Equivariant architectures respecting the relevant point group; frame-indifference for constitutive operators; permutation invariance over discrete populations.
- **Thermodynamic admissibility.** GENERIC or port-Hamiltonian structure separating reversible and irreversible parts, guaranteeing non-negative dissipation by construction rather than by penalty.
- **Range constraints.** Simplex parameterisation for fractions; positivity for densities and damage; bounded distributions.
- **Monotonicity.** Damage, accumulated driving measures, and consumed driving force are monotone in time — enforce by monotone parameterisation or non-negative increments.
- **Conservation.** Mass balance across transformation and partitioning steps.

Constraints declared under interface item 6 (Core §4) MUST appear here as architecture, not as loss terms.

### 2.3 Training objectives

Combine: data fidelity on measurements and high-fidelity simulation trajectories; PDE and constitutive residuals at collocation points; statistical descriptor matching; **semigroup consistency** (§9.2); **closure-defect penalties** (§6); manifold and reachability regularisation (§7.0); and calibration terms (§9.5).

Weight these with care. Physics-residual weights are among the most consequential and least reported hyperparameters in this literature; they MUST be selected by validation performance and MUST be reported.

### 2.4 Stability-aware training

Training MUST target rollout accuracy, not one-step accuracy.

- **Multi-step / pushforward training** with truncated backpropagation through the rollout.
- **Noise injection** on inputs, so the operator learns to contract its own error distribution rather than only the data manifold.
- **Spectral normalisation or explicit Lipschitz control, tuned per segment.** Contraction is appropriate near erasures; over-constraining prevents representation of genuine instabilities. See §2.5 — this is where the physical/numerical distinction becomes operational.
- **Manifold projection at each step** (§7.0), which removes off-manifold error components. This is the strongest practical justification for manifold learning and SHOULD be claimed as such rather than on sample-efficiency grounds alone.
- **Error as a function of rollout length MUST be reported**, always.

### 2.5 Amplification decomposition and the three regimes **[Pass B]**

> **Requirement.** Report \(L_{\text{total}} = L_{\text{phys}} \times L_{\text{num}}\), not a single Lipschitz constant, and report the **local spectrum** across the state space rather than a global bound.

\(L_{\text{phys}}\) is estimated from the high-fidelity solver or from repeat experiments; \(L_{\text{num}}\) is the excess. Conflating them causes real physics to be spectrally normalised away.

| Regime | Character | Treatment |
|---|---|---|
| Contractive, \(L \ll 1\) | post-erasure, relaxation | cheap surrogates suffice; errors decay |
| Neutral, \(L \approx 1\) | controlled transformation | linear accumulation; multi-step training, noise injection |
| Expansive, \(L > 1\) | localisation, coalescence, abnormal growth | §2.7 |

To be written: estimation procedure for the local spectrum by finite differences in \(d_\mathcal{S}\); its cost; the sample size required for a stable estimate.

### 2.6 Backward error budgeting **[Pass B]**

Given a terminal tolerance \(\tau\) on a target readout, allocate per-operator one-step budgets \(\varepsilon_k\) backwards through the chain using estimated \(L_k\) and erasure contraction factors. This is an engineering artifact with immediate use: **it tells you where to spend data and simulation budget.**

Allocation MUST be weighted by decision sensitivity (§7.3), not uniformly. Accuracy is needed near the specification boundary and nowhere else.

To be written: the backward recursion; treatment of assimilation updates as budget credits; a worked allocation.

### 2.7 The refusal criterion **[Pass B]**

Where amplification is physical rather than numerical, a better surrogate is not the answer. The specification MUST provide, and an implementation MUST select among:

1. **Predict the invariant or bifurcation label** rather than the trajectory.
2. **Predict the distribution over outcomes** — sensitivity is physical, not numerical failure.
3. **Event-triggered handoff** to a high-fidelity solver, with the trigger condition specified.

To be written: the trigger condition; how handoff preserves the ensemble; how refusal is reported without being mistaken for model failure.

---

## 3. Observability and sensor design

*Serves Core §3.8. Prerequisite for §1.*

### 3.1 Construction

Fix a nominal trajectory \(\{\bar s_k\}\) generated by nominal controls \(\{\bar u_k\}\). Define the tangent maps

\[
F_k = D_s\,\mathcal{G}^{(k)}_{\text{evol}}(\bar s_k, \bar u_k), \qquad
H'_j = D_s H_j(\bar s_j),
\]

and the state-transition operator \(\Phi_{j,k} = F_{j-1}F_{j-2}\cdots F_k\), with \(\Phi_{k,k} = I\). Observations are \(y_j = H_j(s_j) + \eta_j\), \(\eta_j \sim \mathcal{N}(0, R_j)\).

A perturbation \(\delta s_k\) produces observation perturbations \(\delta y_j = H'_j \Phi_{j,k}\, \delta s_k\) at all downstream indices. The Fisher information about \(s_k\) carried by the sensor suite is therefore the **observability Gramian**

\[
\boxed{\;\mathbf{G}_k \;=\; \sum_{j \ge k} \Phi_{j,k}^{*}\, H_j'^{*}\, R_j^{-1}\, H'_j\, \Phi_{j,k}\;}
\]

With prior covariance \(P_k^0\), the posterior covariance is \(P_k = \big((P_k^0)^{-1} + \mathbf{G}_k\big)^{-1}\). Eigendirections of \(\mathbf{G}_k\) with large eigenvalue are well determined; directions in \(\ker \mathbf{G}_k\) retain their prior variance and are unidentifiable from data.

The sum runs over \(j \ge k\) only. Upstream observations constrain \(s_k\) solely through the forward dynamics, which is a prior contribution, not an information contribution — this is the filtering/smoothing distinction, and \(\mathbf{G}_k\) is the smoothing object. Retrospective inference (Core §3.8) is therefore the correct setting for latent-variable identifiability.

**Proposition 3.1 (deterministic Gramian is an upper bound).** *Under process noise \(Q_k \succ 0\), achievable information about \(s_k\) is strictly less than \(\mathbf{G}_k\): model error degrades a perturbation before it reaches a downstream sensor. Consequently a direction unidentifiable under \(\mathbf{G}_k\) is unconditionally unidentifiable.*

This is what makes the deterministic construction useful for design: it is optimistic, so its negative findings are sound. An implementation MAY use \(\mathbf{G}_k\) for triage but MUST NOT quote its eigenvalues as achieved posterior precision.

### 3.2 Erasure operators block observability — and remove the need for it

The Jacobian of an erasure operator \(\mathcal{E}\) is severely rank-deficient; that is what "image of substantially lower effective dimension" means. Write \(r = \operatorname{rank} F_\mathcal{E}\).

**Proposition 3.2 (erasure truncates the Gramian).** *If an erasure with Jacobian rank \(r\) lies between \(k\) and \(j\), then \(\operatorname{rank}\big(H'_j \Phi_{j,k}\big) \le r\). Hence*
\[
\mathbf{G}_k = \mathbf{G}_k^{\text{intra}} + \mathbf{G}_k^{\text{post}}, \qquad \operatorname{rank} \mathbf{G}_k^{\text{post}} \le r,
\]
*where \(\mathbf{G}_k^{\text{intra}}\) collects sensors before the erasure and \(\mathbf{G}_k^{\text{post}}\) those after it.*

**Corollary 3.3 (erasure kernels are marginalisable by construction).** *Directions in \(\ker F_\mathcal{E}\) are unidentifiable from post-erasure data* and *have no influence on any post-erasure readout. They cannot be dangerous.*

Corollary 3.3 is the formal content of the informal claim in Core §3.8 that an erasure "destroys upstream observability and simultaneously removes the need for it." Danger arises only from directions that **survive** the erasure yet are weakly observed — the row space of \(F_\mathcal{E}\) intersected with the near-kernel of \(\mathbf{G}_k\). Analysis is therefore performed per segment, and the surviving subspace is the only thing that must be carried across a segment boundary.

### 3.3 The decision-weighted spectrum

The raw spectrum of \(\mathbf{G}_k\) is metric-dependent, and a state with heterogeneous units admits no natural metric. Weight instead by influence on the declared targets.

For target readouts \(\rho^{(1)},\dots,\rho^{(M)}\) with importance weights \(W\), define the **sensitivity operator**

\[
S_k = \big[\,D\rho^{(1)}\Phi_{N,k}\;;\;\cdots\;;\;D\rho^{(M)}\Phi_{N,k}\,\big].
\]

Target-variance contributed by state uncertainty at index \(k\) is \(\operatorname{Var}(\rho) \approx S_k P_k S_k^{*}\). Decomposing along eigendirections \(v_i\) of \(P_k\) gives the **danger score**

\[
\boxed{\;\mathcal{D}_i \;=\; \big(v_i^{*} S_k^{*} W S_k v_i\big) \times \big(v_i^{*} P_k v_i\big)\;}
\qquad\text{(influence} \times \text{residual uncertainty)}
\]

with \(\sum_i \mathcal{D}_i = \operatorname{tr}(W S_k P_k S_k^{*})\), the total target variance attributable to index \(k\). The triage is the 2×2 on the two factors:

| | **Identifiable** (small \(v^*Pv\)) | **Unidentifiable** (large \(v^*Pv\)) |
|---|---|---|
| **Influential** (large \(S v\)) | **Observed** or **Inferred** | **DANGEROUS** |
| **Non-influential** (small \(S v\)) | Observed but irrelevant | **Marginalisable** |

*Observed* and *inferred* are distinguished by which terms of the Gramian sum supply the information: a direction is **observed** if a single near-diagonal term \(j \approx k\) dominates, and **inferred** if information accrues only through \(\sum_{j > k}\) — the case in which the chain model, not the instrument, is doing the work. Inferred components are the framework's distinctive contribution and SHOULD be reported separately, since they are exactly what a tabular baseline cannot recover.

**Requirements.**
- The **dangerous set MUST be reported**, ranked by \(\mathcal{D}_i\). It is the sensing investment case.
- Marginalisation MUST be justified by demonstrated \(S_k v_i \approx 0\) at stated tolerance, never by convenience or by unavailability of data.
- \(\mathcal{D}_i\) is defined relative to a **declared** target set; if targets change, triage MUST be re-run.

### 3.4 Value of information and sensor placement

For a candidate modality with linearised operator \(H'_c\) and noise \(R_c\) at index \(c\), the augmented Gramian is

\[
\mathbf{G}_k' = \mathbf{G}_k + \Phi_{c,k}^{*} H_c'^{*} R_c^{-1} H'_c \Phi_{c,k},
\]

and the expected reduction in target variance is \(\Delta V_c = \operatorname{tr}\big(W S_k (P_k - P_k') S_k^{*}\big)\), computable by Woodbury without re-inversion when \(H'_c\) is low-rank — which it is, for essentially every real instrument.

Placement is then the maximisation of \(\Delta V_c / \text{cost}_c\) over candidate (modality, index) pairs. Note this is A-optimality **on the readout**, not on the state; the two differ, and optimising state precision buys instruments that resolve directions nobody needs.

### 3.5 Computation

Never form \(\Phi_{j,k}\). All quantities reduce to matrix–vector products available by autodiff through the learned graph: \(\Phi_{j,k}v\) is a forward JVP, \(\Phi_{j,k}^{*}w\) a reverse VJP. The Gramian action \(\mathbf{G}_k v\) costs one JVP and one VJP per instrumented index. Randomised or Lanczos eigensolvers recover the leading \(r\) directions in \(O(r)\) Gramian actions, so the total cost is \(O(r \times \text{instrumented indices})\) autodiff passes — tractable for the chain lengths of interest.

### 3.6 Trajectory dependence — a required caveat

The construction is a linearisation, so observability is a property of an operating point, not of a chain. A system may be observable at nominal settings and lose identifiability elsewhere in the window.

> **Requirement.** Compute \(\mathbf{G}_k\) and \(\mathcal{D}_i\) over an ensemble of nominal trajectories spanning the declared operating window, and report the **worst case over the window**, not the nominal case. Reporting nominal-point observability alone is non-conforming at OMI-1.

### 3.7 Modality catalogue **[Pass C]**

To be written: what each instrument class constrains, with latency, spatial coverage, and typical \(R\). Includes the structural observation that integrated response signals generated by the apparatus itself — force, torque, pressure, power draw — are Type-0 readouts of the constitutive response and therefore direct observations of \(z\). They are present in essentially every process historian, sampled continuously, and used almost exclusively for dimensional control. `[REQUIRES: instrument list, sampling rates, noise characterisation for the target chain]`

---

## 4. Class B machinery

*Serves Core §3.6. The weakest practical link in v1.2, and the section most likely to determine whether v1.3 is believed.*

### 4.1 The object to be estimated

Let \(D(x)\) be a scalar **failure driver field** over the driven volume, such that failure occurs when \(\max_{x \in V} D(x) > D_c\). The Class B readout is

\[
P\big(\rho_V \text{ fails}\big) \;=\; P\Big(\max_{x\in V} D(x) > D_c\Big),
\]

a functional of the *upper tail* of \(D\). Nothing in the bulk of the microstructure distribution determines it.

### 4.2 Driver/tail separation

The resolution is to stop asking the generative model for the tail. Choose a threshold \(u\) at a quantile where the SVE ensemble is still densely supported — typically the 90th to 95th percentile of \(D\).

- **Below \(u\):** the distribution of \(D\) is learned from SVE ensembles generated by the manifold prior. This is interpolation, and the prior is reliable here.
- **Above \(u\):** the tail is **not learned.** It is inherited from an independently measured defect population, transferred through domain physics (§4.3).

The two are joined at \(u\), with threshold-stability diagnostics (mean-residual-life plot, parameter stability across \(u\)) reported.

> **Requirement.** An implementation MUST state the join threshold, the quantile at which it sits, the number of ensemble members above it, and the sensitivity of the final risk estimate to \(u\) over at least a factor of two in exceedance probability.

### 4.3 Tail transfer: the defect-population → driver map

The measured defect population is a distribution over **descriptors** (size, aspect ratio, spacing, chemistry). The driver \(D\) is a physical field. These are different quantities, and the bridge between them is domain physics that MUST be declared:

\[
\Psi : \text{defect descriptor} \longrightarrow \text{local driver amplification}.
\]

\(\Psi\) is typically known analytically or semi-analytically — inclusion stress concentration from an Eshelby-type solution, notch-root amplification from depth and root radius, local hardenability shift from segregation severity. Critically, \(\Psi\) is in most cases a **power law or slowly varying** function of the descriptor, and that is what makes the transfer exact in the tail.

**Proposition 4.1 (tail-index transfer).** *If a defect descriptor \(a\) has a regularly varying tail \(P(a > x) \sim C x^{-\alpha}\), and the driver amplifies as \(D \sim k\,a^{\beta}\), then*
\[
P(D > d) \;\sim\; C\,(d/k)^{-\alpha/\beta},
\]
*so the driver tail index is \(\alpha/\beta\), and in generalised-Pareto shape parameters*
\[
\boxed{\;\xi_D \;=\; \beta\,\xi_a\;}
\]

The tail exponent of the driver is the **measured** tail exponent of the defect population, rescaled by the exponent of the physics map. The generative model is never asked to extrapolate; automated defect-population characterisation supplies \(\xi_a\), mechanics supplies \(\beta\), and \(\xi_D\) follows.

**Sanity check.** For defect-initiated fatigue with a threshold scaling as \((\sqrt{\text{area}})^{-1/6}\), the driver exponent in \(\sqrt{\text{area}}\) is \(\beta = 1/6\), so \(\xi_D = \xi_a/6\): a heavy-tailed inclusion population produces a markedly *lighter*-tailed strength distribution. This is the observed phenomenon that fatigue limits scatter far less than inclusion sizes do, recovered rather than assumed. Any implementation of §4 SHOULD reproduce a known scaling of this kind as a check on \(\Psi\).

> **Interface addition.** Declaration of \(\Psi\) is required per Class B readout. It belongs to interface item 4 of Core §4 and is stated there as item 4(b).

### 4.4 Volume scaling and dimensional reduction of the weakest-link count

Core §3.6 assumes independent sub-volumes. Real driver fields are spatially correlated, with correlation length \(\ell_D\) obtained from the two-point autocorrelation of the **driver field**, not of the structure generally.

Write \(N_{\text{eff}} = V / V_{\text{corr}}\). If \(\ell_D\) is small relative to every dimension of the process zone, \(V_{\text{corr}} \sim \ell_D^3\) and \(N_{\text{eff}}\) is simply a recalibration of \(V_0\) — no change in the size-effect *exponent*, only its intercept, and calibration at one specimen size extrapolates correctly.

The interesting and common case is otherwise. **Process zones are usually thin**: a sheared edge, an outer fibre under a plunger, a surface layer, a plastic zone at a notch. When \(\ell_D\) exceeds the zone thickness \(t\), independent units tile only in-plane:

\[
N_{\text{eff}} \;\sim\; \frac{A}{\ell_D^{2}} \;=\; \frac{V}{t\,\ell_D^{2}} \qquad (\ell_D > t),
\]

so the effective count scales with a **reduced power of volume**. The size effect with respect to in-plane area is preserved; the size effect with respect to thickness is suppressed.

**Proposition 4.2 (dimensional reduction).** *Where the driver correlation length exceeds a dimension of the process zone, the weakest-link count scales with the reduced-dimensional measure of that zone, and the apparent Weibull size-effect exponent in the suppressed direction tends to zero.*

This is the quantitative content of Core §3.6's claim that the two-tier formulation explains why rankings invert between specimen thicknesses: two materials with different \(\ell_D\) cross over as \(t\) sweeps through their correlation lengths. Naive independent scaling, calibrated at one thickness, over-predicts the size effect at another and mis-orders the materials.

> **Requirements.** Report \(\ell_D\) and the process-zone aspect ratio relative to it. Where \(\ell_D\) exceeds any zone dimension, the reduced scaling MUST be used and the reduction MUST be stated. Anisotropic correlation (banded structures) requires a directional \(\ell_D\) and reduction along each suppressed axis independently.

### 4.5 Rare-event sampling

Uniform SVE sampling does not reach the tail: estimating \(P_f \sim 10^{-4}\) by direct sampling needs \(O(10^6)\) realisations.

- **Subset simulation.** Intermediate thresholds \(d_1 < \cdots < d_c\) with conditional exceedance ~0.1 each; modified Metropolis sampling conditional on each level. Cost \(O(c \cdot N_s)\) — roughly \(4 \times 500\) evaluations for \(P_f \sim 10^{-4}\), three orders of magnitude cheaper.
- **Conditional generative sampling** — preferred where available. Train the manifold prior conditioned on defect descriptors; sample descriptors from the *measured* tail; generate SVEs conditionally. This is §4.2's separation implemented directly as a sampler, and it avoids MCMC entirely.

### 4.6 Validation without validating the tail

A \(10^{-4}\) quantile cannot be validated with thirty specimens. Validate the *construction* instead, in four rungs:

1. **Bulk driver distribution** — validatable at modest \(n\) against SVE ensembles and available direct measurement.
2. **Defect population tail** \(\xi_a\) — independently measured by established characterisation methodology, with its own error bars, and not by this framework.
3. **The map \(\Psi\) — by fractography.** Post-mortem examination of failed specimens gives the *initiating* defect and its descriptor. The extreme-value model predicts a distribution over initiating-defect size; comparing predicted against observed initiation sites tests \(\Psi\) directly and does so at \(n \approx 20\). **This is the cheapest and most diagnostic rung and SHOULD be run first.**
4. **Volume-scaling exponent** — at ≥3 driven volumes, chosen to straddle \(\ell_D\) where §4.4's reduction is expected.

> **Requirements.**
> - **MUST NOT** emit point predictions for Class B readouts. Distributions, with credible intervals widening explicitly in volume extrapolation.
> - **MUST report the extrapolation ratio**: the design-point driver value divided by the largest observed value in the calibration data, and the same for defect descriptor. Extrapolating three decades beyond data is permissible; concealing that one is doing so is not.
> - Where rung 3 fails — failures do not initiate where the model says they should — the entire construction is void and MUST NOT be reported as calibrated by rungs 1, 2 and 4 passing.

---

## 5. Structure and data

### 5.1 Hybrid systems: guards, type safety, and erasure interaction **[Pass C]**

*Serves Core §3.4.* Mode set and guard specification; type-safety rules across transitions; how jump maps interact with erasure analysis and segment boundaries; whether a jump map can itself be an erasure. Event catalogue by domain.

### 5.2 Body-indexed state and registration **[Pass C]**

*Serves Core §2.5.* Coupling conditions between neighbouring material points; discretisation of the body index; through-thickness and transverse resolution requirements.

**The registration operator.** An apparatus in continuous operation is observed in the apparatus frame (fixed instruments, moving material) while the state evolves in the material frame. The map

\[
\mathcal{T} : (\text{apparatus time}, \text{instrument position}) \longrightarrow \text{material coordinate}
\]

is a required preprocessing operator with its own error model, and assimilation MUST account for registration uncertainty. Mis-registration of observations to material position is among the largest practical sources of corrupted data in continuous domains, and an implementation MUST report its registration error budget.

### 5.3 Data reality and closed-loop confounding **[Pass C]**

*No Core antecedent — absent from v1.2 entirely, and arguably the most consequential practical addition.*

> **Process data is collected under closed-loop control.** The controller compensates disturbances, so observed correlations between setpoints and outcomes are not causal. A model fitted on closed-loop data and then used for open-loop inverse design will fail — and will fail *confidently*, because the training fit looked excellent.

Remedies to be specified:

- use **actuator and measured** variables, never setpoints;
- carry disturbance estimates as inputs;
- exploit deliberate excitation — planned trials, and natural experiments already in the historian (grade changes, interruptions, input-source switches);
- instrumental-variable framing where exogenous disturbances are available;
- state causal assumptions explicitly rather than leaving them implicit in a regression.

Also: sensor drift and recalibration steps; setpoint-versus-actual divergence; **missing-not-at-random** sampling (specimens taken *because* something looked wrong); unlogged interventions.

**Grouped splits MUST be enforced at the data-loader level**, so that random splits are structurally impossible rather than merely discouraged. Provenance identifiers are first-class metadata.

---

## 6. Closure-defect measurement **[Pass C]**

*Serves Core §3.7.* Measurement procedure for \(\|\mathcal{D}_\lambda\|\); choice of norm; expected magnitudes for common homogenisation schemes, with the note that bound-type schemes produce a *systematic bias* rather than a variance; the closure-defect penalty as a training term with a measured residual, replacing v1.1's assumption of exact closure.

---

## 7. Inverse design in practice

*Serves Core §5.*

### 7.0 Manifolds: realistic versus reachable

Two low-dimensional structures MUST NOT be conflated. \(\mathcal{M}_{\text{real}}\) — physically realistic states, learned by autoencoders, diffusion models, or geometry-aware operators, used for regularisation and projection. \(\mathcal{M}_{\text{reach}} \subseteq \mathcal{M}_{\text{real}}\) — states attainable by the actual apparatus, estimated by forward-sampling the evolution graph over \(\mathcal{U}_{\text{adm}}\).

### 7.1 Reachability certificates **[Pass B]**

Core §5 requires the output contract *route, or certificate of non-reachability plus nearest reachable state*. Learned reachable sets are unsound and cannot discharge it. Sound certificates are built from declared invariants:

> A **reachability certificate** is a functional \(\Phi : \mathcal{S} \to \mathbb{R}\) with a provable bound \(\Phi(s_{k+1}) \le \Phi(s_k) + c(u_k)\) for all admissible \(u\). Any target with \(\Phi\) beyond the achievable bound is provably unreachable.

Candidates are drawn from interface item 6 — conservation balances, monotone accumulations, equilibrium-limited fractions at attainable driving levels. Barrier-function style; no learning required.

Practical hierarchy to be written: forward sampling (useful, unsound) → latent-space over-approximation (interval, zonotope, ellipsoidal) → invariant certificates (sound, necessary conditions only). Plus the nearest-reachable-state computation.

### 7.2 Apparatus parameterisation **[Pass C]**

\(\mathcal{U}_{\text{adm}}\) is not a box. Apparatus geometry couples the controls, so achievable driving programmes occupy a structured low-dimensional set.

> **Requirement.** Inverse design MUST be parameterised in apparatus settings, never in desired driving paths. Optimising over idealised histories produces recipes the apparatus cannot execute.

To be written: construction of the constraint manifold from apparatus specification; treatment of rate limits and capacity couplings; mixed-integer handling of discrete decisions, where scenario enumeration is usually sufficient because the discrete space is small.

### 7.3 Decision layer **[Pass C]**

Selects within the degenerate solution set that Core §5 establishes but does not resolve.

- Optimise **probability of conformance** against specification windows, not expected value.
- Carry **asymmetric costs** — field failure, downgrade, rework, and re-run differ by orders of magnitude.
- **Derive accuracy requirements from the decision.** This feeds §2.6's budget allocation and is the correct way to distribute modelling effort.
- Connect CVaR to the conformance and defect-rate language in which approval decisions are actually made.

---

## 8. The sufficiency campaign **[Pass C]**

*Serves Core §2.1.*

Design principle: **matched-state, divergent-history pairs.** Generate pairs with equal measured state under the candidate description but different histories; apply identical subsequent driving; report the response gap normalised by measurement scatter as the **sufficiency deficit**.

Campaign matrix, ordered by expected information per unit cost. Flagship-domain instance:

| Pair | Matched on | Divergent history | Subsequent test | Tests |
|---|---|---|---|---|
| 1 | defect density | monotonic vs. reversed driving | reverse-loading response | kinematic hardening in \(z\) |
| 2 | aggregate hardness | short-hot vs. long-warm thermal path | tensile + bend | thermal-path memory |
| 3 | phase fraction | continuous vs. isothermal route | subsequent transformation + tensile | morphology and partitioning |
| 4 | prior grain size | different reheat paths | quench + bend | grain-size sufficiency for toughness |
| 5 | layer weight | different inter-diffusion history | adhesion + uptake | \(\Gamma\) sufficiency |
| 6 | texture | different deformation schedules | formability | texture vs. defect substructure |

To be written: power analysis — \(n \approx 2(z_{1-\alpha/2} + z_{1-\beta})^2(\sigma/\delta)^2\) per arm, with worked values for Class A and Class B responses (the latter needing substantially more, given tail scatter); pre-simulation of the campaign to predict which pairs diverge; the augmentation loop that consumes the results.

> **Framing requirement.** A failed sufficiency test is the most informative outcome. The direction of divergence names the missing state variable. This is a state-discovery procedure, not a validation gate, and MUST be reported as such.

---

## 9. Conformance and validation

### 9.1 Conformance levels

| Level | Requirement |
|---|---|
| **OMI-0** | Typed chain; declared state and interface (Core §4); readouts typed and classed; grouped splits enforced; rollout-length error curve reported |
| **OMI-1** | OMI-0 + sufficiency test run and reported (§8); semigroup residuals (§9.2); observability triage with dangerous set declared (§3); calibration diagnostics (§9.5); \(\|\mathcal{D}_\lambda\|\) wherever scale bridging occurs (§6) |
| **OMI-2** | OMI-1 + prospective inverse-design trial with reported hit rate and interval calibration (§9.3); reachability certificates (§7.1); Class B volume-scaling validation at ≥3 volumes (§4.4) |

An implementation MUST state its level and MUST NOT claim a level whose reporting requirements it has not met.

### 9.2 Automated test suite

Runnable in continuous integration. Each returns a residual, not a pass/fail, and thresholds are set per §9.4.

- semigroup consistency on random sub-interval splits;
- matched-history sufficiency residual;
- closure defect \(\|\mathcal{D}_\lambda\|\);
- rollout-length error curve;
- local Lipschitz spectrum, decomposed;
- calibration — PIT histograms, CRPS, empirical coverage of nominal intervals;
- **adversarially-sampled** constraint satisfaction. The optimiser is an adversary, so the test MUST be too; in-distribution constraint checks are insufficient.
- reachability certificate checks;
- innovation-based drift monitoring (§10).

### 9.3 Baselines, and when not to use OMI

Compare against: gradient-boosted trees on process-log summary statistics; end-to-end tabular regression; the physics simulator alone; per-stage regression without operator composition.

**Splitting.** Never randomly. Group by provenance unit, batch, campaign and composition family. Random splits leak: adjacent samples from one unit are near-duplicates and inflate scores by a wide margin. **Extrapolation tests** hold out entire regions of the control space or whole composition variants, not scattered points.

**Prospective validation of inverse design.** Retrospective inverse-design accuracy is nearly meaningless — the model recovers routes it has seen. The real test is prospective: propose settings, execute them, report hit rate and interval calibration. An implementation that cannot state its prospective hit rate has not been validated for the purpose it claims.

**The honest case.** If tabular baselines achieve most of the forward accuracy at a fraction of the cost — plausible for well-instrumented, narrow-window production — then the operator graph must be justified on grounds it can actually claim: inverse design under constraints; interrogable intermediate states; transfer by operator reuse; extrapolation outside the historical window; uncertainty that propagates with physical structure.

**[Pass C]** — convert this into a scored go/no-go table with thresholds on window width relative to measurement noise, planned new variants, presence of geometry-dependent responses, and labelled-record count. Stating when *not* to use OMI is a strength, and leaving it qualitative is a weakness.

**Interrogability MUST be delivered, not asserted.** If a domain expert cannot read the intermediate state, one of the justifications above is void. The latent representation MUST be equipped with interpretable coordinates — by construction (supervised components tied to measurable descriptors) or by post-hoc probes **with reported fidelity per descriptor**.

### 9.4 Falsification thresholds **[Pass D]**

Each criterion in Core §6.1 requires a stated tolerance or a procedure for setting one per application. To be written: threshold-setting derived from decision sensitivity (§7.3), so that "super-linear growth" and "below application tolerance" acquire numbers rather than rhetoric.

### 9.5 Uncertainty taxonomy and calibration reporting

Separate the sources, because they drive different decisions.

- **Aleatoric** — irreducible variability: unit-to-unit and within-unit composition variation within specification, input-dimension scatter, defect-population randomness, sensor noise. Drives robust design, tolerance setting, and specification limits.
- **Epistemic** — reducible ignorance: model-form error, closure defect, sparse coverage of the control space. Drives active experimental design and characterisation budget.

Propagate by probabilistic neural operators, deep ensembles, or moment propagation. State plainly what is otherwise glossed: **ensembles decalibrate under exactly the distribution shift that inverse design creates.** Countermeasures: conformal prediction for distribution-free coverage in-distribution; explicit out-of-distribution detection on the state manifold; trust-region-constrained optimisation (§7); prospective validation of proposed optima (§9.3).

Calibration diagnostics MUST be reported, not only point-error metrics.

---

## 10. Operations and lifecycle **[Pass C]**

Deployed operator graphs decay: tooling wears, apparatus ages, sensors drift, input sources change.

> **Proposition.** In the assimilation formulation, the **innovation sequence is a sufficient statistic for model drift.** Deployment monitoring therefore falls out of Core §3.8 at no additional cost.

To be written: innovation-based drift detection with control limits; scheduled recalibration; continual learning with forgetting protection; champion/challenger deployment and mandatory shadow-mode running before any closed-loop use; operator versioning and rollback, so that a chain is a pinned set of operator versions.

---

## 11. Instantiations — full declarations **[Pass D]**

Each declares the seven interface items of Core §4, in order.

- **§11.1 Flagship** — metallurgical process chain. Erasure completeness quantified; observability triage against a real sensor suite; Class B done properly with process-zone volume, \(N_{\text{eff}}\) correction and measured-population tail anchoring, validated across ≥3 gauges; hybrid event catalogue; reachability with at least one non-reachability certificate for a commercially requested but impossible target; cost-weighted decision layer.
- **§11.2 Contrast** — electrochemical cell under service. Declares an **empty erasure inventory** and must therefore satisfy condition (b) of the dichotomy explicitly; observability triage under a genuinely poor observation suite; three-level tier recursion; usage inverse in place of process inverse.
- **§11.3 Second flagship instance** — a continuous, closed-loop-controlled route, included specifically to exercise §5.2 (registration), §5.3 (confounding) and §3 (in-line sensing), which the flagship under-tests.
- **§11.4 Sketches** — interface-only, one page each, to demonstrate the interface is fillable outside both: layer-wise additive processing (hybrid structure and body-indexed state at their most extreme); device yield (where Class B volume scaling recovers the classical defect-density model, an independent confirmation of §4's mathematics); crystallisation and formulation (polymorph selection as a bifurcating evolution operator; dissolution as a Class B readout).

---

## 12. Reference implementation architecture **[Pass C]**

Opinionated by design: a named default is more useful than a survey.

**Core abstractions.** `State` (named slots \(m, z, \nu, \Gamma\); mode label; body index), `Control` (time-parameterised), `EvolutionOperator` (`.step`, `.lift`, `.lipschitz_estimate`, `.is_erasure`), `Readout` (declares type 0/1/2, class A/B, volume argument), `Assimilator`, `Chain` (mode-labelled DAG), `Constraints`.

**End-to-end differentiability is a requirement, not a nicety** — inverse design needs gradients through the whole chain. Gradient checkpointing for long rollouts; adjoint for continuous segments.

**Ensemble representation** is the key engineering decision. Particle ensembles in *latent* coordinates, encoder/decoder fixed per segment, is the recommended default: general enough for multimodal transformation, affordable at ~10² particles. Full-state particles are too heavy; latent Gaussians are wrong precisely at transformation.

**Type-1 export to external solvers.** A constitutive operator must be callable from a compiled solver at the integration point. Two requirements flow backwards into the theory:

- the solver needs a **consistent tangent** or it will not converge — autodiff of the surrogate supplies it, and this SHOULD be claimed as an advantage of the learned formulation;
- history-variable vectors are of fixed, modest size in commercial solvers, placing a **hard cap on the latent dimension of \(z\)**. A deployment constraint that constrains state selection (§1) should be shown explicitly.

**Data layer.** Registration (§5.2); operator versioning; provenance per operator; provenance identifiers as first-class metadata enforcing §9.3 splits.

**Compute budget realism [Pass C].** Order-of-magnitude figures: training-set sizes per segment; inference latency required for at-line use; ensemble sizes; implied latent dimensions. Numbers make the architecture credible; their absence makes it aspirational.
