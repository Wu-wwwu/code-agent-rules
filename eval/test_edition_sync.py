"""统一核心与四个独立版本的一致性回归测试。"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_sync_module():
    module_path = ROOT / "tools" / "sync_editions.py"
    spec = importlib.util.spec_from_file_location("sync_editions", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载同步工具: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EditionSyncTests(unittest.TestCase):
    def test_all_entries_materialize_the_same_core(self) -> None:
        sync = load_sync_module()
        core = sync.CORE_PATH.read_text(encoding="utf-8").rstrip()
        manifest = json.loads(sync.EDITIONS_PATH.read_text(encoding="utf-8"))

        self.assertEqual({"mini", "lite", "rules", "self"}, set(manifest))
        for edition, config in manifest.items():
            with self.subTest(edition=edition):
                entry = ROOT / config["entry"]
                content = entry.read_text(encoding="utf-8")
                materialized = content.split(sync.START, 1)[1].split(sync.END, 1)[0].strip()
                self.assertEqual(core, materialized)

    def test_runtime_sets_do_not_depend_on_source_or_other_editions(self) -> None:
        manifest = json.loads((ROOT / "source" / "editions.json").read_text(encoding="utf-8"))
        edition_names = set(manifest)

        for edition, config in manifest.items():
            with self.subTest(edition=edition):
                runtime = set(config["runtime"])
                self.assertIn(edition, runtime)
                self.assertNotIn("source", runtime)
                self.assertNotIn("tools", runtime)
                self.assertFalse((edition_names - {edition}) & runtime)
                self.assertIn(config["entry"].split("/", 1)[0], runtime)

                for directory in runtime:
                    for path in (ROOT / directory).rglob("*"):
                        if not path.is_file() or path.suffix not in {".md", ".py", ".json"}:
                            continue
                        content = path.read_text(encoding="utf-8")
                        self.assertNotIn("source/core.md", content, path)
                        self.assertNotIn("source/editions.json", content, path)
                        self.assertNotIn("tools/sync_editions.py", content, path)


if __name__ == "__main__":
    unittest.main()
