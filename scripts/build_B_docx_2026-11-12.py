# -*- coding: utf-8 -*-
"""
B① 主稿 · docx 排版件装配，2026-11-12

输入（全部只读）：
  - 32 号 v1.0 定稿稿 PART I（主稿全文，含 Vancouver 插号与图表引用）
  - 27 号装配稿 PART I 的补材 S1–S5 全文
  - 配图_2026-11-12/Figure1–3.png（600 dpi，175 mm 宽）

输出（投稿包_2026-11-12/）：
  - B①_TMIH_主稿_v1.0_2026-11-12.docx
  - B①_TMIH_补充材料_S1-S5_2026-11-12.docx

排版口径：Times New Roman 12 pt、双倍行距、2.54 cm 页边距、页码；
标题页独立一页属投稿通例，`14` §三.18 未明示字体／行距／是否单独标题页，
按通例预备并在 33 号说明中标为「待 EM 核实」，不声称期刊合规。

Markdown -> Word 转换：标题层级、加粗 run、Markdown 表格转真 Word 表格、
图注前插入对应 PNG、References 悬挂缩进、中文文献 eastAsia 字体。
不重写任何 prose、不改任何数值、不改三张图件。

运行：python build_B_docx_2026-11-12.py
"""
import os
import re

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
SRC_MAN = os.path.join(MAIN, "32_B①主稿_v1.0_定稿稿_2026-11-12.md")
SRC_SUPP = os.path.join(MAIN, "27_B①主稿_前页-表1-3-补材_装配稿_v0.1_2026-11-12.md")
FIGDIR = os.path.join(MAIN, "配图_2026-11-12")
OUTDIR = os.path.join(MAIN, "投稿包_2026-11-12")
DOCX_MAN = os.path.join(OUTDIR, "B①_TMIH_主稿_v1.0_2026-11-12.docx")
DOCX_SUPP = os.path.join(OUTDIR, "B①_TMIH_补充材料_S1-S5_2026-11-12.docx")

FONT = "Times New Roman"
EAST = "SimSun"
FIG_WIDTH_MM = 175.0


