"""检查规则 Markdown 中的跨文件章节引用。"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_SOURCES = (
    ROOT / "README.md",
    ROOT / "mini",
    ROOT / "lite",
    ROOT / "rules",
    ROOT / "self",
    ROOT / "documents",
    ROOT / "eval",
)
IGNORED_PARTS = {".git", ".kilo", ".pytest_cache", "__pycache__", "node_modules", "worktrees"}


def iter_markdown_files() -> tuple[Path, ...]:
    """Return only maintained rule, document, and evaluation Markdown files."""
    files: list[Path] = []
    for source in MARKDOWN_SOURCES:
        candidates = (source,) if source.is_file() else source.rglob("*.md")
        for path in candidates:
            if path.is_file() and not (IGNORED_PARTS & set(path.relative_to(ROOT).parts)):
                files.append(path)
    return tuple(sorted(set(files)))


MARKDOWN_FILES = iter_markdown_files()
POINTER_FILES = (ROOT / "AGENTS.md", ROOT / "CLAUDE.md")
LOCAL_AGENT_POINTERS = {"mini/agent.md", "lite/agent.md", "rules/agent.md", "self/core.md"}
AGENT_ENTRY_SUFFIXES = tuple(f"/{path}" for path in LOCAL_AGENT_POINTERS)

STABLE_REFERENCE = re.compile(
    r"`(?P<path>(?:\./|\.\./|/)?[^`\r\n]+\.md)`(?P<titles>(?:「[^」]+」)+)"
)
TITLE = re.compile(r"「([^」]+)」")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
NUMBER_PREFIX = re.compile(r"^\d+(?:\.\d+)*[.、]?\s*")
LEGACY_SECTION_REFERENCE = re.compile(
    r"(?:`[^`\r\n]+\.md`|(?<![\w./-])/?[\w./-]+\.md)\s*§"
)
WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")


def normalized_heading(raw_heading: str) -> str:
    """移除 Markdown 标记和可变数字编号，保留稳定语义标题。"""
    heading = raw_heading.strip().strip("#").strip()
    return NUMBER_PREFIX.sub("", heading).strip()


def check_pointer_file(pointer_file: Path, errors: list[str]) -> None:
    """确保工具入口是唯一、无包装且可访问的规则指针。"""
    label = pointer_file.relative_to(ROOT).as_posix()
    if not pointer_file.is_file():
        errors.append(f"{label}: 文件不存在，无法提供规则指针")
        return

    content = pointer_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    if len(lines) != 1 or not lines[0]:
        errors.append(f"{label}: 必须且只能包含一行非空规则路径")
        return

    pointer = lines[0]
    if pointer != pointer.strip():
        errors.append(f"{label}: 路径前后不得包含空白")
        return
    if pointer.startswith(("#", "-", "*", "`")) or pointer.endswith("`"):
        errors.append(f"{label}: 只能写裸路径，不得包含 Markdown 标记或说明")
        return

    normalized = pointer.replace("\\", "/")
    is_absolute = (
        normalized.startswith("/")
        or pointer.startswith("\\\\")
        or WINDOWS_ABSOLUTE_PATH.match(pointer) is not None
    )

    if not is_absolute:
        if normalized not in LOCAL_AGENT_POINTERS:
            errors.append(
                f"{label}: 相对指针只能是 mini/agent.md、lite/agent.md、rules/agent.md 或 self/core.md"
            )
            return
        if not (ROOT / normalized).is_file():
            errors.append(f"{label}: 指针目标不存在: {pointer}")
        return

    if not normalized.endswith(AGENT_ENTRY_SUFFIXES):
        errors.append(
            f"{label}: 固定路径必须指向 mini/agent.md、lite/agent.md、rules/agent.md 或 self/core.md"
        )
        return

    if not Path(pointer).is_file():
        errors.append(f"{label}: 固定路径不可访问或目标不存在: {pointer}")



def check_pointer_consistency(errors: list[str]) -> None:
    """Ensure two supported root entry files select one controller edition."""
    values: dict[Path, str] = {}
    for pointer_file in POINTER_FILES:
        if not pointer_file.is_file():
            continue
        try:
            lines = pointer_file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        if len(lines) == 1 and lines[0].strip() == lines[0] and lines[0]:
            values[pointer_file] = lines[0].replace("\\", "/")
    if len(values) == len(POINTER_FILES) and len(set(values.values())) != 1:
        rendered = ", ".join(
            f"{path.relative_to(ROOT).as_posix()}={value}"
            for path, value in values.items()
        )
        errors.append(f"根目录入口必须选择同一个总控版本: {rendered}")


def resolve_reference(source: Path, reference: str) -> Path:
    """Resolve project-root or rule-file-relative Markdown references."""
    if reference.startswith("/"):
        return ROOT / reference.lstrip("/")
    if reference.startswith("methods/"):
        relative_source = source.relative_to(ROOT)
        if relative_source.parts[0] in {"mini", "lite"}:
            return ROOT / relative_source.parts[0] / reference
    return (source.parent / reference).resolve()


def main() -> int:
    errors: list[str] = []
    heading_cache: dict[Path, set[str]] = {}

    for pointer_file in POINTER_FILES:
        check_pointer_file(pointer_file, errors)
    check_pointer_consistency(errors)

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
            target = resolve_reference(source, match.group("path"))
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
