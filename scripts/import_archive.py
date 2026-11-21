#!/usr/bin/env python3
"""Import the author's public Substack and Medium articles into this Jekyll blog.

Run from repository root. Idempotent; never modifies existing posts.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import mimetypes
import re
import sys
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse, urljoin

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
from markdownify import markdownify as to_markdown

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "_posts"
IMAGES = ROOT / "assets" / "imported"
REPORT = ROOT / "import-report.md"
SUBSTACK = "https://kylejennings.substack.com"
SUBSTACK_RSS = SUBSTACK + "/feed"
MEDIUM = "https://medium.com/feed/@kylejennings57"
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; PersonalBlogArchiver/1.0)"})
result = {"imported": [], "skipped": [], "failed": [], "images": 0}


def get(url, timeout=35, **kwargs):
    for n in range(3):
        try:
            r = session.get(url, timeout=timeout, **kwargs)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if n == 2:
                raise
            time.sleep(2 * (n + 1))


def slugify(value):
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")


def comparable(title):
    return re.sub(r"^(?:the-)?(?:\d+-)?", "", slugify(title))


def existing_posts():
    data = []
    for path in POSTS.glob("*"):
        if path.suffix not in (".md", ".markdown"):
            continue
        text = path.read_text(encoding="utf-8")
        m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
        if not m:
            continue
        front = yaml.safe_load(m.group(1)) or {}
        data.append({
            "title": comparable(front.get("title", path.stem)),
            "source": str(front.get("source_url", "")).rstrip("/"),
            "path": path,
            "body": text[m.end():],
        })
    return data


known = existing_posts()
known_titles = [x["title"] for x in known]
known_urls = {x["source"] for x in known if x["source"]}


def duplicate(title, url):
    if url.rstrip("/") in known_urls:
        return True
    norm = comparable(title)
    for old in known_titles:
        if norm == old or (len(norm) > 7 and SequenceMatcher(None, norm, old).ratio() >= 0.88):
            return True
    return False


def classify(title, tags=None):
    terms = " ".join([title] + (tags or [])).lower()
    if re.search(r"algorithm|internet|social media|content|entertain|meritocracy|marketer|marketing|socrates|psychology|curiosity", terms):
        return "Culture & Ideas"
    if re.search(r"freelan|business|client|entrepren|work|career|productiv|job", terms):
        return "Work & Life"
    if re.search(r"experiment|journal|update|this week", terms):
        return "Experiments"
    return "Personal & Reflections"


def published_date(value):
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value, dt.timezone.utc)
    if not value:
        raise ValueError("Missing original publication date")
    if isinstance(value, str):
        value = value.strip()
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        date = dt.datetime.fromisoformat(value)
    else:
        date = value
    if date.tzinfo is None:
        date = date.replace(tzinfo=dt.timezone.utc)
    return date


def save_images(soup, slug, base_url):
    IMAGES.mkdir(parents=True, exist_ok=True)
    for idx, img in enumerate(soup.select("img"), 1):
        src = (img.get("data-src") or img.get("src") or "").strip()
        if not src and img.get("srcset"):
            src = img["srcset"].split(",")[0].strip().split(" ")[0]
        if not src or src.startswith("data:"):
            img.decompose()
            continue
        remote = urljoin(base_url, src)
        if not remote.startswith(("https://", "http://")):
            img.decompose()
            continue
        try:
            response = get(remote, timeout=28)
            media = response.headers.get("content-type", "").split(";")[0].lower()
            ext = { "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif" }.get(media)
            if not ext or len(response.content) > 12_000_000:
                raise ValueError("unsupported image or too large")
            path = IMAGES / f"{slug}-{idx:02d}{ext}"
            if not path.exists():
                path.write_bytes(response.content)
            img["src"] = "/assets/imported/" + path.name
            img.attrs.pop("srcset", None)
            img.attrs.pop("data-src", None)
            img.attrs.pop("loading", None)
            result["images"] += 1
        except Exception as exc:
            print(f"Image not mirrored ({remote}): {exc}", file=sys.stderr)
            # Preserve externally hosted image rather than dropping it.
            img["src"] = remote
            img.attrs.pop("srcset", None)


def clean_body(body_html, slug, source_url):
    soup = BeautifulSoup(body_html, "html.parser")
    for element in soup.select("script, style, noscript, form, button, .subscription-widget, .subscribe-widget"):
        element.decompose()
    for a in soup.select("a[href]"):
        a["href"] = urljoin(source_url, a["href"])
    save_images(soup, slug, source_url)
    # markdownify preserves original links, headings, emphasis, and inline images.
    content = to_markdown(str(soup), heading_style="ATX", bullets="-").strip()
    content = re.sub(r"\n{4,}", "\n\n\n", content)
    if len(BeautifulSoup(body_html, "html.parser").get_text(" ", strip=True)) < 180:
        raise ValueError("Only an excerpt or empty body was accessible")
    return content


def import_post(source, title, date_value, url, body_html, subtitle="", tags=None, cover=""):
    title = html.unescape(str(title or "")).strip()
    if not title or not url:
        return
    if duplicate(title, url):
        result["skipped"].append((source, title, "already present"))
        return
    if not body_html or len(BeautifulSoup(body_html, "html.parser").get_text(" ", strip=True)) < 180:
        result["failed"].append((source, title, "full article body unavailable"))
        return
    try:
        date = published_date(date_value)
        name = slugify(title)[:76] or "essay"
        filename = date.strftime("%Y-%m-%d") + "-" + name + ".md"
        path = POSTS / filename
        if path.exists():
            result["skipped"].append((source, title, "same dated filename"))
            return
        # Preserve cover if not already embedded within article; same local mirroring.
        soup = BeautifulSoup(body_html, "html.parser")
        if cover and not soup.select_one("img"):
            cover_tag = soup.new_tag("img", src=cover, alt="")
            soup.insert(0, cover_tag)
        body = clean_body(str(soup), name, url)
        date_iso = date.isoformat(timespec="seconds")
        meta = {
            "layout": "post",
            "title": title,
            "date": date_iso,
            "category": classify(title, tags),
            "source_url": url,
            "source_platform": source,
        }
        if subtitle:
            meta["description"] = html.unescape(str(subtitle)).strip()[:280]
        if tags:
            meta["tags"] = [str(t) for t in tags][:12]
        yaml_text = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=120)
        POSTS.mkdir(parents=True, exist_ok=True)
        path.write_text("---\n" + yaml_text + "---\n\n" + body +
                        f"\n\n---\n\n*Originally published on [{source}]({url}).*\n", encoding="utf-8")
        known_titles.append(comparable(title))
        known_urls.add(url.rstrip("/"))
        result["imported"].append((source, title, path.as_posix().replace(str(ROOT) + "/", "")))
    except Exception as exc:
        result["failed"].append((source, title, str(exc)))
        print(f"Failed {source} / {title}: {exc}", file=sys.stderr)


def substack_archive():
    cursor = None
    seen = set()
    for page in range(100):
        params = {"sort": "new", "limit": 25}
        if cursor:
            params["cursor"] = cursor
        r = get(SUBSTACK + "/api/v1/archive", params=params)
        data = r.json()
        if isinstance(data, list):
            items = data
            next_cursor = None
        else:
            items = data.get("posts") or data.get("items") or []
            next_cursor = data.get("nextCursor") or data.get("next_cursor")
        if not items:
            break
        for item in items:
            key = item.get("id") or item.get("slug")
            if key in seen:
                continue
            seen.add(key)
            if item.get("type") in ("podcast", "thread") or not item.get("slug"):
                continue
            slug = item["slug"]
            url = item.get("canonical_url") or SUBSTACK + "/p/" + slug
            title = item.get("title") or slug
            if duplicate(title, url):
                result["skipped"].append(("Substack", title, "already present"))
                continue
            try:
                detail = get(SUBSTACK + "/api/v1/posts/" + slug).json()
                body = detail.get("body_html") or detail.get("bodyHtml")
                if not body:
                    result["failed"].append(("Substack", title, "body unavailable (possibly restricted)"))
                    continue
                tags = [t.get("name", "") for t in detail.get("postTags", []) if isinstance(t, dict)]
                import_post("Substack", title, item.get("post_date") or detail.get("post_date"),
                            url, body, item.get("subtitle") or detail.get("subtitle") or "",
                            tags, item.get("cover_image") or detail.get("cover_image") or "")
            except Exception as exc:
                result["failed"].append(("Substack", title, str(exc)))
        print(f"Substack page {page+1}: {len(items)} entries")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor


def substack_rss():
    """Fallback to Substack's published RSS feed when private APIs reject us.

    RSS generally contains only recent posts, so this is not a complete
    historical archive; the report explicitly records this limitation.
    """
    feed = feedparser.parse(get(SUBSTACK_RSS).content)
    if not feed.entries:
        raise ValueError("Substack RSS returned no entries")
    for item in feed.entries:
        url = item.get("link", "")
        title = BeautifulSoup(item.get("title", ""), "html.parser").get_text(" ", strip=True)
        body = (item.get("content") or [{}])[0].get("value") or ""
        if not body:
            body = item.get("summary", "")
        if item.get("published_parsed"):
            date = dt.datetime(*item.published_parsed[:6], tzinfo=dt.timezone.utc)
        elif item.get("updated_parsed"):
            date = dt.datetime(*item.updated_parsed[:6], tzinfo=dt.timezone.utc)
        else:
            date = None
        tags = [tag.get("term", "") for tag in item.get("tags", [])]
        import_post("Substack", title, date, url, body, tags=tags)
    print(f"Substack RSS entries inspected: {len(feed.entries)}")
    return len(feed.entries)


def medium_posts():
    feed = feedparser.parse(get(MEDIUM).content)
    if not feed.entries:
        raise ValueError("Medium feed returned no posts")
    for item in feed.entries:
        url = item.get("link", "")
        title = BeautifulSoup(item.get("title", ""), "html.parser").get_text(" ", strip=True)
        content = (item.get("content") or [{}])[0].get("value") or ""
        date = item.get("published") or item.get("updated")
        # RSS date (RFC 822) is not ISO; use parsed struct_time if available.
        if item.get("published_parsed"):
            date = dt.datetime(*item.published_parsed[:6], tzinfo=dt.timezone.utc)
        elif item.get("updated_parsed"):
            date = dt.datetime(*item.updated_parsed[:6], tzinfo=dt.timezone.utc)
        tags = [tag.get("term", "") for tag in item.get("tags", [])]
        import_post("Medium", title, date, url, content, tags=tags)


def main():
    try:
        substack_archive()
    except Exception as exc:
        print(f"Substack API unavailable ({exc}); trying public RSS.", file=sys.stderr)
        try:
            count = substack_rss()
            result["failed"].append(("Substack", "Historical archive", f"Archive API returned {type(exc).__name__}: {exc}; RSS only lists {count} recent posts. For the complete archive, use the official Substack export."))
        except Exception as rss_exc:
            result["failed"].append(("Substack", "Archive and RSS", f"API: {exc}; RSS: {rss_exc}"))
            print(f"Substack RSS also failed: {rss_exc}", file=sys.stderr)
    try:
        medium_posts()
    except Exception as exc:
        result["failed"].append(("Medium", "Feed fetch", str(exc)))
        print(f"Medium feed failed: {exc}", file=sys.stderr)
    lines = [
        "# Writing archive import report", "",
        "Import sources: https://kylejennings.substack.com/ and https://medium.com/@kylejennings57/",
        "",
        f"- Imported: **{len(result['imported'])}**",
        f"- Already present / skipped: **{len(result['skipped'])}**",
        f"- Images mirrored or reused: **{result['images']}**",
        f"- Failed or incomplete: **{len(result['failed'])}**",
        "", "## Imported", "",
    ]
    lines += [f"- {source}: {title} — \`{path}\`" for source, title, path in result["imported"]] or ["None"]
    lines += ["", "## Already present", ""]
    lines += [f"- {source}: {title} ({reason})" for source, title, reason in result["skipped"]] or ["None"]
    lines += ["", "## Needs attention", ""]
    lines += [f"- {source}: {title} — {reason}" for source, title, reason in result["failed"]] or ["None"]
    lines += ["", "This report covers publicly accessible material only. Check every original against its imported copy.", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({key: len(val) if isinstance(val, list) else val for key, val in result.items()}, indent=2))
    # Failure to contact a platform should be visible, but imported content should
    # still be committed to preserve completed work.
    # The workflow can complete with partial coverage; see report for gaps.
    # A successful GitHub Action must not be confused with a complete import.


if __name__ == "__main__":
    main()
