# -*- coding: utf-8 -*-
"""B① 返修 · 生成并执行 v1.2 出图脚本（2026-11-12）

原 draw_B_figures_2026-11-12.py 是配图轮冻结件，不回写。
本脚本以字符串补丁方式从它派生 v1.2 版，改动仅四处：
  1. 对齐数据源指向官方病例数主口径表 res_B_burden_primary_2026-11-12.csv；
  2. 输出目录改为 配图_v1.2_2026-11-12/；
  3. Figure 1(A) 纵轴、Figure 3 图例与 3(B) 纵轴按术语裁定改名；
  4. 图注直接从 39 号 v1.2 主稿实读，杜绝图文不一致。
每条补丁断言唯一命中；派生脚本独立可复跑。
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
MAIN = os.path.join(ROOT, "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）")
SRC = os.path.join(HERE, "draw_B_figures_2026-11-12.py")
DST = os.path.join(HERE, "draw_B_figures_v1_2_2026-11-12.py")
MANUSCRIPT = os.path.join(MAIN, "39_B①主稿_v1.2_分母重算定稿_2026-11-12.md")

src = open(SRC, encoding="utf-8").read()


def rep(old, new, count=None):
    global src
    c = src.count(old)
    assert c == (count if count is not None else 1), f"补丁命中 {c} 次：{old[:70]}"
    src = src.replace(old, new)


rep('    "配图_2026-11-12",', '    "配图_v1.2_2026-11-12",')
rep('"misalign": "res_B_uncertainty_misalignment_ci_revised_2026-11-11.csv"',
    '"misalign": "res_B_burden_primary_2026-11-12.csv"')
rep('mi = {r["disease"]: r for r in load("misalign")\n'
    '      if r["calibre"] == "latest_burden_year"}',
    'mi = {r["disease"]: r for r in load("misalign")}')
rep('ylabel="Cumulative products (n)"',
    'ylabel="Currently listed FPPs by prequalification year (cumulative n)"')
# manifest 的画布文字登记须与真实 ylabel 同字符串，否则元数据与图件不一致
rep('"Year", "Cumulative products (n)", "AAPC (% per year)"',
    '"Year", "Currently listed FPPs by prequalification year (cumulative n)", "AAPC (% per year)"')
rep('label="Supply share"', 'label="Listing-row share"')
rep('"Burden share", "Supply share",', '"Burden share", "Listing-row share",')
# 3(B) 纵轴与画布文字登记同一字符串，两处一并替换
rep('"Coverage index (0–1)"', '"C and R25 (0–1 index)"', count=2)

# 图注：从 v1.2 主稿实读，不再在出图脚本里另写一份
new_captions = '''CAPTIONS_BLOCK = r"""''' + MANUSCRIPT.replace("\\", "/") + '''"""
_m = open(CAPTIONS_BLOCK, encoding="utf-8").read()
_cap_lines = [l.strip() for l in _m.splitlines() if re.match(r"^Figure [123] ", l)]
assert len(_cap_lines) == 3, "主稿图注行数异常"
CAPTIONS = "# Figure captions (English, for the manuscript)\\n\\n" + \\
           "\\n\\n".join(_cap_lines) + "\\n"'''
src, n = re.subn(r'CAPTIONS = f""".*?"""', lambda _: new_captions, src, count=1, flags=re.S)
assert n == 1, "CAPTIONS 段替换失败"
# 主稿图注已自带全部年份与 n，不再需要动态年份变量
src = src.replace(
    '_burden_years = {d: f"{mi[d][\'burden_year_min\']}–{mi[d][\'burden_year_max\']}"\n'
    '                 for d in ("Malaria", "Tuberculosis")}\n', "")
# 出图脚本需要 re 与 MANUSCRIPT 路径
src = src.replace("import os\n", "import os\nimport re\n", 1)
src = src.replace('"""\nimport csv', '"""\nimport csv', 1)

open(DST, "w", encoding="utf-8").write(src)
print(f"派生脚本：{os.path.basename(DST)}")
r = subprocess.run([sys.executable, DST], cwd=HERE, capture_output=True, text=True)
print(r.stdout[-2500:])
if r.returncode != 0:
    print(r.stderr[-2500:])
    raise SystemExit(r.returncode)
print("VERDICT = FIGURES V1.2 OK")
