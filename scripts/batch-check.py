#!/usr/bin/env python3
"""Process N unchecked posts and update broken-images-progress.md."""

from __future__ import annotations

import importlib.util
import re
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROGRESS = REPO / "broken-images-progress.md"
BASE = "https://blog-archive.arutyunov.info/"
CTX = ssl.create_default_context()

spec = importlib.util.spec_from_file_location("chk", REPO / "scripts/check-post-images.py")
chk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chk)


def all_post_urls() -> list[str]:
    seen: list[str] = []
    seen_set: set[str] = set()
    for p in range(1, 25):
        url = BASE if p == 1 else f"{BASE}page-{p}/"
        try:
            html = urllib.request.urlopen(url, context=CTX).read().decode("utf-8", "replace")
        except Exception:
            break
        for m in re.finditer(r'href="([^"]+)"', html):
            h = m.group(1)
            if "go=all/" not in h and "/all/" not in h:
                continue
            absu = urllib.parse.urljoin(BASE, h)
            if "blog-archive" not in absu:
                continue
            if "go=all/" in absu:
                slug_m = re.search(r"go=all/([^/?#]+)", absu)
                if slug_m:
                    absu = f"{BASE}all/{slug_m.group(1)}/"
            if "/all/" not in absu:
                continue
            norm = absu.rstrip("/") + "/"
            if norm not in seen_set:
                seen_set.add(norm)
                seen.append(norm)
    return seen


def done_slugs(md: str) -> set[str]:
    return set(re.findall(r"\[([^\]]+)\]\(https://blog-archive\.arutyunov\.info/all/([^/)]+)/\)", md))


def format_detail(slug: str, images: list[dict]) -> str:
    lines = [f"\n### {slug}\n", "| URL | Файл в репозитории |", "|-----|-------------------|"]
    for row in images:
        path = row.get("mirrored") or "—"
        lines.append(f"| `{row['url']}` | `{path}` |")
    return "\n".join(lines) + "\n"


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    md = PROGRESS.read_text(encoding="utf-8")
    done = {m.group(2) for m in re.finditer(r"/all/([^/)]+)/\)", md) if "Проверено" in md or "| да |" in md}
    # slugs from table rows with | да |
    done = set(re.findall(r"\[([^\]]+)\]\(https://blog-archive\.arutyunov\.info/all/([^/)]+)/\).*\| да \|", md))
    done_slugs_set = {s[1] if isinstance(s, tuple) else s for s in done}
    if not done_slugs_set:
        done_slugs_set = set(re.findall(r"/all/([^/)]+)/\).*?\| да \|", md))

    # simpler: extract slugs from lines with | да |
    done_slugs_set = set()
    for line in md.splitlines():
        if "| да |" in line and "/all/" in line:
            m = re.search(r"/all/([^/)]+)/", line)
            if m:
                done_slugs_set.add(m.group(1))

    queue = [u for u in all_post_urls() if u.rstrip("/").split("/")[-1] not in done_slugs_set]
    batch = queue[:n]
    print(f"queue {len(queue)}, processing {len(batch)}", file=sys.stderr)

    new_rows: list[str] = []
    new_details: list[str] = []

    for i, post_url in enumerate(batch):
        slug = post_url.rstrip("/").split("/")[-1]
        print(f"{i+1}/{len(batch)} {slug}", file=sys.stderr)
        result = chk.analyze_post(post_url, mirror=True)
        new_rows.append(
            f"| [{slug}]({post_url}) | да | нет |"
        )
        if result["images"]:
            new_details.append(format_detail(slug, result["images"]))

    # insert new rows before first ### or at end of table
    if "### " in md:
        head, tail = md.split("### ", 1)
        tail = "### " + tail
    else:
        head, tail = md.rstrip() + "\n", ""

    head_lines = head.rstrip().splitlines()
    # append rows after header row of table
    out_lines = []
    inserted = False
    for line in head_lines:
        out_lines.append(line)
        if not inserted and line.startswith("|") and "Запись" not in line and "---" not in line:
            # after last table row before empty or ###
            pass
    # rebuild: find ## Записи section and append after last | да | row
    idx = head.rstrip().find("| [kak-ya-vas-uvolyu]")
    if idx < 0:
        # append after table separator block
        parts = head.rstrip().split("\n\n")
        table_part = parts[0] if len(parts) == 1 else "\n\n".join(parts[:-1]) if parts[-1].startswith("###") else head
    out = head.rstrip()
    if out.endswith("```"):
        pass
    # simple append to summary table
    marker = "| [kak-ya-vas-uvolyu]"
    if marker in out:
        pos = out.find(marker)
        line_end = out.find("\n", pos)
        out = out[: line_end + 1] + "\n".join(new_rows) + "\n" + out[line_end + 1 :]
    else:
        # append before first ###
        if "\n### " in out:
            a, b = out.split("\n### ", 1)
            out = a.rstrip() + "\n" + "\n".join(new_rows) + "\n\n### " + b
        else:
            out = out.rstrip() + "\n" + "\n".join(new_rows) + "\n"

    out = out + "".join(new_details)
    if tail and not out.endswith(tail):
        if "### " in md and "### " not in out.split("## Записи")[-1]:
            pass
    # preserve old detail sections from tail
    if "### " in md:
        old_details = md[md.find("### "):]
        # keep vospriyatie and add new details only for new slugs
        existing_detail_slugs = set(re.findall(r"\n### ([^\n]+)", md))
        for det in new_details:
            slug_d = det.split("\n")[1].replace("### ", "")
            if slug_d not in existing_detail_slugs:
                old_details += det
        out = out.split("### ")[0].rstrip() + "\n\n" + old_details.lstrip()
    else:
        out = out + "".join(new_details)

    PROGRESS.write_text(out, encoding="utf-8")
    print(f"updated {PROGRESS}", file=sys.stderr)


if __name__ == "__main__":
    main()
