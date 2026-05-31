#!/usr/bin/env python3
"""External <img src> in post bodies: list URLs, mirror reachable files."""

from __future__ import annotations

import json
import re
import ssl
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

BLOG_HOST = "blog-archive.arutyunov.info"
IGNORE_HOSTS = {"mc.yandex.ru", "www.google-analytics.com"}
IMG_SRC_RE = re.compile(r'<img[^>]+src=["\']?([^"\'>\s]+)', re.I)
CTX = ssl.create_default_context()
REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = REPO_ROOT / "external-images"


def extract_note_body(html: str) -> str:
    start = html.find('class="e2-note-text')
    if start < 0:
        return ""
    start = html.find(">", start) + 1
    end = html.find('class="e2-note-meta', start)
    if end < 0:
        end = html.find('class="e2-comments', start)
    return html[start:end] if end > start else ""


def post_slug(post_url: str) -> str:
    path = urllib.parse.urlparse(post_url).path.rstrip("/")
    return path.split("/")[-1] or "post"


def external_images(post_url: str, html: str) -> list[str]:
    body = extract_note_body(html)
    seen: set[str] = set()
    out: list[str] = []
    for match in IMG_SRC_RE.finditer(body):
        absolute = urllib.parse.urljoin(post_url, match.group(1))
        host = urllib.parse.urlparse(absolute).netloc.lower()
        if not host or host == BLOG_HOST or host in IGNORE_HOSTS:
            continue
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


def local_name_for_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    name = Path(path).name or "image"
    if not Path(name).suffix:
        name += ".bin"
    return re.sub(r"[^\w.\-]+", "_", name)


def try_download(url: str) -> tuple[bool, bytes | None, str]:
    candidates = [
        url,
        url.replace("http://", "https://", 1),
        url.replace("http://bvz.name", "http://www.bvz.name"),
        url.replace("http://bvz.name", "https://www.bvz.name"),
    ]
    last_err = ""
    for candidate in dict.fromkeys(candidates):
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
            r = subprocess.run(
                [
                    "curl",
                    "-fsSL",
                    "-A",
                    "Mozilla/5.0",
                    "-m",
                    "30",
                    "-o",
                    tmp_path,
                    "-w",
                    "%{http_code}",
                    candidate,
                ],
                capture_output=True,
                text=True,
                timeout=35,
                check=False,
            )
            code = (r.stdout or "").strip()
            if code == "200":
                data = Path(tmp_path).read_bytes()
                Path(tmp_path).unlink(missing_ok=True)
                if len(data) > 20:
                    return True, data, candidate
            Path(tmp_path).unlink(missing_ok=True)
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
        req = urllib.request.Request(candidate, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=25, context=CTX) as resp:
                if 200 <= resp.status < 400:
                    return True, resp.read(), candidate
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
    return False, None, last_err


def analyze_post(post_url: str, mirror: bool = True) -> dict:
    html = urllib.request.urlopen(post_url, context=CTX).read().decode("utf-8", "replace")
    slug = post_slug(post_url)
    images = external_images(post_url, html)
    entries: list[dict] = []
    for i, img_url in enumerate(images):
        row: dict = {"url": img_url, "mirrored": None, "mirror_error": None}
        if mirror:
            ok, data, detail = try_download(img_url)
            if ok and data is not None:
                dest_dir = ASSETS_DIR / slug
                dest_dir.mkdir(parents=True, exist_ok=True)
                name = local_name_for_url(detail)
                dest = dest_dir / (f"{i:02d}_{name}" if i else name)
                dest.write_bytes(data)
                row["mirrored"] = str(dest.relative_to(REPO_ROOT))
            else:
                row["mirror_error"] = detail
        entries.append(row)
    return {"post_url": post_url, "slug": slug, "images": entries}


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <post-url> [--no-mirror]", file=sys.stderr)
        sys.exit(1)
    mirror = "--no-mirror" not in sys.argv
    url = next(a for a in sys.argv[1:] if not a.startswith("-"))
    print(json.dumps(analyze_post(url, mirror=mirror), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
