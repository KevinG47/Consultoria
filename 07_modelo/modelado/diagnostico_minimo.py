# -*- coding: utf-8 -*-
"""Diagnostico post-hoc (solo lectura) del trace minimo. No reajusta nada."""
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
_CACHE_DIR = SCRIPT_DIR.parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)
os.environ["LOCALAPPDATA"] = str(_CACHE_DIR)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_DIR / "matplotlib"))
os.environ.setdefault("PYTENSOR_FLAGS", "cxx=,base_compiledir="
                      + str(Path(os.environ.get("TEMP", ".")) / "dsh_bayes" / "pytensor").replace("\\", "/"))

try:  # ArviZ usa platformdirs: redirigir su cache ANTES de importar arviz
    import platformdirs as _pd
    _orig = _pd.user_cache_dir

    def _uc(appname=None, appauthor=None, version=None, roaming=False):
        if appname == "arviz":
            return str(_CACHE_DIR / "arviz")
        return _orig(appname, appauthor, version, roaming)

    _pd.user_cache_dir = _uc
except Exception:
    pass

import numpy as np  # noqa: E402
import arviz as az  # noqa: E402

tr = SCRIPT_DIR / "modelos" / "trace_bayesiano_minimo.nc"
idata = az.from_netcdf(tr)
print("grupos:", list(idata.groups()))
print("\n--- resumen por variable (r_hat, ess bulk/tail) ---")
res = az.summary(idata, var_names=["beta", "kappa1", "kappa2", "sigma_u",
                                   "sigma_v", "u", "v"],
                 kind="diagnostics", round_to=4)
print(res.to_string())

print("\n--- divergencias por cadena ---")
div = idata.sample_stats["diverging"].to_numpy()  # (chain, draw)
for c in range(div.shape[0]):
    print(f"  cadena {c}: {int(div[c].sum())} / {div.shape[1]}")
draws = np.where(div.any(axis=0))[0]
print("  draws con divergencia:", draws.tolist())
print("\n--- step size y tree depth ---")
for k in ("step_size", "tree_depth", "n_steps"):
    if k in idata.sample_stats:
        arr = idata.sample_stats[k].to_numpy()
        print(f"  {k}: media {float(np.mean(arr)):.4f} | max {float(np.max(arr)):.4f}")
print("\n--- energia ---")
if "energy" in idata.sample_stats:
    e = idata.sample_stats["energy"].to_numpy()
    print(f"  BFMI por cadena: {[round(float(v), 4) for v in az.bfmi(idata)]}")
print("\n--- betas (media posterior) ---")
for i, b in enumerate(idata.posterior["beta"].mean(("chain", "draw")).to_numpy()):
    print(f"  beta[{i}] = {float(b):+.4f}")
print(f"  kappa1 = {float(idata.posterior['kappa1'].mean()):+.4f} | "
      f"kappa2 = {float(idata.posterior['kappa2'].mean()):+.4f}")
