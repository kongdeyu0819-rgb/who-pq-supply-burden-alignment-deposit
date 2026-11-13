# -*- coding: utf-8 -*-
"""B① · v1.2.1 公开仓库本地镜像构建（离线），2026-11-13

策略：`公开仓库_v1.2_2026-11-12/`（对应真实 tag v1.2.0）冻结不回写；
新建 `公开仓库_v1.2.1_2026-11-13/`，作为与唯一送审包一致的固定版本。

v1.2.1 相对 v1.2.0 只做标签语义、定义、措辞、留痕与排版修订，统计数值零改动：
  * 三张既有派生表以 v1.2.1 修订版替换（脚本逐格断言除允许列外完全相同）；
  * 新增标签字典、结核外部效标分组、India 记录核查与两份修订台账；
  * 新增三张送审 TIFF 图件与 v1.2.1 全链可复跑脚本；
  * 根文件 DAS／README／REPRODUCE 改指 v1.2.1，v1.0.0 与 v1.2.0 登记为历史版本。

新增／替换文件逐件做凭据与四篇防火墙扫描，并额外做对外元说明扫描。
MANIFEST 不自登记（与 v1.0.0／v1.2.0 结构一致）。

运行：python build_B_deposit_v1_2_1_2026-11-13.py
"""
import csv
import datetime
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(r"D:\D\我的论文\全球卫生新博士课题")
MAIN = ROOT / "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）"
SCRIPTS = ROOT / "数据" / "scripts"
PROC_V = ROOT / "数据" / "processed_v1.2.1_2026-11-13"
SUBMISSION = MAIN / "投稿包_v1.2.1_唯一固定版本_2026-11-13"
BASE = MAIN / "公开仓库_v1.2_2026-11-12"
NEW = MAIN / "公开仓库_v1.2.1_2026-11-13"
TAG = "v1.2.1"
HTML = "https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit"

# 三张既有表的替换：路径、源、允许改动列、是否允许新增行
UPDATED = [
    ("data/processed/res_B_burden_primary_2026-11-12.csv",
     "res_B_burden_primary_2026-11-12.csv", {"method_note"}, False),
    ("data/processed/res_B_burden_sensitivity_2026-11-12.csv",
     "res_B_burden_sensitivity_2026-11-12.csv", {"calibre", "note"}, False),
    ("data/processed/res_B_country_set_reconciliation_2026-11-12.csv",
     "res_B_country_set_reconciliation_2026-11-12.csv", {"calibre", "note"}, True),
]

NEW_DATA = [
    "res_B_calibre_dictionary_2026-11-13.csv",
    "res_B_tb_benchmark_summary_2026-11-13.csv",
    "res_B_india_record_check_2026-11-13.json",
    "res_B_notes_change_audit_2026-11-13.json",
    "res_B_manuscript_v1_2_1_change_audit.json",
]

NEW_SCRIPTS = [
    "revise_B_derived_notes_v1_2_1_2026-11-13.py",
    "make_B_supplement_v1_2_1_2026-11-13.py",
    "build_B_supplement_v1_2_1_2026-11-13.py",
    "revise_B_manuscript_v1_2_1_2026-11-13.py",
    "build_B_docx_v1_2_1_2026-11-13.py",
    "make_B_pdf_proof_v1_2_1_2026-11-13.py",
    "build_B_pdf_proof_v1_2_1_2026-11-13.py",
    "audit_B_pdf_pages_v1_2_1_2026-11-13.py",
    "build_B_unique_version_v1_2_1_2026-11-13.py",
    "verify_B_manuscript_v1_2_1_2026-11-13.py",
    "build_B_deposit_v1_2_1_2026-11-13.py",
    "publish_B_deposit_v1_2_1_2026-11-13.py",
    "verify_B_deposit_v1_2_1_2026-11-13.py",
]

NEW_FIGURES = ["Figure1.tif", "Figure2.tif", "Figure3.tif"]

# 第三段拆开拼装，避免扫描器在自身源码里命中自己写下的字面量。
CRED = re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
                  + b"comtrade" + rb"[\._]key", re.I)
BAD = [b"comtrade", b"hs_code", b"U1/U2/U3", b"export value",
       b"dualchain_china_pq_access"]
