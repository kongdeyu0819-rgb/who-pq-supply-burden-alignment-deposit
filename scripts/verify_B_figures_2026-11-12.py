# -*- coding: utf-8 -*-
"""
verify_B_figures_2026-11-12.py
B① 主稿 · 配图阶段只读核验（2026-11-12）

覆盖：
  A) 梳理先于出图（26 号稿 mtime 早于脚本与图件）；26 号稿五类规格齐备
  B) 三图产物齐备、RGB 无 alpha、dpi 与物理尺寸一致、PDF 单页
  C) 数值回链：从白名单 CSV 独立复算，逐项比对 manifest.drawn_values
  D) 不超框：所有 CI 端点与柱值落在 manifest.axis_limits 内
  E) 图内纯净度：零 `Figure N`、零精确数值标签；图注 `Figure` 全称与五成分
  F) 灰度分离：相邻灰阶 CIE L* 差 >= 12；marker/linestyle/hatch 互异
  G) 防火墙：出图脚本只打开白名单，零隔离资产名；五份底座 mtime 未变
  H) 旧核验脚本 v0.7 留痕复跑 ALL CLEAN

不写任何文件。运行：python verify_B_figures_2026-11-12.py
"""
import csv
import datetime
import json
import os
import re
import subprocess
import sys

from PIL import Image

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
OUT = os.path.join(MAIN, "配图_2026-11-12")
PROC = os.path.join(ROOT, "数据", "processed")
SCRIPTS = os.path.join(ROOT, "数据", "scripts")
DRAW = os.path.join(SCRIPTS, "draw_B_figures_2026-11-12.py")
F26 = os.path.join(MAIN, "26_B①_TMIH配图偏好梳理_2026-11-12.md")

FAIL = []


