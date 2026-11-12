# -*- coding: utf-8 -*-
"""
B① 主稿 · 只读诊断：病种特异供应份额 s 的口径校验（2026-11-11）

背景：审查结论指出 compute_B_uncertainty_2026-11-11.py 的 RQ2 错位指数把
「648 行全领域 FPP 国别分布」当作三个病种各自的供应份额 s，属对象错配。
修正口径：按 Therapeutic Area × Applicant 逐行 join 出病种特异的持证商国分布。

本脚本只读取 raw/ 与既有 res_B_anchor_*，不写任何结果文件，用于独立复现
审查方给出的交叉校验基准：
  匹配率        疟疾 98/98、HIV 255/255、结核 126/126（零未匹配）
  M(病种特异 s) 疟疾 1.9118、结核 1.3983、HIV 1.9760
  前25%高负担国供应份额(修正) 疟疾 6.12%、结核 90.48%、HIV 0.78%
  病种特异持证商分布 疟疾 IND 53.1%/CHN 24.5%；HIV IND 75.7%；TB IND 84.9%

口径与负担权重构造严格复制 compute_B_uncertainty_2026-11-11.py 的 D 段，
唯一差别是 s 由「全领域常量」换成「按治疗领域重建」。
"""
import csv, os, collections
import numpy as np

ROOT = r"D:\D\我的论文\全球卫生新博士课题\数据"
RAW = os.path.join(ROOT, "raw")
PROC = os.path.join(ROOT, "processed")

AGG = {
    "AFE", "AFW", "ARB", "CSS", "EAS", "ECS", "EMU", "EUU", "FCS", "HIC",
    "HPC", "IBD", "IBT", "IDA", "IDB", "IDX", "LAC", "LCN", "LDC", "LIC",
    "LMC", "LMY", "LTE", "MEA", "MIC", "MNA", "NAF", "NAC", "OED", "OSS",
    "PRE", "PSS", "PST", "SAS", "SSA", "SSF", "SST", "TEA", "TEC", "TLA",
    "TMN", "TSA", "TSS", "UMC", "WLD", "EAR", "EAP", "ECA", "MENA",
    "LMIC", "LIC", "LMC", "UMC",
}

ISO2_TO_ISO3 = {
    "IN": "IND", "CN": "CHN", "CH": "CHE", "GB": "GBR", "DE": "DEU",
    "US": "USA", "ES": "ESP", "NL": "NLD", "KR": "KOR", "RO": "ROU",
    "FR": "FRA", "PK": "PAK", "BD": "BGD", "SE": "SWE", "AT": "AUT",
    "LV": "LVA", "DK": "DNK", "BE": "BEL", "UA": "UKR", "ID": "IDN",
    "IE": "IRL", "EG": "EGY", "IT": "ITA", "NG": "NGA", "PT": "PRT",
    "JP": "JPN", "CA": "CAN", "UG": "UGA", "ZA": "ZAF",
}
ISO3_TO_ISO2 = {v: k for k, v in ISO2_TO_ISO3.items()}
ALL_ISO3 = set(ISO2_TO_ISO3.values())


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def tidy(path, exclude_agg=True):
    out = collections.defaultdict(dict)
    for r in read(path):
        iso = (r["iso3"] or "").strip()
        if exclude_agg and iso in AGG:
            continue
        try:
            y, v = int(r["year"]), float(r["value"])
        except (ValueError, TypeError):
            continue
        out[iso][y] = v
    return out


def pop_at(pop, iso, year):
    d = pop.get(iso, {})
    if not d:
        return None
    if year in d:
        return d[year]
    cand = [y for y in d if y <= year]
    return d[max(cand)] if cand else d[min(d)]


def build_burden(burden, mode, pop, drop_second_latest=False):
    """复制主脚本 D 段：各国取最新可得年（或次最新），构成归一化负担份额 b。"""
    w, years_used = {}, []
    for iso, series in burden.items():
        ys = sorted(series)
        if not ys:
            continue
        y = ys[-2] if (drop_second_latest and len(ys) >= 2) else ys[-1]
        val = series[y]
        if val is None or val < 0:
            continue
        if mode == "rate_x_pop":
            p = pop_at(pop, iso, min(y, 2023))
            if p is None or p <= 0:
                continue
            weight = val * p
        else:
            weight = val
        if weight <= 0:
            continue
        w[iso] = weight
        years_used.append(y)
    if not w:
        return None
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}, years_used


def M_and_top(bvec, svec, universe):
    """M=Σ|s−b|；前25%高负担国家的 b 份额与 s 份额。"""
    s = np.array([svec.get(iso, 0.0) for iso in universe], dtype=float)
    b = np.array([bvec.get(iso, 0.0) for iso in universe], dtype=float)
    M = float(np.abs(s - b).sum())
    order = np.argsort(b)[::-1]
    k = max(1, int(np.ceil(0.25 * len(universe))))
    return M, float(b[order[:k]].sum()), float(s[order[:k]].sum())


print("=" * 78)
print("STEP 1  构造 applicant → iso2 → iso3 映射")
print("=" * 78)
mp = read(os.path.join(PROC, "res_B_anchor_applicant_country_reviewed.csv"))
app2iso2 = {}
for r in mp:
    a = (r.get("applicant") or "").strip()
    i2 = (r.get("iso3") or "").strip()   # 该列实为 ISO2
    if a and i2:
        app2iso2[a] = i2
