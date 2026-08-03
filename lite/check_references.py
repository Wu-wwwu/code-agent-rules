"""Check Lite method routes and cross-references."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
METHODS = ROOT / "methods"
ROUTED = {
    "bug-diagnosis.md", "business-rules.md", "data-entity-analysis.md",
    "decision-recall.md", "dependency-upgrade.md", "destructive-analysis.md",
    "multi-agent.md", "neutral-design.md", "performance-evidence.md",
    "project-context.md", "technology-selection.md", "toolchain-scope.md",
}
SUPPORT = {"project-documents.md", "templates.md"}


def main() -> int:
    errors = []
    triggers = (ROOT / "triggers.md").read_text(encoding="utf-8")
    refs = re.findall(r"`methods/([^`]+\.md)`", triggers)
    routed = set(refs) - SUPPORT
    if routed != ROUTED:
        errors.append(f"route mismatch: missing={sorted(ROUTED-routed)}, extra={sorted(routed-ROUTED)}")
    for source in [ROOT / "triggers.md", *sorted(METHODS.glob("*.md"))]:
        text = source.read_text(encoding="utf-8")
        for ref in re.findall(r"`methods/([^`]+\.md)`", text):
            if not (METHODS / ref).is_file():
                errors.append(f"{source.name}: methods/{ref} not found")
    if errors:
        print("ERROR:\n" + "\n".join(f"- {e}" for e in errors))
        return 1
    print(f"OK: Lite references valid ({len(list(METHODS.glob('*.md')))} methods)")
    return 0


if __name__ == "__main__":
    sys.exit(main())