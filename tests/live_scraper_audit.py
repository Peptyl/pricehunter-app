"""
PriceHunter Live Scraper Audit
================================
Tests every scraper against every product in the catalog.
Reports: what works, what's broken, what's missing, accuracy issues.

Run: python tests/live_scraper_audit.py
"""

import json
import sys
import os
import time
import re
import requests
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.engine import (
    ProductSKU, ScrapedResult, MatchValidator,
    NotinoScraper, NicheGallerieScraper, DouglasScraper,
    FragranceBuyScraper, MaxAromaScraper, JomashopScraper,
    FragranceNetScraper, SeeScentsScraper,
)

# ============================================================================
# AUDIT INFRASTRUCTURE
# ============================================================================

@dataclass
class ScrapeAttempt:
    retailer: str
    product_id: str
    url: str
    status: str  # "success", "http_error", "parse_error", "no_url", "blocked", "timeout"
    http_status: Optional[int] = None
    product_title: Optional[str] = None
    extracted_price: Optional[float] = None
    extracted_currency: Optional[str] = None
    extracted_size_ml: Optional[int] = None
    in_stock: Optional[bool] = None
    confidence: Optional[float] = None
    rejection_reason: Optional[str] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None
    raw_snippet: Optional[str] = None

@dataclass
class AuditReport:
    total_attempts: int = 0
    successes: int = 0
    failures: int = 0
    no_url: int = 0
    http_errors: int = 0
    parse_errors: int = 0
    blocked: int = 0
    timeouts: int = 0
    low_confidence: int = 0
    size_mismatches: int = 0
    attempts: List[ScrapeAttempt] = field(default_factory=list)


def load_catalog() -> List[ProductSKU]:
    """Load product catalog"""
    catalog_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "product_catalog_top20.json"
    )
    with open(catalog_path, 'r') as f:
        data = json.load(f)

    products = []
    for p in data["products"]:
        products.append(ProductSKU(
            id=p["id"],
            brand=p["brand"],
            name=p["name"],
            size_ml=p["size_ml"],
            concentration=p["concentration"],
            typical_retail_gbp=p["typical_retail_gbp"],
            aliases=p.get("aliases", []),
            retailer_urls=p.get("retailer_urls", {}),
            size_variants=p.get("size_variants_ml", []),
        ))
    return products


