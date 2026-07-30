"""Cross-reference checker for mini rules.

Validates that all `methods/xxx.md` references in triggers.md and methods/*.md
resolve to existing files, and that referenced sections exist.
Run: python check_references.py (from mini/ directory)
"""

import re
import sys
from pathlib import Path

MINI_ROOT = Path(__file__).resolve().parent
METHODS_DIR = MINI_ROOT / "methods"


def check_triggers():
    """Check all method references in triggers.md."""
    triggers = MINI_ROOT / "triggers.md"
    if not triggers.exists():
        return []  # No triggers file — nothing to check
    content = triggers.read_text(encoding="utf-8")
    refs = re.findall(r"`methods/([^`]+\.md)`", content)
    return _resolve(refs, source="triggers.md")


def check_methods():
    """Check cross-references within method files."""
    errors = []
    for mf in sorted(METHODS_DIR.glob("*.md")):
        content = mf.read_text(encoding="utf-8")
        # Find method cross-references inside other method files
        refs = re.findall(r"`methods/([^`]+\.md)`", content)
        for ref_file in refs:
            target = METHODS_DIR / ref_file
            if not target.exists():
                errors.append(
                    f"  {mf.name}: references methods/{ref_file} -> NOT FOUND"
                )
        # Check /documents/ references (warn if not adjacent)
        doc_refs = re.findall(r"/documents/([^`\s\)]+)", content)
        for doc_ref in doc_refs:
            doc_path = MINI_ROOT.parent / "documents" / doc_ref
            if not doc_path.exists():
                errors.append(
                    f"  {mf.name}: references /documents/{doc_ref} -> NOT FOUND"
                )
    return errors


def _resolve(refs, source):
    """Resolve method file references to disk."""
    errors = []
    seen = set()
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        target = METHODS_DIR / ref
        if not target.exists():
            errors.append(f"  {source}: references methods/{ref} -> NOT FOUND")
    return errors


def main():
    errors = []
    errors.extend(check_triggers())
    errors.extend(check_methods())

    if errors:
        print(f"ERROR: {len(errors)} reference issue(s) found:")
        for e in errors:
            print(e)
        return 1
    else:
        # Count verified files
        methods_count = len(list(METHODS_DIR.glob("*.md")))
        print(f"OK: All references valid ({methods_count} methods, "
              f"{(MINI_ROOT / 'triggers.md').exists() and '1 triggers' or 'no triggers'})")
        return 0


if __name__ == "__main__":
    sys.exit(main())
