#!/usr/bin/env python3
"""Check external <img src> URLs in blog post bodies."""

from __future__ import annotations

import re
import ssl
import sys
import urllib.parse
import urllib.request

BLOG_HOST = "blog-archive.arutyunov.info"
IGNORE_HOSTS = {"mc.yandex.ru", "www.google-analytics.com"}
IMG_SRC_RE = re.compile(r'<img[^>]+src=["\']?([^"\'>\s]+)', re.I)
CTX = ssl.create_default_context()


def extract_note_body(html: str) -> str:
    start = html.find('class="e2-note-text')
    if start < 0:
        return ""
    start = html.find(">", start) + 1
    end = html.find('class="e2-note-meta', start)
    if end < 0:
        end = html.find('class="e2-comments', start)
    return html[start:end] if end > start else ""


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


def check_url(url: str) -> tuple[bool, str]:
    candidates = [
        url,
        url.replace("http://", "https://", 1),
        url.replace("http://bvz.name", "http://www.bvz.name"),
        url.replace("http://bvz.name", "https://www.bvz.name"),
    ]
    last_err = ""
    for candidate in dict.fromkeys(candidates):
        req = urllib.request.Request(candidate, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=20, context=CTX) as resp:
                if 200 <= resp.status < 400:
                    return True, candidate
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
    return False, last_err


def analyze_post(post_url: str) -> dict:
    html = urllib.request.urlopen(post_url, context=CTX).read().decode("utf-8", "replace")
    images = external_images(post_url, html)
    broken: list[dict] = []
    ok: list[str] = []
    for img_url in images:
        good, detail = check_url(img_url)
        if good:
            ok.append(img_url)
        else:
            broken.append({"url": img_url, "error": detail})
    return {
        "post_url": post_url,
        "external_count": len(images),
        "broken": broken,
        "ok": ok,
    }


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <post-url>", file=sys.stderr)
        sys.exit(1)
    result = analyze_post(sys.argv[1])
    print(f"Post: {result['post_url']}")
    print(f"External images: {result['external_count']}")
    print(f"OK: {len(result['ok'])}  Broken: {len(result['broken'])}")
    for row in result["broken"]:
        print(f"  BROKEN  {row['url']}")
        print(f"          {row['error']}")
    for row in result["ok"]:
        print(f"  OK      {row}")


if __name__ == "__main__":
    main()
