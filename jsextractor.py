#!/usr/bin/env python3
import argparse
import hashlib
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
import urllib3
from bs4 import BeautifulSoup


JS_MIME_HINTS = (
    "javascript",
    "ecmascript",
    "text/js",
    "application/js",
)


def valid_url(value: str) -> str:
    parsed = urlparse(value)

    if parsed.scheme not in ("http", "https"):
        raise argparse.ArgumentTypeError("URL must start with http:// or https://")

    if not parsed.netloc:
        raise argparse.ArgumentTypeError("Invalid URL")

    return value


def parse_headers(header_list: list[str]) -> dict:
    headers = {}

    for item in header_list:
        if ":" not in item:
            raise argparse.ArgumentTypeError(
                f"Invalid header format: {item}. Use 'Name: value'"
            )

        name, value = item.split(":", 1)
        name = name.strip()
        value = value.strip()

        if not name:
            raise argparse.ArgumentTypeError(
                f"Invalid header name: {item}"
            )

        headers[name] = value

    return headers


def load_cookie_file(cookie_file: str) -> str:
    """
    Supports simple Netscape/curl cookie jar format.

    Example line:
    .example.com TRUE / FALSE 2147483647 session abc123

    Output:
    session=abc123
    """
    cookies = []

    try:
        with open(cookie_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                parts = line.split("\t")

                # Netscape cookie format has 7 fields:
                # domain, flag, path, secure, expiration, name, value
                if len(parts) >= 7:
                    name = parts[5].strip()
                    value = parts[6].strip()

                    if name:
                        cookies.append(f"{name}={value}")

    except OSError as e:
        raise argparse.ArgumentTypeError(f"Cannot read cookie file: {e}")

    return "; ".join(cookies)


def safe_filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = unquote(parsed.path)

    filename = os.path.basename(path)
    if not filename:
        filename = "index.js"

    if not filename.endswith(".js"):
        filename += ".js"

    short_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
    name, ext = os.path.splitext(filename)

    return f"{name}.{short_hash}{ext}"


def extract_js_urls(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = set()

    # <script src="...">
    for tag in soup.find_all("script"):
        src = tag.get("src")
        if src:
            urls.add(urljoin(base_url, src))

    # <link rel="preload" as="script" href="...">
    # <link rel="modulepreload" href="...">
    for tag in soup.find_all("link"):
        href = tag.get("href")
        as_attr = (tag.get("as") or "").lower()
        rel = " ".join(tag.get("rel") or []).lower()

        if href and (as_attr == "script" or "modulepreload" in rel):
            urls.add(urljoin(base_url, href))

    # Fallback for Next.js hydration payload / inline JS references
    for match in re.findall(r'["\']([^"\']+?\.js(?:\?[^"\']*)?)["\']', html):
        urls.add(urljoin(base_url, match))

    return sorted(urls)


def download_file(session: requests.Session, url: str, outdir: Path, timeout: int) -> bool:
    filename = safe_filename_from_url(url)
    outpath = outdir / filename

    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()

        content_type = r.headers.get("content-type", "").lower()
        parsed_path = urlparse(url).path.lower()

        if not parsed_path.endswith(".js") and not any(x in content_type for x in JS_MIME_HINTS):
            print(f"[skip] not JS: {url} ({content_type})")
            return False

        outpath.write_bytes(r.content)
        print(f"[ok] {url} -> {outpath}")
        return True

    except requests.RequestException as e:
        print(f"[fail] {url} | {e}")
        return False


def build_session(args) -> requests.Session:
    session = requests.Session()

    # TLS verification. -k/--insecure mirrors curl -k (needed for self-signed /
    # localhost / hostname-mismatch certs). Applies to page fetch and downloads.
    session.verify = not args.insecure
    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    default_headers = {
        "User-Agent": args.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    custom_headers = parse_headers(args.header)

    session.headers.update(default_headers)
    session.headers.update(custom_headers)

    cookie_values = []

    if args.cookie:
        cookie_values.append(args.cookie.strip())

    if args.cookie_file:
        loaded_cookie = load_cookie_file(args.cookie_file)
        if loaded_cookie:
            cookie_values.append(loaded_cookie)

    if cookie_values:
        # If user also passed -H "Cookie: ...", this will override/merge into Cookie header.
        # Final Cookie header becomes all cookie sources joined by "; ".
        existing_cookie = session.headers.get("Cookie")
        if existing_cookie:
            cookie_values.insert(0, existing_cookie)

        session.headers["Cookie"] = "; ".join(
            cookie.strip().rstrip(";")
            for cookie in cookie_values
            if cookie.strip()
        )

    return session


def main():
    parser = argparse.ArgumentParser(
        prog="jsextractor",
        description="Extract and download JavaScript files from a web page.",
        epilog="""
Examples:
  jsextractor https://example.com -o example_js
  jsextractor https://example.com -o example_js --timeout 30
  jsextractor https://example.com -o example_js -A "Mozilla/5.0"
  jsextractor https://example.com -o example_js -H "Authorization: Bearer TOKEN"
  jsextractor https://example.com -o example_js -H "X-Custom: value"
  jsextractor https://example.com -o example_js -b "session=abc123; csrftoken=xyz"
  jsextractor https://example.com -o example_js --cookie-file cookies.txt
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "url",
        type=valid_url,
        help="Target URL. Must start with http:// or https://",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output directory for downloaded JS. Default: js_<hostname>",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Request timeout in seconds. Default: 20",
    )

    parser.add_argument(
        "-A",
        "--user-agent",
        default=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        help="Custom User-Agent",
    )

    parser.add_argument(
        "-H",
        "--header",
        action="append",
        default=[],
        help="Custom HTTP header. Can be used multiple times. Example: -H 'Authorization: Bearer TOKEN'",
    )

    parser.add_argument(
        "-b",
        "--cookie",
        help="Raw Cookie header value. Example: -b 'session=abc123; csrftoken=xyz'",
    )

    parser.add_argument(
        "--cookie-file",
        help="Cookie file in Netscape/curl cookie jar format",
    )

    parser.add_argument(
        "-k",
        "--insecure",
        action="store_true",
        help="Skip TLS certificate verification (like curl -k). "
             "Needed for self-signed / localhost / hostname-mismatch certs.",
    )

    parser.add_argument(
        "--no-redirect",
        action="store_true",
        help="Do not follow redirects on the initial page fetch (like curl without -L). "
             "Useful to see auth 3xx instead of silently landing on a login page.",
    )

    args = parser.parse_args()

    if not args.output:
        host = urlparse(args.url).netloc.replace(":", "_") or "site"
        args.output = f"js_{host}"

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        session = build_session(args)
    except argparse.ArgumentTypeError as e:
        parser.error(str(e))

    try:
        resp = session.get(
            args.url,
            timeout=args.timeout,
            allow_redirects=not args.no_redirect,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[error] failed to fetch page: {e}", file=sys.stderr)
        sys.exit(1)

    if resp.history:
        chain = " -> ".join(str(r.status_code) for r in resp.history)
        print(f"[warn] redirected ({chain}) to: {resp.url}")
        if any(x in resp.url.lower() for x in ("login", "/auth")):
            print("[warn] landed on an auth/login page — session cookie likely expired/invalid")
            print("[warn] JS will be scraped from the login page, NOT the target")

    js_urls = extract_js_urls(resp.url, resp.text)

    if not js_urls:
        print("[info] no JavaScript files found")
        sys.exit(0)

    print(f"[info] found {len(js_urls)} JavaScript files")
    print(f"[info] output: {outdir.resolve()}")

    success = 0

    for js_url in js_urls:
        if download_file(session, js_url, outdir, args.timeout):
            success += 1

    print(f"[done] downloaded {success}/{len(js_urls)} JavaScript files")


if __name__ == "__main__":
    main()
