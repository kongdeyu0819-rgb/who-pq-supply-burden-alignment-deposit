# -*- coding: utf-8 -*-
"""B① · v1.2.1 唯一固定版本：公开仓库与送审包收口终检（只读），2026-11-13

断言分组：真实链接与匿名访问、送审包与仓库版本一致、仓库内容完整性与哈希、
标签语义与数值零改动、历史版本冻结、凭据／防火墙／元说明扫描、旧终检留痕复跑。
输出 res_B_deposit_v1_2_1_verify_2026-11-13.json（内部留痕，不入库、不随送审包提交）。

运行：python verify_B_deposit_v1_2_1_2026-11-13.py
"""
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(r"D:\D\我的论文\全球卫生新博士课题")
MAIN = ROOT / "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）"
SUB = MAIN / "投稿包_v1.2.1_唯一固定版本_2026-11-13"
MIRROR = MAIN / "公开仓库_v1.2.1_2026-11-13"
LINK = MAIN / "公开仓库_v1.2.1_真实链接_2026-11-13.json"
PROOF = MAIN / "投稿包_2026-11-12" / "_proof_build_v1.2.1"
RESULT = PROOF / "res_B_deposit_v1_2_1_verify_2026-11-13.json"
SCRIPTS = ROOT / "数据" / "scripts"
TAG = "v1.2.1"
HTML = "https://github.com/kongdeyu0819-rgb/who-pq-supply-burden-alignment-deposit"

checks = []


def check(item, ok, note=""):
    checks.append({"item": item, "ok": bool(ok), "note": str(note)})


def read(p):
    return Path(p).read_text(encoding="utf-8")


def jload(p):
    return json.loads(read(p))


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def anon(url):
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except urllib.error.URLError:
        return -1


