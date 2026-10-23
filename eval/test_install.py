"""安装辅助的临时目录回归测试。"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rules_installer", ROOT / "install.py")
assert SPEC and SPEC.loader
INSTALLER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = INSTALLER
SPEC.loader.exec_module(INSTALLER)


class InstallerTests(unittest.TestCase):
    def run_installer(self, *arguments: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return INSTALLER.main(list(arguments))

    def test_self_project_install(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.assertEqual(0, self.run_installer("project", directory, "--edition", "self"))
            self.assertTrue((target / "self" / "core.md").is_file())
            self.assertEqual("self/core.md\n", (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_default_project_install_uses_mini(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.assertEqual(0, self.run_installer("project", directory))
            self.assertTrue((target / "mini" / "agent.md").is_file())
            self.assertTrue((target / "mini" / "triggers.md").is_file())
            self.assertFalse((target / "documents").exists())
            self.assertEqual("mini/agent.md\n", (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_project_install_includes_documents_only_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.assertEqual(
                0,
                self.run_installer("project", directory, "--include-documents"),
            )
            self.assertTrue((target / "documents" / "business-rules.md").is_file())
            self.assertEqual("mini/agent.md\n", (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_lite_agent_install_uses_absolute_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            entry_file = Path(directory) / "agent" / "RULES.md"
            self.assertEqual(
                0,
                self.run_installer(
                    "agent", "custom", "--edition", "lite", "--entry-file", str(entry_file)
                ),
            )
            self.assertEqual(
                f"{(ROOT / 'lite' / 'agent.md').resolve().as_posix()}\n",
                entry_file.read_text(encoding="utf-8"),
            )

    def test_lite_project_install(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.assertEqual(0, self.run_installer("project", directory, "--edition", "lite"))
            self.assertTrue((target / "lite" / "agent.md").is_file())
            self.assertTrue((target / "lite" / "methods" / "templates.md").is_file())
            self.assertFalse((target / "documents").exists())
            self.assertEqual("lite/agent.md\n", (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_project_install_excludes_generated_cache_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            generated = ROOT / "mini" / "__pycache__" / "generated-test.pyc"
            generated.parent.mkdir(exist_ok=True)
            generated.write_bytes(b"cache")
            try:
                self.assertEqual(0, self.run_installer("project", directory))
                self.assertFalse((target / "mini" / "__pycache__").exists())
                self.assertEqual([], list(target.rglob("*.pyc")))
            finally:
                generated.unlink(missing_ok=True)

    def test_project_install_rolls_back_when_a_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            original_copy2 = INSTALLER.shutil.copy2
            calls = 0

            def fail_on_second_copy(source, destination, *args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected copy failure")
                return original_copy2(source, destination, *args, **kwargs)

            with mock.patch.object(INSTALLER.shutil, "copy2", side_effect=fail_on_second_copy):
                self.assertEqual(1, self.run_installer("project", directory))
            self.assertEqual([], list(target.iterdir()))
            self.assertEqual([], list(target.rglob("*.bak.*")))

    def test_project_install_restores_overwritten_file_when_later_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            entry = target / "AGENTS.md"
            entry.write_text("old pointer\n", encoding="utf-8")
            operations = [
                INSTALLER.pointer_operation(entry, "mini/agent.md"),
                INSTALLER.WriteOperation(
                    source=ROOT / "mini" / "agent.md",
                    destination=target / "mini" / "agent.md",
                ),
            ]
            original_copy2 = INSTALLER.shutil.copy2
            calls = 0

            def fail_on_second_copy(source, destination, *args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected copy failure")
                return original_copy2(source, destination, *args, **kwargs)

            with mock.patch.object(INSTALLER.shutil, "copy2", side_effect=fail_on_second_copy):
                with self.assertRaises(INSTALLER.InstallError):
                    INSTALLER.apply_operations(operations, force=True, dry_run=False)
            self.assertEqual("old pointer\n", entry.read_text(encoding="utf-8"))
            self.assertEqual([], list(target.rglob("*.bak.*")))

    def test_pointer_verification_failure_rolls_back_all_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            entry = target / "AGENTS.md"
            entry.write_text("old pointer\n", encoding="utf-8")
            operations = [
                INSTALLER.WriteOperation(
                    source=ROOT / "mini" / "agent.md",
                    destination=target / "mini" / "agent.md",
                ),
                INSTALLER.pointer_operation(entry, "mini/agent.md"),
            ]

            def fail_verification() -> None:
                raise INSTALLER.InstallError("injected verification failure")

            with self.assertRaisesRegex(INSTALLER.InstallError, "injected verification failure"):
                INSTALLER.apply_operations(
                    operations,
                    force=True,
                    dry_run=False,
                    verify=fail_verification,
                )
            self.assertEqual("old pointer\n", entry.read_text(encoding="utf-8"))
            self.assertFalse((target / "mini").exists())
            self.assertEqual([], list(target.rglob("*.bak.*")))

    def test_rules_project_preserves_existing_documents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            document = target / "documents" / "architecture.md"
            document.parent.mkdir(parents=True)
            document.write_text("project fact\n", encoding="utf-8")
            self.assertEqual(0, self.run_installer("project", directory, "--edition", "rules", "--include-documents"))
            self.assertTrue((target / "rules" / "agent.md").is_file())
            self.assertEqual("project fact\n", document.read_text(encoding="utf-8"))
            self.assertEqual("rules/agent.md\n", (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_conflict_stops_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "AGENTS.md").write_text("custom instructions\n", encoding="utf-8")
            self.assertEqual(1, self.run_installer("project", directory, "--edition", "self"))
            self.assertFalse((target / "self").exists())
            self.assertEqual("custom instructions\n", (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_force_backs_up_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "AGENTS.md").write_text("old\n", encoding="utf-8")
            self.assertEqual(0, self.run_installer("project", directory, "--force"))
            self.assertEqual("mini/agent.md\n", (target / "AGENTS.md").read_text(encoding="utf-8"))
            backups = list(target.glob("AGENTS.md.bak.*"))
            self.assertEqual(1, len(backups))
            self.assertEqual("old\n", backups[0].read_text(encoding="utf-8"))

    def test_custom_agent_install_uses_absolute_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            entry_file = Path(directory) / "agent" / "RULES.md"
            self.assertEqual(
                0,
                self.run_installer(
                    "agent", "custom", "--edition", "rules", "--entry-file", str(entry_file)
                ),
            )
            self.assertEqual(
                f"{(ROOT / 'rules' / 'agent.md').resolve().as_posix()}\n",
                entry_file.read_text(encoding="utf-8"),
            )

    def test_default_agent_install_uses_mini(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            entry_file = Path(directory) / "agent" / "RULES.md"
            self.assertEqual(
                0,
                self.run_installer("agent", "custom", "--entry-file", str(entry_file)),
            )
            self.assertEqual(
                f"{(ROOT / 'mini' / 'agent.md').resolve().as_posix()}\n",
                entry_file.read_text(encoding="utf-8"),
            )

    def test_agent_entry_cannot_overwrite_edition_source(self) -> None:
        flag_sets = ((), ("--force",), ("--dry-run",), ("--force", "--dry-run"))
        editions = (
            ("mini", Path("mini/agent.md")),
            ("lite", Path("lite/agent.md")),
            ("self", Path("self/core.md")),
            ("rules", Path("rules/agent.md")),
        )
        for edition, relative_source in editions:
            for path_kind in ("absolute", "parent-alias"):
                for flags in flag_sets:
                    with self.subTest(edition=edition, path_kind=path_kind, flags=flags):
                        with tempfile.TemporaryDirectory() as directory:
                            isolated_root = Path(directory)
                            sources = {
                                Path("mini/agent.md"): b"mini source\n",
                                Path("lite/agent.md"): b"lite source\n",
                                Path("self/core.md"): b"self source\n",
                                Path("rules/agent.md"): b"rules source\n",
                            }
                            for relative_path, content in sources.items():
                                source = isolated_root / relative_path
                                source.parent.mkdir(parents=True, exist_ok=True)
                                source.write_bytes(content)

                            selected_source = isolated_root / relative_source
                            entry_file = selected_source
                            if path_kind == "parent-alias":
                                entry_file = selected_source.parent / ".." / selected_source.parent.name / selected_source.name

                            with mock.patch.object(INSTALLER, "ROOT", isolated_root):
                                result = self.run_installer(
                                    "agent",
                                    "custom",
                                    "--edition",
                                    edition,
                                    "--entry-file",
                                    str(entry_file),
                                    *flags,
                                )

                            self.assertEqual(1, result)
                            for relative_path, content in sources.items():
                                self.assertEqual(content, (isolated_root / relative_path).read_bytes())
                            self.assertEqual([], list(isolated_root.rglob("*.bak.*")))

    def test_agent_entry_hardlink_cannot_overwrite_source(self) -> None:
        for edition, relative_source in (("self", Path("self/core.md")), ("rules", Path("rules/agent.md"))):
            with self.subTest(edition=edition):
                with tempfile.TemporaryDirectory() as directory:
                    isolated_root = Path(directory)
                    source = isolated_root / relative_source
                    source.parent.mkdir(parents=True)
                    source.write_bytes(b"source must remain unchanged\n")
                    entry_file = isolated_root / "alias.md"
                    entry_file.hardlink_to(source)
                    with mock.patch.object(INSTALLER, "ROOT", isolated_root):
                        result = self.run_installer(
                            "agent",
                            "custom",
                            "--edition",
                            edition,
                            "--entry-file",
                            str(entry_file),
                            "--force",
                        )
                    self.assertEqual(1, result)
                    self.assertEqual(b"source must remain unchanged\n", source.read_bytes())
                    self.assertEqual(b"source must remain unchanged\n", entry_file.read_bytes())

    def test_agent_entry_symlink_cannot_overwrite_external_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / "external.md"
            external.write_text("external content\n", encoding="utf-8")
            entry_file = root / "RULES.md"
            try:
                os.symlink(external, entry_file)
            except OSError as error:
                self.skipTest(f"symbolic links unavailable: {error}")

            self.assertEqual(
                1,
                self.run_installer(
                    "agent",
                    "custom",
                    "--entry-file",
                    str(entry_file),
                    "--force",
                ),
            )
            self.assertTrue(entry_file.is_symlink())
            self.assertEqual("external content\n", external.read_text(encoding="utf-8"))
            self.assertEqual([], list(root.rglob("*.bak.*")))

    def test_agent_entry_junction_cannot_overwrite_external_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external_directory:
            if os.name != "nt":
                self.skipTest("Windows junctions are only available on Windows")
            root = Path(directory)
            external = Path(external_directory)
            linked_directory = root / "linked"
            environment = os.environ.copy()
            environment.update(
                {
                    "CODE_AGENT_JUNCTION_PATH": str(linked_directory),
                    "CODE_AGENT_JUNCTION_TARGET": str(external),
                }
            )
            try:
                created = subprocess.run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-NonInteractive",
                        "-Command",
                        "New-Item -ItemType Junction -Path $env:CODE_AGENT_JUNCTION_PATH "
                        "-Target $env:CODE_AGENT_JUNCTION_TARGET | Out-Null",
                    ],
                    capture_output=True,
                    text=True,
                    env=environment,
                    check=False,
                )
            except OSError as error:
                self.skipTest(f"junction creation unavailable: {error}")
            if created.returncode != 0:
                self.skipTest(f"junction creation unavailable: {created.stderr.strip()}")

            self.assertTrue(linked_directory.exists())
            self.assertFalse(linked_directory.is_symlink())
            external_entry = external / "RULES.md"
            external_entry.write_text("external content\n", encoding="utf-8")
            entry_file = linked_directory / "RULES.md"

            for context in (
                contextlib.nullcontext(),
                mock.patch.object(INSTALLER.Path, "is_junction", None, create=True),
            ):
                with context:
                    self.assertEqual(
                        1,
                        self.run_installer(
                            "agent",
                            "custom",
                            "--entry-file",
                            str(entry_file),
                            "--force",
                        ),
                    )
                self.assertEqual("external content\n", external_entry.read_text(encoding="utf-8"))
                self.assertEqual([], list(external.rglob("*.bak.*")))

    def test_project_entry_under_symlink_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            target = Path(directory)
            linked_directory = target / "linked"
            try:
                os.symlink(outside, linked_directory, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symbolic links unavailable: {error}")

            self.assertEqual(
                1,
                self.run_installer(
                    "project",
                    directory,
                    "--entry-file",
                    "linked/AGENTS.md",
                ),
            )
            self.assertFalse((Path(outside) / "AGENTS.md").exists())
            self.assertFalse((target / "mini").exists())

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(0, self.run_installer("project", directory, "--dry-run"))
            self.assertEqual([], list(Path(directory).iterdir()))

    def test_project_entry_cannot_escape_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory).parent / "outside-agents.md"
            self.assertEqual(
                1,
                self.run_installer(
                    "project", directory, "--entry-file", str(Path("..") / outside.name)
                ),
            )
            self.assertFalse(outside.exists())

    def test_project_entry_cannot_collide_with_rule_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                1,
                self.run_installer(
                    "project", directory, "--entry-file", str(Path("mini") / "agent.md")
                ),
            )
            self.assertEqual([], list(Path(directory).iterdir()))

    def test_project_entry_cannot_be_rule_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                1,
                self.run_installer("project", directory, "--entry-file", "mini"),
            )
            self.assertEqual([], list(Path(directory).iterdir()))

    def test_parent_file_conflict_stops_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            documents = target / "documents"
            documents.write_text("not a directory\n", encoding="utf-8")
            self.assertEqual(1, self.run_installer("project", directory, "--edition", "rules", "--include-documents"))
            self.assertFalse((target / "rules").exists())
            self.assertEqual("not a directory\n", documents.read_text(encoding="utf-8"))

    def test_lite_rejects_root_document_templates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                1,
                self.run_installer(
                    "project",
                    directory,
                    "--edition",
                    "lite",
                    "--include-documents",
                ),
            )
            self.assertEqual([], list(Path(directory).iterdir()))


if __name__ == "__main__":
    unittest.main()
