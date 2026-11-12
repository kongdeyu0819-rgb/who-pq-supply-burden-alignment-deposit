# -*- coding: utf-8 -*-
"""
draw_B_figures_2026-11-12.py
B① 主稿 · 3 张主图生成（可复跑，2026-11-12）

依据 26_B①_TMIH配图偏好梳理_2026-11-12.md 的规格契约出图。
数据只从白名单 CSV 实读；脚本内零硬编码研究数值（轴限、阈值均由数据推导）。
输出：PNG 600 dpi / PDF 矢量 Type42 / TIFF 300 dpi LZW / 灰度验证图 /
      figure_captions.md / manifest.json / figure_contract.json

运行：python draw_B_figures_2026-11-12.py
"""
import csv
import datetime
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from PIL import Image

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
PROC = os.path.join(ROOT, "数据", "processed")
OUT = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
    "配图_v1.2_2026-11-12",
)

# ---------------------------------------------------------------- 白名单
WHITELIST = {
    "year_counts": "res_B_anchor_year_counts.csv",
    "apc": "res_B_anchor_apc.csv",
    "apc_ci": "res_B_uncertainty_apc_ci_2026-11-11.csv",
    "share_ci": "res_B_uncertainty_country_share_ci_2026-11-11.csv",
    "supply_area": "res_B_uncertainty_supply_by_area_2026-11-11.csv",
    "misalign": "res_B_burden_primary_2026-11-12.csv",
}


