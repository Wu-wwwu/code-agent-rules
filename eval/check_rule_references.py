"""检查规则 Markdown 中的跨文件章节引用。"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = tuple(ROOT.rglob("*.md"))

STABLE_REFERENCE = re.compile(
    r"`(?P<path>/(?:rules|self)/[^`]+\.md)`(?P<titles>(?:「[^」]+」)+)"
)
TITLE = re.compile(r"「([^」]+)」")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
NUMBER_PREFIX = re.compile(r"^\d+(?:\.\d+)*[.、]?\s*")
LEGACY_SECTION_REFERENCE = re.compile(
    r"(?:`[^`\r\n]+\.md`|(?<![\w./-])/?[\w./-]+\.md)\s*§"
)


def normalized_heading(raw_heading: str) -> str:
    """移除 Markdown 标记和可变数字编号，保留稳定语义标题。"""
    heading = raw_heading.strip().strip("#").strip()
    return NUMBER_PREFIX.sub("", heading).strip()


def main() -> int:
    errors: list[str] = []
    heading_cache: dict[Path, set[str]] = {}

    for source in MARKDOWN_FILES:
        content = source.read_text(encoding="utf-8")
        relative_source = source.relative_to(ROOT).as_posix()

        for match in LEGACY_SECTION_REFERENCE.finditer(content):
            line = content.count("\n", 0, match.start()) + 1
            errors.append(
                f"{relative_source}:{line}: 跨文件规则引用不得使用数字章节号: "
                f"{match.group(0)!r}"
            )

        for match in STABLE_REFERENCE.finditer(content):
            target = ROOT / match.group("path").lstrip("/")
            line = content.count("\n", 0, match.start()) + 1
            if not target.is_file():
                errors.append(
                    f"{relative_source}:{line}: 引用文件不存在: {match.group('path')}"
                )
                continue

            if target not in heading_cache:
                target_content = target.read_text(encoding="utf-8")
                heading_cache[target] = {
                    normalized_heading(heading)
                    for heading in HEADING.findall(target_content)
                }

            for title in TITLE.findall(match.group("titles")):
                if title not in heading_cache[target]:
                    errors.append(
                        f"{relative_source}:{line}: {match.group('path')} 中不存在标题「{title}」"
                    )

    if errors:
        print("规则引用检查失败：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"规则引用检查通过：已扫描 {len(MARKDOWN_FILES)} 个 Markdown 文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
