"""Pin BLAS/OpenMP to one thread for the sweep drivers.

Seeded campaigns are reproducible only at a fixed BLAS thread count and fixed
library versions: threaded reductions change floating-point results in the
last digits, and over 40 sequential runs that can flip a recommendation (0.4
memo, section 5). Each driver imports this module before numpy, so the setting
also holds in its worker processes. With two or more workers, one thread per
process is also faster here.

``environment()`` reports what was in effect, so summaries record the
conditions under which they reproduce.
"""
from __future__ import annotations

import os

THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
for _v in THREAD_VARS:
    os.environ.setdefault(_v, "1")


def environment() -> dict:
    import numpy
    import scipy
    import sklearn
    from threadpoolctl import threadpool_info
    return {"blas_threads": sorted({p["num_threads"] for p in threadpool_info()}),
            "env": {v: os.environ.get(v) for v in THREAD_VARS},
            "numpy": numpy.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__}
