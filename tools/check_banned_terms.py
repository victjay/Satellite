"""
check_banned_terms.py — v1.2
Banned-term scanner (regex-based, covers case/space/hyphen variants).
Run: python tools/check_banned_terms.py
Exit 1 if any banned term found; exit 0 if clean.
"""
import sys
import pathlib
import re

BANNED_PATTERNS = [
    r"\breal[\s\-]?time\b",
    r"\bframework\b",
    r"\bfleet\s+availability\b",
    r"통신\s*가능",
    r"\blink\s+available\b",
    r"\bvisible\s+for\s+communication\b",
    r"\bBER\s+1e",
    r"\bEb/N0\b",
]

SCAN_TARGETS = ["app.py", "modules/", "README.md", "data/"]

EXCLUDE_FILENAMES = {
    "check_banned_terms.py",
    "mock_tles.json",
}

EXCLUDE_NAME_PREFIXES = (
    "CLAUDE_CODE_PROMPT",
    "GPT_VERIFICATION",
)

EXCLUDE_DIRNAMES = {"docs"}


def scan():
    """Scan all target files for banned patterns; return list of violation strings."""
    found = []
    for target in SCAN_TARGETS:
        p = pathlib.Path(target)
        if not p.exists():
            continue
        if p.is_dir():
            files = (
                list(p.rglob("*.py"))
                + list(p.rglob("*.md"))
                + list(p.rglob("*.json"))
            )
        else:
            files = [p]
        for f in files:
            if (
                f.name in EXCLUDE_FILENAMES
                or any(f.name.startswith(pfx) for pfx in EXCLUDE_NAME_PREFIXES)
                or any(part in EXCLUDE_DIRNAMES for part in f.parts)
            ):
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            for pattern in BANNED_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    found.append(f"{f}: pattern='{pattern}' → found: {matches}")
    return found


if __name__ == "__main__":
    issues = scan()
    if issues:
        print("❌ Banned terms found:")
        for i in issues:
            print(f"  {i}")
        sys.exit(1)
    else:
        print("✅ No banned terms found.")
        sys.exit(0)
