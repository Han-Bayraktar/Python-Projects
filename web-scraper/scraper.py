#!/usr/bin/env python3
"""
Web Scraper Application
I used the site: https://quotes.toscrape.com since it's safe to use for scraping.
Features:
- Paginated scraping (follows "Next" links)
- CSV export
- Polite scraping with delay and custom User-Agent
- Basic retries for HTTP errors
Usage bash code example:
    python scraper.py --csv data.csv --limit-pages 3 --delay 1.0
"""
from __future__ import annotations
import argparse
import csv
import logging
import random
import sqlite3
import sys
import time
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com"
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TIMEOUT = 15

def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

def get_session(user_agent: Optional[str] = None) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
    })
    return s

def fetch_html(session: requests.Session, url: str, retries: int = 3, backoff: float = 1.5) -> str:
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            logging.debug(f"GET {url} (attempt {attempt}/{retries})")
            resp = session.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            last_exc = e
            wait = backoff ** attempt + random.uniform(0, 0.2)
            logging.warning(f"Request failed: {e!r}. Retrying in {wait:.2f}s")
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url} after {retries} retries") from last_exc

def parse_quotes(html: str) -> Tuple[List[Dict], Optional[str]]:
    soup = BeautifulSoup(html, "lxml")
    items = []
    for q in soup.select("div.quote"):
        text = q.select_one("span.text")
        author = q.select_one("small.author")
        tag_nodes = q.select("div.tags a.tag")
        items.append({
            "quote": (text.get_text(strip=True) if text else ""),
            "author": (author.get_text(strip=True) if author else ""),
            "tags": ", ".join(t.get_text(strip=True) for t in tag_nodes) if tag_nodes else "",
        })
    # next page
    next_link = soup.select_one("li.next a")
    next_href = next_link.get("href") if next_link else None
    return items, next_href

def save_to_csv(rows: Iterable[Dict], csv_path: str) -> None:
    rows = list(rows)
    if not rows:
        logging.info("No data to write to CSV.")
        return
    fieldnames = list(rows[0].keys())
    write_header = not _file_exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
    logging.info(f"Wrote {len(rows)} rows to {csv_path}")

def _file_exists(path: str) -> bool:
    try:
        import os
        return os.path.exists(path) and os.path.getsize(path) > 0
    except Exception:
        return False

def init_sqlite(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote TEXT NOT NULL,
            author TEXT,
            tags TEXT
        );
        """
    )
    con.commit()
    con.close()

def save_to_sqlite(rows: Iterable[Dict], db_path: str) -> None:
    rows = list(rows)
    if not rows:
        logging.info("No data to write to SQLite.")
        return
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executemany(
        "INSERT INTO quotes (quote, author, tags) VALUES (?, ?, ?)",
        [(r["quote"], r["author"], r["tags"]) for r in rows],
    )
    con.commit()
    con.close()
    logging.info(f"Inserted {len(rows)} rows into {db_path}")

def scrape(
    limit_pages: Optional[int],
    delay: float,
    user_agent: Optional[str],
    csv_path: Optional[str],
    sqlite_path: Optional[str],
    verbose: bool,
) -> None:
    setup_logging(verbose)
    session = get_session(user_agent)
    url = BASE_URL
    page = 0

    if sqlite_path:
        init_sqlite(sqlite_path)

    while True:
        page += 1
        logging.info(f"Scraping page {page}: {url}")
        html = fetch_html(session, url)
        items, next_href = parse_quotes(html)

        if csv_path:
            save_to_csv(items, csv_path)
        if sqlite_path:
            save_to_sqlite(items, sqlite_path)

        if limit_pages and page >= limit_pages:
            logging.info("Reached page limit. Stopping.")
            break
        if not next_href:
            logging.info("No next page link. Finished.")
            break

        # polite delay
        sleep_for = max(0.0, delay + random.uniform(0, delay * 0.15 if delay else 0.0))
        if sleep_for:
            logging.debug(f"Sleeping for {sleep_for:.2f}s")
            time.sleep(sleep_for)

        url = urljoin(url, next_href)

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Simple web scraper (quotes.toscrape.com)")
    p.add_argument("--csv", dest="csv_path", default="data.csv", help="CSV output path (default: data.csv). Use '' to disable.")
    p.add_argument("--sqlite", dest="sqlite_path", default="", help="SQLite DB path (disabled if empty). Example: data.db")
    p.add_argument("--limit-pages", type=int, default=0, help="Stop after N pages (0 = no limit).")
    p.add_argument("--delay", type=float, default=1.0, help="Polite delay between page requests in seconds (default: 1.0)")
    p.add_argument("--user-agent", default="", help="Custom User-Agent string")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    return p

def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    csv_path = args.csv_path if args.csv_path.strip() else None
    sqlite_path = args.sqlite_path.strip() or None
    limit_pages = args.limit_pages if args.limit_pages > 0 else None
    try:
        scrape(
            limit_pages=limit_pages,
            delay=args.delay,
            user_agent=(args.user_agent or None),
            csv_path=csv_path,
            sqlite_path=sqlite_path,
            verbose=args.verbose,
        )
        return 0
    except KeyboardInterrupt:
        logging.warning("Interrupted by user.")
        return 2
    except Exception as e:
        logging.exception("Scraper failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
