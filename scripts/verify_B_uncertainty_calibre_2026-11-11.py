# -*- coding: utf-8 -*-
"""
B① 主稿 · 不确定度补算前的口径自检（2026-11-11）

用途：确认派生 CI 与既有已验证数字同口径，不改动任何既有 CSV。
检查项：
  1. FPP 清单行数、治疗领域分母（中国 PQ 广度的分母来源）
  2. 复核后国别份额分母、HHI 4073.8 的可复现口径
  3. 中国 52 条 PQ 产品的治疗领域分布
  4. AAPC 19.11/24.85/14.75/18.28 的对数线性回归复现
  5. GHO/WB 负担侧国家数、年份范围与区域聚合码
输出：仅打印；不写文件。
"""
import csv, math, collections, os, re

ROOT = r"D:\D\我的论文\全球卫生新博士课题\数据"
RAW = os.path.join(ROOT, "raw")
PROC = os.path.join(ROOT, "processed")


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def aapc_from_cumulative(rows, col):
    """严格复刻 anchor_B_feasibility_2026-11-07.py 的 aapc()：log(累积) ~ year 的 OLS 斜率。"""
    xs, ys = [], []
    for r in rows:
        xs.append(int(r["year"]))
        c = float(r[col])
        ys.append(math.log(c) if c > 0 else 0.0)
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return (math.exp(b) - 1) * 100, b, xs, ys


print("=" * 72)
print("1. FPP 清单与治疗领域分母")
fpp = read(os.path.join(RAW, "who_pq_fpp_2026-09-15.csv"))
print("   FPP 数据行数 =", len(fpp))
ta = collections.Counter((r["Therapeutic Area"] or "").strip() for r in fpp)
for k, v in ta.most_common(12):
    print(f"   {k!r}: {v}")
years = []
for r in fpp:
    m = re.search(r"(19|20)\d{2}", (r["Date of Prequalification"] or ""))
    if m:
        years.append(int(m.group(0)))
print("   可解析获证年 =", len(years), " 范围 =", min(years), max(years))

print("=" * 72)
print("2. 复核后国别份额与 HHI 口径")
rev = read(os.path.join(PROC, "res_B_anchor_concentration_reviewed.csv"))
tot = sum(int(r["product_rows"]) for r in rev)
print("   国别数 =", len(rev), " product_rows 合计 =", tot)
hhi_rounded = sum(float(r["share_pct"]) ** 2 for r in rev)
hhi_exact = sum((100.0 * int(r["product_rows"]) / tot) ** 2 for r in rev)
hhi_649 = sum((100.0 * int(r["product_rows"]) / 649) ** 2 for r in rev)
print("   HHI(用已四舍五入 share_pct 平方和) =", round(hhi_rounded, 2))
print("   HHI(用 product_rows/648 精确份额)   =", round(hhi_exact, 2))
print("   HHI(用 product_rows/649 精确份额)   =", round(hhi_649, 2))
pre = read(os.path.join(PROC, "res_B_anchor_concentration.csv"))
print("   复核前 concentration.csv 末两行 =", pre[-2:])
print("   复核前 countries 行数 =", len(pre) - 1)

print("=" * 72)
print("3. 中国 PQ 广度（res_B_china_pq_breadth_input.csv）")
cn = read(os.path.join(PROC, "res_B_china_pq_breadth_input.csv"))
print("   中国产品行数 =", len(cn))
cnta = collections.Counter((r["therapeutic_area"] or "").strip() for r in cn)
for k, v in cnta.most_common():
    print(f"   {k!r}: {v}")

print("=" * 72)
print("4. AAPC 复现（res_B_anchor_year_counts.csv，25 行）")
yc = read(os.path.join(PROC, "res_B_anchor_year_counts.csv"))
print("   逐年行数 =", len(yc), " year 范围 =", yc[0]["year"], yc[-1]["year"])
for col, name in [("cumulative_pq_products", "ALL_FPP"),
                  ("cumulative_malaria", "Malaria"),
                  ("cumulative_hiv", "HIV/AIDS"),
                  ("cumulative_tb", "Tuberculosis")]:
    a, b, xs, ys = aapc_from_cumulative(yc, col)
    print(f"   {name:12s} 复现 AAPC = {a:.4f}  (登记值见 res_B_anchor_apc.csv)  b={b:.8f}")
print("   首末累积：", {c: (yc[0][c], yc[-1][c]) for c in
                      ["cumulative_pq_products", "cumulative_malaria",
                       "cumulative_hiv", "cumulative_tb"]})

print("=" * 72)
print("5. 负担侧 GHO / WB 覆盖")
AGG = {"AFE", "AFW", "ARB", "CSS", "EAS", "ECS", "EMU", "EUU", "FCS", "HIC",
       "HPC", "IBD", "IBT", "IDA", "IDB", "IDX", "LAC", "LCN", "LDC", "LIC",
       "LMC", "LMY", "LTE", "MEA", "MIC", "MNA", "NAF", "NAC", "OED", "OSS",
       "PRE", "PSS", "PST", "SAS", "SSA", "SSF", "SST", "TEA", "TEC", "TLA",
       "TMN", "TSA", "TSS", "UMC", "WLD", "EAR", "EAP", "ECA", "LAC", "MENA",
       "SAS", "SSA", "HIC", "LIC", "LMC", "UMC", "LMIC"}
for f in ["gho_mal_inc.csv", "gho_hiv_pl.csv", "gho_tb_inc.csv",
          "gho_uhc.csv", "wb_pop.csv", "wb_gdp_pc.csv", "wb_che_pc.csv"]:
    d = read(os.path.join(RAW, f))
    yrs = [int(r["year"]) for r in d if r["year"].strip().isdigit()]
    isos = set(r["iso3"] for r in d)
    print(f"   {f:22s} 行={len(d):5d} 国家码={len(isos):4d} "
          f"年份={min(yrs)}–{max(yrs)} 聚合码={len(isos & AGG)}")

print("=" * 72)
print("6. 国别映射置信度分布")
mp = read(os.path.join(PROC, "res_B_anchor_applicant_country_reviewed.csv"))
print("   映射表行数 =", len(mp), " 列 =", list(mp[0].keys()))
conf = collections.Counter((r.get("confidence") or "").strip() for r in mp)
print("   confidence 分布 =", dict(conf))
print("   is_china=yes 行数 =", sum(1 for r in mp if (r.get("is_china") or "").strip() == "yes"))
print("=" * 72)
