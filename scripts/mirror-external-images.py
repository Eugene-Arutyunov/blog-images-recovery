#!/usr/bin/env python3
"""Download all reachable external <img> from checked posts; refresh detail tables."""

from __future__ import annotations

import importlib.util
import re
import ssl
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROGRESS = REPO / "broken-images-progress.md"
BASE = "https://blog-archive.arutyunov.info/"
CTX = ssl.create_default_context()

spec = importlib.util.spec_from_file_location("chk", REPO / "scripts/check-post-images.py")
chk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chk)


def post_urls_from_md(md: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in md.splitlines():
        if line.startswith("| [") and "| да |" in line:
            m = re.search(r"\[([^\]]+)\]\((https://[^)]+)\)", line)
            if m:
                out[m.group(1)] = m.group(2)
    return out


def detail_table(slug: str, rows: list[dict]) -> str:
    lines = [
        f"### {slug}",
        "",
        "| URL | Файл в репозитории |",
        "|-----|-------------------|",
    ]
    for row in rows:
        path = row.get("mirrored") or "—"
        lines.append(f"| `{row['url']}` | `{path}` |")
    return "\n".join(lines) + "\n"


def main() -> None:
    md = PROGRESS.read_text(encoding="utf-8")
    posts = post_urls_from_md(md)
    details: dict[str, str] = {}
    mirrored_total = 0

    for slug in sorted(posts.keys()):
        post_url = posts[slug]
        try:
            html = urllib.request.urlopen(post_url, context=CTX).read().decode(
                "utf-8", "replace"
            )
        except Exception:
            continue
        urls = chk.external_images(post_url, html)
        if not urls:
            continue
        rows = []
        dest_dir = REPO / "external-images" / slug
        for i, img_url in enumerate(urls):
            ok, data, final = chk.try_download(img_url)
            row = {"url": img_url, "mirrored": None}
            if ok and data:
                dest_dir.mkdir(parents=True, exist_ok=True)
                name = chk.local_name_for_url(final)
                dest = dest_dir / (f"{i:02d}_{name}" if i else name)
                dest.write_bytes(data)
                row["mirrored"] = str(dest.relative_to(REPO))
                mirrored_total += 1
            rows.append(row)
        details[slug] = detail_table(slug, rows)
        saved = sum(1 for r in rows if r["mirrored"])
        print(f"{slug}: {len(urls)} external, saved {saved}")

    header_end = md.find("\n### ")
    if header_end < 0:
        header = md.rstrip() + "\n\n"
    else:
        header = md[:header_end].rstrip() + "\n\n"

    out = header
    for slug in sorted(details.keys(), key=lambda s: (s != "vospriyatie", s)):
        out += details[slug] + "\n"

    PROGRESS.write_text(out, encoding="utf-8")
    print(f"mirrored_total={mirrored_total} posts_with_external={len(details)}")


if __name__ == "__main__":
    main()
