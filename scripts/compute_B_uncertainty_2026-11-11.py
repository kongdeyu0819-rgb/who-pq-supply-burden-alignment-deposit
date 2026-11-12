# -*- coding: utf-8 -*-
"""
B① 主稿 · 描述性估计值的不确定度补算（2026-11-11；当日修订版）

授权范围（用户 2026-11-11）：补 AAPC 的 95% CI、HHI/国别份额的 bootstrap CI、
中国 PQ 广度的二项 CI、负担加权错位指数及其不确定性；重算 RQ2 错位指数。

【2026-11-11 修订记录】审查结论指出原 RQ2 把「648 行全领域 FPP 国别分布」
误作三个病种各自的供应份额 s（对象错配：L369/L373/L417 的 supply 为全局常量，
L447 循环三病种时从未按治疗领域重算）。本版改为按
Therapeutic Area × Applicant 逐行 join res_B_anchor_applicant_country_reviewed.csv
的 iso2，再经 ISO 3166-1 的 29 国码表转 iso3，在各病种内部按产品行数归一化；
旧口径仅作为留痕对照行，不进入正文。只读交叉校验见
verify_B_disease_specific_supply_2026-11-11.py（三病种 |ΔM|=0、|Δs|=0）。

同步按审查要求固定 Methods 口径：M 的统计含义与天花板、病种间不可比、
产品行级 bootstrap 为主不确定度、二项区间降为描述性构成区间、
HAC lag 与 n=25 的小样本局限须交代、M 与 D 同报并给公式、
AAPC 主口径 t 区间、RQ2 主口径为疟疾＋结核（HIV 仅补材）。

硬约束：
  - 只新增/更新 res_B_uncertainty_* 派生 CSV，不改动任何 res_B_anchor_* / dualchain_* 既有文件；
  - 既有已验证数字（19.11/24.85/14.75/18.28、413/52、24/98 等）一律不改写；HHI 登记值 4073.8 已于 2026-11-11 经用户裁定回填为 4175.53（95% CI 3737.94–4643.50），回填由独立脚本 apply_B_hhi_backfill_2026-11-11.py 执行，本脚本不改准备层文档；
  - 若发现既有登记值与取数底座不自洽，只记录并上报，不静默更正；
  - 不写正文 prose、不出投稿图。

口径复现自检见同目录 verify_B_uncertainty_calibre_2026-11-11.py。

输出（数据/processed/）：
  res_B_uncertainty_apc_ci_2026-11-11.csv
  res_B_uncertainty_concentration_ci_2026-11-11.csv
  res_B_uncertainty_country_share_ci_2026-11-11.csv
  res_B_uncertainty_china_breadth_ci_2026-11-11.csv
  res_B_uncertainty_supply_by_area_2026-11-11.csv
  res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv
  res_B_uncertainty_misalignment_by_country_revised_2026-11-11.csv
  res_B_uncertainty_summary_2026-11-11.json

文件名说明（2026-11-11 v1 归位后）：修订前两份不带 _revised 的结果为 v1 错误口径
（全领域 648 行 s），已归入 数据/processed/_archive_v1/ 并加 _v1_deprecated 后缀；
RQ2 权威文件名唯一为上面带 _revised 后缀的两份。其中
res_B_uncertainty_misalignment_ci_2026-11-11.csv 的原件亦已物理移入归档目录
（与既有副本逐字节一致）；processed 根不再保留任何不带 _revised 的错位结果。
正文、图表、补充材料一律只读 _revised 两份与 summary.json。

依赖：numpy, scipy（Python 3.13.14 / numpy 2.4.6 / scipy 1.18.0 实跑）
"""
import csv, json, math, os, collections
import numpy as np
from scipy import stats

ROOT = r"D:\D\我的论文\全球卫生新博士课题\数据"
RAW = os.path.join(ROOT, "raw")
PROC = os.path.join(ROOT, "processed")
STAMP = "2026-11-11"
SEED = 20261111
B_BOOT = 10000
B_BLOCK = 5000
BLOCK_LEN = 3
HAC_LAG = 3

rng = np.random.default_rng(SEED)

# World Bank / WHO 区域聚合码（须剔除；仅 WB 文件含此类码）
AGG = {
    "AFE", "AFW", "ARB", "CSS", "EAS", "ECS", "EMU", "EUU", "FCS", "HIC",
    "HPC", "IBD", "IBT", "IDA", "IDB", "IDX", "LAC", "LCN", "LDC", "LIC",
    "LMC", "LMY", "LTE", "MEA", "MIC", "MNA", "NAF", "NAC", "OED", "OSS",
    "PRE", "PSS", "PST", "SAS", "SSA", "SSF", "SST", "TEA", "TEC", "TLA",
    "TMN", "TSA", "TSS", "UMC", "WLD", "EAR", "EAP", "ECA", "MENA",
    "LMIC", "HIC", "LIC", "LMC", "UMC",
}

# res_B_anchor_concentration_reviewed.csv 的 iso3 列实际为 ISO 3166-1 alpha-2 两位码，
# 而 GHO / World Bank 原始数据为 alpha-3 三位码。两者不转换则供应份额与负担份额
# 的支持集完全不相交，Σ|s−b| 恒等于 2（退化值）。此处按 ISO 3166-1 显式映射 29 国。
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


def write(name, header, rows):
    path = os.path.join(PROC, name)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  -> {name}  ({len(rows)} 行)")


def pct_ci_from_slope(b, se, df):
    """把 log 尺度斜率 CI 变换回 AAPC 百分数尺度。"""
    t = stats.t.ppf(0.975, df)
    return 100 * (math.exp(b - t * se) - 1), 100 * (math.exp(b + t * se) - 1), t


