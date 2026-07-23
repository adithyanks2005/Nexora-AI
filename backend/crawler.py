"""
backend/crawler.py
------------------
Lightweight web crawler for Nexora AI.

Features:
  - Fetches a URL with a safe timeout and User-Agent header
  - Parses HTML with BeautifulSoup (html.parser - no lxml required)
  - Extracts: title, meta description, h1-h3 headings, all links, plain text preview
  - Optional robots.txt respect (enabled by default)
  - Enforces a max content-size cap to avoid memory issues on huge pages
  - Returns a clean CrawlResult dict - no external state
"""
from __future__ import annotations

import re
import time
import urllib.parse
import urllib.robotparser
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException

# -- Constants ----------------------------------------------------------------
CRAWLER_UA        = "NexoraBot/1.0 (+https://nexora-ai-flax.vercel.app/llms.txt)"
REQUEST_TIMEOUT   = 15
MAX_CONTENT_BYTES = 2 * 1024 * 1024
MAX_TEXT_PREVIEW  = 500
MAX_LINKS         = 50


# -- Robots helpers -----------------------------------------------------------

async def _robots_allowed_async(url: str) -> bool:
    """Return True if NexoraBot is permitted to fetch url per robots.txt."""
    import asyncio
    def _check() -> bool:
        try:
            parsed = urllib.parse.urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{base}/robots.txt")
            rp.read()
            return rp.can_fetch(CRAWLER_UA, url)
        except Exception:
            return True
    return await asyncio.to_thread(_check)


# -- HTML parsing helpers -----------------------------------------------------

def _parse_html(html: str, base_url: str) -> dict[str, Any]:
    """Parse html and return structured content dict."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="beautifulsoup4 is not installed. Run: pip install beautifulsoup4",
        )

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Meta description
    description = ""
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").lower()
        prop = (meta.get("property") or "").lower()
        content = meta.get("content") or ""
        if name in ("description", "og:description") or prop in ("og:description",):
            description = content.strip()
            if description:
                break

    # Headings
    headings: list[dict[str, str]] = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if text:
            headings.append({"level": tag.name, "text": text})

    # Links
    seen_links: set[str] = set()
    links: list[dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        abs_href = urllib.parse.urljoin(base_url, href)
        if abs_href.startswith("http") and abs_href not in seen_links:
            seen_links.add(abs_href)
            links.append({"url": abs_href, "text": text[:120]})
            if len(links) >= MAX_LINKS:
                break

    # Plain text preview (remove noise tags first)
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    raw_text = soup.get_text(separator=" ", strip=True)
    text_preview = re.sub(r"\s{2,}", " ", raw_text)[:MAX_TEXT_PREVIEW]

    # JSON-LD detection
    has_json_ld = bool(soup.find("script", {"type": "application/ld+json"}))

    return {
        "title":        title,
        "description":  description,
        "headings":     headings,
        "links":        links,
        "text_preview": text_preview,
        "has_json_ld":  has_json_ld,
    }


# -- Public API ---------------------------------------------------------------

async def crawl_url(url: str, *, respect_robots: bool = True) -> dict[str, Any]:
    """
    Asynchronously fetch url and return a structured CrawlResult dict.
    Raises HTTPException on invalid URL, robots block, network error, or non-200 response.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only http:// and https:// URLs are supported.")

    if respect_robots and not await _robots_allowed_async(url):
        raise HTTPException(status_code=403, detail=f"robots.txt disallows crawling {url} by NexoraBot.")

    headers = {
        "User-Agent":      CRAWLER_UA,
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    start = time.monotonic()

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=headers) as client:
        try:
            resp = await client.get(url)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail=f"Request to {url} timed out after {REQUEST_TIMEOUT}s.")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Network error fetching {url}: {exc}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Target URL returned HTTP {resp.status_code}.")

    content_type = resp.headers.get("content-type", "")
    if "html" not in content_type and "xml" not in content_type:
        raise HTTPException(status_code=415, detail=f"Unsupported content type: {content_type}.")

    raw = resp.content[:MAX_CONTENT_BYTES]
    html = raw.decode(resp.encoding or "utf-8", errors="replace")
    elapsed_ms = round((time.monotonic() - start) * 1000)

    parsed_data = _parse_html(html, base_url=str(resp.url))

    return {
        "url":         str(resp.url),
        "status_code": resp.status_code,
        "elapsed_ms":  elapsed_ms,
        "crawled_at":  datetime.now(timezone.utc).isoformat(),
        **parsed_data,
        "links_count": len(parsed_data["links"]),
    }
