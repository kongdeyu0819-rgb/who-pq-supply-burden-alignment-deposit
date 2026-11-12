# -*- coding: utf-8 -*-
"""
B① 主稿 · v1.2 docx 排版件装配，2026-11-12

输入（全部只读）：
  - 39 号 v1.2 分母重算定稿稿 PART I（主稿全文）
  - 40 号补充材料 v1.2（S1–S8 全文）
  - 配图_v1.2_2026-11-12/Figure1–3.png

输出（投稿包_2026-11-12/）：
  - B①_TMIH_主稿_v1.2_2026-11-12.docx
  - B①_TMIH_补充材料_v1.2_S1-S8_2026-11-12.docx

排版函数复用 build_B_docx_2026-11-12.py（Times New Roman 12 pt、双倍行距、
2.54 cm 页边距、页码、真 Word 表格、References 悬挂缩进、图注前插图）。
不重写任何 prose、不改任何数值、不改三张图件。v1.0/v1.1 冻结件不回写。

运行：python build_B_docx_v1_2_2026-11-12.py
"""
import importlib.util
import os
import re

from docx import Document

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "base_docx", os.path.join(HERE, "build_B_docx_2026-11-12.py")
)
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

MAIN = base.MAIN
OUTDIR = base.OUTDIR
SRC_MAN = os.path.join(MAIN, "39_B①主稿_v1.2_分母重算定稿_2026-11-12.md")
SRC_SUPP = os.path.join(MAIN, "40_B①主稿_补充材料_v1.2_S1-S8_2026-11-12.md")
FIGDIR = os.path.join(MAIN, "配图_v1.2_2026-11-12")
DOCX_MAN = os.path.join(OUTDIR, "B①_TMIH_主稿_v1.2_2026-11-12.docx")
DOCX_SUPP = os.path.join(OUTDIR, "B①_TMIH_补充材料_v1.2_S1-S8_2026-11-12.docx")

REQUIRED_MAN = (
    "[1,2,3]", "[13]", "Figure 1(A,B)", "Table S2", "Table S6",
    "MALARIA_EST_CASES", "13.19%", "1.9225", "93.92%", "0.3082", "0.0652",
)
STALE_PRIMARY = ("1.9118", "1.8505–1.9527", "91.44% of estimated malaria burden and 6.12%")
REQUIRED_SUPP = (
    "## Table S1.", "## Table S2.", "## Notes S3.", "## Table S4.",
    "## Table S5.", "## Table S6.", "## Table S7.", "## Table S8.",
    "MALARIA_EST_CASES", "13.19%", "1.9225", "1.9118",
)


def check_table_shapes(text, label):
    """所有 Markdown 表格块列数一致，避免 docx 排版层静默截断。"""
    blocks = re.split(r"\n\s*\n", text.strip())
    n = 0
    for b in blocks:
        lines = [l.rstrip() for l in b.splitlines() if l.strip()]
        if not lines or not all(l.startswith("|") for l in lines):
            continue
        body = [l for l in lines if not re.match(r"^\|[\s:\-|]+\|$", l.strip())]
        widths = {len(l.strip().strip("|").split("|")) for l in body}
        assert len(widths) == 1, f"{label} 表格列数不一致：{widths} / {body[0][:80]}"
        n += 1
    return n


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    base.FIGDIR = FIGDIR

    man_raw = open(SRC_MAN, encoding="utf-8").read()
    man = man_raw.split("# PART I — Manuscript text", 1)[1].split("# PART II", 1)[0].strip()
    for k in REQUIRED_MAN:
        assert k in man, f"v1.2 主稿缺关键内容：{k}"
    for k in STALE_PRIMARY:
        assert k not in man, f"v1.2 主稿残留旧主结果：{k}"
    # 对照数值只允许 Results 3.4 与 Discussion 4.4 两处方向性说明
    for token in ("0.0670", "0.3184"):
        assert man.count(token) == 1, f"对照数值 {token} 在主文命中 {man.count(token)} 次，应为 1 次"

    supp = open(SRC_SUPP, encoding="utf-8").read().strip()
    for k in REQUIRED_SUPP:
        assert k in supp, f"v1.2 补材缺关键内容：{k}"
    t_man = check_table_shapes(man, "主稿")
    t_supp = check_table_shapes(supp, "补材")

    d1 = Document()
    base.setup(d1)
    c1 = base.render(d1, man, with_figures=True)
    d1.core_properties.title = (
        "Geographic alignment between certificate-holder countries of "
        "WHO-prequalified medicines and malaria, tuberculosis and HIV/AIDS burden"
    )
    d1.core_properties.subject = "TMIH Research Article, B① manuscript v1.2 (official malaria case-count denominator)"
    d1.core_properties.keywords = "WHO prequalification; malaria; tuberculosis; HIV/AIDS; certificate-holder countries"
    d1.save(DOCX_MAN)

    d2 = Document()
    base.setup(d2)
    c2 = base.render(d2, supp, with_figures=False)
    d2.core_properties.title = "Supplementary material S1-S8 (v1.2)"
    d2.core_properties.subject = "TMIH Research Article, B① supplementary tables v1.2"
    d2.save(DOCX_SUPP)

    for p in (DOCX_MAN, DOCX_SUPP):
        assert os.path.getsize(p) > 20000, f"docx 疑似未嵌入内容：{p}"

    print("WROTE", os.path.basename(DOCX_MAN), f"({os.path.getsize(DOCX_MAN)//1024} KB)")
    print("  blocks:", c1, "| markdown tables:", t_man)
    print("WROTE", os.path.basename(DOCX_SUPP), f"({os.path.getsize(DOCX_SUPP)//1024} KB)")
    print("  blocks:", c2, "| markdown tables:", t_supp)
    print("figure files:", [f"Figure{n}.png" for n in (1, 2, 3)])
    print("VERDICT = DOCX V1.2 OK")


if __name__ == "__main__":
    main()
