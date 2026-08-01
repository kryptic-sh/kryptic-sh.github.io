#!/usr/bin/env python3
"""Static site assembler for kryptic.sh.

Stdlib only. Reads templates/layout.html + content/*.html, writes dist/.

Content file format:

    <!--meta
    { ...JSON front-matter... }
    meta-->
    <!--head-->
    ...per-page <style>/<link> injected into <head>...
    <!--/head-->
    <!--body-->
    ...page sections (hero, features, install, ...)...
    <!--/body-->

Front-matter keys:
    slug         "" for the homepage, else the app slug ("hjkl", ...)
    repo         GitHub repo name for the footer link (omit → org link)
    title        <title> + og/twitter title
    description  meta/og/twitter description
    keywords     meta keywords
    accent       theme-color hex (must match the page's --accent)
    og_image     absolute path, e.g. "/hjkl/og-image.png"
    assets       favicon/manifest base path; defaults to "/<slug>/" when
                 public/<slug>/favicon.svg exists, else "/"
    nav          [{"href": "#why", "label": "why"}, ...] (external links
                 get target=_blank automatically for http(s) hrefs)
    jsonld       structured-data object, serialized verbatim
"""

import json
import re
import shutil
import sys
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"

# siblings-bar order; "" = homepage
SIBLINGS = [
    ("", "kryptic"),
    ("sqeel", "sqeel"),
    ("buffr", "buffr"),
    ("hjkl", "hjkl"),
    ("inbx", "inbx"),
    ("hodl", "hodl"),
    ("pikr", "pikr"),
    ("gpur", "gpur"),
    ("crcbl", "crcbl"),
    ("hrdr", "hrdr"),
    ("infr", "infr"),
    ("krypt", "krypt"),
]

META_RE = re.compile(r"<!--meta\s*(.*?)\s*meta-->", re.S)
HEAD_RE = re.compile(r"<!--head-->\s*(.*?)\s*<!--/head-->", re.S)
BODY_RE = re.compile(r"<!--body-->\s*(.*?)\s*<!--/body-->", re.S)


def die(msg: str) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_content(path: Path):
    text = path.read_text()
    m = META_RE.search(text)
    if not m:
        die(f"{path}: missing <!--meta ... meta--> block")
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        die(f"{path}: bad front-matter JSON: {e}")
    body = BODY_RE.search(text)
    if not body:
        die(f"{path}: missing <!--body--> ... <!--/body--> block")
    head = HEAD_RE.search(text)
    return meta, (head.group(1) if head else ""), body.group(1)


def siblings_html(current_slug: str) -> str:
    parts = []
    for slug, label in SIBLINGS:
        if parts:
            parts.append('<span class="sep">·</span>')
        if slug == current_slug:
            parts.append(f'<span class="current">{label}</span>')
        else:
            href = "/" if slug == "" else f"/{slug}/"
            parts.append(f'<a href="{href}">{label}</a>')
    return "\n        ".join(parts)


def nav_html(links) -> str:
    parts = []
    for link in links:
        href, label = link["href"], link["label"]
        if href.startswith("http"):
            parts.append(
                f'<a href="{href}" target="_blank" rel="noopener">{label} ↗</a>'
            )
        else:
            parts.append(f'<a href="{href}">{label}</a>')
    return "\n        ".join(parts)


def brand_html(slug: str) -> str:
    if not slug:
        return '<span class="prompt">$</span> kryptic<span class="cursor"></span>'
    return (
        '<span class="prompt">$</span> <a href="/">kryptic</a>/'
        f"{slug}<span class=\"cursor\"></span>"
    )


def render(layout: str, meta: dict, head_extra: str, content: str) -> str:
    slug = meta.get("slug", "")
    canonical = "https://www.kryptic.sh/" + (f"{slug}/" if slug else "")
    assets = meta.get("assets")
    if assets is None:
        assets = f"/{slug}/" if slug and (ROOT / "public" / slug / "favicon.svg").exists() else "/"
    repo = meta.get("repo")
    footer = (
        f'<a href="https://github.com/kryptic-sh/{repo}">github</a>'
        if repo
        else '<a href="https://github.com/kryptic-sh">github</a>'
    )
    subs = {
        "title": meta["title"],
        "description": meta["description"],
        "keywords": meta.get("keywords", ""),
        "accent": meta["accent"],
        "canonical": canonical,
        "og_image": meta.get("og_image", "/og-image.png"),
        "favicon_base": assets,
        "jsonld": json.dumps(meta["jsonld"], indent=8).strip(),
        "siblings": siblings_html(slug),
        "brand": brand_html(slug),
        "nav_links": nav_html(meta.get("nav", [])),
        "footer_links": footer,
        "head_extra": head_extra,
        "content": content,
    }
    out = layout
    for key, val in subs.items():
        out = out.replace("{{" + key + "}}", val)
    leftover = re.findall(r"\{\{\w+\}\}", out)
    if leftover:
        die(f"unsubstituted template vars for slug '{slug}': {leftover}")
    return out


def main() -> None:
    layout = (ROOT / "templates" / "layout.html").read_text()

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # 1. static files (favicons, og images, manifests, CNAME, robots, ...)
    public = ROOT / "public"
    if public.exists():
        shutil.copytree(public, DIST, dirs_exist_ok=True)
    (DIST / ".nojekyll").touch()

    # 2. shared assets
    shutil.copytree(ROOT / "assets", DIST / "assets")

    # 3. pages
    pages = sorted((ROOT / "content").glob("*.html"))
    if not pages:
        die("no content pages found")
    for page in pages:
        meta, head_extra, body = parse_content(page)
        html = render(layout, meta, head_extra, body)
        slug = meta.get("slug", "")
        out = DIST / slug / "index.html" if slug else DIST / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html)
        print(f"built {out.relative_to(ROOT)}")

    if not (DIST / "CNAME").exists():
        die("missing public/CNAME")
    print(f"done: {sum(1 for _ in DIST.rglob('*') if _.is_file())} files in dist/")


if __name__ == "__main__":
    main()
