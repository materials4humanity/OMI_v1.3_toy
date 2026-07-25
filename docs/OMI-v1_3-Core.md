# OMI: Operator Materials Intelligence — Core

**A Domain-Neutral Framework for Process–Structure–Response Linkages via Graphs of Infinite-Dimensional Operators**

**Version 1.3 — Pass A skeleton, July 2026**

> **Document status.** This is the Pass A skeleton of the Core document. Theory carried forward from v1.2 is present in full, with notation substituted (§0.2) and domain vocabulary removed. Sections marked **[Pass B]** or **[Pass C]** carry a statement of the result and its intended content but not its derivation; those are the passes that require new technical work. Procedures, estimators, thresholds and numbers live in the companion **Implementation Specification** (cited throughout as **→ Spec §x**), which is versioned separately.
>
> **Allocation rule.** Core contains everything falsifiable. Spec contains everything executable. A claim belongs here; a procedure belongs there. Every claim below that has a Spec procedure carries a pointer, and the pointers are indexed in Appendix D.

---

## Abstract

OMI is a physics-informed mathematical framework for representing and learning Process–Structure–Response linkages in **PSR systems**: systems of structured matter whose internal organisation evolves under driving conditions, and whose measurable responses are mediated by that organisation. Behaviour is modelled as a directed graph whose nodes are infinite-dimensional state spaces and whose edges are operators. The framework rests on two primitives — **evolution operators**, which advance the state under driving conditions, and **readout operators**, which extract observables from a state or trajectory — and one axiom: that the state can be chosen large enough to be *sufficient* for its own future.

Version 1.3 makes the framework domain-neutral and its claims operational. Generality is no longer asserted but **demonstrated through an instantiation interface** (§4): a seven-item declaration that any domain must supply in order to be brought inside the framework, together with worked instantiations that exercise it in opposite regimes.

Three new results carry the version. First, **state selection is a measurable bias–variance trade-off** rather than a matter of judgement: the bias term is supplied by the sufficiency protocol and the variance term by the observability spectrum, so the framework's one free choice becomes an empirical optimisation (§2.2). Second, the **error-control dichotomy**: long-chain composability requires either contractive erasure operators that bound accumulated error or observation density sufficient for assimilation to correct drift, and a domain with neither lies outside the framework's competence (§3.9). This supplies the scoping criterion that a general framework needs in order to remain falsifiable. Third, an explicit **refusal criterion**: where dynamics are genuinely expansive, autoregressive operator rollout is the wrong tool, and the framework says so rather than supplying a worse answer (§3.9).

Three further corrections. The state tuple of v1.2 is generalised to a **four-slot schema** in which residual stress is recognised as the mechanical instance of a general nonlocal field (§3.1). **Discrete events and spatial extent** are admitted: the process is a hybrid continuous–discrete system, and the state is a field over the material body rather than a single point (§3.4, §2.5). And the inverse-problem taxonomy is generalised from process/structure to **control/structure**, with process and usage inverses as domain instances of the former (§5).

---

## 0. Version history and notation changes

### 0.1 Changes from v1.2

| Issue in v1.2 | Resolution in v1.3 | Section |
|---|---|---|
| Domain-specific throughout; generality asserted, not demonstrated | Instantiation interface; Core purged of domain vocabulary; two instantiations chosen to invert one another | §4, §7 |
| Sufficiency–learnability trade-off named, then left to judgement | State selection as a measurable bias–variance problem | §2.2 |
| State tuple presented as *the* state; \(\sigma_{\text{res}}\) is a mechanical special case | Four-slot schema with \(\nu\) as the general nonlocal / self-consistent field | §3.1 |
| Erasure ("reset") operators framed metallurgically; silent on domains that lack them | **Error-control dichotomy**; erasure or observation, or out of scope | §3.9 |
| Composition instability stated; no guidance where \(L>1\) | Explicit refusal criterion and change of representation | §3.9, → Spec §2 |
| Observability "should be performed per chain"; no construction given | Computable identifiability triage stated as a result | §3.8, → Spec §3 |
| Class B tail estimation on learned manifolds left unresolved (v1.2 §9) | Driver/tail separation; tails anchored on independently measured defect populations | §3.6, → Spec §4 |
| Discrete events absent; state implicitly spatially uniform | Hybrid continuous–discrete structure; body-indexed state | §3.4, §2.5 |
| Process/structure inverse distinction presumes a controllable apparatus | **Control inverse** (process and usage instances) vs. structure inverse | §5 |
| Solutions are sets; no criterion for selecting within the set | Decision layer selects within the degeneracy | §5, → Spec §7 |
| No implementation guidance; no conformance regime | Companion Implementation Specification with conformance levels OMI-0/1/2 | → Spec §9 |
| Notation collisions | Resolved | §0.2 |

### 0.2 Notation changes from v1.2

Readers of v1.2 should note six substitutions. They are mechanical but pervasive.

| v1.2 | v1.3 | Reason |
|---|---|---|
| \(\mathcal{P}\), \(p\) — driving parameters | \(\mathcal{U}\), \(u\) — **controls** | Collided with \(\mathscr{P}(\mathcal{S})\); aligns §5 with optimal-control convention |
| \(\sigma_{\text{res}}\) | \(\nu\) | Generalised: nonlocal / self-consistent field. Residual stress is its mechanical instance |
| \(\mathcal{R}_\lambda\) — coarse-graining | \(\Pi_\lambda\) | Collided with \(\mathcal{R}_{\text{const}}\); projection notation is standard |
| \(\mathcal{G} = (\Omega, \partial\Omega\text{-data})\) | \(\mathfrak{B}\) | Collided with \(\mathcal{G}_{\text{evol}}\) |
| \(\mathcal{M}_{\text{field}}\) | \(\mathfrak{F}\) | \(\mathcal{M}\) reserved for \(\mathcal{M}_{\text{real}}\), \(\mathcal{M}_{\text{reach}}\) |
| reset operator | **erasure operator** \(\mathcal{E}\) | "Reset" now collides with hybrid-system jump maps (§3.4) |

---

## 1. Introduction

Classical informatics for structured matter treats process–structure–property–performance relationships as static mappings between tabular features. This obscures three facts:

1. Structure is a continuous, evolving physical field, not a feature vector.
2. Much of the state that governs its evolution is not directly observable.
3. What is conventionally called "performance" is not a function of the material alone.

OMI replaces tabular mappings with an operator-graph representation grounded in functional analysis, internal-state-variable thermodynamics, and physics-informed machine learning. The graph makes explicit the causal and temporal structure of processing and service, separates *advancing the state* from *observing it*, and separates *the material* from *the component*.

### 1.1 Scope: PSR systems

The framework applies to systems exhibiting three features together:

- a **control axis** — driving conditions that can be specified, whether by an apparatus or by a usage pattern;
- **internal state that is not directly observable** and that governs future evolution;
- **responses mediated by structure** rather than read directly from composition or geometry.