def wilson(k, n, z=1.959963984540054):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def clopper_pearson(k, n):
    lo = 0.0 if k == 0 else stats.beta.ppf(0.025, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(0.975, k + 1, n - k)
    return lo, hi


summary = {"stamp": STAMP, "seed": SEED, "bootstrap_draws": B_BOOT,
           "block_bootstrap_draws": B_BLOCK, "block_len": BLOCK_LEN,
           "hac_lag": HAC_LAG, "notes": [],
           "revision_2026_11_11": {
               "trigger": "审查结论：RQ2 供应份额 s 用错对象（全领域 648 行当作病种特异）",
               "supply_scope": "disease_specific (Therapeutic Area x Applicant)",
               "cross_check_script": "verify_B_disease_specific_supply_2026-11-11.py",
               "cross_check": "三病种 M 与前25%份额基准 |Δ|=0；匹配率 98/98、255/255、126/126",
               "aapc_main_ci": "OLS t 区间进 Results；HAC/块自助进 Methods 与补充材料",
               "rq2_primary_diseases": ["Malaria", "Tuberculosis"],
               "hiv": "仅补充材料（GHO HIV 快照 2000–2006）",
               "index": "M 与 D 同报并给公式；另报 C 与 R25 两个有区分度的备择指标",
           }}

# =====================================================================
# A. AAPC 的 95% CI
#    点估计严格复用 anchor_B_feasibility_2026-11-07.py：
#    log(逐年累积产品数) ~ year 的 OLS 斜率 b，AAPC = (exp(b)-1)*100。
#    主口径 = 同一 OLS 的 t 区间；敏感性 = Newey-West HAC 区间 + 残差
#    moving-block bootstrap 区间（累积序列存在强自相关，naive OLS 区间偏窄）。
#    ⚠ Methods 须交代：HAC lag=3 为经验选择（未用数据驱动定阶），n=25 未作
#      小样本自由度校正，故 HAC/块自助区间仅作敏感性，不进 Abstract 主句。
# =====================================================================
print("\n[A] AAPC 95% CI")
yc = read(os.path.join(PROC, "res_B_anchor_year_counts.csv"))
apc_registered = {r["segment"]: float(r["AAPC_pct_per_year"])
                  for r in read(os.path.join(PROC, "res_B_anchor_apc.csv"))}
apc_rows = []
apc_summary = {}
for col, seg in [("cumulative_pq_products", "ALL_FPP"),
                 ("cumulative_malaria", "Malaria"),
                 ("cumulative_hiv", "HIV/AIDS"),
                 ("cumulative_tb", "Tuberculosis")]:
    x = np.array([int(r["year"]) for r in yc], dtype=float)
    c = np.array([float(r[col]) for r in yc], dtype=float)
    y = np.where(c > 0, np.log(np.maximum(c, 1.0)), 0.0)
    n = len(x)
    mx = x.mean()
    u = x - mx
    sxx = float((u ** 2).sum())
    b = float((u * y).sum() / sxx)          # my 项因 u 和为 0 而消去
    a = float(y.mean() - b * mx)
    e = y - (a + b * x)
    sse = float((e ** 2).sum())
    se_ols = math.sqrt(sse / (n - 2) / sxx)
    df = n - 2

    # Newey-West / Bartlett HAC（小样本未作自由度校正）
    S = float(((e * u) ** 2).sum())
    for lag in range(1, HAC_LAG + 1):
        w = 1.0 - lag / (HAC_LAG + 1)
        S += 2 * w * float((e[lag:] * u[lag:] * e[:-lag] * u[:-lag]).sum())
    se_hac = math.sqrt(max(S / sxx ** 2, 0.0))

    lo_o, hi_o, tcrit = pct_ci_from_slope(b, se_ols, df)
    lo_h, hi_h, _ = pct_ci_from_slope(b, se_hac, df)

    # 残差 circular moving-block bootstrap（保留一阶自相关）
    boots = np.empty(B_BLOCK)
    k = int(math.ceil(n / BLOCK_LEN))
    starts = rng.integers(0, n, size=(B_BLOCK, k))
    for i in range(B_BLOCK):
        seq = np.concatenate([e[(s + np.arange(BLOCK_LEN)) % n] for s in starts[i]])[:n]
        bb = float((u * (a + b * x + seq)).sum() / sxx)
        boots[i] = 100 * (math.exp(bb) - 1)
    lo_b, hi_b = np.percentile(boots, [2.5, 97.5])

    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - sse / sst if sst > 0 else float("nan")
    acf1 = float(np.corrcoef(e[1:], e[:-1])[0, 1])

    point = 100 * (math.exp(b) - 1)
    assert abs(point - apc_registered[seg]) < 0.01, (seg, point, apc_registered[seg])
    apc_rows.append([
        seg, round(point, 2), apc_registered[seg], round(b, 8),
        round(se_ols, 8), round(tcrit, 4), round(lo_o, 2), round(hi_o, 2),
        round(se_hac, 8), round(lo_h, 2), round(hi_h, 2),
        round(float(lo_b), 2), round(float(hi_b), 2),
        round(r2, 4), round(acf1, 4), n,
        "主口径=同一对数线性OLS的t区间；敏感性=HAC(3)+残差block bootstrap(3)；"
        "累积序列强自相关，naive区间偏窄；HAC lag=3为经验选择、n=25未作小样本校正；"
        "点估计未改动",
    ])
    apc_summary[seg] = {"point": round(point, 2), "ci_ols": [round(lo_o, 2), round(hi_o, 2)],
                        "ci_hac": [round(lo_h, 2), round(hi_h, 2)],
                        "ci_block": [round(float(lo_b), 2), round(float(hi_b), 2)],
                        "r2": round(r2, 4), "acf1": round(acf1, 4)}
    print(f"  {seg:12s} 点={point:6.2f}  t-CI=[{lo_o:.2f},{hi_o:.2f}]  "
          f"HAC-CI=[{lo_h:.2f},{hi_h:.2f}]  block-CI=[{lo_b:.2f},{hi_b:.2f}]  "
          f"ACF1={acf1:.3f}")
write(f"res_B_uncertainty_apc_ci_{STAMP}.csv",
      ["segment", "aapc_recomputed_pct", "aapc_registered_pct", "log_slope_b",
       "se_ols", "t_crit_df23", "ci95_lo_ols", "ci95_hi_ols",
       "se_hac_lag3", "ci95_lo_hac", "ci95_hi_hac",
       "ci95_lo_block_boot", "ci95_hi_block_boot",
       "r_squared", "resid_acf1", "n_years", "method_note"], apc_rows)
summary["aapc"] = apc_summary
summary["notes"].append(
    "累积存量序列存在强正自相关；同一 OLS 的 t 区间为主口径（与登记点估计同模型），"
    "HAC 与残差 block bootstrap 区间为敏感性，审稿时须同时呈现，不可只报最窄者。"
    "HAC lag=3 为经验选择、未据数据定阶，n=25 未作小样本自由度校正，Methods 须交代。")

# =====================================================================
# B. 生产者集中度：HHI / CRn / 国别份额
#    ⚠ 自检发现：登记值 4073.8 来自复核前 res_B_anchor_concentration.csv 的
#    HHI_total=4073.76（印度 408 行口径）；复核后
#    res_B_anchor_concentration_reviewed.csv（印度 413 行、合计 648 行）
#    自洽值为 4174.84（share_pct 平方和）/ 4175.53（精确份额）。
#    本脚本只记录差异并上报，不改写 4073.8。
# =====================================================================
print("\n[B] 集中度 HHI / CRn / 国别份额")
rev = read(os.path.join(PROC, "res_B_anchor_concentration_reviewed.csv"))
pre = read(os.path.join(PROC, "res_B_anchor_concentration.csv"))
hhi_registered = float([r for r in pre if r["hq_country"] == "HHI_total"][0]["hhi_contribution"])
countries = [r["iso3"] for r in rev]
counts = np.array([int(r["product_rows"]) for r in rev], dtype=int)
N = int(counts.sum())
assert N == 648, N
shares = 100.0 * counts / N
hhi_exact = float((shares ** 2).sum())
hhi_rounded = float(sum(float(r["share_pct"]) ** 2 for r in rev))
idx_vec = np.repeat(np.arange(len(countries)), counts)
assert len(idx_vec) == N

boot_hhi = np.empty(B_BOOT)
boot_cr1 = np.empty(B_BOOT)
boot_cr4 = np.empty(B_BOOT)
boot_cr8 = np.empty(B_BOOT)
boot_country = np.empty((B_BOOT, len(countries)))
for i in range(B_BOOT):
    s = rng.choice(idx_vec, size=N, replace=True)
    cnt = np.bincount(s, minlength=len(countries))
    sh = 100.0 * cnt / N
    boot_hhi[i] = (sh ** 2).sum()
    desc = np.sort(sh)[::-1]
    boot_cr1[i] = desc[0]
    boot_cr4[i] = desc[:4].sum()
    boot_cr8[i] = desc[:8].sum()
    boot_country[i] = sh


def q(v):
    lo, hi = np.percentile(v, [2.5, 97.5])
    return round(float(lo), 2), round(float(hi), 2)


desc = np.sort(shares)[::-1]
metrics = [
    ("HHI", round(hhi_exact, 2), q(boot_hhi), "Σ(国别份额%)²，分母=复核后 648 行"),
    ("CR1_pct", round(float(desc[0]), 2), q(boot_cr1), "最大单一持证商国份额"),
    ("CR4_pct", round(float(desc[:4].sum()), 2), q(boot_cr4), "前 4 国份额合计"),
    ("CR8_pct", round(float(desc[:8].sum()), 2), q(boot_cr8), "前 8 国份额合计"),
]
conc_rows = []
for name, point, (lo, hi), note in metrics:
    conc_rows.append([name, point, lo, hi, B_BOOT,
                      "产品行级非参数 bootstrap（648 行有放回重抽）；区间为描述性构成波动，"
                      "清单本身是 2026-09-15 存量快照而非随机样本", note])
    print(f"  {name:9s} 点={point:8.2f}  95% CI=[{lo:.2f},{hi:.2f}]")
conc_rows += [
    ["HHI_registered_in_12_16", round(hhi_registered, 2), "", "", "",
     "登记值 4073.8 已作废；2026-11-11 用户裁定回填为 4175.53；实为复核前 concentration.csv 的 HHI_total", "已回填，仅留痕"],
    ["HHI_reviewed_from_share_pct", round(hhi_rounded, 2), "", "", "",
     "复核后 CSV 的 share_pct（已四舍五入）平方和", "与登记值差 ≈101"],
    ["HHI_reviewed_exact", round(hhi_exact, 2), q(boot_hhi)[0], q(boot_hhi)[1], B_BOOT,
     "复核后 CSV 的 product_rows/648 精确份额平方和", "建议的复核后自洽值"],
]
write(f"res_B_uncertainty_concentration_ci_{STAMP}.csv",
      ["metric", "point", "ci95_lo", "ci95_hi", "bootstrap_draws", "method_note", "calibre_note"],
      conc_rows)

# 逐国份额 CI
share_rows = []
for j, iso in enumerate(countries):
    lo, hi = q(boot_country[:, j])
    share_rows.append([iso, int(counts[j]), round(float(shares[j]), 2), lo, hi,
                       int(rev[j]["n_holders"]), B_BOOT])
write(f"res_B_uncertainty_country_share_ci_{STAMP}.csv",
      ["iso3", "product_rows", "share_pct", "ci95_lo", "ci95_hi", "n_holders", "bootstrap_draws"],
      share_rows)

# 国别映射置信度扰动（口径敏感性，非抽样区间）
mp = read(os.path.join(PROC, "res_B_anchor_applicant_country_reviewed.csv"))
triples = [((r.get("iso3") or "").strip(), int(r["n_products"]),
            (r.get("confidence") or "").strip()) for r in mp]
sens_rows = sum(n for _, n, cf in triples if cf in ("medium", "low", "unresolved"))
keep_counts = collections.Counter()
for iso, cnt0, cf in triples:
    if cf == "high":
        keep_counts[iso] += cnt0
keep_total = sum(keep_counts.values())
if keep_total > 0:
    hhi_highonly = sum((100.0 * v / keep_total) ** 2 for k, v in keep_counts.items() if k in countries)
else:
    hhi_highonly = float("nan")
print(f"  映射敏感性：medium/low/unresolved 合计 {sens_rows} 行；"
      f"仅保留 high 置信（分母 {keep_total}）时 HHI = {hhi_highonly:.2f}")
summary["concentration"] = {
    "hhi_registered": round(hhi_registered, 2),
    "hhi_reviewed_exact": round(hhi_exact, 2),
    "hhi_reviewed_from_rounded_share": round(hhi_rounded, 2),
    "hhi_boot_ci": list(q(boot_hhi)),
    "hhi_high_confidence_only": round(hhi_highonly, 2),
    "denominator": N,
    "mapping_sensitivity_rows": sens_rows,
    "cr1_cr4_cr8": {m[0]: {"point": m[1], "ci": list(m[2])} for m in metrics[1:]},
}
summary["notes"].append(
    "HHI 4073.8 与复核后取数底座不自洽（实为复核前 408 行印度口径）；本次仅记录上报，"
    "未改写任何登记数字。4175.53 为复核后 648 行自洽值，作为派生统计与后续正文的采用值；"
    "是否回填 12/16 及工作记忆由孔老师单点裁定，不阻塞 Methods/Results 起草。")
summary["notes"].append(
    "存量快照是完整清单而非随机样本，产品行 bootstrap 区间只表达构成波动；"
    "国别映射置信度扰动单独作为口径敏感性，两者不可混称抽样置信区间。")

# =====================================================================
# C. 中国 PQ 广度：二项精确 CI
#    分子 = res_B_china_pq_breadth_input.csv 按治疗领域计数；
#    分母 = FPP 全清单该治疗领域产品数。
#    ⚠ 清单为完整存量快照，k/n 不构成二项抽样。Clopper–Pearson / Wilson
#      在此降为「有限清单构成比的描述性区间」：数学含义是二项参考模型
#      k~Bin(n,p) 下 k/n 的精确覆盖区间宽度，用于刻画构成比的区间宽度，
#      不解释为超总体随机抽样的抽样误差。Methods 须明写此含义。
# =====================================================================
print("\n[C] 中国 PQ 广度二项 CI")
fpp = read(os.path.join(RAW, "who_pq_fpp_2026-09-15.csv"))
ta_total = collections.Counter((r["Therapeutic Area"] or "").strip() for r in fpp)
cn = read(os.path.join(PROC, "res_B_china_pq_breadth_input.csv"))
ta_cn = collections.Counter((r["therapeutic_area"] or "").strip() for r in cn)
assert sum(ta_cn.values()) == 52
cn_rows = []
cn_summary = {}
for area in ["Malaria", "HIV/AIDS", "Tuberculosis", "Covid-19",
             "Reproductive health", "Hepatitis B and C"]:
    k, n = ta_cn.get(area, 0), ta_total.get(area, 0)
    if n == 0:
        continue
    cp_lo, cp_hi = clopper_pearson(k, n)
    w_lo, w_hi = wilson(k, n)
    p = 100.0 * k / n
    cn_rows.append([area, k, n, round(p, 2),
                    round(100 * cp_lo, 2), round(100 * cp_hi, 2),
                    round(100 * w_lo, 2), round(100 * w_hi, 2),
                    "有限清单构成比的描述性区间：Clopper-Pearson 为主、Wilson 为对照；"
                    "数学含义为二项参考模型 k~Bin(n,p) 下 k/n 的精确覆盖区间宽度，"
                    "刻画有限清单构成比的区间宽度，不解释为超总体随机抽样的抽样误差"])
    cn_summary[area] = {"k": k, "n": n, "pct": round(p, 2),
                        "cp_ci": [round(100 * cp_lo, 2), round(100 * cp_hi, 2)],
                        "wilson_ci": [round(100 * w_lo, 2), round(100 * w_hi, 2)]}
    print(f"  {area:22s} {k:3d}/{n:3d} = {p:5.2f}%  "
          f"CP 95% CI=[{100*cp_lo:.2f},{100*cp_hi:.2f}]")
write(f"res_B_uncertainty_china_breadth_ci_{STAMP}.csv",
      ["therapeutic_area", "china_products_k", "global_fpp_n", "share_pct",
       "ci95_lo_clopper_pearson", "ci95_hi_clopper_pearson",
       "ci95_lo_wilson", "ci95_hi_wilson", "method_note"], cn_rows)
summary["china_breadth"] = cn_summary
summary["notes"].append(
    "中国 PQ 广度的 Clopper–Pearson / Wilson 区间为「有限清单构成比的描述性区间」："
    "在二项参考模型 k~Bin(n,p) 下刻画 k/n 的精确覆盖宽度，不代表超总体抽样误差，"
    "故与「清单为完整存量快照、点估计无抽样误差」不冲突；Methods 须写明其数学含义。")

# =====================================================================
# D. 负担加权错位指数（2026-11-11 修订版：s 改为病种特异）
#    修订依据：原实现把 res_B_anchor_concentration_reviewed.csv 的
#    「648 行全领域 FPP 国别分布」当作三个病种各自的供应份额 s（对象错配）。
#    修正：按 FPP.Therapeutic Area × Applicant 逐行 join
#    res_B_anchor_applicant_country_reviewed.csv(iso2) → ISO 3166-1 alpha-3，
#    在各病种内部按产品行数归一化，得到病种特异 s。
#    M = Σ|s_i − b_i|（0–2，两份额分布的 L1 距离 / 总变差距离×2），
#    D = 0.5M（0–1）；b_i = 该病种负担相对规模的国别份额：
#      malaria: GHO 发病率(每千高危人口) × 人口
#      TB     : GHO 发病率(每十万) × 人口
#      HIV    : GHO PLHIV 人数（绝对数，不再乘人口）
#    同一指标内的单位常数在归一化时抵消；各国取该指标最新可得年。
#    ⚠ M≈2 贴天花板，主要反映「持证商国集合与 100+ 负担国集合几乎不重叠」
#      这一 PQ 清单固有结构，不等于「供应量相对负担接近完全错配」。
#      故同时报告两个有区分度的备择指标：
#        C   = Σ b_i·1[s_i>0]（负担加权供应覆盖率，0–1）
#        R25 = (前 25% 高负担国家的 s 份额) / (同组 b 份额)
#    ⚠ 病种间 M 不可比：n=100/193/151，负担单位与年份范围均不同。
# =====================================================================
print("\n[D] 负担加权错位指数（病种特异 s）")


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


pop = tidy(os.path.join(RAW, "wb_pop.csv"))
gho = {
    "Malaria": (tidy(os.path.join(RAW, "gho_mal_inc.csv")), "rate_x_pop", "per 1000 at risk"),
    "Tuberculosis": (tidy(os.path.join(RAW, "gho_tb_inc.csv")), "rate_x_pop", "per 100k"),
    "HIV/AIDS": (tidy(os.path.join(RAW, "gho_hiv_pl.csv")), "count", "PLHIV count"),
}

# 全领域（旧口径）s：仅作修订留痕对照，不再进入任何病种 M 的主口径
raw_supply_all = {r["iso3"]: int(r["product_rows"]) for r in rev}
assert set(raw_supply_all) == set(ISO2_TO_ISO3), "国别码表需覆盖全部 29 个持证商国"
supply_all_legacy = {ISO2_TO_ISO3[k]: v / N for k, v in raw_supply_all.items()}


def build_supply_by_area():
    """按 Therapeutic Area × Applicant 构造病种特异供应份额 s。

    FPP 每行一个产品；Applicant 经复核映射表得持证商国 ISO2，再转 ISO3。
    分母 = 该治疗领域内成功匹配的产品行数（不是 648 行全领域分母）。
    """
    fpp_rows = read(os.path.join(RAW, "who_pq_fpp_2026-09-15.csv"))
    mpr = read(os.path.join(PROC, "res_B_anchor_applicant_country_reviewed.csv"))
    app2iso2 = {}
    for r in mpr:
        a = (r.get("applicant") or "").strip()
        i2 = (r.get("iso3") or "").strip()   # 该列实为 ISO 3166-1 alpha-2
        if a and i2:
            app2iso2[a] = i2
    assert set(app2iso2.values()) <= set(ISO2_TO_ISO3), "申请国映射越出 29 国码表"

    by_ta = collections.defaultdict(list)
    for r in fpp_rows:
        by_ta[(r.get("Therapeutic Area") or "").strip()].append(r)

    out = {}
    for ta in ["Malaria", "Tuberculosis", "HIV/AIDS"]:
        rows = by_ta.get(ta, [])
        cnt, unmatched, labels = collections.Counter(), [], []
        for r in rows:
            a = (r.get("Applicant") or "").strip()
            i2 = app2iso2.get(a)
            if i2 is None or i2 not in ISO2_TO_ISO3:
                unmatched.append(a)
                continue
            iso3 = ISO2_TO_ISO3[i2]
            cnt[iso3] += 1
            labels.append(iso3)             # 产品行级国别标签，供 s 侧 bootstrap
        matched = len(labels)
        assert matched == len(rows), f"{ta} 存在未匹配 applicant：{sorted(set(unmatched))}"
        out[ta] = {
            "shares": {k: v / matched for k, v in cnt.items()},
            "counts": dict(cnt),
            "labels": labels,
            "matched": matched,
            "total": len(rows),
            "n_holder_countries": len(cnt),
        }
    return out


supply_by_area = build_supply_by_area()
for ta, d in supply_by_area.items():
    print(f"  [{ta}] 病种特异 s：{d['matched']}/{d['total']} 行匹配（零未匹配），"
          f"持证商国 {d['n_holder_countries']} 个，"
          f"IND={100*d['shares'].get('IND',0):.2f}%  "
          f"CHN={100*d['shares'].get('CHN',0):.2f}%")

# 病种特异持证商分布单独落盘，供 Results 3.4 与制图直接回链
sp_rows = []
for ta, d in supply_by_area.items():
    for iso, nprod in sorted(d["counts"].items(), key=lambda z: -z[1]):
        i2 = ISO3_TO_ISO2.get(iso, "")
        sp_rows.append([ta, iso, i2, nprod, d["matched"],
                        round(100.0 * nprod / d["matched"], 2),
                        round(100.0 * raw_supply_all.get(i2, 0) / N, 2),
                        d["n_holder_countries"]])
write(f"res_B_uncertainty_supply_by_area_{STAMP}.csv",
      ["disease", "iso3_gho_wb", "iso2_in_concentration_reviewed",
       "product_rows_in_area", "area_denominator", "disease_specific_share_pct",
       "all_area_share_pct_legacy", "n_holder_countries"], sp_rows)


def pop_at(iso, year):
    d = pop.get(iso, {})
    if not d:
        return None
    if year in d:
        return d[year]
    cand = [y for y in d if y <= year]
    return d[max(cand)] if cand else d[min(d)]


def build_misalignment(burden, mode, svec, drop_second_latest=False):
    """返回 (universe, s数组, b数组, M, C, 元数据)；svec 为病种特异份额。"""
    w = {}
    years_used = []
    for iso, series in burden.items():
        ys = sorted(series)
        if drop_second_latest and len(ys) >= 2:
            y = ys[-2]
        else:
            y = ys[-1]
        val = series[y]
        if val is None or val < 0:
            continue
        if mode == "rate_x_pop":
            p = pop_at(iso, min(y, 2023))
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
    universe = sorted(set(w) | ALL_ISO3)
    b = np.array([w.get(iso, 0.0) for iso in universe], dtype=float)
    b = b / b.sum()
    s = np.array([svec.get(iso, 0.0) for iso in universe], dtype=float)
    M = float(np.abs(s - b).sum())
    C = float(b[s > 0].sum())            # 负担加权供应覆盖率
    meta = {
        "n_countries": len(universe),
        "n_burden_countries": len(w),
        "n_supply_countries_active": int((s > 0).sum()),
        "n_supply_countries_without_burden": len(set(svec) - set(w)),
        "burden_year_min": int(min(years_used)),
        "burden_year_max": int(max(years_used)),
        "burden_year_median": float(np.median(years_used)),
        "sum_s": round(float(s.sum()), 4),
        "sum_b": round(float(b.sum()), 4),
    }
    return universe, s, b, M, C, meta


def boot_misalignment_supply(labels, universe, b, draws=B_BOOT):
    """主不确定度：产品行级 bootstrap，只重抽 s 侧，b 固定。

    每次从该病种产品行（带国别标签）有放回重抽并重建病种特异 s；
    M 的目标参数（同一 universe 上 Σ|s−b|）不变，避免国家层重抽后
    s/b 各自重新归一化所导致的参数漂移。近上界 2 时 percentile 区间
    仍会左偏，Methods 须交代。
    """
    pos = {iso: i for i, iso in enumerate(universe)}
    lab_ix = np.array([pos[l] for l in labels], dtype=int)
    K = len(lab_ix)
    out = np.empty(draws)
    ix = rng.integers(0, K, size=(draws, K))
    for i in range(draws):
        cnt = np.bincount(lab_ix[ix[i]], minlength=len(universe))
        s_boot = cnt.astype(float) / K
        out[i] = np.abs(s_boot - b).sum()
    lo, hi = np.percentile(out, [2.5, 97.5])
    return round(float(lo), 4), round(float(hi), 4)


def boot_misalignment_country(s, b, draws=5000):
    """口径敏感性（非主 CI）：国家层重抽后 s/b 各自重新归一化。

    ⚠ 该法改变目标参数（估计的是子样本构成上的 M），且 M 近上界 2 时
      percentile 区间必然左偏；只记录为敏感性，不写进 Abstract/Results 主句。
    """
    n = len(s)
    out = np.empty(draws)
    ix = rng.integers(0, n, size=(draws, n))
    for i in range(draws):
        j = ix[i]
        ss, bb = s[j], b[j]
        ss = ss / ss.sum() if ss.sum() > 0 else ss
        bb = bb / bb.sum() if bb.sum() > 0 else bb
        out[i] = np.abs(ss - bb).sum()
    lo, hi = np.percentile(out, [2.5, 97.5])
    return round(float(lo), 4), round(float(hi), 4)


MIS_HEADER = [
    "disease", "burden_unit", "calibre", "supply_scope", "supply_denominator",
    "n_supply_countries_active", "supply_ind_pct", "supply_chn_pct",
    "n_countries", "n_burden_countries",
    "M_sum_abs_diff", "D_normalised", "ci95_lo_M", "ci95_hi_M",
    "ci95_lo_M_countryboot", "ci95_hi_M_countryboot",
    "burden_weighted_supply_coverage_C", "top25_coverage_ratio_R25",
    "top25pct_burden_share_of_b", "top25pct_burden_share_of_s",
    "M_all_area_s_legacy", "top25pct_supply_share_all_area_legacy",
    "n_supply_countries_without_burden",
    "burden_year_min", "burden_year_max", "burden_year_median",
    "comparable_across_diseases", "method_note",
]


def mis_row(**kw):
    d = {h: "" for h in MIS_HEADER}
    d.update(kw)
    return [d[h] for h in MIS_HEADER]


mis_rows, by_country_rows, mis_summary = [], [], {}
for disease, (burden, mode, unit) in gho.items():
    sd = supply_by_area[disease]
    svec = sd["shares"]
    res = build_misalignment(burden, mode, svec)
    if res is None:
        continue
    universe, s, b, M, C, meta = res
    lo, hi = boot_misalignment_supply(sd["labels"], universe, b, draws=B_BOOT)
    clo, chi = boot_misalignment_country(s, b, draws=5000)
    D = M / 2

    # 方向：负担前 25% 国家的 b 份额与 s 份额，以及供应/负担份额比
    order = np.argsort(b)[::-1]
    k_top = max(1, int(math.ceil(0.25 * len(universe))))
    top_b = float(b[order[:k_top]].sum())
    top_s = float(s[order[:k_top]].sum())
    R25 = top_s / top_b if top_b > 0 else float("nan")

    # 旧口径（全领域 648 行 s）留痕对照，仅用于说明修订影响
    s_legacy = np.array([supply_all_legacy.get(iso, 0.0) for iso in universe])
    M_legacy = float(np.abs(s_legacy - b).sum())
    top_s_legacy = float(s_legacy[order[:k_top]].sum())

    # 共同支持敏感性：仅保留有负担观测的国家，s 与 b 在该集合内重新归一化
    common = [iso for iso in universe if iso in burden]
    wc = {}
    for iso in common:
        y = max(burden[iso])
        val = burden[iso][y]
        if mode == "rate_x_pop":
            p = pop_at(iso, min(y, 2023))
            if p is None or p <= 0:
                continue
            wc[iso] = val * p
        else:
            wc[iso] = val
    b_c = np.array([wc.get(iso, 0.0) for iso in common], dtype=float)
    s_c = np.array([svec.get(iso, 0.0) for iso in common], dtype=float)
    if b_c.sum() > 0:
        b_c = b_c / b_c.sum()
    if s_c.sum() > 0:
        s_c = s_c / s_c.sum()
    M_common = float(np.abs(s_c - b_c).sum())

    # 次最新负担年敏感性
    res2 = build_misalignment(burden, mode, svec, drop_second_latest=True)
    M_prev = res2[3] if res2 else None

    base = dict(disease=disease, burden_unit=unit,
                supply_scope="disease_specific",
                supply_denominator=sd["matched"],
                n_supply_countries_active=sd["n_holder_countries"],
                supply_ind_pct=round(100 * svec.get("IND", 0), 2),
                supply_chn_pct=round(100 * svec.get("CHN", 0), 2))
    mis_rows.append(mis_row(**base, calibre="latest_burden_year",
        n_countries=meta["n_countries"],
        n_burden_countries=meta["n_burden_countries"],
        M_sum_abs_diff=round(M, 4), D_normalised=round(D, 4),
        ci95_lo_M=lo, ci95_hi_M=hi,
        ci95_lo_M_countryboot=clo, ci95_hi_M_countryboot=chi,
        burden_weighted_supply_coverage_C=round(C, 4),
        top25_coverage_ratio_R25=round(R25, 4),
        top25pct_burden_share_of_b=round(top_b, 4),
        top25pct_burden_share_of_s=round(top_s, 4),
        M_all_area_s_legacy=round(M_legacy, 4),
        top25pct_supply_share_all_area_legacy=round(top_s_legacy, 4),
        n_supply_countries_without_burden=meta["n_supply_countries_without_burden"],
        burden_year_min=meta["burden_year_min"],
        burden_year_max=meta["burden_year_max"],
        burden_year_median=round(meta["burden_year_median"], 1),
        comparable_across_diseases="no (n/unit/year differ)",
        method_note=(
            f"s 为病种特异（Therapeutic Area × Applicant，分母 {sd['matched']} 行、"
            f"{sd['n_holder_countries']} 个持证商国），非 648 行全领域分布；"
            "M=Σ|s−b| 为两份额分布的 L1 距离（0–2），D=0.5M（0–1）；"
            "主 CI 为产品行级 bootstrap（10000 次，只重抽 s 侧、b 固定，目标参数不变）；"
            "国家层重抽区间仅作敏感性（重归一化改变目标参数、近上界左偏）；"
            "M 贴天花板反映持证商国集合与负担国集合几乎不重叠，非供应量错配程度，"
            "解释以 C 与 R25 为主；病种间 M 不可比（n/负担单位/年份范围不同）；"
            "仅描述地理分布，不作因果解释")))
    mis_rows.append(mis_row(**base, calibre="common_support_only",
        n_countries=len(common),
        M_sum_abs_diff=round(M_common, 4), D_normalised=round(M_common / 2, 4),
        comparable_across_diseases="sensitivity only",
        method_note="仅保留有负担观测的国家，s 与 b 在共同集合内重新归一化；"
                    "共同支持可缓解支持集不重叠对 M 的影响"))
    mis_rows.append(mis_row(**base, calibre="second_latest_burden_year",
        n_countries=res2[5]["n_countries"] if res2 else "",
        M_sum_abs_diff=round(M_prev, 4) if M_prev is not None else "",
        D_normalised=round(M_prev / 2, 4) if M_prev is not None else "",
        comparable_across_diseases="sensitivity only",
        method_note="各国改用次最新可得负担年，检验负担年错配"))
    mis_rows.append(mis_row(disease=disease, burden_unit=unit,
        calibre="all_area_s_legacy", supply_scope="all_area_648",
        supply_denominator=N, n_supply_countries_active=len(raw_supply_all),
        n_countries=meta["n_countries"],
        n_burden_countries=meta["n_burden_countries"],
        M_sum_abs_diff=round(M_legacy, 4), D_normalised=round(M_legacy / 2, 4),
        top25pct_burden_share_of_b=round(top_b, 4),
        top25pct_burden_share_of_s=round(top_s_legacy, 4),
        top25pct_supply_share_all_area_legacy=round(top_s_legacy, 4),
        comparable_across_diseases="legacy only",
        method_note="修订前口径（全领域 648 行 s）留痕对照；不进入正文，"
                    "仅用于说明本次修订对 M 与方向分解的影响"))

    mis_summary[disease] = {
        "unit": unit, "supply_scope": "disease_specific",
        "supply_denominator": sd["matched"],
        "n_supply_countries_active": sd["n_holder_countries"],
        "supply_ind_pct": round(100 * svec.get("IND", 0), 2),
        "supply_chn_pct": round(100 * svec.get("CHN", 0), 2),
        "M": round(M, 4), "D": round(D, 4),
        "boot_ci_M_supply_rows": [lo, hi],
        "boot_ci_M_country_sensitivity": [clo, chi],
        "burden_weighted_supply_coverage_C": round(C, 4),
        "top25_coverage_ratio_R25": round(R25, 4),
        "M_common_support": round(M_common, 4),
        "M_second_latest_year": round(M_prev, 4) if M_prev is not None else None,
        "top25pct_burden_share": round(top_b, 4),
        "top25pct_supply_share": round(top_s, 4),
        "M_all_area_s_legacy": round(M_legacy, 4),
        "top25pct_supply_share_all_area_legacy": round(top_s_legacy, 4),
        "n_countries": meta["n_countries"],
        "n_burden_countries": meta["n_burden_countries"],
        "n_supply_countries_without_burden": meta["n_supply_countries_without_burden"],
        "burden_year_range": [meta["burden_year_min"], meta["burden_year_max"]],
    }
    mprev_s = f"{M_prev:.4f}" if M_prev is not None else "NA"
    print(f"  {disease:14s} ({unit:13s}) M={M:.4f} D={D:.4f} "
          f"主CI=[{lo:.4f},{hi:.4f}]  C={C:.4f} R25={R25:.4f}  "
          f"前25%高负担国 s={100*top_s:.2f}% / b={100*top_b:.2f}%  "
          f"共同支持 M={M_common:.4f}  次新年 M={mprev_s}  "
          f"负担年 {meta['burden_year_min']}–{meta['burden_year_max']}")

    for iso, si, bi in zip(universe, s, b):
        i2 = ISO3_TO_ISO2.get(iso, "")
        by_country_rows.append([disease, iso, i2,
                                round(float(si), 6), round(float(bi), 6),
                                round(float(si - bi), 6), round(float(abs(si - bi)), 6),
                                int(sd["counts"].get(iso, 0)),
                                int(raw_supply_all.get(i2, 0)),
                                round(supply_all_legacy.get(iso, 0.0), 6)])

write(f"res_B_uncertainty_misalignment_ci_revised_{STAMP}.csv", MIS_HEADER, mis_rows)
write(f"res_B_uncertainty_misalignment_by_country_revised_{STAMP}.csv",
      ["disease", "iso3_gho_wb", "iso2_in_concentration_reviewed",
       "supply_share_s_disease_specific", "burden_share_b", "s_minus_b",
       "abs_s_minus_b", "pq_product_rows_in_area",
       "pq_product_rows_all_area_legacy", "all_area_supply_share_legacy"],
      by_country_rows)
summary["misalignment"] = mis_summary
summary["notes"].append(
    "【2026-11-11 修订】RQ2 的供应份额 s 由「648 行全领域 FPP 国别分布」改为"
    "按 Therapeutic Area × Applicant 逐行 join 的病种特异分布"
    "（疟疾 98、结核 126、HIV 255 行，三病种均零未匹配，分母为各病种产品数）；"
    "旧口径 M 仅作留痕对照行，不进入正文。")
summary["notes"].append(
    "M=Σ|s−b| 是两份额分布的 L1 距离，取值上界 2；疟疾/HIV 的 M 贴近上界主要反映"
    "「持证商国集合（29 国以内）与负担国集合（100+ 国）几乎不重叠」这一 PQ 清单"
    "固有结构，不等于供应量相对负担接近完全错配。故同报负担加权供应覆盖率 C"
    "与高负担组供应/负担份额比 R25 作为有区分度的备择指标；病种间 M 不可比"
    "（n=100/193/151、负担单位与年份范围不同），不得并列下结论。")
summary["notes"].append(
    "M 的主不确定度为产品行级 bootstrap（只重抽 s 侧、b 固定，目标参数不变）；"
    "国家层重抽后各自重新归一化会改变目标参数且近上界时 percentile 区间必然左偏，"
    "仅记为敏感性。HAC lag=3 为经验选择、n=25 未作小样本自由度校正，"
    "AAPC 的 HAC/块自助区间只作敏感性，Methods 须交代。")
summary["notes"].append(
    "国别码制：concentration_reviewed.csv 的 iso3 列实为 ISO2，GHO/WB 为 ISO3；"
    "不做转换则支持集不相交、M 恒等于 2。本次沿用 ISO 3166-1 的 29 国显式码表，"
    "逐国明细保留双码列。")
summary["notes"].append(
    "GHO 本地快照 gho_hiv_pl.csv 仅覆盖 2000–2006 且为 PLHIV 绝对人数，"
    "与 2002–2026 观察窗严重错配；HIV 仅作补充材料，RQ2 主口径为疟疾＋结核。")
summary["notes"].append(
    "负担份额由 GHO 指标值×人口（疟疾/TB）或 PLHIV 人数（HIV）归一化得到，"
    "同一指标内单位常数在归一化中抵消；疟疾指标原单位为每千高危人口，"
    "以总人口作代理会高估高危人群规模，属已登记的口径局限。")

# =====================================================================
# E. 汇总
# =====================================================================
with open(os.path.join(PROC, f"res_B_uncertainty_summary_{STAMP}.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"\n  -> res_B_uncertainty_summary_{STAMP}.json")
print("\n完成。既有 res_B_anchor_* / dualchain_* 文件未被写入。")
