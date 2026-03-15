#!/usr/bin/env python3
"""
Retailer Onboarding Pipeline
==============================
Automates the process of adding new retailers to Olfex:
1. Detect site platform (Shopify, WooCommerce, custom SSR, SPA)
2. Test extraction methods (JSON-LD, Shopify API, HTML selectors, Playwright)
3. Validate against known products
4. Generate scraper config
5. Add to retailer registry

Usage:
    python retailer_onboarding.py --domain allbeauty.com
    python retailer_onboarding.py --domain notino.de --product-urls urls.txt
    python retailer_onboarding.py --domain luckyscent.com --auto-search

Exit codes:
    0: Success
    1: Domain not accessible
    2: No extraction method found
    3: Registry update failed
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Try to import Playwright (optional)
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
}

SHOPIFY_SIGNALS = [
    "cdn.shopify.com", "Shopify.theme", "shopify-section",
    "myshopify.com", "/cart.js", "Shopify.routes"
]

WOOCOMMERCE_SIGNALS = [
    "woocommerce", "wc-ajax", "wp-content", "add_to_cart",
    "product-type-simple", "/wp-json/wc/"
]

SPA_SIGNALS = [
    "react", "__NEXT_DATA__", "vue", "angular", "app-root",
    "bundle.js", "chunk.js", "__NUXT__", "_app"
]

REGISTRY_PATH = Path(__file__).parent.parent / "data" / "retailer_registry.json"


@dataclass
class ExtractionResult:
    """Result of a single extraction attempt."""
    method: str
    success: bool
    price: Optional[float] = None
    title: Optional[str] = None
    currency: Optional[str] = None
    time_ms: float = 0.0
    confidence: float = 0.0
    notes: str = ""
    raw_data: Optional[Dict] = None


@dataclass
class PlatformResult:
    """Detected platform and metadata."""
    platform: str
    confidence: float
    signals_found: List[str] = field(default_factory=list)
    needs_playwright: bool = False
    needs_proxy: bool = False
    detected_framework: Optional[str] = None
    anti_bot_detected: bool = False


@dataclass
class OnboardingReport:
    """Complete onboarding report for a retailer."""
    domain: str
    timestamp: str
    platform: PlatformResult
    test_results: Dict[str, List[ExtractionResult]]
    best_method: str
    best_confidence: float
    currency: str
    country: Optional[str]
    estimated_tier: int
    config: Dict
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    urls_tested: List[str] = field(default_factory=list)


class PlatformDetector:
    """Detects website platform from HTML/headers."""

    @staticmethod
    def detect(html: str, url: str, headers: Dict) -> PlatformResult:
        """Detect the e-commerce platform from HTML and headers."""
        signals_found = []
        platform = "unknown"
        confidence = 0.0
        needs_playwright = False
        needs_proxy = False
        anti_bot_detected = False
        detected_framework = None

        # Combine HTML and headers for signal detection
        content = html.lower()
        header_str = str(headers).lower()

        # Check for Shopify signals
        shopify_count = sum(1 for signal in SHOPIFY_SIGNALS if signal.lower() in content)
        if shopify_count >= 2:
            platform = "shopify"
            signals_found = [s for s in SHOPIFY_SIGNALS if s.lower() in content]
            confidence = min(0.95, 0.5 + shopify_count * 0.15)

        # Check for WooCommerce signals
        woocommerce_count = sum(1 for signal in WOOCOMMERCE_SIGNALS if signal.lower() in content)
        if woocommerce_count >= 2 and confidence < 0.7:
            platform = "woocommerce"
            signals_found = [s for s in WOOCOMMERCE_SIGNALS if s.lower() in content]
            confidence = min(0.95, 0.5 + woocommerce_count * 0.15)

        # Check for SPA frameworks
        spa_count = sum(1 for signal in SPA_SIGNALS if signal.lower() in content)
        if spa_count >= 1 and confidence < 0.7:
            platform = "spa"
            signals_found = [s for s in SPA_SIGNALS if s.lower() in content]
            confidence = 0.5 + min(spa_count * 0.2, 0.4)
            needs_playwright = True

            # Detect specific framework
            if "__NEXT_DATA__" in content:
                detected_framework = "Next.js"
            elif "vue" in content:
                detected_framework = "Vue.js"
            elif "__NUXT__" in content:
                detected_framework = "Nuxt"
            elif "react" in content:
                detected_framework = "React"
            elif "angular" in content:
                detected_framework = "Angular"

        # Detect anti-bot measures
        if "cloudflare" in header_str or "x-amzn-waf-action" in header_str:
            anti_bot_detected = True
            needs_proxy = True
            confidence *= 0.9

        # Check for SSR (has JSON-LD and good content)
        if platform == "unknown" and "<script type=\"application/ld+json\">" in html:
            platform = "custom_ssr"
            confidence = 0.85

        return PlatformResult(
            platform=platform,
            confidence=confidence,
            signals_found=signals_found,
            needs_playwright=needs_playwright,
            needs_proxy=needs_proxy,
            detected_framework=detected_framework,
            anti_bot_detected=anti_bot_detected
        )


class ExtractionTester:
    """Tests different extraction methods on product pages."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    async def test_json_ld(self, url: str, html: Optional[str] = None) -> ExtractionResult:
        """Test JSON-LD schema extraction."""
        start = time.time()
        try:
            if not html:
                resp = self.session.get(url, timeout=15)
                html = resp.text

            soup = BeautifulSoup(html, "html.parser")
            scripts = soup.find_all("script", type="application/ld+json")

            for script in scripts:
                try:
                    data = json.loads(script.string)
                    product = self._extract_product_from_json_ld(data)
                    if product:
                        elapsed = time.time() - start
                        price = self._extract_price(product)
                        return ExtractionResult(
                            method="json_ld",
                            success=True,
                            price=price,
                            title=product.get("name"),
                            currency=self._extract_currency(product),
                            time_ms=elapsed * 1000,
                            confidence=0.95 if price and price > 0 else 0.5,
                            raw_data=product
                        )
                except (json.JSONDecodeError, TypeError):
                    continue

            return ExtractionResult(
                method="json_ld",
                success=False,
                time_ms=(time.time() - start) * 1000,
                notes="No Product JSON-LD found"
            )

        except Exception as e:
            logger.error(f"JSON-LD extraction failed: {e}")
            return ExtractionResult(
                method="json_ld",
                success=False,
                time_ms=(time.time() - start) * 1000,
                notes=str(e)
            )

    async def test_shopify_api(self, url: str) -> ExtractionResult:
        """Test Shopify .json endpoint."""
        start = time.time()
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            product_handle = parsed.path.strip("/").split("/")[-1]

            json_url = f"{base_url}/products/{product_handle}.json"
            resp = self.session.get(json_url, timeout=15)

            if resp.status_code == 200:
                data = resp.json()
                product = data.get("product", {})
                if product:
                    variant = product.get("variants", [{}])[0]
                    price = variant.get("price") or product.get("variants", [{}])[0].get("price")
                    return ExtractionResult(
                        method="shopify_json_api",
                        success=True,
                        price=float(price) if price else None,
                        title=product.get("title"),
                        currency=self._detect_currency_from_shopify(product),
                        time_ms=(time.time() - start) * 1000,
                        confidence=0.9,
                        raw_data=product
                    )

            return ExtractionResult(
                method="shopify_json_api",
                success=False,
                time_ms=(time.time() - start) * 1000,
                notes=f"Shopify API returned {resp.status_code}"
            )

        except Exception as e:
            logger.error(f"Shopify API test failed: {e}")
            return ExtractionResult(
                method="shopify_json_api",
                success=False,
                time_ms=(time.time() - start) * 1000,
                notes=str(e)
            )

    async def test_html_selectors(self, url: str, html: Optional[str] = None) -> ExtractionResult:
        """Test common HTML/CSS selectors for price extraction."""
        start = time.time()
        try:
            if not html:
                resp = self.session.get(url, timeout=15)
                html = resp.text

            soup = BeautifulSoup(html, "html.parser")

            # Common price selectors
            price_selectors = [
                ".price .amount",
                ".product-price",
                ".price-current",
                "[data-price]",
                "[itemprop='price']",
                ".woocommerce-Price-amount",
                ".js-price",
                ".current-price",
                "[data-current-price]",
            ]

            title_selectors = [
                "h1.product-title",
                "h1[itemprop='name']",
                ".product-name",
                "h1.name",
            ]

            price = None
            title = None
            confidence = 0.0

            # Try to find price
            for selector in price_selectors:
                elements = soup.select(selector)
                if elements:
                    price_text = elements[0].get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price and price > 0:
                        confidence = 0.7
                        break

            # Try to find title
            for selector in title_selectors:
                elements = soup.select(selector)
                if elements:
                    title = elements[0].get_text(strip=True)
                    break

            return ExtractionResult(
                method="html_selectors",
                success=price is not None and price > 0,
                price=price,
                title=title,
                time_ms=(time.time() - start) * 1000,
                confidence=confidence,
                notes=f"Found with selector search" if price else "No price found with common selectors"
            )

        except Exception as e:
            logger.error(f"HTML selector test failed: {e}")
            return ExtractionResult(
                method="html_selectors",
                success=False,
                time_ms=(time.time() - start) * 1000,
                notes=str(e)
            )

    async def test_playwright(self, url: str) -> ExtractionResult:
        """Test full browser rendering with Playwright."""
        if not PLAYWRIGHT_AVAILABLE:
            return ExtractionResult(
                method="playwright",
                success=False,
                notes="Playwright not installed"
            )

        start = time.time()
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                page.set_default_timeout(15000)

                await page.goto(url, wait_until="networkidle")
                await page.wait_for_load_state("domcontentloaded")

                # Try JSON-LD after rendering
                json_ld = await page.evaluate("""() => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (let script of scripts) {
                        try {
                            const data = JSON.parse(script.textContent);
                            if (data['@type'] === 'Product' ||
                                (data['@graph'] && data['@graph'].some(g => g['@type'] === 'Product'))) {
                                return data;
                            }
                        } catch (e) {}
                    }
                    return null;
                }""")

                if json_ld:
                    product = json_ld if json_ld.get("@type") == "Product" else (
                        next((g for g in json_ld.get("@graph", []) if g.get("@type") == "Product"), None)
                    )
                    if product:
                        price = self._extract_price(product)
                        await browser.close()
                        return ExtractionResult(
                            method="playwright_json_ld",
                            success=True,
                            price=price,
                            title=product.get("name"),
                            currency=self._extract_currency(product),
                            time_ms=(time.time() - start) * 1000,
                            confidence=0.95,
                            raw_data=product
                        )

                # Fallback: Extract with selectors
                page_content = await page.content()
                html_result = await self.test_html_selectors(url, page_content)
                html_result.method = "playwright_selectors"
                await browser.close()
                return html_result

        except Exception as e:
            logger.error(f"Playwright test failed: {e}")
            return ExtractionResult(
                method="playwright",
                success=False,
                time_ms=(time.time() - start) * 1000,
                notes=str(e)
            )

    async def test_all_methods(self, urls: List[str]) -> Dict[str, List[ExtractionResult]]:
        """Test all methods against multiple URLs."""
        results = {
            "json_ld": [],
            "shopify_json_api": [],
            "html_selectors": [],
            "playwright": []
        }

        for url in urls:
            logger.info(f"Testing URL: {url}")

            try:
                # Fetch HTML once for reuse
                resp = self.session.get(url, timeout=15)
                html = resp.text
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                continue

            # Test each method
            json_ld_result = await self.test_json_ld(url, html)
            results["json_ld"].append(json_ld_result)

            shopify_result = await self.test_shopify_api(url)
            results["shopify_json_api"].append(shopify_result)

            html_result = await self.test_html_selectors(url, html)
            results["html_selectors"].append(html_result)

            if PLAYWRIGHT_AVAILABLE:
                pw_result = await self.test_playwright(url)
                results["playwright"].append(pw_result)

        return results

    # Helper methods
    @staticmethod
    def _extract_product_from_json_ld(data):
        """Extract Product object from JSON-LD (handles @graph wrapper)."""
        if isinstance(data, dict):
            if data.get("@type") == "Product":
                return data
            if "@graph" in data:
                for item in data["@graph"]:
                    if item.get("@type") == "Product":
                        return item
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    return item
        return None

    @staticmethod
    def _extract_price(product: Dict) -> Optional[float]:
        """Extract price from product dict (handles various structures)."""
        try:
            offers = product.get("offers", {})
            if isinstance(offers, dict):
                price = offers.get("price")
                if price:
                    return float(price)
            elif isinstance(offers, list) and offers:
                price = offers[0].get("price")
                if price:
                    return float(price)
        except (ValueError, TypeError, KeyError):
            pass
        return None

    @staticmethod
    def _extract_currency(product: Dict) -> Optional[str]:
        """Extract currency from product dict."""
        offers = product.get("offers", {})
        if isinstance(offers, dict):
            return offers.get("priceCurrency")
        elif isinstance(offers, list) and offers:
            return offers[0].get("priceCurrency")
        return None

    @staticmethod
    def _detect_currency_from_shopify(product: Dict) -> Optional[str]:
        """Detect currency from Shopify product."""
        # Shopify typically stores currency in shop metadata
        # For now, return from first variant
        variant = product.get("variants", [{}])[0]
        return variant.get("currency") or "USD"

    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        """Parse price from text (handles various formats)."""
        import re
        # Remove currency symbols and non-numeric characters
        match = re.search(r'[\d,]+\.?\d*', price_text.replace(",", ""))
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        return None


