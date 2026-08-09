"""Part 6's **pre-registered** thresholds and the third arm's calibrated inflation factor.

Committed in its own commit, **before any sweep code exists**, so the ordering is visible in
`git log` rather than asserted in a report — ADR-045's requirement, and M11.4/M11.5's precedent.
The reasoning for every value is `docs/V1.5-PART6-PREREGISTRATION.md`; this module is the
machine-readable copy the sweep will import, so a value cannot drift between the document and
the run.

Nothing here is computed at import time. Every number was measured by
`scripts/run_v15_part6_preregistration.py` at this commit and pasted in, which is what makes
"pre-registered" a checkable property of the git history rather than a claim.
"""

from __future__ import annotations

NULL_Z_MEAN = 0.926
"""Measured mean of `z_n` over 40 null campaigns at 32 samples. Reference: `E|Z| = 0.798`."""

NULL_Z_Q95 = 2.213
"""Measured 95th percentile of the same. Reference: `|Z|` 95th percentile `= 1.960`."""

CONTROL_LIMIT = NULL_Z_Q95
"""The monitor's declared control limit: the **measured** null quantile, not the normal one.

ADR-063 declares a standard-normal reference and the innovation spread matches the filter's own
prediction to `0.2%`, so `z_n` is genuinely standardised. But innovations within one campaign
are mildly correlated, putting the null distribution about 16% above `E|Z|`. Using `1.960` would
be anti-conservative **in the direction of the claim**, so the measured quantile is used and the
discrepancy is disclosed rather than absorbed."""

REQUIRED_SEPARATION = 2.0
"""Registered criterion 1: the framework statistic's separation of the insufficiency arm from
the **noise** arm, in noise-arm sigma units, at 32 samples.

Two nuisance-arm sigmas — the same "clearly above the scatter" bar Part 5(1)'s dry-run used, so
Part 5's and Part 6's gates read on one scale."""

REQUIRED_GROWTH = 2.0
"""Registered criterion 2: the same separation's growth between 8 and 32 samples.

Carried over unchanged from `tests/oracles/test_statistic_dry_run.py`. ADR-066's closed form
predicts `sqrt(32/8) = 2.000` under a constant bias, so this is the floor the statistic's own
arithmetic already guarantees rather than a bar chosen to be clearable."""

COMPARATOR_CEILING = 1.0
"""Registered criterion 3: the comparator "cannot attribute" only if its own separation on the
**registered** contrast is below one noise-arm sigma at 32 samples.

Below one sigma rather than below the framework's reading, because "the GP does worse" and "the
GP cannot" are different claims and only the second is registered."""

NOISE_INFLATION = 1.160
"""The third arm's observation-noise multiplier, solved so arm X's **innovation variance**
matches arm I's (ADR-066 as amended).

Measured at 24 declared seeds (`CALIBRATION_SEEDS`) disjoint from the sweep's: arm X's
innovation variance `0.0047533` against arm I's `0.0047509`, a match to `0.05%`. Innovation
variance is affine in the squared inflation, so two grid points determine the solution exactly
and no search is involved.

**Matched on a physical quantity, deliberately, and this replaced a circular first version.**
Calibrating instead on the *comparator's* fitted noise would set the numerator of the
comparator's separation to approximately zero, making criterion 3 true by construction. Matching
the innovation variance fixes neither instrument's reading: the framework statistic is a
function of the innovation *mean*, and the comparator's is a fitted noise level on a surface
over composition."""

CALIBRATION_INNOVATION_VARIANCE_INSUFFICIENT = 0.0047509
CALIBRATION_INNOVATION_VARIANCE_NOISY = 0.0047533
"""The two matched variances, recorded so the calibration can be checked without re-solving."""

CALIBRATION_SEEDS = tuple(range(2000, 2024))
"""Seeds used for the calibration. **Disjoint from the sweep's**, which will use `0 .. 23` for
the arms and `1000 ..` for the null-calibration replicates, so no campaign is shared between
setting a threshold and being judged by one."""

REGISTERED_CONTRAST = ("insufficient", "noisy")
"""The contrast the claim is registered on, named so a sweep cannot quietly evaluate a different
one. The precondition's own contrast — `("insufficient", "null")` — is already reported in
`docs/V1.5-PART6.md` §3 and is **not** what any criterion above is evaluated on."""
