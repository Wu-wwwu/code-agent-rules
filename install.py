"""将 Code Agent Rules 安装到项目或指定 Code Agent 的规则入口。"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parent
EDITIONS = {
    "mini": ("mini/agent.md", ("mini",)),
    "lite": ("lite/agent.md", ("lite",)),
    "rules": ("rules/agent.md", ("rules",)),
    "self": ("self/core.md", ("self",)),
}
DOCUMENT_EDITIONS = {"mini", "rules"}
AGENT_PRESETS = {
    "cline": Path.home() / "Documents" / "Cline" / "Rules" / "AGENTS.md",
    "claude": Path.home() / ".claude" / "CLAUDE.md",
    "codex": Path.home() / ".codex" / "AGENTS.md",
}
IGNORED_TREE_PARTS = {".git", ".pytest_cache", "__pycache__"}


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


def same_file_identity(source: Path, destination: Path) -> bool:
    """Detect hard links and other aliases before writing a pointer."""
    if not source.exists() or not destination.exists():
        return False
    try:
        return source.samefile(destination)
    except FileNotFoundError:
        return False
    except OSError as error:
        raise InstallError(f"无法确认安装目标是否与规范源相同: {destination}") from error


def verify_pointer(destination: Path, pointer: str, target: Path) -> None:
    """Read back a written pointer and its referenced rule entry."""
    expected = f"{pointer}\n"
    try:
        actual = destination.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise InstallError(f"无法回读规则入口: {destination}") from error
    if actual != expected:
        raise InstallError(f"规则入口回读内容不符: {destination}")
    if not target.is_file():
        raise InstallError(f"规则入口目标不可访问: {target}")


def backup_path(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(f"{path.name}.bak.{stamp}")
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.bak.{stamp}.{index}")
        index += 1
    return candidate


def reject_source_aliases(operations: Iterable[WriteOperation]) -> None:
    """Reject any destination that aliases a source file in this installation."""
    operations = list(operations)
    sources = [operation.source for operation in operations if operation.source is not None]
    for operation in operations:
        if any(source is not None and same_file_identity(source, operation.destination) for source in sources):
            raise InstallError(
                f"安装目标不能与规范源文件共享文件身份: {operation.destination}"
            )


def reject_symlink_paths(operations: Iterable[WriteOperation]) -> None:
    """Reject symlink-like destinations and parents before any write can follow them."""
    def is_link(path: Path) -> bool:
        is_junction = getattr(path, "is_junction", None)
        return path.is_symlink() or (is_junction is not None and is_junction())

    for operation in operations:
        path = Path(os.path.abspath(operation.destination))
        for component in (path, *path.parents):
            if is_link(component):
                raise InstallError(
                    f"安装目标不能是符号链接/junction或位于其目录下: {operation.destination}"
                )


def tree_operations(source_dir: Path, destination_dir: Path, *, preserve_existing: bool) -> list[WriteOperation]:
    return [
        WriteOperation(
            source=source,
            destination=destination_dir / source.relative_to(source_dir),
            preserve_existing=preserve_existing,
        )
        for source in source_dir.rglob("*")
        if source.is_file()
        and not (IGNORED_TREE_PARTS & set(source.relative_to(source_dir).parts))
        and source.suffix.lower() != ".pyc"
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


def apply_operations(
    operations: Iterable[WriteOperation],
    *,
    force: bool,
    dry_run: bool,
    verify: Callable[[], None] | None = None,
) -> tuple[int, int, int]:
    operations = list(operations)
    written = skipped = backed_up = 0
    changed: list[tuple[Path, Path | None, bool]] = []
    backups: list[Path] = []
    created_directories: set[Path] = set()
    try:
        for operation in operations:
            destination = operation.destination
            if operation_is_current(operation):
                skipped += 1
                continue
            if destination.exists() and operation.preserve_existing:
                skipped += 1
                print(f"保留现有项目文档: {destination}")
                continue

            backup: Path | None = None
            existed_before = destination.exists()
            if existed_before and not force:
                raise InstallError(f"写入前目标出现不同内容，安装已停止: {destination}")
            if existed_before and force:
                backup = backup_path(destination)
                backups.append(backup)
                print(f"备份: {destination} -> {backup}")
                if not dry_run:
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(destination, backup)
                backed_up += 1

            print(f"{'计划写入' if dry_run else '写入'}: {destination}")
            if not dry_run:
                parent = destination.parent
                while not parent.exists():
                    created_directories.add(parent)
                    parent = parent.parent
                destination.parent.mkdir(parents=True, exist_ok=True)
                changed.append((destination, backup, existed_before))
                if operation.source is not None:
                    shutil.copy2(operation.source, destination)
                else:
                    destination.write_text(operation.content or "", encoding="utf-8")
            written += 1
        if verify is not None and not dry_run:
            verify()
    except (OSError, UnicodeError, InstallError) as error:
        rollback_errors: list[str] = []
        for destination, backup, existed_before in reversed(changed):
            try:
                if destination.exists():
                    if destination.is_dir():
                        shutil.rmtree(destination)
                    else:
                        destination.unlink()
                if backup is not None and backup.exists():
                    shutil.move(backup, destination)
                elif existed_before:
                    rollback_errors.append(f"无法恢复 {destination}")
            except OSError as rollback_error:
                rollback_errors.append(f"恢复 {destination} 失败: {rollback_error}")
        for backup in backups:
            if backup.exists():
                try:
                    backup.unlink()
                except OSError as cleanup_error:
                    rollback_errors.append(f"清理备份 {backup} 失败: {cleanup_error}")
        for directory in sorted(created_directories, key=lambda path: len(path.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        detail = f"；回滚失败: {'；'.join(rollback_errors)}" if rollback_errors else "；已回滚已写入的文件"
        raise InstallError(f"写入过程中失败: {error}{detail}") from error
    return written, skipped, backed_up


def install_project(args: argparse.Namespace) -> None:
    target = Path(args.target).expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise InstallError(f"项目目标必须是目录: {target}")

    entry_destination = Path(os.path.abspath(target / args.entry_file))
    try:
        entry_destination.relative_to(target)
    except ValueError as error:
        raise InstallError("项目 --entry-file 必须位于目标项目目录内") from error

    entry, directories = EDITIONS[args.edition]
    if not (ROOT / entry).is_file():
        raise InstallError(f"规则入口不存在: {ROOT / entry}")
    if getattr(args, "include_documents", False):
        if args.edition not in DOCUMENT_EDITIONS:
            raise InstallError("--include-documents 仅适用于 mini 或 rules 版本")
        directories = (*directories, "documents")
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
    reject_source_aliases(operations)
    reject_symlink_paths(operations)
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
    written, skipped, backed_up = apply_operations(
        operations,
        force=args.force,
        dry_run=args.dry_run,
        verify=lambda: verify_pointer(entry_destination, entry, target / entry),
    )
    action = "预览完成" if args.dry_run else "项目安装完成"
    print(f"{action}: edition={args.edition}, 写入 {written}, 跳过 {skipped}, 备份 {backed_up}")


def resolve_agent_entry(args: argparse.Namespace) -> Path:
    if args.entry_file:
        return Path(os.path.abspath(Path(args.entry_file).expanduser()))
    if args.agent == "custom":
        raise InstallError("agent=custom 时必须提供 --entry-file")
    return AGENT_PRESETS[args.agent].resolve()


def install_agent(args: argparse.Namespace) -> None:
    destination = resolve_agent_entry(args)
    entry, _ = EDITIONS[args.edition]
    source_entry = (ROOT / entry).resolve()
    if not source_entry.is_file():
        raise InstallError(f"规则入口不存在: {source_entry}")
    if destination == source_entry or same_file_identity(source_entry, destination):
        raise InstallError("用户级规则入口不能是当前 edition 的规范规则源文件或其文件别名")

    operation = pointer_operation(destination, source_entry.as_posix())
    reject_symlink_paths((operation,))
    preflight((operation,), force=args.force)
    written, skipped, backed_up = apply_operations(
        (operation,),
        force=args.force,
        dry_run=args.dry_run,
        verify=lambda: verify_pointer(destination, source_entry.as_posix(), source_entry),
    )
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
    project.add_argument(
        "--include-documents",
        action="store_true",
        help="显式复制项目文档模板；模板内容必须先验证，不自动作为项目事实",
    )
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