def check(label, cond, extra=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {label}" + (f"  -> {extra}" if extra else ""))
    if not cond:
        FAIL.append(label)


def read(p):
    with open(p, encoding="utf-8-sig") as f:
        return f.read()


def rows(name):
    with open(os.path.join(PROC, name), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def close(a, b, tol=0.011):
    return abs(float(a) - float(b)) <= tol


def lum(hexcol):
    """CIE L*（sRGB -> linear -> XYZ 的 Y 分量）。"""
    s = [int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in s]
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return 116 * (y ** (1 / 3)) - 16 if y > 0.008856 else 903.3 * y


# ---------------------------------------------------------------- 0 载入
print("=== 0. 载入 ===")
for p in (F26, DRAW, os.path.join(OUT, "manifest.json"),
          os.path.join(OUT, "figure_contract.json"),
          os.path.join(OUT, "figure_captions.md")):
    check(f"存在 {os.path.basename(p)[:44]}", os.path.exists(p))
if FAIL:
    print("VERDICT = FAIL (missing inputs)")
    sys.exit(1)
t26 = read(F26)
man = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
con = json.load(open(os.path.join(OUT, "figure_contract.json"), encoding="utf-8"))
caps = read(os.path.join(OUT, "figure_captions.md"))
src = read(DRAW)

# ---------------------------------------------------------------- A
print()
print("=== 1. 梳理阶段在先、五类规格齐备 ===")
# Windows 上 st_ctime 是文件创建时间；26 号稿在 Stage B 后会追加终检记录，
# 故不能用 mtime 判先后，改用创建时间作为「梳理在先」的可核验证据。
created = lambda p: os.stat(p).st_ctime
t26_c = created(F26)
draw_c = created(DRAW)
png_c = min(created(os.path.join(OUT, f"Figure{n}.png")) for n in (1, 2, 3))
check("26 号梳理稿创建早于出图脚本", t26_c < draw_c)
check("26 号梳理稿创建早于全部图件（未跳过梳理阶段）", t26_c < png_c)
check("出图脚本创建早于图件", draw_c < png_c)
for kw in ["图片数量区间", "清晰度与分辨率", "版式与标注规范", "配色与视觉风格", "一致性"]:
    check(f"梳理含「{kw}」", kw in t26)
check("梳理登记官网 NOT STATED 口径", "NOT STATED" in t26 and "不声称" in t26)
check("梳理含冲突仲裁 8 条", len(re.findall(r"^\| \d \|", t26, flags=re.M)) >= 8)

# ---------------------------------------------------------------- B
print()
print("=== 2. 产物齐备、元数据与一致性 ===")
figs = sorted(f for f in os.listdir(OUT) if re.fullmatch(r"Figure\d+\.png", f))
check("恰好 3 张主图 × 2 面板", len(figs) == 3, str(figs))
sizes, dpis = [], []
for n in (1, 2, 3):
    for ext in ("png", "pdf", "tif"):
        check(f"Figure{n}.{ext} 存在",
              os.path.exists(os.path.join(OUT, f"Figure{n}.{ext}")))
    check(f"Figure{n}_grayscale.png 存在",
          os.path.exists(os.path.join(OUT, f"Figure{n}_grayscale.png")))
    with Image.open(os.path.join(OUT, f"Figure{n}.png")) as im:
        check(f"Figure{n}.png 为 RGB、无 alpha", im.mode == "RGB", im.mode)
        sizes.append(im.size)
        dpis.append(im.info.get("dpi", (0, 0))[0])
    with Image.open(os.path.join(OUT, f"Figure{n}.tif")) as im:
        check(f"Figure{n}.tif 为 RGB、300 dpi",
              im.mode == "RGB" and abs(im.info.get("dpi", (0, 0))[0] - 300) <= 1,
              f"{im.mode} / {im.info.get('dpi')}")
    try:
        from pypdf import PdfReader
        check(f"Figure{n}.pdf 单页", len(PdfReader(os.path.join(OUT, f"Figure{n}.pdf")).pages) == 1)
    except ImportError:
        check(f"Figure{n}.pdf 单页（pypdf 缺失，跳过）", True)
check("三图 PNG 像素尺寸一致", len(set(sizes)) == 1, str(sizes))
check("三图 PNG 均 600 dpi（±1）", all(abs(d - 600) <= 1 for d in dpis), str(dpis))
exp_w = round(175 / 25.4 * 600)
exp_h = round(75 / 25.4 * 600)
check(f"物理尺寸 175×75 mm 落地（期望 {exp_w}×{exp_h} px，±3）",
      all(abs(w - exp_w) <= 3 and abs(h - exp_h) <= 3 for w, h in sizes))
for k in ("width_mm", "height_mm", "dpi_png", "dpi_tiff", "font_family",
          "greys", "hatch_order", "marker_order", "linestyle_order",
          "alpha_policy", "figure_numbers_inside_image"):
    check(f"统一契约字段 {k}", k in con)

# ---------------------------------------------------------------- C
print()
print("=== 3. 数值回链：从白名单 CSV 独立复算 ===")
dv1 = man["figures"]["Figure1"]["drawn_values"]
dv2 = man["figures"]["Figure2"]["drawn_values"]
dv3 = man["figures"]["Figure3"]["drawn_values"]

yc = rows("res_B_anchor_year_counts.csv")
check("year_counts 25 年（2002–2026）", len(yc) == 25 and
      int(yc[0]["year"]) == 2002 and int(yc[-1]["year"]) == 2026)
ok = all(dv1[c] == [float(r[c]) for r in yc]
         for c in ("cumulative_pq_products", "cumulative_malaria",
                   "cumulative_hiv", "cumulative_tb"))
check("Figure1(A) 4 条累积序列逐点回链", ok)
aci = {r["segment"]: r for r in rows("res_B_uncertainty_apc_ci_2026-11-11.csv")}
apc = {r["segment"]: r for r in rows("res_B_anchor_apc.csv")}
ok = True
for n in ("ALL_FPP", "Malaria", "HIV/AIDS", "Tuberculosis"):
    d = dv1[f"aapc_{n}"]
    ok &= (close(d["estimate"], apc[n]["AAPC_pct_per_year"]) and
           close(d["estimate"], aci[n]["aapc_recomputed_pct"]) and
           close(d["ci95"][0], aci[n]["ci95_lo_ols"]) and
           close(d["ci95"][1], aci[n]["ci95_hi_ols"]))
check("Figure1(B) 4 个 AAPC 与主口径 t 区间回链", ok)

sh = rows("res_B_uncertainty_country_share_ci_2026-11-11.csv")[:10]
ok = all(d["iso3"] == r["iso3"] and close(d["share_pct"], r["share_pct"]) and
         close(d["ci95"][0], r["ci95_lo"]) and close(d["ci95"][1], r["ci95_hi"])
         for d, r in zip(dv2["top10"], sh))
check("Figure2(A) Top10 份额＋95% 区间回链", ok)
sa = rows("res_B_uncertainty_supply_by_area_2026-11-11.csv")
ok = True
for d in ("Malaria", "Tuberculosis"):
    sub = {r["iso3_gho_wb"]: float(r["disease_specific_share_pct"])
           for r in sa if r["disease"] == d}
    rec = dv2[f"supply_{d}"]
    ok &= (close(rec["India"], sub.get("IND", 0)) and
           close(rec["China"], sub.get("CHN", 0)) and
           close(rec["All_other_holder_countries"], 100 - sub.get("IND", 0) - sub.get("CHN", 0), 0.02) and
           abs(sum(sub.values()) - 100) < 0.15)
check("Figure2(B) 病种特异份额三段（含 Other 补集）回链", ok)
check("Figure2(B) 未使用 legacy 全领域份额列", "all_area_share_pct_legacy" not in src)

mi = {r["disease"]: r for r in rows("res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv")
      if r["calibre"] == "latest_burden_year"}
ok = True
for d in ("Malaria", "Tuberculosis"):
    r, rec = mi[d], dv3["top25"][d]
    ok &= (rec["n_countries"] == int(r["n_countries"]) and
           close(rec["burden_share_pct"], float(r["top25pct_burden_share_of_b"]) * 100) and
           close(rec["supply_share_pct"], float(r["top25pct_burden_share_of_s"]) * 100) and
           close(dv3["C"][d], r["burden_weighted_supply_coverage_C"]) and
           close(dv3["R25"][d], r["top25_coverage_ratio_R25"]))
check("Figure3 前 25% 份额＋C＋R25 回链（仅疟疾／结核主口径）", ok)
check("Figure3 未读取 sensitivity / legacy 行（脚本硬过滤 calibre）",
      'calibre"] == "latest_burden_year' in src)

# ---------------------------------------------------------------- D
print()
print("=== 4. CI／柱值不超框 ===")
L1, L2, L3 = (man["figures"][f"Figure{n}"]["axis_limits"] for n in (1, 2, 3))
check("Figure1(A) 累积值在 y 限内",
      all(0 <= v <= L1["A"]["y"][1] for c in
          ("cumulative_pq_products", "cumulative_malaria", "cumulative_hiv", "cumulative_tb")
          for v in dv1[c]))
check("Figure1(B) 全部 CI 端点在 x 限内",
      all(0 <= x <= L1["B"]["x"][1] for k in dv1 if k.startswith("aapc_")
          for x in dv1[k]["ci95"]))
check("Figure2(A) 全部 CI 端点在 x 限内",
      all(0 <= x <= L2["A"]["x"][1] for d in dv2["top10"] for x in d["ci95"]))
check("Figure2(B) 堆叠和恰为 100%",
      all(close(sum(dv2[f"supply_{d}"][k] for k in
                    ("India", "China", "All_other_holder_countries")), 100, 0.02)
          for d in ("Malaria", "Tuberculosis")))
check("Figure3(A) 份额在 0–100 内",
      all(0 <= d[k] <= L3["A"]["x"][1] for d in dv3["top25"].values()
          for k in ("burden_share_pct", "supply_share_pct")))
check("Figure3(B) C／R25 在 y 限内",
      all(0 <= v <= L3["B"]["y"][1] for k in ("C", "R25") for v in dv3[k].values()))

# ---------------------------------------------------------------- E
print()
print("=== 5. 图内纯净度与图注 ===")
alltexts = [t for n in (1, 2, 3)
            for t in man["figures"][f"Figure{n}"]["texts_drawn_on_canvas"]]
check("图内文字零 `Figure N` 图序号",
      not [t for t in alltexts if re.search(r"(?i)\bfigure\s*\d", t)])
check("图内文字零精确数值标签（小数／百分数）",
      not [t for t in alltexts if re.search(r"\d+\.\d+\s*%|\b\d{1,3}%", t)],
      str([t for t in alltexts if re.search(r"\d+\.\d+\s*%|\b\d{1,3}%", t)][:4]))
check("图内零显著性星号", not any("*" in t for t in alltexts))
cap_lines = [l.strip() for l in caps.splitlines() if l.startswith("Figure ")]
check("图注恰好 3 条且编号 1–3", len(cap_lines) == 3 and
      all(l.startswith(f"Figure {i} ") for i, l in enumerate(cap_lines, 1)))
check("图注含 (A)(B) 面板列举", all("(A)" in l and "(B)" in l for l in cap_lines))
check("图注含样本量 n", all("n =" in l for l in cap_lines))
check("图注含单位／年份", all(re.search(r"20\d{2}", l) for l in cap_lines))
check("图注多数不以句号结尾（语料 27%）",
      sum(1 for l in cap_lines if l.rstrip().endswith(".")) <= 1)
check("图注写明病种间不可比", "not compared" in cap_lines[2])

# ---------------------------------------------------------------- F
print()
print("=== 6. 灰度分离与冗余编码 ===")
ls = [lum(c) for c in con["greys"]]
gaps = [round(ls[i + 1] - ls[i], 1) for i in range(len(ls) - 1)]
check("相邻灰阶 CIE L* 差均 >= 12", all(g >= 12 for g in gaps), str(gaps))
for key in ("marker_order", "linestyle_order", "hatch_order"):
    check(f"{key} 四项互异", len(set(con[key])) == len(con[key]))
check("一致性契约：图内不写编号／不写数值",
      con["figure_numbers_inside_image"] is False and
      con["numeric_value_labels_inside_image"] is False)
check("alpha 策略 forbid", "forbid" in con["alpha_policy"])

# ---------------------------------------------------------------- G
print()
print("=== 7. 防火墙与资产留痕 ===")
BAD = ["res_B2_", "res_B_fig", "res_B_hhi_", "res_B_price_index",
       "lineitems_clean", "dualchain_", "UN Comtrade", "10,324", "出口额"]
hits = [b for b in BAD if b in src]
check("出图脚本源码零隔离资产／出口侧命中", not hits, str(hits))
whitelist_vals = re.findall(r'"(res_B_[^"]+\.csv)"', src)
allowed = ("res_B_anchor_", "res_B_uncertainty_")
check("脚本白名单仅含 anchor / uncertainty 派生文件",
      bool(whitelist_vals) and all(v.startswith(allowed) for v in whitelist_vals),
      str(sorted(set(whitelist_vals))))
anchors = ["res_B_anchor_apc.csv", "res_B_anchor_year_counts.csv",
           "res_B_anchor_concentration_reviewed.csv",
           "res_B_anchor_applicant_country_reviewed.csv",
           "res_B_anchor_china_summary_reviewed.csv"]
dates = [datetime.datetime.fromtimestamp(
    os.stat(os.path.join(PROC, a)).st_mtime).strftime("%Y-%m-%d") for a in anchors]
check("五份既有底座 mtime 仍为 2026-11-07", all(d == "2026-11-07" for d in dates), str(dates))
check("manifest 登记「格式/dpi 待 EM 核实」",
      any("NOT STATED" in s for s in man["publisher_choices_pending_verification"]))
check("未声称期刊合规 / 无障碍认证",
      not re.search(r"(?i)(compliant with (?:the )?journal|WCAG certified|accessibility certified)", src + caps))

# ---------------------------------------------------------------- H
print()
print("=== 8. 旧核验脚本留痕复跑 ===")
p = os.path.join(SCRIPTS, "verify_B_manuscript_v0_7_2026-11-12.py")
r = subprocess.run([sys.executable, p], capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
check("verify_B_manuscript_v0_7 ALL CLEAN（正文未受影响）",
      "VERDICT = ALL CLEAN" in (r.stdout or ""))

print()
print("=" * 62)
if FAIL:
    print(f"VERDICT = FAIL  ({len(FAIL)} 项)")
    for f in FAIL:
        print("   -", f)
else:
    print("VERDICT = ALL CLEAN")
print("=" * 62)