This is the physics of structured matter under controlled driving. It covers materials processing and service, electrochemical systems, catalysis, crystallisation and formulation, geomechanics, cementitious systems, tissue engineering and food science. It does not cover domains with no control axis and no property/performance distinction; claiming those would weaken everything else. Materials science is the densest instance and supplies the flagship instantiation (§7.1), but no part of Parts I–II depends on it.

### 1.2 Claims and non-claims

OMI claims to provide: a consistent ontology for PSR linkages; a composable substrate for neural operator surrogates; a principled route to uncertainty propagation and inverse design; a declared interface by which a new domain enters the framework; and a set of falsifiable assumptions.

It does **not** claim that operator learning is always the right tool (→ Spec §9.3), that scale bridging is exact (§3.7), that the state is ever fully observed (§3.8), or that every PSR system is within competence (§3.9).

---

## 2. Conceptual foundations

### 2.1 State sufficiency: the central axiom and its price

**Axiom S (Sufficiency).** *There exists a state space \(\mathcal{S}\) such that for any admissible driving programme, the future evolution of the system depends on its history only through the current state \(s_t \in \mathcal{S}\).*

This axiom licences everything downstream: Markovian evolution, operator composition, modular reuse, checkpointing, and sequential state estimation. It must therefore be stated as an axiom, not smuggled in as notation.

The critical observation is that **Markovianity is not a physical fact about matter; it is a property of a choice of state space.** Any system is Markovian in a sufficiently large state and non-Markovian in a sufficiently small one.

Resolved structural fields alone are generically insufficient. Wherever response depends on driving *path*, the state must carry path-dependent internal variables that no imaging modality reveals: kinematic hardening variables govern reverse-loading response; defect-population partitioning governs recovery and reorganisation kinetics; sub-resolution clustering governs ageing; nucleation-site populations govern damage initiation. None of these appear in a structural image. §3.1 gives the schema that repairs this; §7 gives the domain instances.

**The sufficiency test (operational).** Axiom S is falsifiable and should be tested, not asserted. Prepare or simulate specimen pairs with matched \(s\) but deliberately different histories — equal defect density reached by monotonic versus reversed driving; equal aggregate hardness reached by different thermal paths; equal phase fraction reached by different transformation routes. Subject both to identical subsequent driving and compare responses. Divergence beyond measurement scatter falsifies sufficiency for that \(\mathcal{S}\), and the *direction* of divergence indicates the missing state variable. This test is a required element of validation for each chain, and its outcome must be reported.
**→ Spec §8** for campaign design, pair selection, and statistical power.

### 2.2 State selection as a measurable trade-off **[Pass B]**

v1.2 named the burden and left it there:

> **Sufficiency–learnability trade-off:** choose \(\mathcal{S}\) large enough that Axiom S holds to within application tolerance, and small enough that operators on \(\mathcal{S}\) can be learned from available data.

This should not be a matter of judgement, because both of its terms are measurable by machinery the framework already defines. Enlarging \(\mathcal{S}\) **reduces model bias**, measured by the sufficiency deficit of §2.1. Enlarging \(\mathcal{S}\) **increases estimation variance**, because the components added are precisely the unobservable ones, and their posterior spread propagates; this is measured by the observability spectrum of §3.8.

> **Result (state selection).** Choose \(\mathcal{S}\) to minimise expected terminal error on the *declared target readouts*:
> \[
> \mathbb{E}\big[\|\hat\rho - \rho\|\big] \;\lesssim\; \underbrace{\mathrm{Bias}(\mathcal{S})}_{\text{sufficiency test}} \;+\; \underbrace{\mathrm{Var}_{\text{est}}(\mathcal{S})}_{\text{observability spectrum}} \;+\; \underbrace{\mathrm{Err}_{\text{learn}}(\mathcal{S})}_{\text{rollout-length curve}} .
> \]

Axiom S thereby becomes a **constructive algorithm** rather than an assumption: propose \(\mathcal{S}\) → run the sufficiency test → read the missing variable from the direction of divergence → augment → check identifiability → retest → stop when the deficit falls below the decision tolerance.

Each term has an estimator. **Bias** is the sufficiency deficit, decomposed to separate genuine insufficiency from measurement noise and from imperfect matching — a raw response gap is not a sufficiency deficit and systematically over-states it. **Variance** is exactly the sum of danger scores from §3.8: a component that is influential and unobservable converts model bias into estimation variance without reducing terminal error, and therefore **makes the model worse**. This is the precise sense in which Axiom S has a price. **Learning error** is not predictable a priori and is read from the rollout-length curve at matched data budget, driven by *effective* rather than nominal dimension.

Axiom S thereby becomes a **constructive algorithm** rather than an assumption: propose \(\mathcal{S}\) → run the sufficiency test → read the missing component from the *fingerprint* of divergence across a discriminating probe set → augment if the bias reduction exceeds the variance and learning costs → retest.

**A consequence with immediate practical force.** Segment-level deficits accumulate with the same amplification structure as learning error, so a deficit upstream of a complete erasure is suppressed by it. **A large deficit in a segment followed by an erasure is not a reason to enlarge the state** — this is the most common source of wasted state augmentation.

**When the loop terminates with a residual deficit**, three outcomes must be distinguished, because only one is a refutation: if the variance term blocks, the needed component exists but cannot be identified, and the answer is sensing (§3.8); if learning error blocks, the answer is data; only if bias blocks *with no bounded candidate available* is Axiom S falsified for that domain (§6.1). Conflating the three is how a framework acquires an undeserved reputation for failure.

**Corollary.** The right state is *target-dependent*. Two chains built for different readouts need not share \(\mathcal{S}\). Users must therefore declare their target readout set before selecting state — which licenses cheap, useful, deliberately incomplete models. **→ Spec §1.**

### 2.3 Two primitives, not three

v1.1 posited three operator classes: fusion, evolution, readout. From v1.2 onward there are two.

- **Evolution operators** advance the state under controls. Both primary processing and service loading are sequences of evolution operators; there is no ontological difference between them.
- **Readout operators** map a state, or a trajectory of states, to observables.

Fusion is not a primitive. Characterisation *is* measurement, measurement *is* readout, and the assimilation of measurements into a state estimate is a filtering algorithm assembled from evolution and readout operators (§3.8). This is not merely economical: it means that the operator relating structure to an imaging modality and the operator relating structure to a mechanical response are objects of the same type, trained by the same machinery, and reusable in both roles.

### 2.4 Two tiers: material and component

A single-tier graph cannot represent geometry-dependent responses. OMI therefore separates:

- **Tier I (material).** State evolution on statistical volume elements under spatially uniform or periodic driving. This is where structural physics lives.
- **Tier II (component).** A boundary value problem on a domain \(\Omega\) with boundary conditions, whose constitutive law is *supplied by a Tier I readout*.

The tiers are coupled in both directions: Tier I supplies constitutive response upward; Tier II supplies localised driving histories and highly-driven volumes downward. This is the classical FE² structure, and operator surrogates are precisely what render it tractable.