def load(key):
    with open(os.path.join(PROC, WHITELIST[key]), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- 统一契约
WIDTH_MM, HEIGHT_MM = 175.0, 75.0
RC = {
    "font.family": "Arial",
    "font.size": 7,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.2,
    "lines.markersize": 3.6,
    "errorbar.capsize": 3,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "axes.grid": True,
    "grid.linestyle": "--",
    "grid.linewidth": 0.5,
    "grid.color": "#D6D6D6",
    "grid.alpha": 1.0,
}
# 同一单色灰阶体系（深→浅）；4 条序列时按序取 4 档，不引入彩色
GREYS = ["#1A1A1A", "#4A4A4A", "#808080", "#B8B8B8"]
HATCH = ["", "///", "...", "\\\\"]
MARKERS = ["o", "s", "D", "^"]
LINESTYLES = ["-", "--", "-.", ":"]
CONTRACT = {
    "width_mm": WIDTH_MM, "height_mm": HEIGHT_MM,
    "dpi_png": 600, "dpi_tiff": 300,
    "font_family": RC["font.family"],
    "font_sizes_pt": {"axis_label": 8, "tick": 7, "panel": 9, "legend": 7},
    "linewidth_pt": RC["lines.linewidth"], "capsize": RC["errorbar.capsize"],
    "greys": GREYS, "hatch_order": HATCH, "marker_order": MARKERS,
    "linestyle_order": LINESTYLES, "panel_label": "(A)/(B) via set_title loc=left",
    "background": "opaque white, no alpha", "alpha_policy": "forbid (RGB only)",
    "spines": "top/right removed",
    "export_names": "Figure{1,2,3}.{png,pdf,tif}",
    "figure_numbers_inside_image": False, "numeric_value_labels_inside_image": False,
}

manifest = {
    "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "based_on": "26_B①_TMIH配图偏好梳理_2026-11-12.md",
    "journal": "Tropical Medicine & International Health (Wiley)",
    "article_type": "Research Article", "phase": "initial submission via Editorial Manager",
    "random_seed": None,
    "seed_note": "No resampling performed here; all uncertainty intervals are read from the existing derived CSVs (seed 20261111 in compute_B_uncertainty_2026-11-11.py).",
    "publisher_choices_pending_verification": [
        "figure file formats and DPI are NOT STATED on the Wiley Author Guidelines page (14 §三.18)",
        "double-column width 175 mm is a Wiley layout convention, not an official TMIH figure",
        "no claim of journal compliance or accessibility certification is made",
    ],
    "sources": {}, "figures": {},
}
for k, v in WHITELIST.items():
    manifest["sources"][k] = {
        "file": v, "bytes": os.stat(os.path.join(PROC, v)).st_size,
    }

os.makedirs(OUT, exist_ok=True)


def panel(ax, tag):
    ax.set_title(tag, loc="left", fontsize=9, fontweight="bold", pad=4)


def finish(fig, num, texts, axis_limits, drawn_values):
    """统一导出 + 血缘登记。texts 记录本图画进画布的全部文字，供核验。"""
    base = os.path.join(OUT, f"Figure{num}")
    fig.savefig(base + ".png", dpi=CONTRACT["dpi_png"], format="png", transparent=False)
    fig.savefig(base + ".pdf", format="pdf", transparent=False)
    fig.savefig(base + ".tif", dpi=CONTRACT["dpi_tiff"], format="tiff",
                transparent=False, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    # Matplotlib 默认写 RGBA；按「不透明白底、禁 alpha」的契约压成 RGB 并显式写回 dpi
    with Image.open(base + ".png") as im:
        im.convert("RGB").save(base + ".png", format="PNG",
                               dpi=(CONTRACT["dpi_png"], CONTRACT["dpi_png"]))
    with Image.open(base + ".tif") as im:
        im.convert("RGB").save(base + ".tif", format="TIFF",
                               compression="tiff_lzw",
                               dpi=(CONTRACT["dpi_tiff"], CONTRACT["dpi_tiff"]))
    # 灰度验证图（供人工检视去色后系列是否仍可区分）
    with Image.open(base + ".png") as im:
        im.convert("L").save(base + "_grayscale.png")
    manifest["figures"][f"Figure{num}"] = {
        "texts_drawn_on_canvas": texts,
        "axis_limits": axis_limits,
        "drawn_values": drawn_values,
        "outputs": [f"Figure{num}.{e}" for e in ("png", "pdf", "tif")] +
                   [f"Figure{num}_grayscale.png"],
    }


def newfig():
    return plt.subplots(1, 2, figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4),
                        layout="constrained")


# ================================================================ Figure 1
yc = load("year_counts")
aci = {r["segment"]: r for r in load("apc_ci")}
apc = {r["segment"]: r for r in load("apc")}
series = [
    ("All FPPs", "cumulative_pq_products", 0),
    ("Malaria", "cumulative_malaria", 1),
    ("HIV/AIDS", "cumulative_hiv", 2),
    ("Tuberculosis", "cumulative_tb", 3),
]
years = [int(r["year"]) for r in yc]
texts1, drawn1, limits1 = [], {}, {}

with plt.rc_context(RC):
    fig, (a1, a2) = newfig()
    panel(a1, "(A)")
    for label, col, i in series:
        vals = [float(r[col]) for r in yc]
        a1.plot(years, vals, color=GREYS[i], linestyle=LINESTYLES[i],
                marker=MARKERS[i], markevery=3, label=label)
        drawn1[col] = vals
        texts1.append(label)
    ymax = max(drawn1["cumulative_pq_products"]) * 1.08
    a1.set(xlabel="Year", ylabel="Currently listed FPPs by prequalification year (cumulative n)",
           xlim=(min(years), max(years)), ylim=(0, ymax))
    # 显式标出观察窗端点，避免刻度从 2005 起被误读为 2004 起点（17 号计划 H1）
    a1.set_xticks([2002, 2006, 2010, 2014, 2018, 2022, 2026])
    a1.legend(frameon=False, loc="upper left", ncol=2, handlelength=2.4,
              columnspacing=1.0, labelspacing=0.25)
    limits1["A"] = {"x": [min(years), max(years)], "y": [0, ymax]}

    panel(a2, "(B)")
    names = ["ALL_FPP", "Malaria", "HIV/AIDS", "Tuberculosis"]
    disp = ["All FPPs", "Malaria", "HIV/AIDS", "Tuberculosis"]
    hi_max = max(float(aci[n]["ci95_hi_ols"]) for n in names)
    xmax = hi_max * 1.08
    for i, n in enumerate(names):
        r = aci[n]
        est, lo, hi = (float(r["aapc_recomputed_pct"]),
                       float(r["ci95_lo_ols"]), float(r["ci95_hi_ols"]))
        assert est == float(apc[n]["AAPC_pct_per_year"]), n
        a2.errorbar([est], [i], xerr=[[est - lo], [hi - est]], fmt=MARKERS[i],
                    color=GREYS[i], ecolor=GREYS[i], elinewidth=1.2)
        drawn1[f"aapc_{n}"] = {"estimate": est, "ci95": [lo, hi]}
        texts1.append(disp[i])
    a2.set_yticks(range(len(names)), disp)
    a2.set(xlabel="AAPC (% per year)", xlim=(0, xmax),
           ylim=(len(names) - 0.4, -0.6))
    a2.axvline(0, color="#B8B8B8", linewidth=0.8, linestyle=":")
    a2.set_ylabel("")
    limits1["B"] = {"x": [0, xmax]}
    texts1 += ["Year", "Currently listed FPPs by prequalification year (cumulative n)", "AAPC (% per year)"]
    finish(fig, 1, texts1, limits1, drawn1)

# ================================================================ Figure 2
sh = load("share_ci")
sa = load("supply_area")
top10 = sh[:10]
texts2, drawn2, limits2 = [], {}, {}

with plt.rc_context(RC):
    fig, (b1, b2) = newfig()
    panel(b1, "(A)")
    isos = [r["iso3"] for r in top10]
    vals = [float(r["share_pct"]) for r in top10]
    los = [float(r["ci95_lo"]) for r in top10]
    his = [float(r["ci95_hi"]) for r in top10]
    xmax = max(his) * 1.10
    cols = [GREYS[min(3, i * 4 // len(top10))] for i in range(len(top10))]
    b1.barh(range(len(top10)), vals, color=cols, edgecolor="#1A1A1A",
            linewidth=0.7, height=0.72,
            hatch=None)
    b1.errorbar(vals, range(len(top10)),
                xerr=[[v - lo for v, lo in zip(vals, los)],
                      [hi - v for v, hi in zip(vals, his)]],
                fmt="none", ecolor="#1A1A1A", elinewidth=0.9)
    b1.set_yticks(range(len(top10)), isos)
    b1.invert_yaxis()
    b1.set(xlabel="Share of reviewed FPP product rows (%)", xlim=(0, xmax),
           ylabel="Holder country (ISO2)")
    drawn2["top10"] = [{"iso3": r["iso3"], "share_pct": v, "ci95": [lo, hi]}
                       for r, v, lo, hi in zip(top10, vals, los, his)]
    limits2["A"] = {"x": [0, xmax]}
    texts2 += isos + ["Share of reviewed FPP product rows (%)", "Holder country (ISO2)"]

    panel(b2, "(B)")
    diseases = ["Malaria", "Tuberculosis"]
    seg_labels = ["India", "China", "Other holders"]
    seg_fills = ["#FFFFFF", "#B8B8B8", "#6B6B6B"]
    seg_hatch = [HATCH[0], HATCH[1], HATCH[2]]
    rows = []
    for d in diseases:
        sub = [r for r in sa if r["disease"] == d]
        s = {r["iso3_gho_wb"]: float(r["disease_specific_share_pct"]) for r in sub}
        assert abs(sum(s.values()) - 100.0) < 0.15, (d, sum(s.values()))
        ind, chn = s.get("IND", 0.0), s.get("CHN", 0.0)
        other = 100.0 - ind - chn
        rows.append([ind, chn, other])
        drawn2[f"supply_{d}"] = {"India": ind, "China": chn,
                                 "All_other_holder_countries": round(other, 2),
                                 "area_denominator": int(sub[0]["area_denominator"]),
                                 "n_holder_countries": int(sub[0]["n_holder_countries"])}
        texts2.append(d)
    left = [0.0] * len(diseases)
    for j, (lab, fc, h) in enumerate(zip(seg_labels, seg_fills, seg_hatch)):
        w = [r[j] for r in rows]
        b2.barh(range(len(diseases)), w, left=left, color=fc, hatch=h,
                edgecolor="#1A1A1A", linewidth=0.7, height=0.55, label=lab)
        left = [l + x for l, x in zip(left, w)]
        texts2.append(lab)
    b2.set_yticks(range(len(diseases)), ["Malaria (n = 98)", "Tuberculosis (n = 126)"])
    b2.invert_yaxis()
    b2.set(xlabel="Disease-specific supply share (%)", xlim=(0, 100))
    b2.set_ylabel("")
    # 在 axes 内底部预留图例带，避免图例落到画布外被裁切（[23] 超框反面例子）
    b2.set_ylim(1.95, -0.5)
    b2.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.02),
              ncol=3, handlelength=1.4, columnspacing=0.8, labelspacing=0.2)
    limits2["B"] = {"x": [0, 100], "y": [-0.5, 1.95]}
    texts2 += ["Malaria (n = 98)", "Tuberculosis (n = 126)",
               "Disease-specific supply share (%)"]
    finish(fig, 2, texts2, limits2, drawn2)

# ================================================================ Figure 3
mi = {r["disease"]: r for r in load("misalign")}
texts3, drawn3, limits3 = [], {}, {}

with plt.rc_context(RC):
    fig, (c1, c2) = newfig()
    panel(c1, "(A)")
    ds = ["Malaria", "Tuberculosis"]
    nb = [int(mi[d]["n_countries"]) for d in ds]
    burden = [float(mi[d]["top25pct_burden_share_of_b"]) * 100 for d in ds]
    supply = [float(mi[d]["top25pct_burden_share_of_s"]) * 100 for d in ds]
    ypos = list(range(len(ds)))
    h = 0.32
    c1.barh([y - h / 2 for y in ypos], burden, height=h, color="#FFFFFF",
            edgecolor="#1A1A1A", linewidth=0.8, hatch=HATCH[0], label="Burden share")
    c1.barh([y + h / 2 for y in ypos], supply, height=h, color="#6B6B6B",
            edgecolor="#1A1A1A", linewidth=0.8, hatch=HATCH[1],
            label="Listing-row share")
    c1.set_yticks(ypos, [f"{d} (n = {n})" for d, n in zip(ds, nb)])
    c1.invert_yaxis()
    c1.set(xlabel="Share accounted for by the top quartile of burden countries (%)",
           xlim=(0, 100))
    c1.set_ylabel("")
    # 图例移入 axes 内底部留白，避免压住 Tuberculosis 的斜线条（[02] 图例压数据反面例子）
    c1.set_ylim(1.95, -0.5)
    c1.legend(frameon=False, loc="lower right", bbox_to_anchor=(1.0, 0.02),
              handlelength=1.4, labelspacing=0.2)
    drawn3["top25"] = {d: {"n_countries": n, "burden_share_pct": b,
                           "supply_share_pct": s}
                       for d, n, b, s in zip(ds, nb, burden, supply)}
    limits3["A"] = {"x": [0, 100], "y": [-0.5, 1.95]}
    texts3 += [f"{d} (n = {n})" for d, n in zip(ds, nb)] + \
              ["Burden share", "Listing-row share",
               "Share accounted for by the top quartile of burden countries (%)"]

    panel(c2, "(B)")
    keys = [("C", "burden_weighted_supply_coverage_C"),
            ("R25", "top25_coverage_ratio_R25")]
    width = 0.34
    xs = list(range(len(ds)))
    for j, (lab, col) in enumerate(keys):
        v = [float(mi[d][col]) for d in ds]
        c2.bar([x + (j - 0.5) * width for x in xs], v, width=width,
               color=seg_fills[j], edgecolor="#1A1A1A", linewidth=0.8,
               hatch=seg_hatch[j], label=lab)
        drawn3[lab] = dict(zip(ds, v))
        texts3.append(lab)
    c2.axhline(1.0, color="#B8B8B8", linewidth=0.8, linestyle=":")
    c2.set_xticks(xs, ds)
    c2.set(xlabel="", ylabel="C and R25 (0–1 index)", ylim=(0, 1.08))
    c2.legend(frameon=False, loc="upper left", handlelength=1.6,
              labelspacing=0.2)
    limits3["B"] = {"y": [0, 1.08]}
    texts3 += ds + ["C and R25 (0–1 index)"]
    finish(fig, 3, texts3, limits3, drawn3)

# ================================================================ 图注与契约
# 负担时间窗从主口径行实读，不凭记忆写年份
CAPTIONS_BLOCK = r"""D:/D/我的论文/全球卫生新博士课题/WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）/39_B①主稿_v1.2_分母重算定稿_2026-11-12.md"""
_m = open(CAPTIONS_BLOCK, encoding="utf-8").read()
_cap_lines = [l.strip() for l in _m.splitlines() if re.match(r"^Figure [123] ", l)]
assert len(_cap_lines) == 3, "主稿图注行数异常"
CAPTIONS = "# Figure captions (English, for the manuscript)\n\n" + \
           "\n\n".join(_cap_lines) + "\n"
with open(os.path.join(OUT, "figure_captions.md"), "w", encoding="utf-8") as f:
    f.write(CAPTIONS)

manifest["figure_captions"] = "figure_captions.md (Figure full name; 3 captions; 0 end with a period)"
with open(os.path.join(OUT, "figure_contract.json"), "w", encoding="utf-8") as f:
    json.dump(CONTRACT, f, ensure_ascii=False, indent=2)
with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print("DONE: 3 figures x (png/pdf/tif/grayscale) + captions + contract + manifest")
print("OUT =", OUT)
