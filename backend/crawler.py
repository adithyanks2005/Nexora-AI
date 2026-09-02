"""Safe, bounded web crawler for MediCura AI."""
from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
import time
import urllib.parse
import urllib.robotparser
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException

CRAWLER_UA = "MediCuraBot/1.0"
REQUEST_TIMEOUT = 10
MAX_CONTENT_BYTES = 2 * 1024 * 1024
MAX_TEXT_PREVIEW = 500
MAX_LINKS = 50
MAX_REDIRECTS = 3
ALLOWED_PORTS = {80, 443}


def _validate_public_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Only public http:// and https:// URLs are supported.")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="URLs with embedded credentials are not allowed.")
    if parsed.port not in (None, *ALLOWED_PORTS):
        raise HTTPException(status_code=400, detail="Only ports 80 and 443 are allowed.")

    host = parsed.hostname
    try:
        ip = ipaddress.ip_address(host)
        addresses = [ip]
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
            addresses = [ipaddress.ip_address(info[4][0]) for info in infos]
        except (socket.gaierror, ValueError):
            raise HTTPException(status_code=400, detail="Target hostname could not be resolved.")

    for ip in addresses:
        if not ip.is_global:
            raise HTTPException(status_code=400, detail="Private, loopback, link-local, or reserved targets are blocked.")
    return url


async def _robots_allowed_async(url: str) -> bool:
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


def _parse_html(html: str, base_url: str) -> dict[str, Any]:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
    except ImportError:
        raise HTTPException(status_code=500, detail="beautifulsoup4 is not installed.")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    description = ""
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").lower()
        prop = (meta.get("property") or "").lower()
        content = meta.get("content") or ""
        if name in ("description", "og:description") or prop == "og:description":
            description = content.strip()
            if description:
                break

    headings: list[dict[str, str]] = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if text:
            headings.append({"level": tag.name, "text": text})

    seen_links: set[str] = set()
    links: list[dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        abs_href = urllib.parse.urljoin(base_url, href)
        if abs_href.startswith(("http://", "https://")) and abs_href not in seen_links:
            seen_links.add(abs_href)
            links.append({"url": abs_href, "text": text[:120]})
            if len(links) >= MAX_LINKS:
                break

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    raw_text = soup.get_text(separator=" ", strip=True)
    text_preview = re.sub(r"\s{2,}", " ", raw_text)[:MAX_TEXT_PREVIEW]
    has_json_ld = bool(soup.find("script", {"type": "application/ld+json"}))
    return {"title": title, "description": description, "headings": headings, "links": links,
            "text_preview": text_preview, "has_json_ld": has_json_ld}


async def crawl_url(url: str, *, respect_robots: bool = True) -> dict[str, Any]:
    _validate_public_url(url)
    if respect_robots and not await _robots_allowed_async(url):
        raise HTTPException(status_code=403, detail="robots.txt disallows crawling this URL.")

    headers = {"User-Agent": CRAWLER_UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    start = time.monotonic()
    current_url = url

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=False, headers=headers) as client:
        for _ in range(MAX_REDIRECTS + 1):
            _validate_public_url(current_url)
            try:
                resp = await client.get(current_url)
            except httpx.TimeoutException:
                raise HTTPException(status_code=504, detail="Target request timed out.")
            except httpx.RequestError:
                raise HTTPException(status_code=502, detail="Target network request failed.")

            if resp.is_redirect:
                location = resp.headers.get("location")
                if not location:
                    raise HTTPException(status_code=502, detail="Redirect response missing Location header.")
                current_url = urllib.parse.urljoin(str(resp.url), location)
                continue
            break
        else:
            raise HTTPException(status_code=508, detail="Too many redirects.")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Target URL returned HTTP {resp.status_code}.")

    content_type = resp.headers.get("content-type", "")
    if "html" not in content_type and "xml" not in content_type:
        raise HTTPException(status_code=415, detail=f"Unsupported content type: {content_type}.")

    raw = resp.content[:MAX_CONTENT_BYTES]
    html = raw.decode(resp.encoding or "utf-8", errors="replace")
    parsed_data = _parse_html(html, base_url=str(resp.url))
    return {"url": str(resp.url), "status_code": resp.status_code,
            "elapsed_ms": round((time.monotonic() - start) * 1000),
            "crawled_at": datetime.now(timezone.utc).isoformat(), **parsed_data,
            "links_count": len(parsed_data["links"])}