Tier II may itself be recursive where the engineering artifact is hierarchical; §7.2 gives an instance in which three levels are required.

### 2.5 The body-indexed state **[Pass C]**

v1.2's Tier I implicitly assumed spatial uniformity. This is untenable for extended bodies: a production unit is not one state but a field of states indexed by material coordinate — position along the body, through-thickness, across-width.

> **Refinement.** The Tier I state is a section of a bundle over the material body: \(s : \mathcal{X}_{\text{body}} \to \mathcal{S}\). Evolution acts pointwise or with local coupling; Tier II remains the component boundary value problem.

Gradients across the body — thermal profile, surface-layer variation, head-to-tail drift — are first-order practical concerns in every extended-body domain, and none of them are representable without this refinement.

**[Pass C]** — requires: coupling conditions between neighbouring material points, and the registration operator relating apparatus-frame observations to material coordinates. **→ Spec §5.2.**

### 2.6 Properties and performances, defined

Let \(\mathcal{T}\) be a class of test configurations (geometry, boundary conditions, specimen size) regarded as equivalent for a given purpose.

> **Definition.** A readout \(\rho\) is a **property relative to \(\mathcal{T}\)** if its value is invariant under variation of the configuration within \(\mathcal{T}\). Equivalently, \(\rho\) is a functional of the constitutive operator alone (§3.5, Type-1). A **performance** is the composition of that constitutive operator with a specific geometry and boundary value problem, and is not a functional of the material state alone.

The classification is by invariance, not by whether a test is standardised:

| Response character | Class | Reason |
|---|---|---|
| Configuration-invariant functionals of \(\mathcal{C}\) — moduli, anisotropy coefficients, interfacial energies | Property | Independent of configuration within \(\mathcal{T}\) |
| Volume-insensitive aggregate response | Property, self-averaging | Converges with volume |
| Onset-of-instability measures | Property, weakly volume-dependent | Instability onset is partly weakest-link |
| Responses depending on specimen dimensions or tooling geometry | **Performance** | Value changes with configuration within \(\mathcal{T}\) |
| Responses depending on edge or surface preparation | **Performance** | Depends on \(\Gamma\) *and* on geometry |
| Structural energy absorption | **Performance** | Section geometry and collapse mechanics |

The v1.1 statement that "a standardised property test is simply a controlled evolution trajectory followed by a readout" is true but insufficient: **standardisation of a test does not make its result a property.** Several of the most commercially decisive metrics in mature domains are performances wearing property clothing, and treating them as readouts from a representative volume is a modelling error, not a simplification. §7.1 gives an instantiation in which three of four decisive responses are performances.

---

## 3. Mathematical framework

### 3.1 The state schema: four slots

The state is a tuple

\[
s = (m,\; z,\; \nu,\; \Gamma) \in \mathcal{S},
\]

with slots defined by *how each behaves under evolution and observation*, not by the physics of any one domain:

- \(m \in \mathfrak{F}\) — **resolved structural fields.** Order parameters, indicator fields, orientation fields, composition fields, geometric descriptors of second-phase and defect populations. Observable in principle by imaging, at a stated resolution limit.
- \(z \in \mathcal{Z}\) — **sub-resolution internal variables.** Path-dependent quantities below imaging resolution: defect densities and their partitioning, kinematic hardening variables, accumulated driving measures, clustering and segregation state, damage variables, distribution moments of unresolved populations. Not observable directly; inferable only through dynamics (§3.8).
- \(\nu\) — **nonlocal / self-consistent fields.** Quantities that do not localise to a material point because they are determined by a global balance: residual stress and eigenstrain in mechanical systems, electrostatic potential and concentration overpotential in electrochemical ones, supersaturation in crystallising ones. Carried separately because pointwise evolution operators cannot own them.
- \(\Gamma\) — **surface and interface state.** Layer structure and constitution at bounding and internal interfaces; interfacial segregation; preparation-induced damage. This slot is not cosmetic: in a large class of systems it is the controlling state for adhesion, transport across interfaces, environmental attack, and initiation-controlled failure.

\(z\) is the bridge to internal-state-variable thermodynamics (Coleman–Gurtin; Rice; Kocks–Mecking; Follansbee–Kocks; Bammann), generalised from constitutive laws to whole chains. **Its inclusion is what makes Axiom S tenable; its unobservability is what forces §3.8.**

Domain occupants of each slot are declared through the instantiation interface (§4, item 1) and tabulated for two domains in §7.

### 3.2 Spaces and type discipline

Fix the following and use them consistently:

- \(\mathcal{S}\) — state space, as above, with a metric \(d_\mathcal{S}\) (e.g. Wasserstein on descriptor measures ⊕ weighted Sobolev norms on fields).
- \(\mathcal{U}\) — **control space.** Time-dependent driving programmes: thermal histories, deformation-rate histories, chemical potentials, atmospheres, applied fields, duty cycles. Elements are functions of time on an interval, not scalars. \(\mathcal{U}_{\text{adm}} \subseteq \mathcal{U}\) is the admissible subset imposed by the apparatus (§4, item 2).
- \(\mathcal{Y}\) — observation space, multi-modal.
- \(\mathcal{R}\) — response space (scalars, curves, fields, or operators — see §3.5).
- \(\mathscr{P}(\mathcal{S})\) — probability measures on \(\mathcal{S}\). **Ensembles live here.** A "statistical representative volume" is an element of \(\mathscr{P}(\mathcal{S})\), not of \(\mathcal{S}\).
- \(\mathfrak{B} = (\Omega, \partial\Omega\text{-data})\) — component geometry and boundary conditions (Tier II).

### 3.3 Evolution operators and their lift to ensembles

An elementary evolution operator over \([t_k, t_{k+1}]\) is

\[
\mathcal{G}^{(k)}_{\text{evol}} : \mathcal{S} \times \mathcal{U} \to \mathcal{S}, \qquad s_{k+1} = \mathcal{G}^{(k)}_{\text{evol}}(s_k, u_k).
\]

**Lift to ensembles.** Because the physical object of interest is an ensemble, define the lifted operator on \(\mathscr{P}(\mathcal{S})\) by pushforward,

