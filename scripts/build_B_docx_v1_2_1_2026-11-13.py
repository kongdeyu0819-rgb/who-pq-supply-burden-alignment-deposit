# -*- coding: utf-8 -*-
"""B① 唯一固定版本 v1.2.1 · Word 装配（2026-11-13）

输入（只读）：
  - 49 号 v1.2.1 主稿 PART I
  - 48 号 v1.2.1 补充材料 S1–S8
  - 配图_v1.2_2026-11-12/Figure1–3.png（图件不变）

输出（投稿包_v1.2.1_唯一固定版本_2026-11-13/）：
  - B①_TMIH_主稿_v1.2.1.docx
  - B①_TMIH_补充材料_S1-S8_v1.2.1.docx

相对 v1.2 Word 的排版修订：
  - 补材 S1–S8 八个小节标题套用 Word Heading 2 样式（导航窗格可见层级），
    并保留独立的 Table/Notes S*. 表题文字；
  - 全部表格首行设置 w:tblHeader，跨页自动重复表头；
  - 全部数据行设置 w:cantSplit，避免单元格文字跨页断裂；
  - 补材页面设为 A4 横向，十列对账表与八列来源表不再挤压；宽表字号 8 pt；
  - 主稿页面保持纵向，排版口径与 v1.2 一致。
不重写 prose、不改任何数值、不改三张图件。
"""
import importlib.util
import os
import re

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "base_docx", os.path.join(HERE, "build_B_docx_2026-11-12.py")
)
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

MAIN = base.MAIN
OUTDIR = os.path.join(MAIN, "投稿包_v1.2.1_唯一固定版本_2026-11-13")
SRC_MAN = os.path.join(MAIN, "49_B①主稿_v1.2.1_唯一固定版本_2026-11-13.md")
SRC_SUPP = os.path.join(MAIN, "48_B①主稿_补充材料_v1.2.1_S1-S8_2026-11-13.md")
FIGDIR = os.path.join(MAIN, "配图_v1.2_2026-11-12")
DOCX_MAN = os.path.join(OUTDIR, "B①_TMIH_主稿_v1.2.1.docx")
DOCX_SUPP = os.path.join(OUTDIR, "B①_TMIH_补充材料_S1-S8_v1.2.1.docx")

REQUIRED_MAN = (
    "[1,2,3]", "[13]", "Figure 1(A,B)", "Table S2", "Table S6",
    "MALARIA_EST_CASES", "13.19%", "1.9225", "93.92%", "0.3082", "0.0652",
    "release v1.2.1", "136 unique non-blank names",
)
STALE = ("release v1.2.0:", "/tree/v1.2.0)", "137 unique names",
         "approximately 15 firms", "1.9118", "91.44% of estimated malaria burden and 6.12%")
REQUIRED_SUPP = tuple(f"## S{i}." for i in range(1, 9)) + (
    "primary_incidence_times_population", "primary_PLHIV_counts",
    "calibre_record_denominator_unchanged", "burden_observed_only",
    "India records present?", "136 unique non-blank", "n_products totals 649",
    "MALARIA_EST_CASES", "13.19%", "1.9225", "1.9118",
)


def check_table_shapes(text, label):
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


def set_header_repeat(table):
    trPr = table.rows[0]._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def set_no_split(table):
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        el = OxmlElement("w:cantSplit")
        trPr.append(el)


def polish_tables(doc, wide_pt=8):
    n_head, n_wide = 0, 0
    for t in doc.tables:
        set_header_repeat(t)
        set_no_split(t)
        n_head += 1
        if len(t.columns) >= 8:
            n_wide += 1
            for row in t.rows:
                for c in row.cells:
                    for p in c.paragraphs:
                        for r in p.runs:
                            r.font.size = base.Pt(wide_pt)
    return n_head, n_wide


def polish_supp_headings(doc):
    n = 0
    for p in doc.paragraphs:
        if re.match(r"^S[1-8]\.\s", p.text.strip()):
            p.style = doc.styles["Heading 2"]
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                base.style_run(r, size=12, bold=True)
                r.font.color.rgb = RGBColor(0, 0, 0)
            n += 1
    return n


def landscape(doc):
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = sec.page_height, sec.page_width
    return sec


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    base.FIGDIR = FIGDIR

    man = open(SRC_MAN, encoding="utf-8").read().split(
        "# PART I — Manuscript text", 1)[1].split("# PART II", 1)[0].strip()
    for k in REQUIRED_MAN:
        assert k in man, f"v1.2.1 主稿缺关键内容：{k}"
    for k in STALE:
        assert k not in man, f"v1.2.1 主稿残留旧内容：{k}"

    supp = open(SRC_SUPP, encoding="utf-8").read().strip()
    for k in REQUIRED_SUPP:
        assert k in supp, f"v1.2.1 补材缺关键内容：{k}"
    assert "137 unique names" not in supp
    t_man = check_table_shapes(man, "主稿")
    t_supp = check_table_shapes(supp, "补材")

    d1 = Document()
    base.setup(d1)
    c1 = base.render(d1, man, with_figures=True)
    h1, w1 = polish_tables(d1)
    d1.core_properties.title = (
        "Geographic alignment between certificate-holder countries of "
        "WHO-prequalified medicines and malaria, tuberculosis and HIV/AIDS burden"
    )
    d1.core_properties.subject = "TMIH Research Article, B① manuscript v1.2.1 (single fixed version)"
    d1.core_properties.keywords = "WHO prequalification; malaria; tuberculosis; HIV/AIDS; certificate-holder countries"
    d1.save(DOCX_MAN)

    d2 = Document()
    base.setup(d2)
    c2 = base.render(d2, supp, with_figures=False)
    landscape(d2)
    h2, w2 = polish_tables(d2)
    n_head_style = polish_supp_headings(d2)
    assert n_head_style == 8, f"套用 Heading 2 的小节标题只有 {n_head_style} 个，应为 8 个"
    d2.core_properties.title = "Supplementary material S1-S8 (v1.2.1, single fixed version)"
    d2.core_properties.subject = "TMIH Research Article, B① supplementary tables v1.2.1"
    d2.save(DOCX_SUPP)

    for p in (DOCX_MAN, DOCX_SUPP):
        assert os.path.getsize(p) > 20000, f"docx 疑似未嵌入内容：{p}"

    # 结构断言：送出去的这一件本身，而不是源 Markdown
    chk = Document(DOCX_SUPP)
    heads = [p.text.strip() for p in chk.paragraphs if p.style.name.startswith("Heading")]
    assert len(heads) == 8 and all(re.match(r"^S[1-8]\.", h) for h in heads), \
        f"补材 docx 标题层级异常：{heads}"
    for t in chk.tables:
        trPr = t.rows[0]._tr.find(qn("w:trPr"))
        assert trPr is not None and trPr.find(qn("w:tblHeader")) is not None, \
            "补材 docx 存在未设置重复标题行的表格"

    print("WROTE", os.path.basename(DOCX_MAN), f"({os.path.getsize(DOCX_MAN)//1024} KB)")
    print("  blocks:", c1, "| tables:", t_man, "| tables with repeated header:", h1)
    print("WROTE", os.path.basename(DOCX_SUPP), f"({os.path.getsize(DOCX_SUPP)//1024} KB)")
    print("  blocks:", c2, "| tables:", t_supp, "| repeated header:", h2, "| wide tables:", w2)
    print("  A4 landscape:", True, "| Heading 2 sections:", n_head_style)
    print("VERDICT = DOCX V1.2.1 OK")


if __name__ == "__main__":
    main()
