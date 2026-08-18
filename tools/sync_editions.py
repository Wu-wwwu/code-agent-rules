"""将统一核心物化到四个可独立发布的规则入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / "source" / "core.md"
EDITIONS_PATH = ROOT / "source" / "editions.json"
START = "<!-- SHARED-CORE:START -->"
END = "<!-- SHARED-CORE:END -->"


class SyncError(RuntimeError):
    """规则源或版本入口不满足同步契约。"""


def load_entries() -> tuple[Path, ...]:
    manifest = json.loads(EDITIONS_PATH.read_text(encoding="utf-8"))
    entries: list[Path] = []
    for edition, config in manifest.items():
        entry = ROOT / config["entry"]
        if not entry.is_file():
            raise SyncError(f"{edition} 入口不存在: {entry.relative_to(ROOT)}")
        entries.append(entry)
    return tuple(entries)


def render(content: str, core: str, entry: Path) -> str:
    if content.count(START) != 1 or content.count(END) != 1:
        raise SyncError(f"入口必须且只能包含一对核心标记: {entry.relative_to(ROOT)}")
    before, remainder = content.split(START, 1)
    _, after = remainder.split(END, 1)
    return f"{before}{START}\n{core.rstrip()}\n{END}{after}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只检查入口是否已与统一核心同步")
    args = parser.parse_args(argv)

    try:
        core = CORE_PATH.read_text(encoding="utf-8")
        stale: list[str] = []
        for entry in load_entries():
            content = entry.read_text(encoding="utf-8")
            expected = render(content, core, entry)
            if expected == content:
                continue
            stale.append(entry.relative_to(ROOT).as_posix())
            if not args.check:
                entry.write_text(expected, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, json.JSONDecodeError, SyncError) as error:
        print(f"版本核心同步失败: {error}", file=sys.stderr)
        return 1

    if args.check and stale:
        print("以下版本入口未与 source/core.md 同步:", file=sys.stderr)
        for path in stale:
            print(f"- {path}", file=sys.stderr)
        return 1

    action = "检查" if args.check else "同步"
    print(f"版本核心{action}通过: {len(load_entries())} 个独立入口。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