# 只拦曾出现在对外件里的「字母加数字」自造层级编号与中文工序代号。
# B1 是论文 B① 在仓库 schema、commit message 与 release 说明里沿用的项目标识，
# 自 v1.0.0 起已公开，不作为元说明拦截对象。
META = re.compile(r"\b(?:M|X)\d{1,3}\b|\bA\d{2,3}\b|\b\d{2}\s*号(?:稿|件|文件|主稿)")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rows(p):
    if p.suffix.lower() != ".csv":
        return None
    with open(p, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def cload(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def assert_numeric_zero_change(old_p, new_p, editable, allow_extra):
    """v1.2.1 数值零改动门禁：除允许列外逐格相同；允许按口径新增行。

    采用「非可编辑列取值元组」的多重集合比对，不依赖行顺序（对账表新增的
    burden_observed_only 行按病种插入，原 9 行顺序可能已变化）。
    """
    from collections import Counter
    a, b = cload(old_p), cload(new_p)
    if allow_extra:
        extra = [r for r in b if r["calibre"] == "burden_observed_only"]
        assert len(extra) == 3, f"{new_p.name} burden_observed_only 行数不是 3"
        b_check = [r for r in b if r["calibre"] != "burden_observed_only"]
    else:
        b_check = b
    assert len(a) == len(b_check), f"{new_p.name} 原有行数变化：{len(a)} -> {len(b_check)}"
    assert a and all(x.keys() == b_check[0].keys() for x in a), f"{new_p.name} 列名变化"
    keys = [k for k in a[0] if k not in editable]
    sig = lambda rows: Counter(tuple(r[k] for k in keys) for r in rows)
    sa, sb = sig(a), sig(b_check)
    assert sa == sb, (f"{new_p.name} 除允许列外存在数值改动："
                      f"旧表独有 {list((sa - sb).elements())[:2]} "
                      f"新表独有 {list((sb - sa).elements())[:2]}")
    return len(b)


def scan(p, layer):
    raw = p.read_bytes()
    assert not CRED.search(raw), f"命中凭据模式：{p}"
    if layer in ("data", "figure"):
        hits = [x.decode() for x in BAD if x in raw.lower()]
        assert not hits, f"{p} 命中四篇防火墙标识：{hits}"
    if p.suffix.lower() in (".py", ".md", ".json", ".csv"):
        t = raw.decode("utf-8", "ignore").replace("A4", "A-four")
        assert not META.search(t), f"{p} 含自造编号／内部元说明"


def main():
    assert BASE.is_dir() and (BASE / "MANIFEST.json").is_file(), "缺 v1.2.0 本地镜像"
    base_mf = json.loads((BASE / "MANIFEST.json").read_text(encoding="utf-8"))
    assert base_mf["repository"]["tag"] == "v1.2.0", "v1.2.0 镜像版本异常"
    assert (SUBMISSION / "MANIFEST.json").is_file(), "缺唯一送审包 MANIFEST"
    sub_mf = json.loads((SUBMISSION / "MANIFEST.json").read_text(encoding="utf-8"))
    assert sub_mf["version"] == TAG, "唯一送审包版本不是 v1.2.1"

    if NEW.exists():
        assert NEW.name == "公开仓库_v1.2.1_2026-11-13", "拒绝删除非本脚本产出的目录"
        shutil.rmtree(NEW)
    shutil.copytree(BASE, NEW, ignore=shutil.ignore_patterns(
        "_build_summary.json", "_build_summary_v1.2.json", "MANIFEST.json"))

    touched = {}   # rel -> (layer, note)
    # ---- 1) 三张既有表：替换并断言数值零改动 ----
    for rel, name, editable, allow_extra in UPDATED:
        src = PROC_V / name
        dst = NEW / rel
        assert src.is_file() and dst.is_file(), f"缺源或目标：{rel}"
        n = assert_numeric_zero_change(dst, src, editable, allow_extra)
        shutil.copyfile(src, dst)
        scan(dst, "data")
        touched[rel] = ("data", f"v1.2.1 label/definition correction; {n} rows; numeric cells unchanged")

    # ---- 2) 新增派生表 ----
    for name in NEW_DATA:
        src = PROC_V / name
        rel = "data/processed/" + name
        assert src.is_file(), f"缺派生表：{src}"
        assert not (NEW / rel).exists(), f"v1.2.0 已有同名文件，禁止覆盖：{rel}"
        shutil.copyfile(src, NEW / rel)
        scan(NEW / rel, "data")
        touched[rel] = ("data", "v1.2.1 calibre dictionary / external benchmark / change audit")

    # ---- 3) 新增送审图件 ----
    for name in NEW_FIGURES:
        src = SUBMISSION / name
        rel = "figures_v1_2_1/" + name
        assert src.is_file(), f"缺送审图件：{src}"
        dst = NEW / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        scan(dst, "figure")
        touched[rel] = ("figure", "TIFF figure file in the single fixed submission package; "
                                  "PNG equivalents are in figures_v1_2/")

    # ---- 4) 新增可复跑脚本 ----
    for name in NEW_SCRIPTS:
        src = SCRIPTS / name
        rel = "scripts/" + name
        assert src.is_file(), f"缺脚本：{src}"
        assert not (NEW / rel).exists(), f"v1.2.0 已有同名脚本，禁止覆盖：{rel}"
        shutil.copyfile(src, NEW / rel)
        scan(NEW / rel, "script")
        touched[rel] = ("script", "v1.2.1 single-fixed-version reproducible script")

    # ---- 5) 根文件版本同步 ----
    das_p = NEW / "DATA_AVAILABILITY_STATEMENT.md"
    das = das_p.read_text(encoding="utf-8")
    assert "release v1.2.0:" in das and "/tree/v1.2.0" in das
    das = das.replace("release v1.2.0:", "release v1.2.1:")
    das = das.replace("/tree/v1.2.0", "/tree/v1.2.1")
    old_par = ("Version v1.2.0 adds the WHO official estimated malaria case-count extract "
               "(MALARIA_EST_CASES, 2024 estimates), the recomputed burden and alignment tables, "
               "extended AAPC robustness results, country-set reconciliation, regenerated figures "
               "and the scripts that reproduce them. The earlier incidence-times-total-population "
               "construction is retained only as a sensitivity comparison. Release v1.0.0 remains "
               "available as the historical version.")
    assert old_par in das, "v1.2.0 DAS 段落与预期不符，拒绝静默改写"
    new_par = (
        "Version v1.2.1 is the single fixed version cited in the manuscript and is aligned with "
        "the submission package. Relative to v1.2.0 it corrects denominator-calibre labels so "
        "that only malaria is labelled as WHO official estimated case counts (tuberculosis uses "
        "incidence per 100,000 population x total population; HIV/AIDS uses people living with "
        "HIV prevalence counts), renames the burden-observed-only calibre, adds a calibre-label "
        "dictionary, a country-set reconciliation with an India-record check and a grouped "
        "tuberculosis external magnitude benchmark, and records the label and wording changes in "
        "two machine-readable audit files. No statistical value was changed. The primary malaria "
        "denominator remains MALARIA_EST_CASES (2024 estimates); the earlier "
        "incidence-times-total-population construction is retained only as a sensitivity "
        "comparison. Releases v1.0.0 and v1.2.0 are retained unchanged as historical versions.")
    das = das.replace(old_par, new_par)
    assert "release v1.2.1:" in das and "No statistical value was changed" in das
    das_p.write_text(das, encoding="utf-8")
    touched["DATA_AVAILABILITY_STATEMENT.md"] = ("root", "DAS points at the real v1.2.1 tag")

    rd_p = NEW / "README.md"
    rd = rd_p.read_text(encoding="utf-8")
    stale = ("Release `v1.0.0` is the version cited in the manuscript's data accessibility\n"
             "statement. Generated 2026-11-12.")
    assert stale in rd, "README 旧版本声明与预期不符"
    rd = rd.replace(stale, "The version cited in the manuscript's data accessibility statement is\n"
                           "release `v1.2.1` (see below). Generated 2026-11-13. Releases `v1.0.0`\n"
                           "and `v1.2.0` are retained unchanged as historical versions.")
    rd += ("\n\n## Version v1.2.1 (13 November 2026) — single fixed version\n\n"
           "This release matches the single fixed submission package. It contains the "
           "label-corrected versions of `res_B_burden_primary_2026-11-12.csv`, "
           "`res_B_burden_sensitivity_2026-11-12.csv` and "
           "`res_B_country_set_reconciliation_2026-11-12.csv` in `data/processed/`; all numeric "
           "cells are identical to v1.2.0, with only `method_note`, `calibre` and `note` columns "
           "changed and three burden-observed-only reconciliation rows added. New files: a calibre "
           "label dictionary, a grouped tuberculosis external magnitude benchmark, a machine-read "
           "India-record check, two change-audit files, the three TIFF figure files under "
           "`figures_v1_2_1/`, and the v1.2.1 reproducible scripts. The three primary denominator "
           "calibres are now labelled semantically rather than uniformly. No analysis was re-run "
           "and no statistical value changed.\n")
    rd_p.write_text(rd, encoding="utf-8")
    touched["README.md"] = ("root", "current version is v1.2.1")

    rp_p = NEW / "REPRODUCE.md"
    rp = rp_p.read_text(encoding="utf-8")
    rp += ("\n\n## v1.2.1 single fixed version (13 November 2026)\n\n"
           "11. `python scripts/revise_B_derived_notes_v1_2_1_2026-11-13.py` rewrites calibre "
           "labels, method notes and reconciliation rows, writes the calibre dictionary, the "
           "India-record check and the grouped external benchmark, and asserts that every "
           "numeric cell outside the editable columns is unchanged.\n"
           "12. `python scripts/make_B_supplement_v1_2_1_2026-11-13.py` and "
           "`python scripts/revise_B_manuscript_v1_2_1_2026-11-13.py` rebuild the S1-S8 "
           "supplementary source and the manuscript; both are wording-only revisions.\n"
           "13. `python scripts/build_B_docx_v1_2_1_2026-11-13.py` and "
           "`python scripts/build_B_unique_version_v1_2_1_2026-11-13.py` assemble the two "
           "submission Word files, archive historical versions and write the submission "
           "MANIFEST with SHA-256 checksums.\n"
           "14. `python scripts/audit_B_pdf_pages_v1_2_1_2026-11-13.py` and "
           "`python scripts/verify_B_manuscript_v1_2_1_2026-11-13.py` run the 65 page-level "
           "checks and the 99 full-manuscript consistency checks. The page audit is performed "
           "on an internal proof PDF; the final submission PDF exported by the journal system "
           "still requires its own page-level audit.\n")
    rp_p.write_text(rp, encoding="utf-8")
    touched["REPRODUCE.md"] = ("root", "v1.2.1 execution order steps 11-14")

    # ---- 6) MANIFEST：按实际落盘重建，不自登记 ----
    old_by_path = {e["path"]: e for e in base_mf["files"]}
    files = []
    for p in sorted(q for q in NEW.rglob("*") if q.is_file()):
        rel = p.relative_to(NEW).as_posix()
        if rel == "MANIFEST.json" or rel.startswith("_build_summary"):
            continue
        d = dict(old_by_path.get(rel, {}))
        d.update({"path": rel, "bytes": p.stat().st_size, "sha256": sha(p)})
        d.setdefault("local_source", "generated")
        d.setdefault("scan_layer", "root")
        if rel in touched:
            d["scan_layer"], d["note"] = touched[rel]
            d["release"] = TAG
        if rel.startswith("data/processed/") and rel in touched:
            d["version_note"] = "v1.2.1 label/definition revision; numeric cells unchanged"
        r = rows(p)
        if r is not None:
            d["rows"] = r
        files.append(d)
    files.sort(key=lambda x: x["path"])

    mf = dict(base_mf)
    mf["built_at_utc"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    mf["repository"] = dict(base_mf["repository"])
    mf["repository"]["tag"] = TAG
    mf["files"] = files
    mf["version_history"] = [
        {"tag": "v1.0.0", "role": "historical initial deposit", "files": 51 + 1},
        {"tag": "v1.2.0", "role": "WHO official malaria case-count denominator; full recomputation",
         "files": len(base_mf["files"]) + 1},
        {"tag": TAG, "role": "single fixed version; label/definition corrections only",
         "files": len(files) + 1, "touched": len(touched)},
    ]
    mf["single_fixed_version"] = {
        "submission_directory": SUBMISSION.name,
        "submission_manifest_version": sub_mf["version"],
        "submission_files": len(sub_mf["files"]) + 1,
        "word_count": sub_mf["word_count"],
        "page_audit": sub_mf["page_audit"],
        "note": "Historical Word/PDF files are archived outside the submission directory.",
    }
    mf["label_semantics"] = {
        "Malaria": "primary_official_case_counts / MALARIA_EST_CASES",
        "Tuberculosis": "primary_incidence_times_population / MDG_0000000020",
        "HIV/AIDS": "primary_PLHIV_counts / PLHIV prevalence stock",
        "assertion": "no statistical value changed in v1.2.1",
    }
    mf["scan_ledger"] = list(base_mf.get("scan_ledger", [])) + [
        {"path": "v1.2.1 added and replaced files",
         "items": [f"credential scan: {len(touched)} files, zero hits",
                   "firewall scan (data/figure layers): zero hits",
                   "external meta-notation scan: zero hits",
                   "numeric zero-change assertion: three derived tables passed"]}
    ]
    (NEW / "MANIFEST.json").write_text(
        json.dumps(mf, ensure_ascii=False, indent=2), encoding="utf-8")

    for name in ("DATA_AVAILABILITY_STATEMENT.md", "README.md", "REPRODUCE.md",
                 ".gitignore", "LICENSE", "MANIFEST.json"):
        p = NEW / name
        assert not CRED.search(p.read_bytes()), f"根文件命中凭据模式：{name}"
        scan(p, "root")

    summary = {
        "tag": TAG, "base_tag": "v1.2.0", "touched_files": len(touched),
        "tracked_files": len(files), "tracked_plus_manifest": len(files) + 1,
        "total_bytes": sum(x["bytes"] for x in files) + (NEW / "MANIFEST.json").stat().st_size,
        "submission_version": sub_mf["version"],
    }
    (NEW / "_build_summary_v1.2.1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"v1.2.1 镜像：{NEW}")
    print(f"改动/新增 {len(touched)} 份 / tracked {len(files)} + MANIFEST 自身 = {len(files)+1}")
    print(f"总字节 {summary['total_bytes']:,}")
    print("数值零改动断言：3 张派生表全部通过")
    print("VERDICT = DEPOSIT V1.2.1 BUILD OK")


if __name__ == "__main__":
    main()
