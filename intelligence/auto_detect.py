#!/usr/bin/env python3
"""
Olfex Auto-Detection Module
===================================
Automatically detects a new retailer's site type, URL patterns, and optimal
scraping strategy. Run this BEFORE writing any new scraper code.

Usage:
    python auto_detect.py https://www.allbeauty.com/creed/aventus-eau-de-parfum-100ml

Output:
    - Site archetype (Shopify, WooCommerce, SPA, SSR)
    - Recommended scraping strategy
    - Price extraction method
    - Warnings and gotchas
    - Ready-to-use scraper config for retailer_registry.json
"""

import json
import re
import sys
import time
import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from retailer_playbook import (
    RetailerDetector,
    SiteArchetype,
    SHOPIFY_SIGNALS,
    WOOCOMMERCE_SIGNALS,
    SPA_SIGNALS,
    TRADITIONAL_SSR_SIGNALS,
    PROVEN_STRATEGIES,
    RETAILER_GOTCHAS,
    NEW_RETAILER_ONBOARDING_CHECKLIST,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Browser-like headers to avoid basic bot detection
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
}


class RetailerOnboarder:
    """
    Complete onboarding workflow for a new fragrance retailer.
    Runs all detection, verification, and config generation steps.
    """

    def __init__(self, domain: str):
        self.domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
        self.base_url = f"https://{self.domain}"
        self.results = {
            "domain": self.domain,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "steps": [],
        }

    def run_full_detection(self, product_url: str) -> Dict:
        """
        Run the complete detection pipeline on a product URL.

        Args:
            product_url: A specific product page URL on the retailer's site

        Returns:
            Complete detection report with recommended config
        """
        logger.info(f"Starting detection for {self.domain}")

        # Step 1: Fetch the product page
        html, headers, status = self._fetch_page(product_url)
        if not html:
            self.results["error"] = f"Could not fetch {product_url} (status: {status})"
            self.results["recommendation"] = "Needs Playwright or proxy. Cannot detect via HTTP GET."
            return self.results

        self.results["steps"].append({
            "step": "fetch_product_page",
            "status": "success",
            "html_length": len(html),
            "http_status": status,
        })

        # Step 2: Detect archetype
        detection = RetailerDetector.detect_archetype(html, product_url, dict(headers))
        self.results["detection"] = {
            "archetype": detection.archetype.value,
            "confidence": detection.confidence,
            "signals": detection.signals,
            "recommended_method": detection.recommended_method,
            "recommended_selectors": detection.recommended_selectors,
            "warnings": detection.warnings,
            "needs_playwright": detection.needs_playwright,
            "needs_proxy": detection.needs_proxy,
        }

        # Step 3: If Shopify detected, verify JSON API
        if detection.archetype == SiteArchetype.SHOPIFY:
            shopify_ok = self._test_shopify_api()
            self.results["steps"].append({
                "step": "shopify_api_check",
                "status": "success" if shopify_ok else "failed",
                "notes": "JSON API enabled" if shopify_ok else "JSON API disabled or not Shopify",
            })

        # Step 4: Test JSON-LD extraction
        json_ld_data = self._extract_json_ld(html)
        self.results["steps"].append({
            "step": "json_ld_extraction",
            "status": "success" if json_ld_data else "not_found",
            "data": json_ld_data if json_ld_data else None,
        })

        # Step 5: Test price extraction
        price_results = self._test_price_extraction(html, json_ld_data)
        self.results["steps"].append({
            "step": "price_extraction",
            "results": price_results,
        })

        # Step 6: Detect currency
        currency = self._detect_currency(html, json_ld_data)
        self.results["currency"] = currency

        # Step 7: Generate recommended config
        self.results["recommended_config"] = self._generate_config(detection, json_ld_data, currency)

        # Step 8: Print onboarding checklist items still needed
        self.results["remaining_checklist"] = [
            "Verify URL pattern with 3-5 more products",
            "Test with different product sizes",
            "Test stock checking",
            "Run 24h stability test",
        ]

        return self.results

    def _fetch_page(self, url: str) -> Tuple[Optional[str], Dict, int]:
        """Fetch a page with browser-like headers."""
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, allow_redirects=True)
            return resp.text, resp.headers, resp.status_code
        except requests.RequestException as e:
            logger.error(f"Fetch failed: {e}")
            return None, {}, 0

    def _test_shopify_api(self) -> bool:
        """Test if Shopify JSON API is available."""
        try:
            resp = requests.get(
                f"{self.base_url}/products.json?limit=1",
                headers=DEFAULT_HEADERS,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return "products" in data
        except Exception:
            pass
        return False

    def _extract_json_ld(self, html: str) -> Optional[Dict]:
        """Extract JSON-LD structured data from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Handle @graph wrapper
                if isinstance(data, dict) and "@graph" in data:
                    for item in data["@graph"]:
                        if item.get("@type") == "Product":
                            return item
                if isinstance(data, dict) and data.get("@type") == "Product":
                    return data
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            return item
            except (json.JSONDecodeError, TypeError):
                continue
        return None

    def _test_price_extraction(self, html: str, json_ld: Optional[Dict]) -> Dict:
        """Test multiple price extraction methods and report what works."""
        results = {}

        # Method 1: JSON-LD
        if json_ld:
            offers = json_ld.get("offers", {})
            if isinstance(offers, list):
                prices = [o.get("price") for o in offers if o.get("price")]
                results["json_ld"] = {
                    "found": bool(prices),
                    "prices": prices,
                    "note": f"{len(prices)} offer(s) found" if prices else "No prices in offers",
                }
            elif isinstance(offers, dict):
                price = offers.get("price")
                results["json_ld"] = {
                    "found": bool(price and float(price) > 0),
                    "price": price,
                    "note": "Price is 0.0 — broken JSON-LD!" if price and float(price) == 0 else "OK",
                }

        # Method 2: Open Graph meta
        soup = BeautifulSoup(html, "html.parser")
        og_price = soup.find("meta", {"property": "product:price:amount"})
        if og_price:
            results["og_meta"] = {
                "found": True,
                "price": og_price.get("content"),
            }

        # Method 3: CSS selectors (common patterns)
        price_selectors = [
            ".price .woocommerce-Price-amount",
            ".product-price",
            ".price-current",
            "[itemprop='price']",
            ".price .amount",
            ".deal-price",
            "#product-price",
        ]
        for selector in price_selectors:
            elements = soup.select(selector)
            if elements:
                text = elements[0].get_text(strip=True)
                results[f"css:{selector}"] = {
                    "found": True,
                    "text": text,
                    "count": len(elements),
                }

        return results

    def _detect_currency(self, html: str, json_ld: Optional[Dict]) -> str:
        """Detect the currency used on the page."""
        # Check JSON-LD first
        if json_ld:
            offers = json_ld.get("offers", {})
            if isinstance(offers, dict):
                currency = offers.get("priceCurrency")
                if currency:
                    return currency
            elif isinstance(offers, list) and offers:
                currency = offers[0].get("priceCurrency")
                if currency:
                    return currency

        # Check OG meta
        soup = BeautifulSoup(html, "html.parser")
        og_currency = soup.find("meta", {"property": "product:price:currency"})
        if og_currency:
            return og_currency.get("content", "")

        # Heuristic from symbols
        if "£" in html[:5000]:
            return "GBP"
        if "€" in html[:5000]:
            return "EUR"
        if "$" in html[:5000]:
            return "USD"

        return "UNKNOWN"

    def _generate_config(self, detection, json_ld: Optional[Dict], currency: str) -> Dict:
        """Generate a ready-to-use scraper_config for retailer_registry.json."""
        strategy = PROVEN_STRATEGIES.get(detection.recommended_method, {})

        config = {
            "id": self.domain.replace(".", "_").replace("-", "_"),
            "name": self.domain.split(".")[0].title(),
            "domain": self.domain,
            "currency": currency,
            "scraper_config": {
                "status": "testing",
                "method": detection.recommended_method,
                "archetype": detection.archetype.value,
                "difficulty": "low" if not detection.needs_playwright else "medium",
                "needs_proxy": detection.needs_proxy,
                "needs_playwright": detection.needs_playwright,
                "rate_limit_rpm": strategy.rate_limit_rpm if strategy else 15,
                "anti_bot_handling": strategy.anti_bot_handling if strategy else "headers_only",
                "cookie_consent_required": strategy.cookie_consent if strategy else False,
                "price_extraction_methods": detection.recommended_selectors,
                "detection_confidence": detection.confidence,
                "detection_signals": detection.signals,
            },
            "warnings": detection.warnings,
        }

        # Add JSON-LD validation result
        if json_ld:
            offers = json_ld.get("offers", {})
            if isinstance(offers, dict) and offers.get("price"):
                price = float(offers["price"])
                config["scraper_config"]["json_ld_reliable"] = price > 0
            elif isinstance(offers, list):
                config["scraper_config"]["json_ld_reliable"] = True
                config["scraper_config"]["json_ld_multi_offer"] = True

        return config


def main():
    if len(sys.argv) < 2:
        print("Usage: python auto_detect.py <product_url>")
        print("Example: python auto_detect.py https://www.allbeauty.com/creed/aventus-100ml")
        sys.exit(1)

    product_url = sys.argv[1]
    parsed = urlparse(product_url)
    domain = parsed.netloc

    onboarder = RetailerOnboarder(domain)
    results = onboarder.run_full_detection(product_url)

    print("\n" + "=" * 70)
    print("RETAILER AUTO-DETECTION REPORT")
    print("=" * 70)
    print(json.dumps(results, indent=2, default=str))

    # Save report
    report_path = f"data/detection_reports/{domain.replace('.', '_')}.json"
    import os
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
