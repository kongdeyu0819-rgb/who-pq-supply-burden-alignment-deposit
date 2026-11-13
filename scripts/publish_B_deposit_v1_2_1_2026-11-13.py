# -*- coding: utf-8 -*-
"""B① 主稿 · v1.2.1 唯一固定版本发布到既有真实 GitHub 仓库，2026-11-13

与历史版本的关系：v1.0.0 与 v1.2.0 的 tag、Release、真实链接证据与本地镜像
全部冻结不回写；本脚本在同一个真实仓库上前进 default branch，并以新的
annotated tag v1.2.1 发布固定版本，使主稿 Data Accessibility Statement 中的
/tree/v1.2.1 成为可匿名访问的真实链接。

凭据纪律：PAT 只从环境变量 B1_GITHUB_PAT 读入内存，脚本内不含任何本地凭据
文件路径；不回显、不写入项目目录与仓库。

流程：身份校验 → 复用既有 public 仓库 → 校验镜像 DAS 与真实 URL 一致 →
Git Data API 提交全部文件 → annotated tag + Release → 匿名访问与远端 tree 逐
文件 SHA 校验 → 历史 tag 未被改写校验 → 写真实链接证据（不含凭据）。

运行：B1_GITHUB_PAT=... python publish_B_deposit_v1_2_1_2026-11-13.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\D\我的论文\全球卫生新博士课题")
MAIN = ROOT / "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）"
OUT = MAIN / "公开仓库_v1.2.1_2026-11-13"
RESULT = MAIN / "公开仓库_v1.2.1_真实链接_2026-11-13.json"
HIST_V12 = MAIN / "公开仓库_v1.2_真实链接_2026-11-12.json"
HIST_V10 = MAIN / "公开仓库_真实链接_2026-11-12.json"

REPO_NAME = "who-pq-supply-burden-alignment-deposit"
TAG = "v1.2.1"
API = "https://api.github.com"


def load_token() -> str:
    tok = os.environ.get("B1_GITHUB_PAT", "").strip()
    assert tok, "未设置 B1_GITHUB_PAT；凭据只在内存，不落盘、不回显"
    return tok


def req(token: str, method: str, path: str, payload: dict | None = None):
    url = path if path.startswith("http") else API + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    r = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "WorkBuddy-B1-deposit-v1-2-1",
            "Content-Type": "application/json",
        })
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            body = resp.read()
            return resp.status, (json.loads(body) if body else {}), dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:400]
        return e.code, {"error": body}, {}


def anon(url: str) -> int:
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except urllib.error.URLError:
        return -1


def descends_from(token, owner, head, ancestor, depth=5):
    """允许在同一 v1.2.1 版本内幂等重跑：head 可以是 v1.2.0 之后的连续提交。"""
    cur = head
    for _ in range(depth):
        if cur == ancestor:
            return True
        st, c, _ = req(token, "GET", f"/repos/{owner}/{REPO_NAME}/git/commits/{cur}")
        if st != 200 or not c.get("parents"):
            return False
        cur = c["parents"][0]["sha"]
    return False


def tag_commit(token, owner, tag):
    st, ref, _ = req(token, "GET", f"/repos/{owner}/{REPO_NAME}/git/ref/tags/{tag}")
    assert st == 200, f"历史 tag {tag} 不可读：{st} {ref}"
    obj = ref["object"]
    if obj["type"] == "commit":
        return obj["sha"]
    st2, to, _ = req(token, "GET", f"/repos/{owner}/{REPO_NAME}/git/tags/{obj['sha']}")
    assert st2 == 200, f"历史 tag 对象 {tag} 不可读：{st2}"
    return to["object"]["sha"]


def main() -> None:
    assert (OUT / "MANIFEST.json").is_file(), "请先运行 build_B_deposit_v1_2_1_2026-11-13.py"
    mf = json.loads((OUT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert mf["repository"]["tag"] == TAG, "MANIFEST 版本不是 v1.2.1"
    h12 = json.loads(HIST_V12.read_text(encoding="utf-8"))
    h10 = json.loads(HIST_V10.read_text(encoding="utf-8"))
    assert h12["tag"] == "v1.2.0" and h10["tag"] == "v1.0.0", "历史链接证据异常，禁止覆盖"

    token = load_token()
    st, me, _ = req(token, "GET", "/user")
    assert st == 200, f"令牌身份校验失败：{st}"
    owner = me["login"]
    assert owner == h12["owner"] == h10["owner"] == "kongdeyu0819-rgb", f"owner 变更，中止：{owner}"

    st, repo, _ = req(token, "GET", f"/repos/{owner}/{REPO_NAME}")
    assert st == 200 and repo["owner"]["login"] == owner, f"既有仓库不可复用：{st}"
    html_url = repo["html_url"]
    assert html_url == h12["html_url"] == h10["html_url"], "真实 URL 与历史证据不一致，中止"
    default_branch = repo["default_branch"]

    das = (OUT / "DATA_AVAILABILITY_STATEMENT.md").read_text(encoding="utf-8")
    assert html_url in das and f"/tree/{TAG}" in das and f"release {TAG}:" in das, \
        "镜像 DAS 未指向真实仓库的 v1.2.1 固定版本"
    assert "release v1.2.0:" not in das and "historical versions" in das.lower(), \
        "镜像 DAS 未如实登记两个历史版本"

    st, head, _ = req(token, "GET",
                      f"/repos/{owner}/{REPO_NAME}/git/ref/heads/{default_branch}")
    assert st == 200, f"读 default branch head 失败：{st}"
    base_commit = head["object"]["sha"]
    assert descends_from(token, owner, base_commit, h12["commit_sha"]), \
        f"远端 head 不在 v1.2.0 之后的提交链上，中止：{base_commit}"

    # 上传白名单 = 实际落盘文件（本地构建台账不入库）
    files = sorted(p for p in OUT.rglob("*")
                   if p.is_file() and not p.name.startswith("_build_summary"))
    tree_items = []
    for p in files:
        rel = p.relative_to(OUT).as_posix()
        b = p.read_bytes()
        st, blob, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/blobs",
                          {"content": base64.b64encode(b).decode("ascii"),
                           "encoding": "base64"})
        assert st in (200, 201), f"blob 失败 {rel}：{st} {blob}"
        tree_items.append({"path": rel, "mode": "100644", "type": "blob",
                           "sha": blob["sha"]})
    print(f"  uploaded {len(files)} blobs", flush=True)

    st, tree, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/trees",
                      {"tree": tree_items})
    assert st in (200, 201), f"tree 失败：{st} {tree}"
    st, basec, _ = req(token, "GET",
                       f"/repos/{owner}/{REPO_NAME}/git/commits/{base_commit}")
    assert st == 200, f"读 base commit 失败：{st}"
    base_tree = basec["tree"]["sha"]

    if tree["sha"] == base_tree:
        commit_sha, commit_action = base_commit, "reused head commit (tree unchanged)"
    else:
        st, commit, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/commits", {
            "message": "B1 TMIH single fixed version v1.2.1: calibre labels, "
                       "definitions and audit trail; no statistical value changed",
            "tree": tree["sha"], "parents": [base_commit]})
        assert st in (200, 201), f"commit 失败：{st} {commit}"
        commit_sha = commit["sha"]
        st, ref, _ = req(token, "PATCH",
                         f"/repos/{owner}/{REPO_NAME}/git/refs/heads/{default_branch}",
                         {"sha": commit_sha, "force": False})
        assert st == 200, f"ref 前进失败：{st} {ref}"
        commit_action = "created new commit and advanced branch"

    # ---- annotated tag（幂等）----
    st, existing_tag, _ = req(token, "GET",
                              f"/repos/{owner}/{REPO_NAME}/git/ref/tags/{TAG}")
    existing_commit = None
    if st == 200:
        obj = existing_tag["object"]
        existing_commit = (obj["sha"] if obj["type"] == "commit"
                           else tag_commit(token, owner, TAG))
    if existing_commit == commit_sha:
        tag_action = "reused existing annotated tag"
    else:
        st, tagobj, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/tags", {
            "tag": TAG,
            "message": "Single fixed version v1.2.1 aligned with the submission package",
            "object": commit_sha, "type": "commit",
            "tagger": {"name": "WorkBuddy deposit builder",
                       "email": "deposit@users.noreply.github.com",
                       "date": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")},
        })
        assert st in (200, 201), f"tag object 失败：{st} {tagobj}"
        st, tagref, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/refs",
                            {"ref": f"refs/tags/{TAG}", "sha": tagobj["sha"]})
        if st == 422 and "already exists" in json.dumps(tagref, ensure_ascii=False).lower():
            st, tagref, _ = req(token, "PATCH",
                                f"/repos/{owner}/{REPO_NAME}/git/refs/tags/{TAG}",
                                {"sha": tagobj["sha"], "force": True})
            assert st == 200, f"tag ref 校正失败：{st} {tagref}"
            tag_action = "advanced existing tag ref to current commit"
        else:
            assert st in (200, 201), f"tag ref 失败：{st} {tagref}"
            tag_action = "created annotated tag ref"

    release_body = (
        "Single fixed version v1.2.1 of the deposit supporting the Tropical Medicine & "
        "International Health submission, aligned with the single fixed submission package. "
        "Relative to v1.2.0 this release corrects denominator-calibre labels so that only "
        "malaria is labelled as WHO official estimated case counts (MALARIA_EST_CASES, 2024 "
        "estimates); tuberculosis uses incidence per 100,000 population x total population "
        "and HIV/AIDS uses people living with HIV prevalence counts. The "
        "burden-observed-only calibre replaces the ambiguous earlier name. Added: a calibre "
        "label dictionary, a grouped tuberculosis external magnitude benchmark, a "
        "machine-read India-record check, two change-audit files, the three TIFF figure "
        "files of the submission package and the v1.2.1 reproducible scripts. No analysis "
        "was re-run and no statistical value changed; the build asserts cell-by-cell "
        "equality outside the editable label and note columns. The earlier "
        "incidence-times-total-population construction remains a sensitivity comparison "
        "only. Releases v1.0.0 and v1.2.0 are retained unchanged as historical versions. "
        "See MANIFEST.json for SHA-256 checksums and REPRODUCE.md for the execution order. "
        "The final submission PDF exported by the journal system still requires its own "
        "page-level audit; the internal proof PDF is not shipped with the submission.")
    st, release, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/releases", {
        "tag_name": TAG,
        "name": "v1.2.1 — single fixed version (label and audit corrections)",
        "body": release_body,
        "draft": False, "prerelease": False,
    })
    if st == 422 and "already_exists" in json.dumps(release, ensure_ascii=False):
        st, release, _ = req(token, "GET",
                             f"/repos/{owner}/{REPO_NAME}/releases/tags/{TAG}")
        assert st == 200, f"复用既有 release 失败：{st}"
        release_action = "reused existing release"
    else:
        assert st in (200, 201), f"release 失败：{st} {release}"
        release_action = "created release"

    # ---- 只读核验 ----
    http = {
        "repository": anon(html_url),
        "tag_tree": anon(f"{html_url}/tree/{TAG}"),
        "das_file": anon(f"{html_url}/blob/{TAG}/DATA_AVAILABILITY_STATEMENT.md"),
        "release_page": anon(f"{html_url}/releases/tag/{TAG}"),
        "historical_v1_2_0": anon(f"{html_url}/tree/v1.2.0"),
        "historical_v1_0_0": anon(f"{html_url}/tree/v1.0.0"),
    }
    st, rtree, _ = req(token, "GET",
                       f"/repos/{owner}/{REPO_NAME}/git/trees/{TAG}?recursive=1")
    assert st == 200, f"远端 v1.2.1 tree 读取失败：{st} {rtree}"
    remote = {x["path"]: x["sha"] for x in rtree["tree"] if x["type"] == "blob"}
    local = {p.relative_to(OUT).as_posix():
             hashlib.sha1(b"blob " + str(len(p.read_bytes())).encode()
                          + b"\0" + p.read_bytes()).hexdigest()
             for p in files}
    assert remote == local, (
        f"远端/本地不一致：缺 {sorted(set(local)-set(remote))[:6]} "
        f"多 {sorted(set(remote)-set(local))[:6]} "
        f"sha 差 {[k for k in set(local)&set(remote) if local[k]!=remote[k]][:6]}")
    assert all(v == 200 for v in http.values()), f"匿名访问异常：{http}"

    hist_tags = {
        "v1.0.0": {"expected": h10["commit_sha"], "observed": tag_commit(token, owner, "v1.0.0")},
        "v1.2.0": {"expected": h12["commit_sha"], "observed": tag_commit(token, owner, "v1.2.0")},
    }
    assert all(v["expected"] == v["observed"] for v in hist_tags.values()), \
        f"历史 tag 被改写：{hist_tags}"

    result = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repository_created_this_run": False,
        "owner": owner,
        "repo": REPO_NAME,
        "html_url": html_url,
        "tag": TAG,
        "tag_url": f"{html_url}/tree/{TAG}",
        "release_url": release.get("html_url"),
        "commit_sha": commit_sha,
        "base_commit_sha": base_commit,
        "idempotency": {"commit": commit_action, "tag": tag_action, "release": release_action},
        "default_branch": default_branch,
        "file_count": len(files),
        "total_bytes": sum(p.stat().st_size for p in files),
        "historical_tags_retained": hist_tags,
        "anonymous_http": http,
        "remote_tree_verified": True,
        "data_accessibility_statement_file": "DATA_AVAILABILITY_STATEMENT.md",
        "single_fixed_version": {
            "submission_directory": "投稿包_v1.2.1_唯一固定版本_2026-11-13",
            "manuscript_das_tag": TAG,
            "numerical_change": "none; label, definition, wording and audit trail only",
        },
        "credential_handling": "PAT supplied through B1_GITHUB_PAT into memory only; "
                               "never echoed, never written to any project file or repository",
    }
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    out = {k: v for k, v in result.items() if k != "credential_handling"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("VERDICT = PUBLISH V1.2.1 OK")


if __name__ == "__main__":
    main()
