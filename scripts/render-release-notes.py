#!/usr/bin/env python3
"""Render the GitHub release body for ASCII Saver source and package assets."""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


def asset_url(repository: str, tag: str, name: str) -> str:
    return f"https://github.com/{repository}/releases/download/{tag}/{name}"


def rpm_number(name: str | Path) -> int:
    match = re.search(r"\.fc(\d+)\.", Path(name).name)
    return int(match.group(1)) if match else 0


def fedora_label(name: str) -> str:
    number = rpm_number(name)
    return f"Fedora {number}" if number else "Fedora"


def package_row(label: str, name: str | Path, command: str, repository: str, tag: str) -> str:
    filename = Path(name).name
    return (
        f"| {label} | [`{filename}`]({asset_url(repository, tag, filename)}) "
        f"| `{command}` |"
    )


def render(assets: Path, version: str, tag: str, repository: str) -> str:
    debs = sorted(assets.glob("*.deb"))
    rpms = sorted(assets.glob("*.rpm"), key=rpm_number, reverse=True)
    arch = sorted(assets.glob("*.pkg.tar.zst"))
    sources = sorted(assets.glob("*.tar.gz"))
    source_checksums = sorted(assets.glob("*.tar.gz.sha256"))
    checksums = assets / "SHA256SUMS"

    lines = [
        f"## ASCII Saver {version}",
        "",
        "System-wide packages with prebuilt GNOME/KDE idle watchers and the "
        "instrumented `ttfx` renderer. The installed system needs its normal "
        "Python/GTK runtime packages, but no virtual environment, compiler, or "
        "Cargo toolchain. The online installer detects your distribution and "
        "selects the matching package automatically.",
        "",
        "### Recommended downloads",
        "",
        "| Distribution | Package | Install |",
        "|---|---|---|",
    ]

    primary_deb = debs[0] if debs else None
    primary_rpm = rpms[0] if rpms else None
    primary_arch = arch[0] if arch else None

    if primary_deb:
        lines.append(package_row("Debian", primary_deb.name, f"sudo apt install ./{primary_deb.name}", repository, tag))
    if primary_rpm:
        lines.append(package_row(fedora_label(primary_rpm.name), primary_rpm.name, f"sudo dnf install ./{primary_rpm.name}", repository, tag))
    if primary_arch:
        lines.append(package_row("Arch Linux", primary_arch.name, f"sudo pacman -U {primary_arch.name}", repository, tag))

    older = []
    if len(rpms) > 1:
        rows = [
            package_row(fedora_label(name), name, f"sudo dnf install ./{name.name}", repository, tag)
            for name in rpms[1:]
        ]
        older.append(("Other Fedora versions", rows))
    if len(debs) > 1:
        rows = [
            package_row("Debian", name, f"sudo apt install ./{name.name}", repository, tag)
            for name in debs[1:]
        ]
        older.append(("Other Debian builds", rows))
    if len(arch) > 1:
        rows = [
            package_row("Arch Linux", name, f"sudo pacman -U {name.name}", repository, tag)
            for name in arch[1:]
        ]
        older.append(("Other Arch builds", rows))

    if older:
        lines.extend(
            [
                "",
                "<details>",
                "<summary><strong>All other distribution versions</strong></summary>",
                "",
            ]
        )
        for heading, rows in older:
            lines.extend([f"#### {heading}", "", "| Distribution | Package | Install |", "|---|---|---|", *rows, ""])
        lines.extend(["</details>"])

    if sources:
        lines.extend(
            [
                "",
                "<details>",
                "<summary><strong>Source archives</strong></summary>",
                "",
            ]
        )
        for name in sources:
            lines.append(f"- [`{name.name}`]({asset_url(repository, tag, name.name)})")
        for name in source_checksums:
            lines.append(f"- [`{name.name}`]({asset_url(repository, tag, name.name)})")
        lines.extend(["", "</details>"])

    if checksums.is_file():
        lines.extend(
            [
                "",
                "<details>",
                "<summary><strong>Checksums</strong></summary>",
                "",
                f"[`SHA256SUMS`]({asset_url(repository, tag, checksums.name)}) "
                "covers every downloadable file in this release.",
                "",
                "</details>",
            ]
        )

    lines.extend(
        [
            "",
            "Uninstalling through the package manager removes the application, "
            "watchers and desktop integration. Personal settings and artwork under "
            "`~/.config/ascii-saver` are preserved.",
            "",
            f"Full details: [CHANGELOG.md](https://github.com/{repository}/blob/{tag}/CHANGELOG.md).",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", type=Path)
    parser.add_argument("version")
    parser.add_argument("tag")
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", "JustAdreamerFL/ascii-saver"),
    )
    args = parser.parse_args()
    args.output.write_text(
        render(args.assets, args.version, args.tag, args.repository),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
