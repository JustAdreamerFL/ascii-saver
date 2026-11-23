"""Pure presentation helpers for the read-only installation diagnostic checks."""
from __future__ import annotations


def diagnostic_summary(checks: list[tuple[str, bool, str]]) -> str:
    passed = sum(1 for _name, ok, _detail in checks if ok)
    count = len(checks)
    if not count:
        return "No diagnostic checks returned."
    if passed == count:
        return f"All {count} checks passed."
    return f"{passed} of {count} checks passed."


def diagnostic_report(checks: list[tuple[str, bool, str]]) -> str:
    lines = ["ASCII Saver diagnostics", diagnostic_summary(checks), ""]
    lines.extend(
        f"{'PASS' if ok else 'FAIL'}  {name}: {detail}"
        for name, ok, detail in checks
    )
    return "\n".join(lines).rstrip() + "\n"