print(f"  applicant_country_reviewed 行数 = {len(mp)}，唯一 applicant = {len(app2iso2)}")
print(f"  n_products 合计 = {sum(int(r['n_products']) for r in mp)}")
print(f"  映射 iso2 全部落在 29 国表内 = {set(app2iso2.values()) <= set(ISO2_TO_ISO3)}")
if not (set(app2iso2.values()) <= set(ISO2_TO_ISO3)):
    print("  !! 越出国别码表：", sorted(set(app2iso2.values()) - set(ISO2_TO_ISO3)))

print()
print("=" * 78)
print("STEP 2  FPP 逐行按 Therapeutic Area × Applicant 建病种特异供应分布")
print("=" * 78)
fpp = read(os.path.join(RAW, "who_pq_fpp_2026-09-15.csv"))
ta_all = collections.Counter((r.get("Therapeutic Area") or "").strip() for r in fpp)
print(f"  FPP 数据行 = {len(fpp)}")
print("  Therapeutic Area 全量分布：")
for ta, n in ta_all.most_common():
    print(f"    {ta!r:34s} {n:4d}")

AREAS = ["Malaria", "HIV/AIDS", "Tuberculosis"]
by_ta = collections.defaultdict(list)
for r in fpp:
    by_ta[(r.get("Therapeutic Area") or "").strip()].append(r)

supply_by_area = {}
for ta in AREAS:
    rows = by_ta.get(ta, [])
    cnt = collections.Counter()
    unmatched = []
    for r in rows:
        a = (r.get("Applicant") or "").strip()
        i2 = app2iso2.get(a)
        if i2 is None or i2 not in ISO2_TO_ISO3:
            unmatched.append(a)
            continue
        cnt[ISO2_TO_ISO3[i2]] += 1
    matched = sum(cnt.values())
    total_area = len(rows)
    supply_by_area[ta] = {k: v / matched for k, v in cnt.items()} if matched else {}
    print(f"\n  [{ta}] 领域产品行 = {total_area}，匹配 = {matched}，"
          f"未匹配 = {len(unmatched)}  匹配率 = {matched}/{total_area}")
    if unmatched:
        print("    未匹配 applicant（去重）：", sorted(set(unmatched))[:12])
    top = sorted(cnt.items(), key=lambda z: -z[1])[:6]
    print("    持证商国分布 top6：",
          ", ".join(f"{ISO3_TO_ISO2.get(k, k)}={100*v/matched:.2f}%" for k, v in top))
    print(f"    IND = {100*cnt.get('IND',0)/matched:.2f}%   "
          f"CHN = {100*cnt.get('CHN',0)/matched:.2f}%   "
          f"持证商国数 = {len(cnt)}")

print()
print("=" * 78)
print("STEP 3  全领域（旧口径）s 对照")
print("=" * 78)
rev = read(os.path.join(PROC, "res_B_anchor_concentration_reviewed.csv"))
raw_supply = {r["iso3"]: int(r["product_rows"]) for r in rev}
N = int(sum(raw_supply.values()))
supply_all = {ISO2_TO_ISO3[k]: v / N for k, v in raw_supply.items()}
print(f"  分母 N = {N}；IND = {100*supply_all.get('IND',0):.2f}%   "
      f"CHN = {100*supply_all.get('CHN',0):.2f}%")

print()
print("=" * 78)
print("STEP 4  复现 M（病种特异 s）与交叉校验基准")
print("=" * 78)
pop = tidy(os.path.join(RAW, "wb_pop.csv"))
gho = {
    "Malaria": (tidy(os.path.join(RAW, "gho_mal_inc.csv")), "rate_x_pop"),
    "Tuberculosis": (tidy(os.path.join(RAW, "gho_tb_inc.csv")), "rate_x_pop"),
    "HIV/AIDS": (tidy(os.path.join(RAW, "gho_hiv_pl.csv")), "count"),
}
BENCH = {
    "Malaria": dict(M_old=1.9489, M_new=1.9118, s_old=0.0154, s_new=0.0612),
    "Tuberculosis": dict(M_old=1.2241, M_new=1.3983, s_old=0.7731, s_new=0.9048),
    "HIV/AIDS": dict(M_old=1.9344, M_new=1.9760, s_old=0.0448, s_new=0.0078),
}
print(f"  {'病种':14s} {'旧M':>8s} {'新M':>8s} {'前25%b':>9s} "
      f"{'旧s':>8s} {'新s':>8s}  {'基准新M':>8s} {'基准新s':>8s}")
for disease, (burden, mode) in gho.items():
    res = build_burden(burden, mode, pop)
    bvec, years_used = res
    universe = sorted(set(bvec) | ALL_ISO3)
    M_old, top_b, top_s_old = M_and_top(bvec, supply_all, universe)
    M_new, _, top_s_new = M_and_top(bvec, supply_by_area[disease], universe)
    bm = BENCH[disease]
    print(f"  {disease:14s} {M_old:8.4f} {M_new:8.4f} {top_b:9.4f} "
          f"{top_s_old:8.4f} {top_s_new:8.4f}  {bm['M_new']:8.4f} {bm['s_new']:8.4f}"
          f"   |ΔM|={abs(M_new-bm['M_new']):.4f} |Δs|={abs(top_s_new-bm['s_new']):.4f}")

print()
print("=" * 78)
print("判定：STEP 4 的 |ΔM| 与 |Δs| 若 ≤0.001，则病种特异 s 的构造口径与审查基准一致，")
print("      可据此修订 compute_B_uncertainty_2026-11-11.py 的 D 段并落正式派生文件。")
print("本脚本全程只读，未写入任何文件。")
print("=" * 78)
