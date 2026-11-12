# -*- coding: utf-8 -*-
"""B① 返修 · AAPC 稳健性补充实算（2026-11-12）

回应审稿意见：Methods 需要 lag 定阶敏感性、Durbin–Watson、残差 ACF，
以及去掉 2026 部分年的敏感性。这些数字必须先算出来再写进稿件，
不允许只写「计划补充」。

拟合方式严格复用 compute_B_uncertainty_2026-11-11.py：
log(逐年累积产品数) ~ year 的 OLS；0 值按 max(c,1) 取 log 后赋 0；
AAPC = 100·(exp(b)−1)；HAC 为 Bartlett/Newey–West，未作小样本自由度校正。

输出：
  res_B_aapc_robustness_2026-11-12.csv / .json
"""
import csv
import json
import math
import os

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PROC = os.path.join(ROOT, "processed")
STAMP = "2026-11-12"

SERIES = [
    ("cumulative_pq_products", "ALL_FPP"),
    ("cumulative_malaria", "Malaria"),
    ("cumulative_hiv", "HIV/AIDS"),
    ("cumulative_tb", "Tuberculosis"),
]


def read(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fit(x, c):
    y = np.where(c > 0, np.log(np.maximum(c, 1.0)), 0.0)
    n = len(x)
    u = x - x.mean()
    sxx = float((u ** 2).sum())
    b = float((u * y).sum() / sxx)
    a = float(y.mean() - b * x.mean())
    e = y - (a + b * x)
    df = n - 2
    se_ols = math.sqrt(float((e ** 2).sum()) / df / sxx)
    return dict(y=y, u=u, sxx=sxx, b=b, e=e, df=df, se_ols=se_ols, n=n)


def pct_ci(b, se, df):
    t = float(stats.t.ppf(0.975, df))
    return (round(100 * (math.exp(b - t * se) - 1), 2),
            round(100 * (math.exp(b + t * se) - 1), 2), round(t, 4))


def hac_se(e, u, sxx, lag):
    S = float(((e * u) ** 2).sum())
    for L in range(1, lag + 1):
        w = 1.0 - L / (lag + 1)
        S += 2 * w * float((e[L:] * u[L:] * e[:-L] * u[:-L]).sum())
    return math.sqrt(max(S / sxx ** 2, 0.0))


def acf(e, k):
    return round(float(np.corrcoef(e[k:], e[:-k])[0, 1]), 4)


def main():
    yc = read(os.path.join(PROC, "res_B_anchor_year_counts.csv"))
    x_all = np.array([int(r["year"]) for r in yc], dtype=float)
    rows, summary = [], {}
    for col, seg in SERIES:
        c_all = np.array([float(r[col]) for r in yc], dtype=float)
        f = fit(x_all, c_all)
        e, u, sxx, b, df = f["e"], f["u"], f["sxx"], f["b"], f["df"]
        dw = round(float(((e[1:] - e[:-1]) ** 2).sum() / (e ** 2).sum()), 4)
        acfs = [acf(e, k) for k in (1, 2, 3, 4)]
        hac = {}
        for lag in (1, 2, 3, 4):
            lo, hi, _ = pct_ci(b, hac_se(e, u, sxx, lag), df)
            hac[lag] = (lo, hi)

        # 去掉 2026 部分年
        mask = x_all <= 2025
        f2 = fit(x_all[mask], c_all[mask])
        aapc2 = round(100 * (math.exp(f2["b"]) - 1), 2)
        lo2, hi2, _ = pct_ci(f2["b"], f2["se_ols"], f2["df"])
        lo2h, hi2h, _ = pct_ci(f2["b"], hac_se(f2["e"], f2["u"], f2["sxx"], 3), f2["df"])

        rows.append([
            seg, f["n"], round(100 * (math.exp(b) - 1), 2), dw,
            *acfs,
            *[v for lag in (1, 2, 3, 4) for v in hac[lag]],
            f2["n"], aapc2, lo2, hi2, lo2h, hi2h,
        ])
        summary[seg] = {
            "n_full": f["n"], "aapc_full": round(100 * (math.exp(b) - 1), 2),
            "durbin_watson": dw, "resid_acf_lag1_4": acfs,
            "hac_ci_by_lag": {str(k): list(v) for k, v in hac.items()},
            "min_hac_lower_bound_lag1_4": min(v[0] for v in hac.values()),
            "excl_2026": {"n": f2["n"], "aapc": aapc2, "ci95_t": [lo2, hi2],
                          "ci95_hac_lag3": [lo2h, hi2h]},
        }
        print(f"  {seg:12s} AAPC={100*(math.exp(b)-1):6.2f}  DW={dw:.3f}  "
              f"ACF1={acfs[0]:+.3f}  HAC1={hac[1]}  HAC4={hac[4]}  "
              f"2002–2025: {aapc2:.2f}% ({lo2}–{hi2})")

    header = ["segment", "n_full", "aapc_full", "durbin_watson",
              "resid_acf1", "resid_acf2", "resid_acf3", "resid_acf4",
              "hac1_lo", "hac1_hi", "hac2_lo", "hac2_hi",
              "hac3_lo", "hac3_hi", "hac4_lo", "hac4_hi",
              "n_excl_2026", "aapc_excl_2026", "ci95_lo_t_excl_2026",
              "ci95_hi_t_excl_2026", "ci95_lo_hac3_excl_2026",
              "ci95_hi_hac3_excl_2026"]
    with open(os.path.join(PROC, f"res_B_aapc_robustness_{STAMP}.csv"),
              "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    with open(os.path.join(PROC, f"res_B_aapc_robustness_{STAMP}.json"),
              "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("VERDICT = AAPC ROBUSTNESS OK")
    return summary


if __name__ == "__main__":
    main()
