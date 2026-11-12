# -*- coding: utf-8 -*-
"""
apply_B_hhi_backfill_2026-11-11.py
B① 主稿 · HHI 历史档案回填（2026-11-11 用户裁定「回填」）

动作：把 12 §2.1、两份 16 的 §2.5 与 §5.3、15 §2 结果行、项目 MEMORY.md
里的 4073.8 统一改为 4175.53（95% CI 3737.94–4643.50），并把
「来源为 res_B_anchor_concentration_reviewed.csv」的错标更正为
「4073.8 出自复核前 res_B_anchor_concentration.csv 的 HHI_total=4073.76，已作废」。

边界：
- 只改上述 6 份 md 的指定行；不改任何 CSV、脚本输出、既有已验证数字。
- 两份 16 用完全相同的替换规则，写回后校验 MD5 一致。
- 07 号（历史锚定方案，与复核前 408 行/62.87% 绑定）及既往日期日志
  属历史留痕，按 append-only 不改，仅在本脚本输出中列出供核对。

运行：python apply_B_hhi_backfill_2026-11-11.py
"""
import os
import hashlib

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
PREP = os.path.join(ROOT, "论文B_重设计与后续研究方案_2026-11-06")
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
MEMDIR = os.path.join(ROOT, ".workbuddy", "memory")

F12 = os.path.join(PREP, "12_数据与结果整理清单_2026-11-10.md")
F15 = os.path.join(PREP, "15_投稿适配性评估_2026-11-10.md")
F16A = os.path.join(PREP, "16_B①主稿开场上下文包_2026-11-10.md")
F16B = os.path.join(MAIN, "16_B①主稿开场上下文包_2026-11-10.md")
FMEM = os.path.join(MEMDIR, "MEMORY.md")

SRC_NOTE = (
    "4073.8 出自复核前 `res_B_anchor_concentration.csv` 的 "
    "`HHI_total=4073.76`，已作废"
)

OLD_12 = "| 生产者集中度 HHI | 4073.8 | `res_B_anchor_concentration_reviewed.csv` |"
NEW_12 = (
    "| 生产者集中度 HHI | **4175.53**（95% CI 3737.94–4643.50） | "
    "`res_B_uncertainty_concentration_ci_2026-11-11.csv`"
    "（复核后 648 行精确份额平方和）；" + SRC_NOTE + " |"
)

OLD_16_HHI = (
    "| 生产者集中度 HHI | **4073.8** | `准备层/12` §2.1"
    "（引 `res_B_anchor_concentration_reviewed.csv`） |"
)
NEW_16_HHI = (
    "| 生产者集中度 HHI | **4175.53**（95% CI 3737.94–4643.50） | "
    "`res_B_uncertainty_concentration_ci_2026-11-11.csv`"
    "（复核后 648 行精确份额平方和）；" + SRC_NOTE + " |"
)

OLD_16_SRC = (
    "| `res_B_anchor_concentration_reviewed.csv` | **RQ2 集中度（复核后）**，29 国 | "
    "`iso3`、`product_rows`、`share_pct`、`n_holders`、`note` | "
    "Abstract/Results 3.3；HHI 4073.8 的取数底座；表A2／图A2 |"
)
NEW_16_SRC = (
    "| `res_B_anchor_concentration_reviewed.csv` | **RQ2 集中度（复核后）**，29 国 | "
    "`iso3`（实为 ISO2）、`product_rows`、`share_pct`、`n_holders`、`note` | "
    "Abstract/Results 3.3 的国别份额与 CRn 取数底座；表A2／图A2。"
    "HHI 取值 **4175.53（95% CI 3737.94–4643.50）** 以 "
    "`res_B_uncertainty_concentration_ci_2026-11-11.csv` 为准；" + SRC_NOTE + " |"
)

OLD_15 = "HHI 4073.8；印度 413 行(63.7%)/35 家"
NEW_15 = "HHI 4175.53（95% CI 3737.94–4643.50）；印度 413 行(63.7%)/35 家"

OLD_MEM = (
    "- 已验证数字（一律用 `*_reviewed.csv`）：AAPC 全 FPP 19.11%／疟疾 24.85%／"
    "HIV 14.75%／TB 18.28%；HHI 4073.8；印度 413 行(63.73%)/35 家；"
    "中国 52 行(8.02%)/≈15 家；中国 PQ 广度 疟疾 24/98、HIV 16/255、TB 1/126。"
    "复核前 408/62.87% 已作废。"
)
NEW_MEM = (
    "- 已验证数字（一律用 `*_reviewed.csv`；HHI 与全部不确定度用 "
    "`res_B_uncertainty_*_2026-11-11.csv`）：AAPC 全 FPP 19.11%／疟疾 24.85%／"
    "HIV 14.75%／TB 18.28%；**HHI 4175.53（95% CI 3737.94–4643.50）**；"
    "印度 413 行(63.73%)/35 家；中国 52 行(8.02%)/≈15 家；"
    "中国 PQ 广度 疟疾 24/98、HIV 16/255、TB 1/126。"
    "复核前 408/62.87% 与 HHI 4073.8（出自 `res_B_anchor_concentration.csv` 的 "
    "`HHI_total=4073.76`）均已作废；2026-11-11 用户裁定回填，"
    "正文／图表／摘要一律只用 4175.53。"
)

JOBS = [
    (F12, [(OLD_12, NEW_12)]),
    (F16A, [(OLD_16_HHI, NEW_16_HHI), (OLD_16_SRC, NEW_16_SRC)]),
    (F16B, [(OLD_16_HHI, NEW_16_HHI), (OLD_16_SRC, NEW_16_SRC)]),
    (F15, [(OLD_15, NEW_15)]),
    (FMEM, [(OLD_MEM, NEW_MEM)]),
]


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def apply(path, pairs):
    with open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig" if bom else "utf-8")
    for old, new in pairs:
        n = text.count(old)
        if n != 1:
            raise RuntimeError(f"锚点不唯一或未找到（n={n}）：{os.path.basename(path)} :: {old[:60]}")
        text = text.replace(old, new, 1)
    out = text.encode("utf-8")
    if bom:
        out = b"\xef\xbb\xbf" + out
    with open(path, "wb") as f:
        f.write(out)
    return len(pairs)


print("=== HHI 回填（4175.53，95% CI 3737.94–4643.50）===")
for path, pairs in JOBS:
    k = apply(path, pairs)
    print(f"  OK  {k} 处  {os.path.relpath(path, ROOT)}")

a, b = md5(F16A), md5(F16B)
print()
print(f"准备层 16 MD5 = {a}")
print(f"主稿   16 MD5 = {b}")
print("两份 16 一致性：" + ("PASS（逐字节一致）" if a == b else "FAIL"))
print()
print("=== 全项目仍含 4073.8 / 4073.76 的 md（预期仅历史留痕）===")
for base, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
    for fn in files:
        if not fn.endswith(".md"):
            continue
        p = os.path.join(base, fn)
        try:
            t = open(p, encoding="utf-8-sig").read()
        except OSError:
            continue
        if "4073.8" in t or "4073.76" in t:
            print("  " + os.path.relpath(p, ROOT))
