import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import trafilatura


def clean_text(text: str) -> str:
    """
    Clean extra whitespace from extracted text.
    """
    return re.sub(r"\s+", " ", text).strip()


def fetch_html(url: str) -> str:
    """
    Fetch HTML content from a webpage using browser-like headers.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


def extract_startupdaily(soup: BeautifulSoup) -> str:
    """
    Extract article text specifically for Startup Daily pages.
    """
    article = soup.find("article")
    if not article:
        return ""

    # Remove noisy injected sections
    for bad_block in article.select(
        "div.code-block, div.pm-ad, section.newsletter-cta, div.modal"
    ):
        bad_block.decompose()

    parts = []

    # Extract headings and paragraphs in order
    for node in article.select(
        "p.wp-block-paragraph, h2.wp-block-heading, h3.wp-block-heading"
    ):
        text = node.get_text(" ", strip=True)
        if text:
            parts.append(text)

    extracted_text = clean_text(" ".join(parts))

    if len(extracted_text) > 300:
        return extracted_text

    return ""


def extract_innovationaus(soup: BeautifulSoup) -> str:
    """
    Extract article text specifically for InnovationAus pages.
    """
    content = soup.select_one("div.entry-content-inner")
    if not content:
        return ""

    # Remove noisy blocks
    for bad_block in content.select("div.fade-bg, script, style"):
        bad_block.decompose()

    parts = []

    # Extract paragraphs and headings in order
    for node in content.select("p, h2, h3"):
        text = node.get_text(" ", strip=True)
        if text:
            parts.append(text)

    extracted_text = clean_text(" ".join(parts))

    if len(extracted_text) > 200:
        return extracted_text

    return ""


def extract_with_trafilatura(url: str, html: str) -> str:
    """
    Fallback cleaner extraction using trafilatura.
    """
    extracted = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=False,
        favor_recall=True
    )

    return clean_text(extracted or "")


def extract_generic_paragraphs(soup: BeautifulSoup) -> str:
    """
    Generic fallback if site-specific extraction fails.
    """
    paragraphs = soup.find_all("p")
    text = " ".join(
        p.get_text(" ", strip=True)
        for p in paragraphs
        if p.get_text(" ", strip=True)
    )
    return clean_text(text)


def scrape_article_text(url: str) -> str:
    """
    Main article scraping function.
    Uses source-specific extraction first, then fallback methods.
    """
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        domain = urlparse(url).netloc.lower()

        # Source-specific extractors
        if "startupdaily.net" in domain:
            text = extract_startupdaily(soup)
            if text:
                return text

        if "innovationaus.com" in domain:
            text = extract_innovationaus(soup)
            if text:
                return text

        # Fallback 1
        text = extract_with_trafilatura(url, html)
        if text and len(text) > 300:
            return text

        # Fallback 2
        return extract_generic_paragraphs(soup)

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""