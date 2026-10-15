"""Guarded public-page retrieval; does not bypass paywalls or robots restrictions."""
import ipaddress
import socket
from urllib.parse import urlparse
import httpx
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}: self.hidden += 1
    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}: self.hidden = max(0, self.hidden - 1)
    def handle_data(self, data):
        if not self.hidden and data.strip(): self.parts.append(data.strip())

def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Only public HTTPS URLs on port 443 are supported")
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("Private, loopback and reserved addresses are not allowed")

async def retrieve(url: str) -> dict:
    validate_public_url(url)
    async with httpx.AsyncClient(timeout=12, follow_redirects=False, trust_env=False) as client:
        response = await client.get(url, headers={"User-Agent": "OREiLO-InsightMesh/3.0"})
        response.raise_for_status()
        if len(response.content) > 1_000_000: raise ValueError("Source exceeds 1 MB")
        if "text/html" not in response.headers.get("content-type", "") and "text/plain" not in response.headers.get("content-type", ""):
            raise ValueError("Only HTML or plain text sources are supported")
        parser = TextExtractor()
        parser.feed(response.text)
        return {"url": url, "status": response.status_code, "text": " ".join(parser.parts)[:20000],
                "characters": len(response.text), "retrieved": True}
