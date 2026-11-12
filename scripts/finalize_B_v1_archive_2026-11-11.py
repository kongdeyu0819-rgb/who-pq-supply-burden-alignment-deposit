# -*- coding: utf-8 -*-
"""
finalize_B_v1_archive_2026-11-11.py
B① 主稿 · v1 留痕文件最终归位与文档状态订正（2026-11-11）

背景：首次交付统计补算结果时，v1 的 misalignment_ci CSV 被作为预览卡片
推送到 WorkBuddy 面板，Windows 以「允许读、不允许写/移动」的共享模式持有句柄；
此后各轮 mv / Rename-Item / .NET File.Move 均失败。会话压缩后面板句柄释放，
本脚本实测锁已消失，遂用 os.replace 原子归位（目标已存在同名副本，内容逐字节一致）。

另：早期 apply_B_status_sync_2026-11-11.py L180-187 用 os.rename 移动到
「已存在」的目标，Windows 抛 FileExistsError 后被笼统打印为 "LOCK 原件仍被
进程独占"，属归因不严谨（失败原因混合了共享锁与目标重名）。本脚本同时订正
18 / 17 / README / compute 四处「暂留」过时表述，避免后续误读。

边界：不改任何数值、不重跑统计、不写正文、不动既有 res_B_anchor_* 底座。
运行：python finalize_B_v1_archive_2026-11-11.py
"""
import os
import hashlib

ROOT = r"D:\D\我的论文\全球卫生新博士课题"
MAIN = os.path.join(
    ROOT,
    "WHO 预认证药品的供应—疾病负担空间可及性格局：质量信号、生产者集中度与公平性缺口（2002–2026）",
)
SCRIPTS = os.path.join(ROOT, "数据", "scripts")
PROC = os.path.join(ROOT, "数据", "processed")
ARCHIVE = os.path.join(PROC, "_archive_v1")

SRC = os.path.join(PROC, "res_B_uncertainty_misalignment_ci_2026-11-11.csv")
DST = os.path.join(ARCHIVE, "res_B_uncertainty_misalignment_ci_2026-11-11_v1_deprecated.csv")

F18 = os.path.join(MAIN, "18_B①统计补算说明_2026-11-11.md")
F17 = os.path.join(MAIN, "17_B①主稿撰写计划_2026-11-11.md")
FREADME = os.path.join(SCRIPTS, "README.md")
FCOMPUTE = os.path.join(SCRIPTS, "compute_B_uncertainty_2026-11-11.py")

JOBS = [
    (F18, [
        ("（因原件仍被本地编辑器进程独占，仅完成归档副本复制；原件暂留 `processed/` 根，关闭该标签后可移走，未强写、未绕云端）",
         "（原件已于本轮以原子替换方式物理移入归档目录，与既有副本逐字节一致；`processed/` 根不再保留 v1 文件）"),
    ]),
    (F17, [
        ("被编辑器锁定的两份 v1 文件禁止引用",
         "已归入 `_archive_v1/` 的两份 v1 文件禁止引用"),
        ("（其中 `ci` 原件因进程独占仅完成归档副本复制，暂留根目录、禁止引用）",
         "（两份原件均已物理移入归档，`processed/` 根无 v1 残留）"),
    ]),
    (FREADME, [
        ("；其中 `ci` 原件因编辑器进程独占仅完成归档副本复制，暂留 `processed/` 根，关闭该标签后可移走。",
         "；两份原件均已物理移入归档，`processed/` 根无 v1 残留。"),
        ("v1 文件归档（可复跑，关闭编辑器标签后会自动移走残留原件）",
         "v1 文件归档（历史一次性脚本，锚点已消费，勿重复运行；最终归位由 `finalize_B_v1_archive_2026-11-11.py` 完成）"),
    ]),
    (FCOMPUTE, [
        ("res_B_uncertainty_misalignment_ci_2026-11-11.csv 因仍被本地编辑器进程独占，\n只完成归档副本复制，原件暂留 processed 根，禁止引用；关闭该标签后可移入归档目录。",
         "res_B_uncertainty_misalignment_ci_2026-11-11.csv 的原件亦已物理移入归档目录\n（与既有副本逐字节一致）；processed 根不再保留任何不带 _revised 的错位结果。"),
    ]),
]

