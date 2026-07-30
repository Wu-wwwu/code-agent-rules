"""将 Code Agent Rules 安装到项目或指定 Code Agent 的规则入口。"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
EDITIONS = {
    "mini": ("mini/anchors.md", ("mini", "documents")),
    "rules": ("rules/agent.md", ("rules", "documents")),
    "self": ("self/core.md", ("self",)),
}
AGENT_PRESETS = {
    "cline": Path.home() / "Documents" / "Cline" / "Rules" / "AGENTS.md",
    "claude": Path.home() / ".claude" / "CLAUDE.md",
    "codex": Path.home() / ".codex" / "AGENTS.md",
}


class InstallError(RuntimeError):
    """可预期、可向用户说明的安装失败。"""


@dataclass(frozen=True)
class WriteOperation:
    source: Path | None
    destination: Path
    content: str | None = None
    preserve_existing: bool = False


def same_file_content(source: Path, destination: Path) -> bool:
    return destination.is_file() and filecmp.cmp(source, destination, shallow=False)


def backup_path(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(f"{path.name}.bak.{stamp}")
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.bak.{stamp}.{index}")
        index += 1
    return candidate


def tree_operations(source_dir: Path, destination_dir: Path, *, preserve_existing: bool) -> list[WriteOperation]:
    return [
        WriteOperation(
            source=source,
            destination=destination_dir / source.relative_to(source_dir),
            preserve_existing=preserve_existing,
        )
        for source in source_dir.rglob("*")
        if source.is_file()
    ]


def pointer_operation(destination: Path, pointer: str) -> WriteOperation:
    return WriteOperation(source=None, destination=destination, content=f"{pointer}\n")


def operation_is_current(operation: WriteOperation) -> bool:
    if operation.source is not None:
        return same_file_content(operation.source, operation.destination)
    return operation.destination.is_file() and operation.destination.read_text(encoding="utf-8") == operation.content


def preflight(operations: Iterable[WriteOperation], *, force: bool) -> None:
    conflicts: list[Path] = []
    for operation in operations:
        destination = operation.destination
        blocking_parent = next(
            (
                parent
                for parent in destination.parents
                if parent.exists() and not parent.is_dir()
            ),
            None,
        )
        if blocking_parent is not None:
            conflicts.append(blocking_parent)
            continue
        if not destination.exists() or operation_is_current(operation):
            continue
        if destination.is_dir():
            conflicts.append(destination)
        elif not operation.preserve_existing and not force:
            conflicts.append(destination)

    if conflicts:
        unique_conflicts = list(dict.fromkeys(conflicts))
        rendered = "\n".join(f"- {path}" for path in unique_conflicts[:20])
        suffix = "\n- ..." if len(unique_conflicts) > 20 else ""
        raise InstallError(
            "以下目标已有不同内容；安装未执行。确认可覆盖后使用 --force：\n"
            f"{rendered}{suffix}"
        )


def apply_operations(operations: Iterable[WriteOperation], *, force: bool, dry_run: bool) -> tuple[int, int, int]:
    written = skipped = backed_up = 0
    for operation in operations:
        destination = operation.destination
        if operation_is_current(operation):
            skipped += 1
            continue
        if destination.exists() and operation.preserve_existing:
            skipped += 1
            print(f"保留现有项目文档: {destination}")
            continue

        if destination.exists() and force:
            backup = backup_path(destination)
            print(f"备份: {destination} -> {backup}")
            if not dry_run:
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup)
            backed_up += 1

        print(f"{'计划写入' if dry_run else '写入'}: {destination}")
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if operation.source is not None:
                shutil.copy2(operation.source, destination)
            else:
                destination.write_text(operation.content or "", encoding="utf-8")
        written += 1
    return written, skipped, backed_up


def install_project(args: argparse.Namespace) -> None:
    target = Path(args.target).expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise InstallError(f"项目目标必须是目录: {target}")

    entry_destination = (target / args.entry_file).resolve()
    try:
        entry_destination.relative_to(target)
    except ValueError as error:
        raise InstallError("项目 --entry-file 必须位于目标项目目录内") from error

    entry, directories = EDITIONS[args.edition]
    operations: list[WriteOperation] = []

    for directory in directories:
        source_dir = ROOT / directory
        destination_dir = target / directory
        operations.extend(
            tree_operations(
                source_dir,
                destination_dir,
                preserve_existing=directory == "documents",
            )
        )

    operations.append(pointer_operation(entry_destination, entry))
    destinations = [operation.destination for operation in operations]
    try:
        resolved_destinations = [destination.resolve().relative_to(target) for destination in destinations]
    except ValueError as error:
        raise InstallError("项目写入目标经符号链接解析后超出目标项目目录") from error
    if len(resolved_destinations) != len(set(resolved_destinations)):
        raise InstallError("项目 --entry-file 与规则或文档安装目标冲突")
    for index, destination in enumerate(resolved_destinations):
        for other in resolved_destinations[index + 1 :]:
            if destination in other.parents or other in destination.parents:
                raise InstallError("项目 --entry-file 不能是规则或文档安装目标的父目录")
    preflight(operations, force=args.force)
    written, skipped, backed_up = apply_operations(operations, force=args.force, dry_run=args.dry_run)
    action = "预览完成" if args.dry_run else "项目安装完成"
    print(f"{action}: edition={args.edition}, 写入 {written}, 跳过 {skipped}, 备份 {backed_up}")


def resolve_agent_entry(args: argparse.Namespace) -> Path:
    if args.entry_file:
        return Path(args.entry_file).expanduser().resolve()
    if args.agent == "custom":
        raise InstallError("agent=custom 时必须提供 --entry-file")
    return AGENT_PRESETS[args.agent].resolve()


def install_agent(args: argparse.Namespace) -> None:
    destination = resolve_agent_entry(args)
    entry, _ = EDITIONS[args.edition]
    source_entry = (ROOT / entry).resolve()
    if not source_entry.is_file():
        raise InstallError(f"规则入口不存在: {source_entry}")
    if destination == source_entry:
        raise InstallError("用户级规则入口不能是当前 edition 的规范规则入口源文件")

    operation = pointer_operation(destination, source_entry.as_posix())
    preflight((operation,), force=args.force)
    written, skipped, backed_up = apply_operations((operation,), force=args.force, dry_run=args.dry_run)
    action = "预览完成" if args.dry_run else "Code Agent 安装完成"
    print(
        f"{action}: agent={args.agent}, edition={args.edition}, "
        f"入口={destination}, 写入 {written}, 跳过 {skipped}, 备份 {backed_up}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="安装 Code Agent Rules；默认遇到已有不同内容即停止。"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    project = subparsers.add_parser("project", help="复制规则到项目并写项目级入口")
    project.add_argument("target", help="目标项目目录")
    project.add_argument("--edition", choices=EDITIONS, default="mini")
    project.add_argument("--entry-file", default="AGENTS.md", help="项目规则入口文件名或相对路径")
    project.add_argument("--force", action="store_true", help="备份后覆盖冲突的规则/入口文件；项目文档仍保留")
    project.add_argument("--dry-run", action="store_true", help="只显示计划，不写文件")
    project.set_defaults(handler=install_project)

    agent = subparsers.add_parser("agent", help="为指定 Code Agent 写用户级绝对规则指针")
    agent.add_argument("agent", choices=(*AGENT_PRESETS, "custom"))
    agent.add_argument("--edition", choices=EDITIONS, default="mini")
    agent.add_argument("--entry-file", help="覆盖预设入口；custom 必填")
    agent.add_argument("--force", action="store_true", help="备份后覆盖已有不同入口")
    agent.add_argument("--dry-run", action="store_true", help="只显示计划，不写文件")
    agent.set_defaults(handler=install_agent)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (InstallError, OSError, UnicodeError) as error:
        print(f"安装失败: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())