def main():
    link = jload(LINK)
    sub_mf = jload(SUB / "MANIFEST.json")
    mf = jload(MIRROR / "MANIFEST.json")
    man = read(MAIN / "49_B①主稿_v1.2.1_唯一固定版本_2026-11-13.md").split("# PART II", 1)[0]
    das = read(MIRROR / "DATA_AVAILABILITY_STATEMENT.md")

    # ---- A. 真实链接与匿名访问 ----
    check("真实链接证据 tag 为 v1.2.1", link["tag"] == TAG, "")
    check("真实仓库 URL 与历史一致", link["html_url"] == HTML, link["html_url"])
    check("tag_url 为 /tree/v1.2.1", link["tag_url"] == f"{HTML}/tree/{TAG}", "")
    check("release_url 指向 v1.2.1", f"/releases/tag/{TAG}" in (link["release_url"] or ""), "")
    check("远端 tree 与本地逐文件 SHA 一致", link["remote_tree_verified"] is True, "")
    check("发布时匿名访问全部 200",
          all(v == 200 for v in link["anonymous_http"].values()), str(link["anonymous_http"]))
    fresh = {
        "repository": anon(HTML),
        "tag_tree": anon(f"{HTML}/tree/{TAG}"),
        "das_file": anon(f"{HTML}/blob/{TAG}/DATA_AVAILABILITY_STATEMENT.md"),
        "release_page": anon(f"{HTML}/releases/tag/{TAG}"),
    }
    for k, v in fresh.items():
        check(f"本轮匿名复核 {k} = 200", v == 200, str(v))
    check("历史 tag v1.0.0 / v1.2.0 未被改写",
          all(v["expected"] == v["observed"] for v in link["historical_tags_retained"].values()),
          str({k: v["observed"][:8] for k, v in link["historical_tags_retained"].items()}))

    # ---- B. 送审包与仓库版本一致 ----
    check("送审包 MANIFEST 版本为 v1.2.1", sub_mf["version"] == TAG, "")
    check("仓库 MANIFEST 版本为 v1.2.1", mf["repository"]["tag"] == TAG, "")
    check("仓库 MANIFEST 登记唯一送审目录",
          mf["single_fixed_version"]["submission_directory"] == SUB.name, "")
    check("仓库 MANIFEST 登记词数 3496 / 300",
          mf["single_fixed_version"]["word_count"]["manuscript_text"] == 3496
          and mf["single_fixed_version"]["word_count"]["abstract"] == 300, "")
    check("主稿 DAS 指向同一个真实 v1.2.1 tag",
          f"release {TAG}: {link['tag_url']}" in man and "/tree/v1.2.0" not in man, "")
    check("仓库 DAS 指向同一个真实 v1.2.1 tag",
          f"release {TAG}: {link['tag_url']}" in das and "release v1.2.0:" not in das, "")
    check("仓库 DAS 如实登记两个历史版本",
          "Releases v1.0.0 and v1.2.0 are retained unchanged" in das, "")
    check("主稿 DAS 如实登记两个历史版本",
          "Releases v1.0.0 and v1.2.0 are retained unchanged" in man, "")

    # ---- C. 送审包内容完整性与哈希 ----
    files = sorted(p.name for p in SUB.iterdir() if p.is_file())
    check("送审目录恰好 9 份文件", len(files) == 9, str(files))
    check("送审目录无历史版本与校样 PDF",
          not any(("v1.0" in f or "v1.1" in f or "S1-S5" in f or f.endswith(".pdf")) for f in files), "")
    check("送审 MANIFEST 逐文件哈希与实际一致",
          all(x["sha256"] == sha256(SUB / x["file"])
              and x["bytes"] == (SUB / x["file"]).stat().st_size
              for x in sub_mf["files"]), f"{len(sub_mf['files'])} 项")
    for name in ("Figure1.tif", "Figure2.tif", "Figure3.tif"):
        check(f"送审图件 {name} 入库且哈希一致",
              (MIRROR / "figures_v1_2_1" / name).is_file()
              and sha256(MIRROR / "figures_v1_2_1" / name) == sha256(SUB / name), "")

    # ---- D. 仓库内容完整性与哈希 ----
    tracked = {e["path"]: e for e in mf["files"]}
    actual = {p.relative_to(MIRROR).as_posix(): p for p in MIRROR.rglob("*")
              if p.is_file() and p.name != "MANIFEST.json"
              and not p.name.startswith("_build_summary")}
    check("仓库 tracked 集合与实际落盘一致", set(tracked) == set(actual),
          f"tracked {len(tracked)} / actual {len(actual)}")
    check("仓库 tracked 逐文件哈希与实际一致",
          all(sha256(actual[k]) == v["sha256"] and actual[k].stat().st_size == v["bytes"]
              for k, v in tracked.items()), f"{len(tracked)} 项")
    check("仓库 file_count 与真实链接证据一致（含 MANIFEST 自身）",
          len(actual) + 1 == link["file_count"],
          f"{len(actual)}+1 vs {link['file_count']}")
    check("仓库总字节与真实链接证据一致（含 MANIFEST 自身）",
          sum(p.stat().st_size for p in actual.values())
          + (MIRROR / "MANIFEST.json").stat().st_size == link["total_bytes"], "")
    check("仓库 MANIFEST 不自登记", "MANIFEST.json" not in tracked, "")
    for rel in ("DATA_AVAILABILITY_STATEMENT.md", "README.md", "REPRODUCE.md",
                "LICENSE", ".gitignore"):
        check(f"仓库根文件 {rel} 存在", rel in tracked, "")
    check("REPRODUCE 登记 v1.2.1 执行顺序 11-14",
          all(f"{n}." in read(MIRROR / "REPRODUCE.md") for n in (11, 12, 13, 14)), "")
    check("README 当前版本声明为 v1.2.1",
          "The version cited in the manuscript's data accessibility statement is\nrelease `v1.2.1`"
          in read(MIRROR / "README.md"), "")

    # ---- E. 标签语义与数值零改动 ----
    lab = mf["label_semantics"]
    check("标签语义登记三病种真实分母",
          "MALARIA_EST_CASES" in lab["Malaria"]
          and "MDG_0000000020" in lab["Tuberculosis"]
          and "PLHIV" in lab["HIV/AIDS"], "")
    check("仓库 MANIFEST 声明零数值改动",
          "no statistical value changed" in lab["assertion"], "")
    sens = list(csv.DictReader(open(MIRROR / "data/processed/res_B_burden_sensitivity_2026-11-12.csv",
                                    encoding="utf-8-sig", newline="")))
    by = {(r["disease"], r["calibre"]) for r in sens}
    for dis, key in (("Malaria", "primary_official_case_counts"),
                     ("Tuberculosis", "primary_incidence_times_population"),
                     ("HIV/AIDS", "primary_PLHIV_counts")):
        check(f"入库敏感性表 {dis} 主口径标签正确", (dis, key) in by, "")
    check("入库敏感性表无 common_support_only 旧名",
          not any(r["calibre"] == "common_support_only" for r in sens), "")
    check("入库派生表含标签字典与两份修订台账",
          all((MIRROR / "data/processed" / n).is_file() for n in
              ("res_B_calibre_dictionary_2026-11-13.csv",
               "res_B_notes_change_audit_2026-11-13.json",
               "res_B_manuscript_v1_2_1_change_audit.json")), "")
    check("数值零改动门禁在构建期通过",
          any("numeric zero-change assertion" in json.dumps(x, ensure_ascii=False)
              for x in mf["scan_ledger"]), "")

    # ---- F. 全库凭据／防火墙／元说明扫描 ----
    cred = re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
                      + b"comtrade" + rb"[\._]key", re.I)
    bad = [b"comtrade", b"hs_code", b"U1/U2/U3", b"export value", b"dualchain_china_pq_access"]
    meta = re.compile(r"\b(?:M|X)\d{1,3}\b|\bA\d{2,3}\b|\b\d{2}\s*号(?:稿|件|文件|主稿)")
    hits_cred, hits_bad, hits_meta, historical_meta = [], [], [], []
    # 只在 v1.2.1 本轮改动／新增的文件上做元说明门禁；历史脚本自 v1.0.0 起
    # 已在公开仓库中，其注释里的「NN 号稿」属既有状态，本轮不静默改写，
    # 如实登记在结果 JSON 的 historical_meta_hits 中。
    touched = {rel for rel, e in tracked.items() if e.get("release") == TAG}
    for rel, p in actual.items():
        raw = p.read_bytes()
        if cred.search(raw):
            hits_cred.append(rel)
        if rel.startswith(("data/", "figures")) and any(x in raw.lower() for x in bad):
            hits_bad.append(rel)
        if p.suffix.lower() in (".py", ".md", ".json", ".csv"):
            m = meta.search(raw.decode("utf-8", "ignore").replace("A4", "A-four"))
            if m and rel in touched:
                hits_meta.append(rel)
            elif m:
                historical_meta.append({"path": rel, "token": m.group()})
    check("全库凭据零命中", not hits_cred, str(hits_cred[:4]))
    check("data/figure 层四篇防火墙零命中", not hits_bad, str(hits_bad[:4]))
    check("v1.2.1 新增／替换文件元说明零命中", not hits_meta, str(hits_meta[:4]))
    check("v1.2.1 改动文件均在 MANIFEST 登记 release 标记", len(touched) >= 24, f"{len(touched)} 份")
    check("发布脚本不含本地凭据文件路径",
          "Github令牌" not in read(MIRROR / "scripts/publish_B_deposit_v1_2_1_2026-11-13.py")
          and "B1_GITHUB_PAT" in read(MIRROR / "scripts/publish_B_deposit_v1_2_1_2026-11-13.py"), "")

    # ---- G. 旧终检留痕复跑 ----
    p = subprocess.run([sys.executable, str(SCRIPTS / "verify_B_manuscript_v1_2_1_2026-11-13.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    check("v1.2.1 全文一致性终检复跑 ALL CLEAN",
          p.returncode == 0 and "ALL CLEAN" in p.stdout, p.stdout.strip()[-160:])
    v = jload(PROOF / "verify_result_v1_2_1.json")
    check("终检 99 项零失败", v["checks"] == 99 and v["failed"] == 0,
          f"{v['checks']} 项 / 失败 {v['failed']}")
    check("最终投稿 PDF 逐页审计如实标注待执行",
          v["details"] and sub_mf["page_audit"]["final_submission_pdf"] == "PENDING", "")

    failed = [c for c in checks if not c["ok"]]
    result = {
        "version": TAG, "date": "2026-11-13", "checks": len(checks),
        "failed": len(failed), "failed_items": [c["item"] for c in failed],
        "details": checks, "fresh_anonymous_http": fresh,
        "v1_2_1_touched_files": sorted(touched),
        "historical_meta_hits": historical_meta,
        "historical_meta_note": "Pre-existing internal document references in v1.0.0/v1.2.0 "
                                "script comments; not touched in v1.2.1 and not part of the "
                                "submission package. Registered, not silently rewritten.",
        "verdict": "ALL CLEAN" if not failed else "FAILED",
    }
    PROOF.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for c in failed:
        print("FAIL:", c["item"], "|", c["note"])
    print(f"v1.2.1 仓库收口终检 {len(checks)} 项，失败 {len(failed)} 项 -> {result['verdict']}")
    print("留痕 ->", RESULT.relative_to(MAIN))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