def test_url_reachability(url: str, timeout: int = 10) -> dict:
    """Test if a URL is reachable and what we get back"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    }
    try:
        start = time.time()
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        elapsed = int((time.time() - start) * 1000)
        return {
            "reachable": True,
            "status_code": resp.status_code,
            "final_url": resp.url,
            "content_length": len(resp.text),
            "response_time_ms": elapsed,
            "content_snippet": resp.text[:1000],
            "response": resp,
        }
    except requests.Timeout:
        return {"reachable": False, "error": "timeout"}
    except requests.ConnectionError as e:
        return {"reachable": False, "error": f"connection_error: {e}"}
    except Exception as e:
        return {"reachable": False, "error": str(e)}


def test_single_scraper(scraper, sku: ProductSKU, retailer_key: str, validator: MatchValidator) -> ScrapeAttempt:
    """Test a single scraper against a single product"""
    url = sku.retailer_urls.get(retailer_key, "")

    if not url:
        return ScrapeAttempt(
            retailer=retailer_key, product_id=sku.id, url="",
            status="no_url"
        )

    # First: test raw URL reachability
    reach = test_url_reachability(url)

    if not reach.get("reachable"):
        return ScrapeAttempt(
            retailer=retailer_key, product_id=sku.id, url=url,
            status="timeout" if "timeout" in reach.get("error", "") else "http_error",
            error_message=reach.get("error"),
        )

    http_status = reach.get("status_code")
    response_time = reach.get("response_time_ms")

    if http_status != 200:
        # Check for common block patterns
        status = "blocked" if http_status in (403, 429, 503) else "http_error"
        return ScrapeAttempt(
            retailer=retailer_key, product_id=sku.id, url=url,
            status=status, http_status=http_status,
            response_time_ms=response_time,
            error_message=f"HTTP {http_status}",
            raw_snippet=reach.get("content_snippet", "")[:200],
        )

    # Check for bot detection / CAPTCHA in response
    content = reach.get("content_snippet", "").lower()
    if any(x in content for x in ["captcha", "robot", "verify you are human", "access denied", "cloudflare"]):
        return ScrapeAttempt(
            retailer=retailer_key, product_id=sku.id, url=url,
            status="blocked", http_status=http_status,
            response_time_ms=response_time,
            error_message="Bot detection / CAPTCHA detected",
            raw_snippet=content[:200],
        )

    # Now: run the actual scraper
    try:
        start = time.time()
        result = scraper.scrape_product(sku)
        scrape_ms = int((time.time() - start) * 1000)

        if result is None:
            return ScrapeAttempt(
                retailer=retailer_key, product_id=sku.id, url=url,
                status="parse_error", http_status=http_status,
                response_time_ms=response_time,
                error_message="Scraper returned None (failed to extract price/title)",
                raw_snippet=reach.get("content_snippet", "")[:300],
            )

        # Run validation
        validated = validator.validate(sku, result)

        attempt = ScrapeAttempt(
            retailer=retailer_key, product_id=sku.id, url=url,
            status="success" if validated.confidence >= 75 else "low_confidence",
            http_status=http_status,
            product_title=result.product_title,
            extracted_price=result.price,
            extracted_currency=result.currency,
            extracted_size_ml=result.extracted_size_ml,
            in_stock=result.in_stock,
            confidence=validated.confidence,
            rejection_reason=validated.rejection_reason,
            response_time_ms=response_time,
            raw_snippet=result.raw_html_snippet[:200] if result.raw_html_snippet else "",
        )

        # Check for size mismatch
        if result.extracted_size_ml and result.extracted_size_ml != sku.size_ml:
            attempt.status = "size_mismatch"
            attempt.error_message = f"Expected {sku.size_ml}ml, got {result.extracted_size_ml}ml"

        return attempt

    except Exception as e:
        return ScrapeAttempt(
            retailer=retailer_key, product_id=sku.id, url=url,
            status="parse_error", http_status=http_status,
            response_time_ms=response_time,
            error_message=str(e),
        )


# ============================================================================
# MAIN AUDIT
# ============================================================================

def run_audit():
    print("=" * 80)
    print("PRICEHUNTER LIVE SCRAPER AUDIT")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Load catalog
    products = load_catalog()
    print(f"\nLoaded {len(products)} products from catalog")

    # Initialize scrapers
    scrapers = {
        "notino": NotinoScraper(),
        "nichegallerie": NicheGallerieScraper(),
        "douglas_de": DouglasScraper(),
        "fragrancebuy": FragranceBuyScraper(),
        "maxaroma": MaxAromaScraper(),
        "jomashop": JomashopScraper(),
        "fragrancenet": FragranceNetScraper(),
        "seescents": SeeScentsScraper(),
    }
    validator = MatchValidator()

    report = AuditReport()
    retailer_stats = {r: {"success": 0, "fail": 0, "no_url": 0} for r in scrapers}
    product_stats = {p.id: {"success": 0, "fail": 0} for p in products}

    # Test a subset first (3 products) for speed, then all if --full flag
    full_mode = "--full" in sys.argv
    test_products = products if full_mode else products[:5]

    print(f"Testing {'ALL' if full_mode else 'first 5'} products × {len(scrapers)} retailers")
    print(f"Total attempts: {len(test_products) * len(scrapers)}")
    print("-" * 80)

    for pi, sku in enumerate(test_products):
        print(f"\n[{pi+1}/{len(test_products)}] {sku.brand} {sku.name} ({sku.size_ml}ml {sku.concentration})")
        print(f"  Expected RRP: £{sku.typical_retail_gbp}")

        for retailer_key, scraper in scrapers.items():
            report.total_attempts += 1

            attempt = test_single_scraper(scraper, sku, retailer_key, validator)
            report.attempts.append(attempt)

            # Update stats
            if attempt.status == "success":
                report.successes += 1
                retailer_stats[retailer_key]["success"] += 1
                product_stats[sku.id]["success"] += 1
                icon = "✓"
                detail = f"£{attempt.extracted_price:.2f} {attempt.extracted_currency} | {attempt.extracted_size_ml}ml | conf={attempt.confidence:.0f}%"
            elif attempt.status == "no_url":
                report.no_url += 1
                retailer_stats[retailer_key]["no_url"] += 1
                icon = "·"
                detail = "no URL in catalog"
            elif attempt.status == "blocked":
                report.blocked += 1
                retailer_stats[retailer_key]["fail"] += 1
                product_stats[sku.id]["fail"] += 1
                icon = "🚫"
                detail = f"BLOCKED ({attempt.error_message})"
            elif attempt.status == "timeout":
                report.timeouts += 1
                retailer_stats[retailer_key]["fail"] += 1
                product_stats[sku.id]["fail"] += 1
                icon = "⏱"
                detail = "TIMEOUT"
            elif attempt.status == "http_error":
                report.http_errors += 1
                retailer_stats[retailer_key]["fail"] += 1
                product_stats[sku.id]["fail"] += 1
                icon = "✗"
                detail = f"HTTP {attempt.http_status} ({attempt.error_message})"
            elif attempt.status == "parse_error":
                report.parse_errors += 1
                retailer_stats[retailer_key]["fail"] += 1
                product_stats[sku.id]["fail"] += 1
                icon = "⚠"
                detail = f"PARSE FAIL: {attempt.error_message}"
            elif attempt.status == "size_mismatch":
                report.size_mismatches += 1
                retailer_stats[retailer_key]["fail"] += 1
                product_stats[sku.id]["fail"] += 1
                icon = "📏"
                detail = f"SIZE MISMATCH: {attempt.error_message} (price: {attempt.extracted_price})"
            elif attempt.status == "low_confidence":
                report.low_confidence += 1
                retailer_stats[retailer_key]["fail"] += 1
                product_stats[sku.id]["fail"] += 1
                icon = "?"
                detail = f"LOW CONFIDENCE ({attempt.confidence:.0f}%): {attempt.rejection_reason}"
            else:
                report.failures += 1
                icon = "✗"
                detail = attempt.error_message or "unknown"

            print(f"  {icon} {retailer_key:20s} → {detail}")

            # Rate limit: 1 second between requests
            time.sleep(1)

    # ============================================================================
    # SUMMARY REPORT
    # ============================================================================

    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)

    total_with_urls = report.total_attempts - report.no_url
    success_rate = (report.successes / total_with_urls * 100) if total_with_urls > 0 else 0

    print(f"\nTotal attempts:     {report.total_attempts}")
    print(f"  Has URL:          {total_with_urls}")
    print(f"  No URL:           {report.no_url}")
    print(f"\nOf those with URLs:")
    print(f"  ✓ Success:        {report.successes} ({success_rate:.1f}%)")
    print(f"  🚫 Blocked:       {report.blocked}")
    print(f"  ⏱ Timeout:       {report.timeouts}")
    print(f"  ✗ HTTP Error:     {report.http_errors}")
    print(f"  ⚠ Parse Error:    {report.parse_errors}")
    print(f"  📏 Size Mismatch: {report.size_mismatches}")
    print(f"  ? Low Confidence: {report.low_confidence}")

    print("\n--- RETAILER BREAKDOWN ---")
    for r, stats in sorted(retailer_stats.items()):
        total = stats["success"] + stats["fail"]
        rate = (stats["success"] / total * 100) if total > 0 else 0
        print(f"  {r:20s}: {stats['success']}/{total} success ({rate:.0f}%), {stats['no_url']} no URL")

    print("\n--- PRODUCT COVERAGE ---")
    for pid, stats in product_stats.items():
        if pid not in [p.id for p in test_products]:
            continue
        total = stats["success"] + stats["fail"]
        print(f"  {pid:35s}: {stats['success']}/{total + report.no_url // len(test_products)} retailers returned valid prices")

    # Save detailed JSON report
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests", "audit_results.json"
    )

    results_json = {
        "audit_date": datetime.now().isoformat(),
        "summary": {
            "total_attempts": report.total_attempts,
            "with_urls": total_with_urls,
            "successes": report.successes,
            "success_rate": success_rate,
            "blocked": report.blocked,
            "timeouts": report.timeouts,
            "http_errors": report.http_errors,
            "parse_errors": report.parse_errors,
            "size_mismatches": report.size_mismatches,
            "low_confidence": report.low_confidence,
        },
        "attempts": [
            {
                "retailer": a.retailer,
                "product_id": a.product_id,
                "url": a.url,
                "status": a.status,
                "http_status": a.http_status,
                "product_title": a.product_title,
                "price": a.extracted_price,
                "currency": a.extracted_currency,
                "size_ml": a.extracted_size_ml,
                "in_stock": a.in_stock,
                "confidence": a.confidence,
                "rejection_reason": a.rejection_reason,
                "error": a.error_message,
                "response_time_ms": a.response_time_ms,
            }
            for a in report.attempts
        ],
    }

    with open(report_path, 'w') as f:
        json.dump(results_json, f, indent=2, default=str)

    print(f"\nDetailed results saved to: {report_path}")
    print("=" * 80)


if __name__ == "__main__":
    run_audit()