RM_APPEND = """
### 2026-11-11 补充收口：v1 原件归位与「独占锁」归因订正

`finalize_B_v1_archive_2026-11-11.py` 已完成：把 `res_B_uncertainty_misalignment_ci_2026-11-11.csv`
原件以 `os.replace` 原子移入 `processed/_archive_v1/`（与既有副本逐字节一致），
`processed/` 根现在只剩两份带 `_revised` 的 RQ2 权威文件。

归因订正：早期「被编辑器进程独占」是两种原因的混合——① 首次交付时该文件被
WorkBuddy 预览面板以共享读方式打开，Windows 拒绝对其写入/移动（真实共享锁，
会话压缩后句柄释放）；② `apply_B_status_sync_2026-11-11.py` 用 `os.rename`
移动到**已存在**的归档目标，Windows 抛 `FileExistsError`，被笼统打印成 "LOCK 仍被
进程独占"。两种失败都与用户是否另行打开外部程序无关。出公开仓库时按白名单
（8 份权威派生文件）打包即可，不必依赖目录整洁。
"""


def read_text(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig" if bom else "utf-8"), bom


def write_text(path, text, bom):
    out = text.encode("utf-8")
    if bom:
        out = b"\xef\xbb\xbf" + out
    with open(path, "wb") as f:
        f.write(out)


# 1) 全量预检锚点，避免部分写入
print("=== 1. 锚点预检 ===")
for path, pairs in JOBS:
    text, _ = read_text(path)
    for old, _new in pairs:
        n = text.count(old)
        print(f"  {os.path.basename(path)} :: n={n} :: {old[:40]}")
        if n != 1:
            raise RuntimeError(f"锚点不唯一或未找到：{os.path.basename(path)} :: {old[:60]}")

# 2) 原子归位：先验证内容一致，再 os.replace（Windows 允许覆盖已存在目标）
print()
print("=== 2. v1 原件归位 ===")
if os.path.exists(SRC):
    assert os.path.exists(DST), "归档副本缺失，中止"
    same = open(SRC, "rb").read() == open(DST, "rb").read()
    print(f"  原件/副本逐字节一致 = {same}")
    if not same:
        raise RuntimeError("原件与归档副本内容不一致，中止（不覆盖）")
    os.replace(SRC, DST)
    print(f"  MOVE OK -> {os.path.relpath(DST, ROOT)}")
else:
    print("  SKIP 原件已不在 processed 根（此前已移走）")

# 3) 文档状态订正
print()
print("=== 3. 文档状态订正 ===")
for path, pairs in JOBS:
    text, bom = read_text(path)
    for old, new in pairs:
        text = text.replace(old, new, 1)
    if path == FREADME and "### 2026-11-11 补充收口：v1 原件归位与「独占锁」归因订正" not in text:
        text = text.rstrip("\n") + "\n" + RM_APPEND
    write_text(path, text, bom)
    print(f"  OK  {os.path.relpath(path, ROOT)}")

# 4) 终检
print()
print("=== 4. 终检 ===")
print("  processed 根错位结果文件：")
for name in sorted(os.listdir(PROC)):
    if name.startswith("res_B_uncertainty_misalignment"):
        print("    " + name)
print("  _archive_v1 内容：")
for name in sorted(os.listdir(ARCHIVE)):
    print(f"    {name}  {os.path.getsize(os.path.join(ARCHIVE, name))} bytes")

f16a = os.path.join(ROOT, "论文B_重设计与后续研究方案_2026-11-06", "16_B①主稿开场上下文包_2026-11-10.md")
f16b = os.path.join(MAIN, "16_B①主稿开场上下文包_2026-11-10.md")
a = hashlib.md5(open(f16a, "rb").read()).hexdigest()
b = hashlib.md5(open(f16b, "rb").read()).hexdigest()
print(f"  两份 16 MD5 一致 = {a == b} ({a[:12]})")
print()
print("DONE")