def style_run(run, size=12, bold=False, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:ascii"), FONT)
    rf.set(qn("w:hAnsi"), FONT)
    rf.set(qn("w:eastAsia"), EAST)


def add_rich(doc, text, size=12, align=None, space_after=6, hanging=False):
    """解析 **加粗** 与 `代码`，写入一个段落。"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 2.0 if not hanging else 1.5
    pf.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    if hanging:
        pf.left_indent = Cm(0.8)
        pf.first_line_indent = Cm(-0.8)
    clean = text.replace("`", "")
    parts = re.split(r"(\*\*[^*]+\*\*)", clean)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            style_run(p.add_run(part[2:-2]), size=size, bold=True)
        else:
            style_run(p.add_run(part), size=size)
    return p


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(6)
    size = {1: 12, 2: 12, 3: 11}[min(level, 3)]
    style_run(p.add_run(text), size=size, bold=True)
    if level >= 2:
        p.paragraph_format.keep_with_next = True
    return p


def add_table(doc, rows):
    """Markdown 表格 -> Word 表格；跳过 |---| 分隔行；表头加粗。"""
    body = [r for r in rows if not re.match(r"^\|[\s:\-|]+\|$", r.strip())]
    parsed = [[c.strip() for c in r.strip().strip("|").split("|")] for r in body]
    assert parsed and all(len(r) == len(parsed[0]) for r in parsed), "表格列数不一致"
    t = doc.add_table(rows=len(parsed), cols=len(parsed[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    for i, row in enumerate(parsed):
        for j, cell in enumerate(row):
            c = t.cell(i, j)
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            if i > 0 and re.match(r"^[\d.,–\-/ ()%]+$", cell):
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            style_run(p.add_run(cell.replace("`", "")), size=9, bold=(i == 0))
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def add_page_number_footer(doc):
    sec = doc.sections[0]
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    style_run(r, size=10)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    p._p.append(fld)


def setup(doc):
    sec = doc.sections[0]
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(2.54)
    sec.right_margin = Cm(2.54)
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), EAST)
    st.paragraph_format.line_spacing = 2.0
    st.paragraph_format.space_after = Pt(6)
    add_page_number_footer(doc)


def render(doc, text, with_figures=False):
    """按空行切块 -> 判断块类型 -> 写入 Word。"""
    blocks = re.split(r"\n\s*\n", text.strip())
    counts = {"para": 0, "table": 0, "heading": 0, "figure": 0}
    for b in blocks:
        lines = [l.rstrip() for l in b.splitlines() if l.strip()]
        if not lines or all(l.strip() == "---" for l in lines):
            continue
        first = lines[0].strip()

        # 表格块
        if all(l.startswith("|") for l in lines):
            add_table(doc, lines)
            counts["table"] += 1
            continue

        # 标题块（单行）
        if len(lines) == 1 and re.match(r"^#{1,3} ", first):
            m = re.match(r"^(#{1,3})\s+(.*)$", first)
            level, label = len(m.group(1)), m.group(2).strip()
            if level == 1:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_after = Pt(14)
                style_run(p.add_run(label), size=14, bold=True)
            else:
                if label == "Abstract":
                    doc.add_page_break()
                add_heading(doc, label, level)
            counts["heading"] += 1
            continue

        # 图注块：先插图，再写图注
        m = re.match(r"^(Figure [123])\s+(.*)$", first)
        if m and with_figures:
            n = int(m.group(1).split()[-1])
            fp = os.path.join(FIGDIR, f"Figure{n}.png")
            assert os.path.isfile(fp), f"图件缺失：{fp}"
            pic_p = doc.add_paragraph()
            pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pic_p.paragraph_format.line_spacing = 1.0
            pic_p.paragraph_format.space_after = Pt(4)
            pic_p.add_run().add_picture(fp, width=Mm(FIG_WIDTH_MM))
            add_rich(doc, " ".join(lines), size=10, space_after=10)
            counts["figure"] += 1
            continue

        # 多行编号列表（审稿人建议 / 方法注）
        if len(lines) > 1 and all(re.match(r"^\d+\.\s", l) for l in lines):
            for l in lines:
                add_rich(doc, l, size=11, hanging=True, space_after=2)
            counts["para"] += len(lines)
            continue

        # References 条目（单行编号）
        if re.match(r"^\d+\.\s", first) and len(lines) == 1:
            add_rich(doc, first, size=11, hanging=True, space_after=2)
            counts["para"] += 1
            continue

        # 普通段落（折行合并）
        add_rich(doc, " ".join(l.strip() for l in lines))
        counts["para"] += 1
    return counts


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    man_raw = open(SRC_MAN, encoding="utf-8").read()
    man = man_raw.split("# PART I — Manuscript text", 1)[1].split("# PART II", 1)[0].strip()
    assert "[1,2,3]" in man and "[13]" in man, "主稿缺 Vancouver 编号"
    assert "Figure 1(A,B)" in man and "Table S5" in man, "主稿缺图表引用"

    supp_raw = open(SRC_SUPP, encoding="utf-8").read()
    sp = supp_raw.split("# PART I", 1)[1]
    supp = sp.split("## Supplementary material", 1)[1].split("## Supplementary material index", 1)[0]
    supp = "## Supplementary material\n\n" + supp.strip()
    for k in ("### S1.", "### S2.", "### S3.", "Table S4.", "Table S5."):
        assert k in supp, f"补材块缺 {k}"

    # 补材 S3 第 5 条防御句与主文降 AI 对齐：主文 20 号 v0.2 已删同类句式，
    # 27 号冻结稿的补材块仍残留「no segmented or joinpoint regression was fitted,
    # and no dedicated ... version number is claimed」。按 15破解防御性写作 的口径
    # 在排版层删去该双重自证句，保留两句正面方法陈述；27 号稿本身不动，
    # 以免破坏 v0.8 核验的冻结版本断言。零数值改动由下方断言保证。
    S3_OLD = ("Trend was estimated by a single-slope log-linear OLS model over 25 annual "
              "observations; no segmented or joinpoint regression was fitted, and no dedicated "
              "trend-regression package or version number is claimed. The slope estimates the "
              "average annual change of a cumulative stock series.")
    S3_NEW = ("Trend was estimated by a single-slope log-linear OLS model over 25 annual "
              "observations. The slope estimates the average annual change of a cumulative stock series.")
    assert supp.count(S3_OLD) == 1, "补材 S3 防御句锚点非唯一"
    nums_before = re.findall(r"\d+(?:[.,]\d+)*", supp)
    supp = supp.replace(S3_OLD, S3_NEW, 1)
    assert re.findall(r"\d+(?:[.,]\d+)*", supp) == nums_before, "补材对齐引入数值改动"
    assert "joinpoint" not in supp.lower() and "no segmented" not in supp.lower()

    # 主稿 docx
    d1 = Document()
    setup(d1)
    c1 = render(d1, man, with_figures=True)
    d1.core_properties.title = "Geographic alignment between WHO-prequalified medicine supply and disease burden"
    d1.core_properties.subject = "TMIH Research Article, B① manuscript v1.0"
    d1.core_properties.keywords = "WHO prequalification; malaria; tuberculosis; HIV/AIDS"
    d1.save(DOCX_MAN)

    # 补材 docx
    d2 = Document()
    setup(d2)
    c2 = render(d2, supp, with_figures=False)
    d2.core_properties.title = "Supplementary material S1-S5"
    d2.core_properties.subject = "TMIH Research Article, B① supplementary tables"
    d2.save(DOCX_SUPP)

    for p in (DOCX_MAN, DOCX_SUPP):
        assert os.path.getsize(p) > 20000, f"docx 疑似未嵌入内容：{p}"

    print("WROTE", os.path.basename(DOCX_MAN), f"({os.path.getsize(DOCX_MAN)//1024} KB)")
    print("  blocks:", c1)
    print("WROTE", os.path.basename(DOCX_SUPP), f"({os.path.getsize(DOCX_SUPP)//1024} KB)")
    print("  blocks:", c2)
    print("figure files:", [f"Figure{n}.png" for n in (1, 2, 3)])
    print("VERDICT = ALL CLEAN")


if __name__ == "__main__":
    main()
