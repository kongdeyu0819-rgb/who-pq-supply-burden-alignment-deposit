# -*- coding: utf-8 -*-
"""
B① 主稿 · v1.2 公开存档发布到既有 GitHub 仓库，2026-11-12

与 v1.0.0 的关系：v1.0.0 的 release、tag、真实链接证据与本地镜像全部冻结不回写；
本脚本在**同一个真实仓库**上前进 default branch，并以新的 annotated tag
v1.2.0 发布固定版本，使主稿 DAS 中的 /tree/v1.2.0 成为可匿名访问的真实链接。

流程（严格顺序，不编造 URL）：
  1) 从本地凭据文档读取 GitHub PAT（只在内存，绝不回显、绝不写入项目目录／仓库）；
  2) 读取 build_B_deposit_v1_2_2026-11-12.py 生成的 `公开仓库_v1.2_2026-11-12/`；
  3) 复用既有 public repository（GET 校验 owner 与 html_url，绝不新建／覆盖他人仓库）；
  4) 校验镜像内 DAS 的 URL 与仓库真实 html_url 一致，不一致即中止；
  5) 通过 Git Data API 一次性提交全部文件（blob → tree → commit → ref）；
  6) 打 annotated tag v1.2.0 并创建 Release；
  7) 只读核验：仓库／tag／DAS 可匿名访问，远端 v1.2.0 tree 与本地 SHA 逐项一致；
  8) 把真实链接／commit／tag 写入 `公开仓库_v1.2_真实链接_2026-11-12.json`（不含凭据）。

运行：python publish_B_deposit_v1_2_2026-11-12.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import docx

ROOT = Path(r"D:\D\我的论文\全球卫生新博士课题")
MAIN = ROOT / "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）"
OUT = MAIN / "公开仓库_v1.2_2026-11-12"
RESULT = MAIN / "公开仓库_v1.2_真实链接_2026-11-12.json"
HISTORY = MAIN / "公开仓库_真实链接_2026-11-12.json"
CRED_DOCX = Path(r"D:\workburry数据\AGENT\医学科研专家\METRN_AIS_科创变更补充\Github令牌.docx")

REPO_NAME = "who-pq-supply-burden-alignment-deposit"
TAG = "v1.2.0"
API = "https://api.github.com"


def load_token() -> str:
    """凭据只在内存；使用带 repo 权限的 classic PAT。"""
    d = docx.Document(str(CRED_DOCX))
    txt = "\n".join([p.text for p in d.paragraphs]
                    + [c.text for t in d.tables for r in t.rows for c in r.cells])
    toks = re.findall(r"gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}", txt)
    classic = [t for t in toks if re.fullmatch(r"ghp_[A-Za-z0-9]{36}", t)]
    assert classic, "凭据文档中未找到 classic PAT"
    return classic[0]


def req(token: str, method: str, path: str, payload: dict | None = None):
    url = path if path.startswith("http") else API + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    r = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "WorkBuddy-B1-deposit-v1-2",
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


def main() -> None:
    assert (OUT / "MANIFEST.json").is_file(), "请先运行 build_B_deposit_v1_2_2026-11-12.py"
    mf = json.loads((OUT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert mf["repository"]["tag"] == TAG, "MANIFEST 版本不是 v1.2.0"
    hist = json.loads(HISTORY.read_text(encoding="utf-8"))
    assert hist["tag"] == "v1.0.0", "v1.0.0 历史证据异常，禁止覆盖"

    token = load_token()
    status, me, _ = req(token, "GET", "/user")
    assert status == 200, f"令牌身份校验失败: {status} {me}"
    owner = me["login"]
    assert owner == hist["owner"] == "kongdeyu0819-rgb", f"仓库 owner 变更，中止: {owner}"

    # ---- 3) 复用既有仓库 ----
    status, repo, _ = req(token, "GET", f"/repos/{owner}/{REPO_NAME}")
    assert status == 200 and repo["owner"]["login"] == owner, \
        f"既有仓库不可复用: {status} {str(repo)[:200]}"
    html_url = repo["html_url"]
    assert html_url == hist["html_url"], "真实 URL 与 v1.0.0 证据不一致，中止"
    default_branch = repo["default_branch"]

    # ---- 4) DAS 的 URL 必须与真实仓库一致（不静默改写）----
    das = (OUT / "DATA_AVAILABILITY_STATEMENT.md").read_text(encoding="utf-8")
    assert html_url in das and f"/tree/{TAG}" in das and "release v1.2.0:" in das, \
        "镜像 DAS 未指向真实仓库的 v1.2.0 固定版本"
    # v1.0.0 只允许作为历史版本被提及，不得再被写成当前固定版本
    assert "release v1.0.0:" not in das.lower() and "historical version" in das.lower(), \
        "镜像 DAS 仍把 v1.0.0 写作当前固定版本"

    st, head, _ = req(token, "GET",
                      f"/repos/{owner}/{REPO_NAME}/git/ref/heads/{default_branch}")
    assert st == 200, f"读 default branch head 失败: {st} {head}"
    base_commit = head["object"]["sha"]

    # 上传白名单 = 实际落盘文件（本地构建台账不入库）
    files = sorted(p for p in OUT.rglob("*")
                   if p.is_file() and p.name != "_build_summary_v1.2.json")
    tree_items = []
    for p in files:
        rel = p.relative_to(OUT).as_posix()
        b = p.read_bytes()
        st, blob, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/blobs",
                          {"content": base64.b64encode(b).decode("ascii"),
                           "encoding": "base64"})
        assert st in (200, 201), f"blob 失败 {rel}: {st} {blob}"
        tree_items.append({"path": rel, "mode": "100644", "type": "blob",
                           "sha": blob["sha"]})
    print(f"  uploaded {len(files)} blobs")

    st, tree, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/trees",
                      {"tree": tree_items})
    assert st in (200, 201), f"tree 失败: {st} {tree}"
    st, basec, _ = req(token, "GET",
                       f"/repos/{owner}/{REPO_NAME}/git/commits/{base_commit}")
    assert st == 200, f"读 base commit 失败: {st} {str(basec)[:200]}"
    base_tree = basec["tree"]["sha"]

    # 幂等一：内容未变则复用当前 head commit，不制造空转提交
    if tree["sha"] == base_tree:
        commit_sha = base_commit
        commit_action = "reused head commit (tree unchanged)"
    else:
        st, commit, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/commits",
                            {"message": "B1 TMIH revision: WHO official malaria case-count denominator, v1.2.0",
                             "tree": tree["sha"], "parents": [base_commit]})
        assert st in (200, 201), f"commit 失败: {st} {commit}"
        commit_sha = commit["sha"]
        st, ref, _ = req(token, "PATCH",
                         f"/repos/{owner}/{REPO_NAME}/git/refs/heads/{default_branch}",
                         {"sha": commit_sha, "force": False})
        assert st == 200, f"ref 前进失败: {st} {ref}"
        commit_action = "created new commit and advanced branch"

    # ---- 6) annotated tag + Release（幂等二／三）----
    st, existing_tag, _ = req(token, "GET",
                              f"/repos/{owner}/{REPO_NAME}/git/ref/tags/{TAG}")
    tag_commit = None
    if st == 200:
        obj = existing_tag["object"]
        if obj["type"] == "commit":
            tag_commit = obj["sha"]
        else:
            st2, to, _ = req(token, "GET",
                             f"/repos/{owner}/{REPO_NAME}/git/tags/{obj['sha']}")
            if st2 == 200:
                tag_commit = to["object"]["sha"]

    if tag_commit == commit_sha:
        tag_action = "reused existing annotated tag"
    else:
        st, tagobj, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/tags", {
            "tag": TAG,
            "message": "WHO official malaria estimated case counts as primary burden denominator",
            "object": commit_sha, "type": "commit",
            "tagger": {"name": "WorkBuddy deposit builder",
                       "email": "deposit@users.noreply.github.com",
                       "date": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")},
        })
        assert st in (200, 201), f"tag object 失败: {st} {str(tagobj)[:200]}"
        st, tagref, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/git/refs",
                            {"ref": f"refs/tags/{TAG}", "sha": tagobj["sha"]})
        if st == 422 and "already exists" in json.dumps(tagref, ensure_ascii=False).lower():
            # 同名 tag 已由前一次发布创建：仅把 ref 校正到当前 commit，不动 v1.0.0
            st, tagref, _ = req(token, "PATCH",
                                f"/repos/{owner}/{REPO_NAME}/git/refs/tags/{TAG}",
                                {"sha": tagobj["sha"], "force": True})
            assert st == 200, f"tag ref 校正失败: {st} {str(tagref)[:200]}"
            tag_action = "advanced existing tag ref to current commit"
        else:
            assert st in (200, 201), f"tag ref 失败: {st} {str(tagref)[:200]}"
            tag_action = "created annotated tag ref"

    release_body = (
        "Revision of the B1 deposit supporting the Tropical Medicine & International "
        "Health submission. The primary malaria burden denominator is now the WHO "
        "official estimated number of malaria cases (MALARIA_EST_CASES, 2024 "
        "estimates); the earlier incidence-per-1,000-at-risk times total population "
        "construction is retained only as a sensitivity comparison. Added: four WHO GHO "
        "raw extracts with provenance, eight recomputed or robustness derived tables, "
        "the regenerated main figures and twelve reproducible scripts. Country sets are "
        "reconciled in res_B_country_set_reconciliation_2026-11-12.csv. The WHO "
        "tuberculosis incident-case indicator is an external magnitude check only "
        "because it contains no India records. Release v1.0.0 is retained unchanged "
        "as the historical version. See MANIFEST.json for SHA-256 checksums and "
        "REPRODUCE.md for the execution order. No proprietary, individual-level, "
        "trade-flow or procurement data are included.")
    st, release, _ = req(token, "POST", f"/repos/{owner}/{REPO_NAME}/releases", {
        "tag_name": TAG,
        "name": "v1.2.0 — WHO official malaria denominator and full recomputation",
        "body": release_body,
        "draft": False, "prerelease": False,
    })
    if st == 422 and "already_exists" in json.dumps(release, ensure_ascii=False):
        st, release, _ = req(token, "GET",
                             f"/repos/{owner}/{REPO_NAME}/releases/tags/{TAG}")
        assert st == 200, f"复用既有 release 失败: {st} {str(release)[:200]}"
        release_action = "reused existing release"
    else:
        assert st in (200, 201), f"release 失败: {st} {str(release)[:200]}"
        release_action = "created release"

    # ---- 7) 只读核验 ----
    http_repo = anon(html_url)
    http_tag = anon(f"{html_url}/tree/{TAG}")
    http_das = anon(f"{html_url}/blob/{TAG}/DATA_AVAILABILITY_STATEMENT.md")
    st, rtree, _ = req(token, "GET",
                       f"/repos/{owner}/{REPO_NAME}/git/trees/{TAG}?recursive=1")
    assert st == 200, f"远端 v1.2.0 tree 读取失败: {st} {str(rtree)[:200]}"
    remote = {x["path"]: x["sha"] for x in rtree["tree"] if x["type"] == "blob"}
    local = {p.relative_to(OUT).as_posix():
             hashlib.sha1(b"blob " + str(len(p.read_bytes())).encode()
                          + b"\0" + p.read_bytes()).hexdigest()
             for p in files}
    assert remote == local, (
        f"远端/本地不一致: 缺 {sorted(set(local)-set(remote))[:6]} "
        f"多 {sorted(set(remote)-set(local))[:6]} "
        f"sha 差 {[k for k in set(local)&set(remote) if local[k]!=remote[k]][:6]}")
    assert http_repo == 200 and http_das == 200, \
        f"匿名访问异常: repo={http_repo} das={http_das}"

    # v1.0.0 tag 仍存在且未被改写
    st, old_tag, _ = req(token, "GET",
                         f"/repos/{owner}/{REPO_NAME}/git/ref/tags/v1.0.0")
    assert st == 200, f"v1.0.0 历史 tag 丢失: {st}"
    assert old_tag["object"]["sha"] != commit_sha, "v1.0.0 不应指向 v1.2.0 commit"

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
        "historical_tag_retained": "v1.0.0",
        "anonymous_http": {"repository": http_repo, "tag_tree": http_tag, "das_file": http_das},
        "remote_tree_verified": True,
        "data_accessibility_statement_file": "DATA_AVAILABILITY_STATEMENT.md",
        "denominator_change": {
            "primary": "MALARIA_EST_CASES (2024 estimates)",
            "comparison": "incidence per 1,000 population at risk x total population (sensitivity only)",
        },
        "credential_handling": "PAT read into memory only; never echoed, never written "
                               "to any project file or repository",
    }
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    out = {k: v for k, v in result.items() if k != "credential_handling"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("VERDICT = PUBLISH V1.2 OK")


if __name__ == "__main__":
    main()
