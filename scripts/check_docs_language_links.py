#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验 docs/ 目录下所有 Markdown 文件是否在首个非空行包含语言切换链接：
- 中文文档 (<name>.md)：首行需为 [English Version](<name>_en.md)
- 英文文档 (<name>_en.md)：首行需为 [中文文档](<name>.md)

脚本在发现不符合规范时返回非零退出码，以用于 CI 阻止合并。
"""
from __future__ import annotations

import sys
import re
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"

ZH_LABEL = "[English Version]"
EN_LABEL = "[中文文档]"

# 允许的匹配正则（更稳健，兼容可能的额外空格）
ZH_PATTERN = re.compile(r"^\[English Version\]\((?P<target>[^)]+)\)\s*$")
EN_PATTERN = re.compile(r"^\[中文文档\]\((?P<target>[^)]+)\)\s*$")


def first_non_empty_line(text: str) -> Tuple[int, str]:
    """返回首个非空行的 (行号, 内容)，若无则 (-1, "")."""
    for idx, raw in enumerate(text.splitlines()):
        line = raw.strip()
        if line:
            return idx, line
    return -1, ""


def expected_counterpart(md_path: Path) -> Path:
    """根据文档路径计算期望的对语言文档路径。"""
    name = md_path.name
    if name.endswith("_en.md"):
        return md_path.with_name(name.replace("_en.md", ".md"))
    else:
        stem = name[:-3]  # 去掉 .md
        return md_path.with_name(f"{stem}_en.md")


def check_file(md_path: Path) -> Tuple[bool, str]:
    """检查单个文件是否符合规则，返回 (是否通过, 错误消息)。"""
    rel = md_path.relative_to(ROOT)
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"读取文件失败: {rel} -> {e}"

    line_no, line = first_non_empty_line(content)
    if line_no == -1:
        return False, f"文件为空或无有效内容: {rel}"

    counterpart = expected_counterpart(md_path)
    # 目标必须是相对链接（仅文件名）
    expected_target = counterpart.name

    if md_path.name.endswith("_en.md"):
        # 英文文档需指向中文文档
        m = EN_PATTERN.match(line)
        if not m:
            return False, f"{rel}: 首行应为 '{EN_LABEL}({expected_target})'，实际为: {line}"
        if m.group("target") != expected_target:
            return False, f"{rel}: 链接目标应为 '{expected_target}'，实际为: {m.group('target')}"
    else:
        # 中文文档需指向英文文档
        m = ZH_PATTERN.match(line)
        if not m:
            return False, f"{rel}: 首行应为 '{ZH_LABEL}({expected_target})'，实际为: {line}"
        if m.group("target") != expected_target:
            return False, f"{rel}: 链接目标应为 '{expected_target}'，实际为: {m.group('target')}"

    # 对语言文档是否存在
    if not counterpart.exists():
        return False, f"{rel}: 缺少对应文档 {counterpart.name}"

    return True, f"OK: {rel}"


def main() -> int:
    if not DOCS_DIR.exists():
        print(f"未找到 docs 目录: {DOCS_DIR}")
        return 1

    md_files: List[Path] = sorted(DOCS_DIR.glob("*.md"))
    if not md_files:
        print("docs 目录下未找到任何 .md 文件")
        return 1

    failed: List[str] = []
    passed_count = 0

    for md in md_files:
        ok, msg = check_file(md)
        if ok:
            print(msg)
            passed_count += 1
        else:
            print(msg)
            failed.append(msg)

    print("-" * 60)
    print(f"检查完成：通过 {passed_count} / 总计 {len(md_files)}")

    if failed:
        print("以下文件未通过校验：")
        for f in failed:
            print(f" - {f}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