\[
\mu_{k+1} = \big(\mathcal{G}^{(k)}_{\text{evol}}(\cdot, u_k)\big)_{\#}\, \mu_k ,
\]

and, when the operator is itself stochastic (unresolved fluctuations, model error, §3.7), by the Markov kernel \(K_k(s, \mathrm{d}s')\) via \(\mu_{k+1} = \int K_k(s,\cdot)\,\mu_k(\mathrm{d}s)\), with Chapman–Kolmogorov guaranteeing consistency of composition. All graph composition below is understood at the level of measures.

**Semigroup structure as free supervision.** For a fixed control programme \(u\) restricted to subintervals,

\[
\mathcal{G}_{t \to t''}(\cdot\,;u) = \mathcal{G}_{t' \to t''}(\cdot\,;u) \circ \mathcal{G}_{t \to t'}(\cdot\,;u), \qquad t < t' < t''.
\]

This is checkable, enforceable as a training loss, and yields unlimited data augmentation: any trajectory can be resampled into arbitrary sub-intervals with arbitrary split points, each a valid training triple. Caveat: this holds for the *state-augmented* dynamics only — it is another consequence of, and hence another test of, Axiom S. Violation of semigroup consistency under sub-interval resampling is a cheap, automatable proxy for insufficiency of \(\mathcal{S}\). **→ Spec §9.2.**

### 3.4 Hybrid structure: continuous evolution, discrete events **[Pass C]**

Real chains are not continuous throughout. They are **hybrid systems**: continuous evolution punctuated by discrete events that change which operator applies.

> **Refinement.** The graph is mode-labelled. Modes \(q \in Q\) each carry their own evolution operator family; guards determine transitions; **jump maps** effect them. Composition respects mode compatibility.

Events to be represented include joins between production units, material removal, recipe and setpoint switches, dimensional changes, interruptions of continuous operation, start-up and shut-down transients, and tooling changes. Interruptions deserve emphasis: material resident in a continuously-operating apparatus during a stoppage receives a wholly different driving history, and this is a dominant source of off-specification output in continuous domains — precisely the case a state-space formulation handles well and a tabular model cannot.

*Terminology.* "Jump map" is the discrete transition of a hybrid system. It is unrelated to the **erasure operator** \(\mathcal{E}\) of §3.9, which is a continuous but strongly contractive evolution operator. v1.2's term "reset" collided with both and has been retired.

**[Pass C]** — requires: guard specification, type-safety rules across mode transitions, and interaction of jump maps with erasure analysis. **→ Spec §5.1.**

### 3.5 Readout operators: three types

Readouts are graded by codomain, and the grading is what makes Tier II possible.

**Type-0 — functional readouts.** \(\rho_0: \mathcal{S} \to \mathbb{R}^n\) or into curve spaces. Phase fractions, texture components, effective moduli, aggregate hardness, transformation-tracking signals, simulated diffraction patterns. Includes the *measurement models* of §3.8.

**Type-1 — operator-valued readouts.**
\[
\mathcal{R}_{\text{const}} : \mathcal{S} \longrightarrow \mathrm{Op}\big(\mathcal{U} \to \mathcal{R} \times \mathcal{S}\big),
\]
returning a **constitutive operator** \(\mathcal{C} = \mathcal{R}_{\text{const}}(s)\) that maps a local driving history to a response history *and* an updated state. Type-1 readouts are the formal content of homogenisation: they are what a material point "is" from the perspective of a boundary value problem. \(\mathcal{C}\) is not a function but an operator with memory — it carries \(z\).

**Type-2 — component readouts.**
\[
\rho_2 : \mathrm{Op} \times \mathfrak{B} \to \mathcal{R}, \qquad \rho_2(\mathcal{C}, \Omega, \text{BC}) = \text{(functional of the BVP solution)} .
\]
These are the performances of §2.6. They cannot be obtained from a Tier I state by any Type-0 readout, because the required information — geometry — is not in the state.

**Unification with §2.6.** Properties are functionals of \(\mathcal{R}_{\text{const}}(s)\) alone; performances require \(\rho_2\). The taxonomy is a type statement, not a convention.

### 3.6 Ensembles, self-averaging, and extreme-value readouts

A representative volume element is a *sufficient* construct only for readouts that self-average. Split the readout classes:

**Class A — self-averaging.** \(\rho(V) \to \rho_\infty\) as \(V \to \infty\), with \(\mathrm{Var}\,\rho(V) \sim V^{-1}\). Effective moduli, anisotropy coefficients, mean aggregate response. Here an RVE exists and apparent-property bounds converge (Hill; Ostoja-Starzewski).

**Class B — weakest-link / extreme-value.** The response is governed by the *worst* local configuration in the driven volume: the largest defect, the most severe heterogeneity band, the most unfavourably oriented local region, the deepest preparation-induced notch. For a volume comprising \(N = V/V_0\) statistically independent sub-volumes,

\[
P\big(\rho_V > x\big) \;=\; \big[P(\rho_0 > x)\big]^{N},
\]

so the mean response **decreases** with volume, the variance does not vanish, and **no RVE exists**: the effective value never converges.

The correct readout signature for Class B is therefore

\[
\mathcal{G}_{\text{readout}} : \mathscr{P}(\mathcal{S}) \times V \to \mathscr{P}(\mathcal{R}),
\]

returning a *distribution* parameterised by driven volume. **Class B readouts must not be reported as point predictions.**

**A structural consequence.** The relevant \(V\) is not the component volume but the **process-zone volume** — the region actually experiencing the failure driver. That volume is computed in Tier II. Class B readouts therefore *couple the two tiers* and cannot be evaluated in Tier I alone. This is a genuine structural result of the two-tier formulation and one of its main practical payoffs: it explains why rankings invert between specimen sizes, and why small coupons systematically over-predict full-scale performance.

**Tail estimation.** v1.2 left this unresolved, correctly identifying it as the weakest practical link: generative priors are least reliable exactly where Class B readouts live. v1.3's resolution is to **stop asking the generative model for the tail.** The bulk distribution of the failure driver is learned from ensembles where the prior is well supported; above a declared threshold the tail is inherited from an independently measured defect population, transferred through a declared physics map \(\Psi\) (§4, item 4b).

> **Result (tail-index transfer).** If a defect descriptor has regularly varying tail index \(\alpha\) and the driver amplifies as \(D \sim a^{\beta}\), the driver tail index is \(\alpha/\beta\); in generalised-Pareto shape parameters, \(\xi_D = \beta\,\xi_a\).

The tail exponent of the driver is the *measured* exponent of the defect population, rescaled by the exponent of the physics. Nothing is extrapolated by the generative model. The construction reproduces known scalings as a check — a heavy-tailed defect population with a weakly amplifying map yields a markedly lighter-tailed strength distribution, which is why initiation-controlled limits scatter far less than the defect sizes that cause them.

**A second correction changes the size effect itself.** The scaling law above assumes independent sub-volumes, but driver fields are spatially correlated with a correlation length \(\ell_D\).

> **Result (dimensional reduction).** Where \(\ell_D\) exceeds a dimension of the process zone, the weakest-link count scales with the *reduced-dimensional* measure of that zone, and the apparent size-effect exponent in the suppressed direction tends to zero.

Process zones are usually thin — a sheared edge, an outer fibre, a surface layer — so this is the common case rather than the exception. It is also the quantitative content of the ranking-inversion claim above: two materials with different \(\ell_D\) cross over as specimen thickness sweeps through their correlation lengths, and independent scaling calibrated at one thickness both over-predicts the size effect and mis-orders the materials at another.

**→ Spec §4** for the join protocol, rare-event sampling, and a validation ladder that tests the construction rather than attempting to validate a tail quantile directly.

### 3.7 Scale bridging: homogenisation, closure, and the honest role of RG

Renormalisation-group coarse-graining is not defensible as general scale-bridging machinery. RG has specific content — a scale-transformation semigroup, flow in theory space, fixed points, universality — and derives its power from scale invariance. Structured matter possesses characteristic lengths and is emphatically *not* scale-free.

**(i) The default machinery is homogenisation.** Computational homogenisation, variational \(\Gamma\)-convergence, bounds hierarchies, and \(n\)-point statistical descriptors (Torquato) — with the Type-1 readout of §3.5 as the formal upscaling map.

**(ii) The closure defect is named and measured.** Coarse-graining does not commute with evolution. For a projection \(\Pi_\lambda\) to scale \(\lambda\),

\[
\mathcal{D}_\lambda \;=\; \Pi_\lambda \circ \mathcal{G}_{\text{evol}} \;-\; \mathcal{G}^{\lambda}_{\text{evol}} \circ \Pi_\lambda \;\neq\; 0 .
\]

Eliminating fine degrees of freedom from Markovian fine-scale dynamics generically produces memory and fluctuation — this is Mori–Zwanzig, and it is the *same* non-Markovianity as Axiom S arriving through a different door. Three admissible treatments, in increasing fidelity: **absorb** (learn the coarse operator directly; simple, but only conditionally Markovian and fails off-distribution); **remember** (augment with a finite memory window or recurrent latent channel approximating the memory kernel); **fluctuate** (add a stochastic closure term calibrated to fine-scale variance, giving a Markov kernel rather than a map).

Whichever is chosen, \(\|\mathcal{D}_\lambda\|\) **must be reported as a validated quantity**, not assumed small. **→ Spec §6** for measurement and expected magnitudes by scheme.

**(iii) RG is retained where it genuinely applies.** Percolation near threshold; self-similar coarsening regimes where dynamic scaling functions exist; avalanche statistics in intermittent dynamics. In these regimes scale invariance is real and universality is useful. Elsewhere the word should not be used.

### 3.8 State estimation: sequential assimilation

**The problem.** Axiom S requires a state including \(z\), \(\nu\) and \(\Gamma\). None is directly measurable. A one-shot fusion operator at \(t=0\) attempts to infer, from incomplete data, exactly the quantities that are least observable — and then propagates that estimate through the entire chain with no further correction.

**The reformulation.** Real systems are instrumented at multiple stages, by modalities that are indirect, partial, and of varying latency and spatial coverage. Treat the chain as a **partially observed Markov process** and the state as something to be *estimated recursively*, not measured once.

- **Prediction.** \(\mu_{k+1|k} = K_k \,\mu_{k|k}\), the lifted evolution operator of §3.3, with process noise representing model error and unresolved fluctuation.
- **Update.** Given observation \(y_{k+1} = H(s_{k+1}) + \eta\),
\[
\frac{\mathrm{d}\mu_{k+1|k+1}}{\mathrm{d}\mu_{k+1|k}}(s) \;\propto\; p\big(y_{k+1} \mid s\big).
\]

> **Proposition (measurement is readout).** The observation operator \(H\) is a Type-0 readout in the sense of §3.5. The map from structure to a simulated imaging modality, a transformation-tracking signal, or an in-line sensor response is the same class of object as the map from structure to a mechanical property.

Consequently OMI needs no fusion primitive. What v1.1 called \(\mathcal{G}_{\text{fuse}}\) is recovered as a special case: filtering restricted to a single time point with no prior dynamics. The general case is strictly better — it uses every measurement in the chain, corrects drift rather than compounding it, and makes the latent internal state *inferable* rather than merely postulated.

**Observability is a computable property of the chain.** Linearising along a nominal trajectory and stacking the forward-propagated observation operators yields the **observability Gramian** \(\mathbf{G}_k = \sum_{j \ge k} \Phi_{j,k}^{*} H_j'^{*} R_j^{-1} H'_j \Phi_{j,k}\), whose spectrum determines directional identifiability and which is computable by autodiff through the learned graph. Because the deterministic Gramian ignores process noise it is an *upper bound* on achievable information — which is what makes it useful for design: **a direction unidentifiable under \(\mathbf{G}_k\) is unconditionally unidentifiable.**

Weighting by influence on the declared target readouts converts the spectrum into a **danger score** \(\mathcal{D}_i = (\text{influence}) \times (\text{residual uncertainty})\), whose ranking is the four-way triage — *observed*, *inferred* (recoverable only through dynamics plus downstream measurement, which is where the chain earns its keep and which no tabular model can recover), *marginalisable*, and **dangerous** (unidentifiable *and* influential). The dangerous set is the actionable output and must be reported: it is the sensing investment case, and §3.4 of the Specification converts it into placement and expected return.

> **Proposition (erasure truncates observability).** If an erasure operator with Jacobian rank \(r\) lies between indices \(k\) and \(j\), then \(\operatorname{rank}(H'_j \Phi_{j,k}) \le r\).
>
> **Corollary.** Directions in \(\ker F_\mathcal{E}\) are unidentifiable from post-erasure data *and* have no influence on post-erasure readouts. They are marginalisable by construction and cannot be dangerous.

The corollary is the formal content of the claim that an erasure destroys upstream observability and simultaneously removes the need for it. Danger arises only from directions that *survive* an erasure yet are weakly observed — which is also why analysis is performed per segment and only the surviving subspace crosses a segment boundary. **→ Spec §3.**

**Retrospective smoothing as a product.** Running the smoother backwards over a rejected unit to infer the most probable latent-state trajectory that explains an observed defect is, for many users, more valuable than the forward surrogate. It is available for free once the graph is built.

**Innovations as a drift monitor.** In a filtering formulation the innovation sequence is a sufficient statistic for model drift, so deployment monitoring falls out of the same machinery. **→ Spec §10.**

### 3.9 Composition, erasure, and the error-control dichotomy

The forward map is the composition

\[
\mathcal{G}_{\text{PSR}} \;=\; \rho \,\circ\, \mathcal{G}^{(N-1)}_{\text{evol}} \circ \cdots \circ \mathcal{G}^{(0)}_{\text{evol}} \,\circ\, (\text{initial state estimate}),
\]

understood on \(\mathscr{P}(\mathcal{S})\), with assimilation updates interleaved wherever measurements exist, and \(\rho\) of Type-0, Type-1, or (with Tier II) Type-2.

**Error compounding.** If each learned operator has one-step error \(\varepsilon\) and Lipschitz constant \(L_k\) on the relevant set, terminal error is bounded by \(\varepsilon \sum_{k}\prod_{j>k} L_j\). Where \(L>1\), this is exponential, and autoregressive rollout of neural operators is *the* dominant practical failure mode.

**Erasure operators bound the damage.** Many operations are strongly contractive: they map a wide set of incoming states onto a narrow outgoing set.

> **Definition.** An **erasure operator** \(\mathcal{E}\) is an evolution operator whose image is of substantially lower effective dimension than its domain, with \(L \ll 1\).

Consequences:

1. **Error accumulation is bounded by the memory structure of the chain, not its length.** Errors incurred before an erasure do not propagate past it, to the extent the erasure is complete.
2. **Erasures are the natural checkpoints for modular training.** Segment the chain at erasures; train segments independently; compose. Modularity acquires a concrete criterion for *where* to modularise.
3. **Erasure completeness is measurable** — mutual information between pre- and post-erasure states, or residual variance explained by upstream variables. What survives an erasure is a well-posed and practically informative question, and is typically where residual field problems originate.

**The error-control dichotomy. [Pass B]** v1.2 treated erasure as a gift and said nothing about domains that lack it. The general statement:

> **Result.** Long-chain composability requires either
> **(a)** contractive erasure operators bounding accumulated error, or
> **(b)** observation density sufficient for assimilation to correct drift.
> A domain with neither lies outside the framework's competence and should be identified as such before work begins.

This is the scoping criterion that keeps a general framework falsifiable. §7.2 gives a domain with (b) but emphatically not (a); §7.1 gives one with both.

**Expansive regimes: an explicit refusal. [Pass B]** Where dynamics are genuinely expansive — localisation, damage coalescence, abnormal growth, autocatalytic transformation — a better surrogate is not the answer. The amplification must first be decomposed as \(L_{\text{total}} = L_{\text{physical}} \times L_{\text{numerical}}\), because an operator with \(L>1\) may be *correct*: the system really is sensitive there, and constraining it away destroys real physics. Where the amplification is physical, the correct response is a **change of representation** — predict the invariant or the bifurcation label rather than the trajectory; predict the distribution over outcomes; or event-trigger a handoff to a high-fidelity solver. A framework that knows when to refuse is more credible than one that always answers. **→ Spec §2.**

---

## 4. The instantiation interface

Generality is a claim, and claims require a mechanism. OMI's mechanism is a declaration: a domain enters the framework by supplying seven items, and is thereafter subject to every result above. Nothing else is required, and nothing less suffices.

> **An instantiation of OMI MUST declare:**
>
> 1. **State schema** — occupants of each slot \((m, z, \nu, \Gamma)\), with resolution limits, and which slots are empty.
> 2. **Control space** \(\mathcal{U}\) and admissible set \(\mathcal{U}_{\text{adm}}\), including the constraint manifold imposed by the apparatus. *Whether a control inverse (§5) exists at all is determined here.*
> 3. **Erasure inventory** — which operators are strongly contractive, what survives each, and — if none — how condition (b) of §3.9 is satisfied instead.
> 4. **Readout catalogue** — every target response typed (0/1/2) and classed (A/B), with the process-zone volume identified for each Class B entry.
>    **4b. For each Class B readout:** the failure driver field, the measured defect population that supplies its tail, and the physics map \(\Psi\) connecting them (§3.6). A Class B readout without a declared \(\Psi\) cannot have its tail anchored and MUST be reported as uncalibrated.
> 5. **Observation suite** — available modalities, what each constrains, latency and coverage.
> 6. **Invariants** — conservation laws and monotone functionals available as hard constraints (→ Spec §5) and as reachability certificates (§5).
> 7. **Scale structure** — where homogenisation is applied, between which scales, and the measured closure defect \(\|\mathcal{D}_\lambda\|\).

Two properties make this more than a checklist. It is **falsifiable per domain**: an instantiation that cannot fill item 3 or item 6 is telling you something. And it is **comparative**: instantiations declared in the same order can be diffed, which is what converts a collection of examples into evidence of generality (§7.3).

---

## 5. Inverse design as constrained optimal control

Adjoints supply gradients, not inverses, and the framework's inverse problems are not inversions at all. The correct formulation:

\[
\min_{u_{0:N-1} \in \mathcal{U}_{\text{adm}}} \; \mathbb{E}\big[\,J(\rho(s_N))\,\big] \;+\; \lambda\,\mathrm{Risk}\big[\rho(s_N)\big]
\]
subject to
\[
s_{k+1} = \mathcal{G}^{(k)}_{\text{evol}}(s_k, u_k), \qquad
s_k \in \mathcal{M}_{\text{real}}, \qquad
u_{0:N-1} \in \mathcal{U}_{\text{adm}}, \qquad
s_k \in \mathcal{U}_{\text{trust}} .
\]

**Two manifolds, not one.** \(\mathcal{M}_{\text{real}}\) is the manifold of physically realistic states; \(\mathcal{M}_{\text{reach}} \subseteq \mathcal{M}_{\text{real}}\) is the subset attainable by the *actual* apparatus under its constraints. The distinction is between a structure that could exist and one you can make. Inverse design that ignores it produces beautiful, unmanufacturable answers.

**Four constraint families, all essential:**

1. **Manufacturability** \(\mathcal{U}_{\text{adm}}\) — the physical limits of the apparatus. These are hard and known; they should be constraints, not penalties. Note that \(\mathcal{U}_{\text{adm}}\) is generally **not a box**: apparatus geometry couples the controls, so achievable driving programmes occupy a low-dimensional structured set. It follows that inverse design must be parameterised **in apparatus settings, never in desired driving paths** — optimising over idealised histories produces recipes the apparatus cannot execute. **→ Spec §7.2.**
2. **Realism** — \(s_k \in \mathcal{M}_{\text{real}}\), enforced by generative prior support rather than by hoping the optimiser stays sensible.
3. **Reachability** — for *structure*-inverse problems, feasibility is not guaranteed. The honest output is either a route or **a certificate that the target lies outside \(\mathcal{M}_{\text{reach}}\), plus the nearest reachable state**. Learned reachable sets are unsound and cannot discharge this contract; sound certificates are constructed from the invariants declared in §4, item 6. **→ Spec §7.1. [Pass B]**
4. **Trust region** \(\mathcal{U}_{\text{trust}}\) — restrict to where the surrogate is calibrated; expand it by targeted experiments rather than by optimism. Ensembles decalibrate under exactly the distribution shift that inverse design creates: **the optimiser is an adversary that seeks the region where the surrogate is most confidently wrong.**

**Two distinct inverse problems** must be kept separate; conflating them is a common source of unrealisable designs.

- **Control inverse** — target response → driving programme. This is the optimal-control problem above. Its domain instances are the *process inverse* (manufacturing: find the apparatus settings) and the *usage inverse* (service: find the duty cycle). **It exists only if item 2 of the interface declares a controllable \(\mathcal{U}\).**
- **Structure inverse** — target response → state. Domain-universal, but its output is a design, not a route: it must then be fed to a control inverse, and may be certified unreachable there.

**Report sets, not points.** These problems are typically ill-posed and the solution set is generically a manifold: many routes yield indistinguishable responses. This is *useful* — the degeneracy is exactly where cost, robustness and throughput can be traded at no performance cost. Characterise the near-optimal set and hand the user a region with its trade-off structure, not a single recipe.

**Selecting within the degeneracy. [Pass C]** v1.2 established that solutions are sets but left the selection criterion unspecified. The criterion is decision-theoretic: map predictive distributions to expected cost under asymmetric consequences, and optimise probability of conformance rather than expected value. A corollary reorganises the whole error budget — **accuracy requirements derive from the decision, not from uniform ambition**: precision is needed near the specification boundary and nowhere else. **→ Spec §7.3.**

**Robustness is the point.** Optimising the mean is close to worthless in production. Optimise a risk functional — CVaR of the response, or probability of meeting specification under the aleatoric distribution — so the answer is an operating window with quantified margin, rather than a knife-edge optimum.

---

## 6. Falsifiability

### 6.1 What would refute OMI as formulated

1. The sufficiency test (§2.1) fails persistently and cannot be repaired by state augmentation of bounded dimension — every candidate \(\mathcal{S}\) is either insufficient or unlearnable from realistic data. *Refutation requires that the **bias** term blocks with no bounded candidate available; blocking by the variance or learning terms is an argument for sensing or data, not a refutation (§2.2, → Spec §1.7).*
2. The closure defect \(\mathcal{D}_\lambda\) cannot be reduced below application tolerance by any of the three treatments in §3.7, making multi-scale composition unusable.
3. Rollout error grows super-linearly in chain length even between erasures, after all stabilisation measures.
4. Operator graphs fail to beat tabular baselines on *both* forward accuracy and prospective inverse-design hit rate, across multiple chains.
5. The state-selection trade-off of §2.2 has no interior optimum — bias and variance cannot be simultaneously brought below tolerance for any \(\mathcal{S}\) in a realistic domain.
6. The error-control dichotomy fails in the permissive direction: a domain with neither erasure nor adequate observation nonetheless supports accurate long-chain composition, indicating the criterion is not the operative one.

**[Pass D]** Each criterion requires a stated threshold or a procedure for setting one per application. A falsification criterion without a tolerance is not falsifiable. **→ Spec §9.4.**

### 6.2 Open problems

- Approximation rates and stability constants for *composed* neural operators; conditions under which composition preserves learned accuracy.
- Learnable Mori–Zwanzig memory kernels for structural coarse-graining, with error bounds.
- Observability theory for internal state variables given a specified sensor suite, and the inverse question: what sensing would make the unidentifiable identifiable.
- Extreme-value readouts on learned manifolds. §3.6 supplies a route around the difficulty rather than through it; whether generative priors can ever be trusted in the tail remains open.
- Formal characterisation of erasure operators and erasure completeness as a domain invariant.
- Transfer of evolution operators across composition families: how much of an operator is composition-conditional versus composition-parameterised.
- Reachable-set computation with mixed continuous and discrete decisions.
- Whether the four-slot schema is complete, or whether some domain requires a fifth.

---

## 7. Instantiations

Both instantiations are declared against the seven items of §4, in the same order, so they can be diffed. **[Pass D]** — full declarations; the tables below are the compact form.

### 7.1 Flagship: a metallurgical process chain

*Selected because it exercises erasure, rich instrumentation, hybrid events, and both readout classes.* Full declaration in **→ Spec §11.1**.

| Stage | Operator | Type | Notes |
|---|---|---|---|
| Incoming unit | prior on \(\mathscr{P}(\mathcal{S})\) | — | \(m\), \(z\) from prior deformation; \(\Gamma\) = coating; \(\nu\) from levelling |
| Heating and soak | \(\mathcal{E}\) | evolution, **erasure** | Erases \(z\) and most of \(m\). Survives: prior grain size, inclusion and segregation state, and \(\Gamma\) — whose own evolution governs later adhesion and environmental uptake |
| Transfer | \(\mathcal{G}_{\text{evol}}\) | evolution | Short, well-instrumented; risk of premature transformation |
| Forming + quench | \(\mathcal{G}_{\text{evol}}\), coupled | evolution | Contact-dependent cooling → spatially varying transformation. **Requires Tier II** |
| In-die sensing | assimilation update | readout (\(H\)) | Updates \(\mu_{k|k}\) |
| Constitutive extraction | \(\mathcal{R}_{\text{const}}\) | **Type-1** | Yields \(\mathcal{C}\) carrying \(z\) |
| Hardness / tensile | \(\rho_0\) | Type-0, Class A | Property |
| Bend angle | \(\rho_2\) | **Type-2, Class B** | Performance; outer-fibre process zone |
| Crash intrusion | \(\rho_2\) | Type-2 | Performance; consumes \(\mathcal{C}\) and geometry |
| Adhesion / environmental cracking | \(\rho_2\) | Type-2, Class B | Governed by \(\Gamma\); extreme-value over interfacial area |

Two observations. The near-erasure means the upstream chain need not be modelled to high fidelity for most downstream responses — but *does* matter for exactly those that survive it, which are the ones causing field problems. And **three of the four commercially decisive responses are Type-2 performances; two are Class B.** A single-tier, RVE-based framework addresses none of them properly.

### 7.2 Contrast: an electrochemical cell under service

*Selected because it inverts the flagship.* Each inversion tests a different structural claim. Full declaration in **→ Spec §11.2**.

| Feature | Flagship | Contrast | Claim tested |
|---|---|---|---|
| Erasure operators | several, strong | **none** | error-control dichotomy (§3.9) |
| Observation suite | rich, multi-modal | terminal current, voltage, surface temperature | observability triage under genuine poverty (§3.8) |
| Dominant slot | \(m\), \(z\) | **\(\Gamma\)** | that \(\Gamma\) is structural, not cosmetic (§3.1) |
| Control axis | apparatus-controlled | **usage-determined** | control inverse as *usage* inverse (§5) |
| Tier structure | two | three (electrode → cell → pack) | tier recursion (§2.4) |
| Class B | edge and interface cracking | initiation-controlled plating and dendrite events | tail machinery in a second physics (§3.6) |
| Nonlocal slot \(\nu\) | residual stress | potential and concentration overpotential | \(\nu\) as a general slot, not a mechanical one (§3.1) |

The absence of erasure is the load-bearing inversion. It forces the framework to state where error control comes from when the physics does not supply it — the answer being continuous assimilation from telemetry, which is exactly what condition (b) of the dichotomy predicts.

### 7.3 What the contrast establishes

Two instantiations that behave identically prove nothing. These behave oppositely on six of seven interface items while remaining subject to the same results, which is the available evidence that the framework's *structure*, rather than its originating domain, is doing the work. **[Pass D]** — a third and fourth short sketch, interface-only, to test that the interface is fillable outside both.

---

## 8. Positioning against prior art

**[Pass D]** — carried from v1.2 and to be extended with the general lineage. Retained entries: Materials Knowledge Systems (Kalidindi, Fullwood, Niezgoda) as nearest neighbour, better suited to well-posed self-averaging linkages with good imaging data; hierarchical systems design and ICME as the goal-oriented inverse-design tradition to which OMI supplies substrate rather than philosophy; internal-state-variable constitutive theory as the tradition whose central hypothesis Axiom S generalises; data assimilation (Evensen; Law–Stuart–Zygalakis), where the contribution is the identification of observation operator with readout operator; Mori–Zwanzig and optimal prediction (Chorin, Hald, Kupferman) for the closure formalism; neural operator theory (Lu et al.; Li et al.; Kovachki, Lanthaler, Mishra) as approximation class, cited with its caveats; statistical volume elements and bounds (Hill; Ostoja-Starzewski; Torquato).

To be added: hybrid dynamical systems and hybrid automata; structural reliability and rare-event simulation, which supply §3.6's tail machinery; optimal experimental design and sensor placement, which supply §3.8's value-of-information calculation; causal inference under closed-loop control (→ Spec §5.3); and system identification, whose observability apparatus §3.8 borrows directly.

---

## Appendix A — Notation

| Symbol | Meaning |
|---|---|
| \(s = (m, z, \nu, \Gamma)\) | State: resolved fields, sub-resolution internal variables, nonlocal field, interface state |
| \(\mathcal{S}\), \(d_\mathcal{S}\) | State space and its metric |
| \(\mathfrak{F}\), \(\mathcal{Z}\) | Space of resolved fields; of internal variables |
| \(\mathscr{P}(\mathcal{S})\) | Probability measures on \(\mathcal{S}\); home of ensembles and SVE populations |
| \(\mathcal{U}\), \(\mathcal{U}_{\text{adm}}\), \(u\) | Control space; admissible subset; a control programme |
| \(\mathcal{Y}\), \(\mathcal{R}\) | Observation space; response space |
| \(\mathfrak{B} = (\Omega, \partial\Omega\text{-data})\) | Component geometry and boundary conditions (Tier II) |
| \(\mathcal{G}_{\text{evol}}\), \(K_k\) | Evolution operator; its Markov-kernel lift |
| \(\mathcal{E}\) | Erasure operator: strongly contractive, dimension-collapsing evolution |
| \(q \in Q\) | Discrete mode label (hybrid structure) |
| \(\rho_0,\ \mathcal{R}_{\text{const}},\ \rho_2\) | Type-0 functional, Type-1 operator-valued, Type-2 component readouts |
| \(\mathcal{C}\) | Constitutive operator returned by a Type-1 readout |
| \(H\) | Observation operator — identically a Type-0 readout |
| \(\Pi_\lambda\), \(\mathcal{D}_\lambda\) | Coarse-graining projection at scale \(\lambda\); its closure defect |
| \(\mathcal{M}_{\text{real}}\), \(\mathcal{M}_{\text{reach}}\) | Realistic states; reachable subset given the apparatus |
| \(\mathcal{U}_{\text{trust}}\) | Trust region where the surrogate is calibrated |
| \(V\), \(V_0\), \(N_{\text{eff}}\) | Driven (process-zone) volume; elementary sub-volume; effective independent count |
| Class A / Class B | Self-averaging / extreme-value readouts |
| \(L_{\text{phys}}\), \(L_{\text{num}}\) | Physical and numerical components of the amplification factor |

## Appendix B — Glossary: general ↔ domain terms

**[Pass A, in progress]** — populated as the domain purge proceeds. Current entries:

| General term (Core) | Flagship instance | Contrast instance |
|---|---|---|
| production unit | coil | cell |
| provenance group | heat, campaign | manufacturing lot |
| apparatus | processing line | charger / duty profile |
| composition family | alloy family | chemistry platform |
| erasure operator | austenitisation, recrystallisation, solutionising | *(none)* |
| imaging modality | EBSD, APT | tomography, cross-sectional microscopy |
| in-line modality | pyrometry, EM sensing, force and torque | terminal current, voltage, surface temperature |
| interface state \(\Gamma\) | coating, oxide, sheared edge | SEI, CEI, collector interface |
| nonlocal field \(\nu\) | residual stress | potential, concentration overpotential |
| process-zone volume | outer fibre under plunger; sheared edge | separator-adjacent electrode surface |

## Appendix C — Summary of structural claims

1. Markovianity is a property of the chosen state space, not of the matter (§2.1).
2. **State selection is a measurable bias–variance trade-off, not a judgement call (§2.2).**
3. Fusion is not a primitive; it is filtering built from evolution and readout (§3.8).
4. The observation operator of data assimilation and the readout operator of the PSR graph are the same object (§3.8).
5. Properties are functionals of the constitutive operator; performances require geometry (§2.6, §3.5).
6. No RVE exists for weakest-link readouts; volume scaling must appear in the readout signature (§3.6).
7. Class B readouts couple the material and component tiers through the process-zone volume (§3.6).
8. Coarse-graining does not commute with evolution; the defect must be measured (§3.7).
9. Error accumulation is bounded by the erasure structure of the chain, not its length (§3.9).
10. **Composability requires erasure or observation; a domain with neither is out of scope (§3.9).**
11. **Where amplification is physical rather than numerical, rollout is the wrong tool and the framework refuses (§3.9).**
12. For inverse design, hard constraints dominate soft penalties, because the optimiser is an adversary (§5).
13. Inverse problems are constrained optimal control; control inverse and structure inverse are distinct; solutions are sets (§5).
14. **A domain enters the framework by declaration, through a seven-item interface (§4).**

## Appendix D — Pointer index to the Implementation Specification

| Core claim | Spec procedure |
|---|---|
| §2.1 sufficiency test | Spec §8 — campaign design, pair selection, power analysis |
| §2.2 state selection | Spec §1 — estimators, stopping rule, demonstration |
| §3.3 semigroup consistency | Spec §9.2 — automated residual check |
| §3.4 hybrid structure | Spec §5.1 — guards, type safety, jump/erasure interaction |
| §2.5 body-indexed state | Spec §5.2 — coupling, registration operator |
| §3.6 Class B tails | Spec §4 — driver/tail separation, rare-event sampling, \(N_{\text{eff}}\), validation |
| §3.7 closure defect | Spec §6 — measurement, expected magnitudes by scheme |
| §3.8 observability triage | Spec §3 — construction, triage, value of information |
| §3.8 innovations monitoring | Spec §10 — drift detection, recalibration, lifecycle |
| §3.9 expansive regimes | Spec §2 — Lipschitz decomposition, error budget, refusal criterion |
| §5.1 apparatus parameterisation | Spec §7.2 — constraint manifold construction |
| §5.3 reachability certificates | Spec §7.1 — invariant-based certificate construction |
| §5 decision layer | Spec §7.3 — conformance probability, cost asymmetry, budget allocation |
| §6.1 falsification thresholds | Spec §9.4 — threshold-setting procedure |
| §7 instantiations | Spec §11 — full seven-item declarations |
| — | Spec §5.3 — data reality, closed-loop confounding, grouped splits |
| — | Spec §9 — conformance levels OMI-0/1/2, test suite, baselines |