class RetailerOnboarder:
    """Main onboarding pipeline orchestrator."""

    def __init__(self, domain: str):
        self.domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
        self.base_url = f"https://{self.domain}"
        self.detector = PlatformDetector()
        self.tester = ExtractionTester()

    async def onboard(self, product_urls: Optional[List[str]] = None) -> OnboardingReport:
        """Execute full onboarding pipeline."""
        logger.info(f"Starting onboarding for {self.domain}")
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Step 1: Verify domain is accessible
        try:
            resp = requests.head(self.base_url, timeout=10, allow_redirects=True)
            if resp.status_code >= 400:
                logger.error(f"Domain not accessible: {resp.status_code}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Cannot access domain: {e}")
            sys.exit(1)

        # Step 2: Get sample product URLs if not provided
        if not product_urls:
            logger.info("Attempting to find sample products...")
            product_urls = await self._find_sample_products()
            if not product_urls:
                logger.warning("Could not find sample products, using homepage")
                product_urls = [self.base_url]

        logger.info(f"Testing with {len(product_urls)} URL(s)")

        # Step 3: Detect platform from first product
        try:
            resp = requests.get(product_urls[0], timeout=15)
            platform = self.detector.detect(resp.text, product_urls[0], dict(resp.headers))
        except Exception as e:
            logger.error(f"Platform detection failed: {e}")
            platform = PlatformResult(
                platform="unknown",
                confidence=0.0,
                needs_playwright=True,
                needs_proxy=False
            )

        # Step 4: Test all extraction methods
        logger.info("Testing extraction methods...")
        test_results = await self.tester.test_all_methods(product_urls)

        # Step 5: Determine best method
        best_method, best_confidence = self._rank_methods(test_results)

        # Step 6: Detect currency, country, other info
        currency = await self._detect_site_info(product_urls[0])
        country = self._guess_country_from_domain()

        # Step 7: Generate configuration
        config = self._generate_config(platform, best_method, currency, best_confidence)

        # Step 8: Compile report
        warnings = []
        if platform.anti_bot_detected:
            warnings.append("Anti-bot measures detected (Cloudflare, WAF). May need proxy.")
        if platform.needs_playwright and best_method not in ["playwright", "playwright_json_ld"]:
            warnings.append("Platform is SPA but best non-Playwright method selected due to performance.")
        if best_confidence < 0.7:
            warnings.append("Low confidence detection. Manual review recommended.")

        recommendations = []
        if best_method == "json_ld":
            recommendations.append("JSON-LD extraction is reliable for this retailer.")
        if platform.platform == "shopify" and test_results["shopify_json_api"]:
            if any(r.success for r in test_results["shopify_json_api"]):
                recommendations.append("Use Shopify JSON API for best performance and reliability.")
        if not PLAYWRIGHT_AVAILABLE and platform.needs_playwright:
            recommendations.append("Install Playwright for better SPA support: pip install playwright")

        report = OnboardingReport(
            domain=self.domain,
            timestamp=timestamp,
            platform=platform,
            test_results=test_results,
            best_method=best_method,
            best_confidence=best_confidence,
            currency=currency,
            country=country,
            estimated_tier=2 if best_confidence < 0.8 else 1,
            config=config,
            warnings=warnings,
            recommendations=recommendations,
            urls_tested=product_urls
        )

        logger.info(f"Onboarding complete. Best method: {best_method} (confidence: {best_confidence:.2f})")
        return report

    def _rank_methods(self, test_results: Dict[str, List[ExtractionResult]]) -> Tuple[str, float]:
        """Rank extraction methods by success rate and confidence."""
        method_scores = {}

        for method, results in test_results.items():
            if not results:
                method_scores[method] = (0.0, 0)
                continue

            successful = [r for r in results if r.success]
            if not successful:
                method_scores[method] = (0.0, 0)
                continue

            avg_confidence = sum(r.confidence for r in successful) / len(successful)
            success_rate = len(successful) / len(results)
            combined_score = (success_rate * 0.6 + avg_confidence * 0.4)
            method_scores[method] = (combined_score, avg_confidence)

        best_method = max(method_scores.items(), key=lambda x: x[1][0])
        return best_method[0], best_method[1][1]

    async def _find_sample_products(self) -> List[str]:
        """Try to find product URLs on the retailer's site."""
        try:
            resp = requests.get(self.base_url, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Look for product links (common patterns)
            patterns = [
                "a[href*='/products/']",
                "a[href*='/product/']",
                "a.product-link",
                "a[data-product-url]",
            ]

            urls = []
            for pattern in patterns:
                links = soup.select(pattern)
                for link in links[:3]:  # Get first 3
                    href = link.get("href", "")
                    if href:
                        full_url = href if href.startswith("http") else self.base_url + href
                        urls.append(full_url)
                if urls:
                    break

            return urls[:5]
        except Exception as e:
            logger.error(f"Product discovery failed: {e}")
            return []

    async def _detect_site_info(self, url: str) -> str:
        """Detect currency, country, and other info."""
        try:
            resp = requests.get(url, timeout=15)
            html = resp.text.lower()

            # Check for currency symbols or meta tags
            if "£" in html:
                return "GBP"
            if "€" in html:
                return "EUR"
            if "$" in html:
                return "USD"
            if "¥" in html:
                return "JPY"

            # Check for country code in domain
            if self.domain.endswith(".uk"):
                return "GBP"
            if self.domain.endswith(".de") or self.domain.endswith(".fr"):
                return "EUR"
            if self.domain.endswith(".ca"):
                return "CAD"

            return "USD"  # Default
        except Exception as e:
            logger.error(f"Site info detection failed: {e}")
            return "USD"

    def _guess_country_from_domain(self) -> Optional[str]:
        """Guess country from domain extension."""
        domain_to_country = {
            ".uk": "UK",
            ".de": "DE",
            ".fr": "FR",
            ".ca": "CA",
            ".us": "US",
            ".jp": "JP",
            ".com": None,
            ".hk": "HK",
        }
        for ext, country in domain_to_country.items():
            if self.domain.endswith(ext):
                return country
        return None

    def _generate_config(self, platform: PlatformResult, best_method: str,
                       currency: str, confidence: float) -> Dict:
        """Generate ready-to-use scraper config."""
        return {
            "id": self.domain.replace(".", "_").replace("-", "_"),
            "name": self.domain.split(".")[0].title(),
            "domain": self.domain,
            "country": self._guess_country_from_domain() or "UNKNOWN",
            "currency": currency,
            "type": "authorized_reseller",  # Default, user should verify
            "tier": 2 if confidence < 0.8 else 1,
            "trust_score": int(confidence * 100),
            "platform": platform.platform,
            "shipping": {
                "ships_to_uk": True,
                "estimated_delivery_days": "3-7"
            },
            "vat_included": currency == "GBP",
            "scraper_config": {
                "status": "testing",
                "method": best_method,
                "fallback_methods": ["html_css", "json_ld"],
                "difficulty": "low" if not platform.needs_playwright else "medium",
                "needs_proxy": platform.needs_proxy,
                "needs_playwright": platform.needs_playwright,
                "rate_limit_rpm": 20,
                "avg_response_ms": 1000,
                "search_url_template": f"https://{self.domain}/search?q={{query}}"
            },
            "notes": f"Auto-detected via onboarding. Platform: {platform.platform} ({platform.confidence:.0%} confidence)"
        }


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Retailer Onboarding Pipeline for Olfex"
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Domain of the retailer (e.g., allbeauty.com)"
    )
    parser.add_argument(
        "--product-urls",
        help="File with product URLs (one per line)"
    )
    parser.add_argument(
        "--auto-search",
        action="store_true",
        help="Automatically find product URLs from the site"
    )
    parser.add_argument(
        "--update-registry",
        action="store_true",
        help="Automatically add successful result to registry"
    )
    parser.add_argument(
        "--output",
        help="Save report to JSON file"
    )

    args = parser.parse_args()

    # Read product URLs if provided
    product_urls = None
    if args.product_urls:
        try:
            with open(args.product_urls) as f:
                product_urls = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(product_urls)} product URLs from {args.product_urls}")
        except FileNotFoundError:
            logger.error(f"File not found: {args.product_urls}")
            sys.exit(1)

    # Run onboarding
    onboarder = RetailerOnboarder(args.domain)
    report = await onboarder.onboard(product_urls)

    # Print report
    print("\n" + "=" * 80)
    print("RETAILER ONBOARDING REPORT")
    print("=" * 80)
    print(f"\nDomain: {report.domain}")
    print(f"Platform: {report.platform.platform} ({report.platform.confidence:.0%} confidence)")
    print(f"Best Method: {report.best_method}")
    print(f"Currency: {report.currency}")
    print(f"Estimated Tier: {report.estimated_tier}")
    print(f"URLs Tested: {len(report.urls_tested)}")

    if report.warnings:
        print(f"\nWarnings:")
        for warning in report.warnings:
            print(f"  ⚠ {warning}")

    if report.recommendations:
        print(f"\nRecommendations:")
        for rec in report.recommendations:
            print(f"  ✓ {rec}")

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_dict = {
            "domain": report.domain,
            "timestamp": report.timestamp,
            "platform": asdict(report.platform),
            "best_method": report.best_method,
            "best_confidence": report.best_confidence,
            "currency": report.currency,
            "country": report.country,
            "estimated_tier": report.estimated_tier,
            "config": report.config,
            "warnings": report.warnings,
            "recommendations": report.recommendations,
            "urls_tested": report.urls_tested,
            "test_results": {
                method: [
                    {
                        "method": r.method,
                        "success": r.success,
                        "price": r.price,
                        "title": r.title,
                        "confidence": r.confidence,
                        "time_ms": r.time_ms,
                        "notes": r.notes
                    }
                    for r in results
                ]
                for method, results in report.test_results.items()
            }
        }

        with open(output_path, "w") as f:
            json.dump(report_dict, f, indent=2, default=str)
        logger.info(f"Report saved to {output_path}")

    # Update registry if requested
    if args.update_registry and report.best_confidence >= 0.7:
        try:
            updated = update_registry(report.config)
            if updated:
                print(f"\n✓ Registry updated successfully!")
                print(f"  Run: git add data/retailer_registry.json")
                sys.exit(0)
            else:
                print(f"\n✗ Registry update failed")
                sys.exit(3)
        except Exception as e:
            logger.error(f"Registry update failed: {e}")
            sys.exit(3)

    sys.exit(0)


def update_registry(config: Dict) -> bool:
    """Add config to retailer registry."""
    try:
        # Ensure ID uniqueness
        with open(REGISTRY_PATH) as f:
            registry = json.load(f)

        existing_ids = {r["id"] for r in registry["retailers"]}
        if config["id"] in existing_ids:
            logger.warning(f"Retailer {config['id']} already exists in registry")
            return False

        # Add to registry
        registry["retailers"].append(config)
        registry["last_updated"] = datetime.utcnow().isoformat() + "Z"

        # Write back
        with open(REGISTRY_PATH, "w") as f:
            json.dump(registry, f, indent=2)

        return True
    except Exception as e:
        logger.error(f"Failed to update registry: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(main())
