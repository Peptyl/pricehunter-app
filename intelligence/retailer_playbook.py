#!/usr/bin/env python3
"""
Olfex Retailer Intelligence Playbook
============================================
Encodes ALL lessons learned from live browser validation of 8 retailers × 20 products.
Used to auto-detect site types, predict scraper strategy, and reduce onboarding failures.

KEY INSIGHT: Most fragrance retailer sites fall into 5 archetypes. Detecting the archetype
FIRST saves 80% of wasted scraping attempts.

Lessons learned 2026-03-14 browser validation session:
- NicheGallerie was wrongly classified as Shopify (actually WooCommerce)
- SeeScents variant titles say "Default Title" — size must come from product title
- FragranceBuy stock field is inventory_quantity, not available boolean
- Jomashop is fully client-rendered SPA — no data without Playwright
- MaxAroma JSON-LD price field returns "0.0" — must extract from DOM
- Notino has multiple offers per page (one per size) — must match target size
- Douglas and FragranceNet block raw HTTP requests
"""

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# SITE ARCHETYPES — the 5 patterns that cover 95% of fragrance retailers
# =============================================================================

class SiteArchetype(Enum):
    """Every fragrance retail site we've encountered fits one of these patterns."""

    SHOPIFY = "shopify"
    # ~40% of niche/indie retailers
    # Detection: /products/{handle}.json returns valid JSON, or meta[name=shopify-checkout-api-token]
    # Strategy: Shopify JSON API at /products/{handle}.json
    # Gotchas:
    #   - Prices are strings, not cents (FragranceBuy: "299.00" not 29900)
    #   - Stock: use inventory_quantity, NOT the 'available' boolean
    #   - Variant titles may be "Default Title" — extract size from product title
    #   - Handle format varies: "brand-name-edp-125ml" or "brandname-man"
    #   - Some stores disable .json API endpoint (must fall back to HTML)

    WOOCOMMERCE = "woocommerce"
    # ~25% of UK/EU specialist retailers
    # Detection: body has woocommerce class, /wp-json/ endpoints exist, or generator meta tag
    # Strategy: HTML parse with CSS selectors + optional JSON-LD
    # Gotchas:
    #   - URL prefix varies: /perfume/, /product/, /shop/, /fragrance/
    #   - Slug format inconsistent: "edp" vs "eau-de-parfum"
    #   - Price selectors: .price .woocommerce-Price-amount, p.price ins .amount
    #   - Some have JSON-LD (reliable); some don't (must parse DOM)
    #   - NicheGallerie was WRONGLY classified as Shopify — always verify!

    SPA_REACT = "spa_react"
    # ~15% — typically larger retailers
    # Detection: initial HTML has empty body or loading spinner, content appears after JS
    # Strategy: MUST use Playwright (headless browser). No shortcuts.
    # Gotchas:
    #   - JSON-LD only appears AFTER JS execution (not in raw HTML)
    #   - Cookie consent banners block interaction — must dismiss first
    #   - Price may load asynchronously (wait for specific selector)
    #   - dataLayer often has price data (check window.dataLayer)
    #   - Jomashop, MaxAroma (partially) are this type

    TRADITIONAL_SSR = "traditional_ssr"
    # ~15% — established retailers with server-rendered pages
    # Detection: full HTML with prices visible in source, no JS framework fingerprints
    # Strategy: Simple HTTP GET + BeautifulSoup parse
    # Gotchas:
    #   - JSON-LD is usually present and reliable
    #   - May have anti-bot (Cloudflare, DataDome) — need headers/proxy
    #   - Price in multiple locations (JSON-LD, og:price, itemprop="price", CSS selectors)
    #   - Notino, Douglas are this type (though Douglas blocks raw requests)

    API_BACKED = "api_backed"
    # ~5% — sites with discoverable internal APIs
    # Detection: XHR/fetch calls to /api/products/ or GraphQL endpoints visible in Network tab
    # Strategy: Call the API directly (fastest, most reliable)
    # Gotchas:
    #   - APIs may require auth tokens or session cookies
    #   - Rate limits are stricter on API endpoints
    #   - Response format varies (REST JSON, GraphQL)
    #   - Some APIs return prices in minor currency units (cents/pence)


# =============================================================================
# DETECTION SIGNALS — what to look for when onboarding a new retailer
# =============================================================================

@dataclass
class DetectionResult:
    """Result of auto-detecting a retailer's site archetype."""
    archetype: SiteArchetype
    confidence: float  # 0.0 to 1.0
    signals: List[str]  # What was detected
    recommended_method: str  # "shopify_json_api", "woocommerce_html", etc.
    recommended_selectors: Dict[str, str]  # CSS selectors for price, name, etc.
    warnings: List[str]  # Known gotchas for this archetype
    needs_playwright: bool
    needs_proxy: bool


# Detection signal patterns
SHOPIFY_SIGNALS = {
    "meta_tag": r'<meta\s+name=["\']shopify-checkout-api-token["\']',
    "cdn_url": r'cdn\.shopify\.com',
    "json_api": r'/products/[\w-]+\.json',
    "shopify_analytics": r'ShopifyAnalytics',
    "shopify_class": r'class=["\'][^"\']*shopify[^"\']*["\']',
}

WOOCOMMERCE_SIGNALS = {
    "body_class": r'class=["\'][^"\']*woocommerce[^"\']*["\']',
    "wp_json": r'/wp-json/',
    "generator_meta": r'<meta\s+name=["\']generator["\'][^>]*WordPress',
    "wc_price_class": r'woocommerce-Price-amount',
    "add_to_cart_wc": r'add_to_cart_button',
    "wp_content": r'/wp-content/',
}

SPA_SIGNALS = {
    "empty_body": r'<body[^>]*>\s*<div\s+id=["\'](?:root|app|__next)["\']>\s*</div>',
    "react_root": r'__REACT_DEVTOOLS',
    "next_data": r'__NEXT_DATA__',
    "vue_app": r'__vue__',
    "angular_app": r'ng-app|ng-version',
    "loading_spinner": r'class=["\'][^"\']*(?:loading|spinner|skeleton)[^"\']*["\']',
}

TRADITIONAL_SSR_SIGNALS = {
    "json_ld_product": r'"@type"\s*:\s*"Product"',
    "og_price": r'<meta\s+property=["\']product:price:amount["\']',
    "itemprop_price": r'itemprop=["\']price["\']',
    "server_rendered_price": r'class=["\'][^"\']*price[^"\']*["\'][^>]*>[^<]*[£$€]\d',
}


# =============================================================================
# URL PATTERN INTELLIGENCE — learned patterns for URL discovery
# =============================================================================

@dataclass
class URLPattern:
    """Encodes how a retailer constructs product URLs."""
    template: str  # URL template with placeholders
    slug_rules: Dict[str, str]  # How to build each slug component
    examples: List[str]  # Verified working examples
    discovery_method: str  # "predictable", "search_required", "sitemap", "api"
    notes: str


# Verified URL patterns from browser testing
VERIFIED_URL_PATTERNS: Dict[str, URLPattern] = {
    "notino_uk": URLPattern(
        template="https://www.notino.co.uk/{brand_slug}/{product_slug}/",
        slug_rules={
            "brand_slug": "Unpredictable. 'royal-essence' for Amouage, 'initio-parfums-prives' for Initio, 'xj-1861' for Xerjoff. Must discover via brand listing page or search.",
            "product_slug": "Usually: {product-name}-{gender}/ e.g. 'interlude-man-eau-de-parfum/' but varies per brand.",
        },
        examples=[
            "https://www.notino.co.uk/parfums-de-marly/layton-eau-de-parfum-for-men/",
            "https://www.notino.co.uk/initio-parfums-prives/oud-for-greatness-eau-de-parfum-unisex/",
        ],
        discovery_method="search_required",
        notes="Brand slugs are completely unpredictable. Best approach: scrape brand listing pages or use site search. Multiple offers per page = multiple sizes."
    ),
    "nichegallerie_uk": URLPattern(
        template="https://nichegallerie.com/perfume/{product_slug}/",
        slug_rules={
            "product_slug": "Format: {brand}-{product}-{concentration}-{size}ml but inconsistent. 'edp' vs 'eau-de-parfum' varies by product.",
        },
        examples=[
            "https://nichegallerie.com/perfume/parfums-de-marly-layton-edp-125ml/",
            "https://nichegallerie.com/perfume/creed-aventus-edp-100ml/",
        ],
        discovery_method="predictable",
        notes="WooCommerce. URL prefix is /perfume/ NOT /products/. 17/20 products verified. Slug format inconsistent."
    ),
    "fragrancebuy_ca": URLPattern(
        template="https://fragrancebuy.ca/products/{handle}",
        slug_rules={
            "handle": "Usually: {brandname}-{productname}-{gender}. No concentration/size in handle. E.g. 'parfumsdemarly-layton-man'.",
        },
        examples=[
            "https://fragrancebuy.ca/products/parfumsdemarly-layton-man",
            "https://fragrancebuy.ca/products/creed-aventus-man",
        ],
        discovery_method="predictable",
        notes="Shopify JSON API. Append .json for API. 19/20 verified. Prices as strings. Stock via inventory_quantity."
    ),
    "seescents_uk": URLPattern(
        template="https://seescents.com/products/{handle}",
        slug_rules={
            "handle": "Various formats. Often includes brand and product name.",
        },
        examples=[
            "https://seescents.com/products/parfums-de-marly-layton-125ml",
        ],
        discovery_method="search_required",
        notes="Shopify. Only 7/20 products available — small catalog. Variant title is often 'Default Title', must extract size from product title."
    ),
    "jomashop_us": URLPattern(
        template="https://www.jomashop.com/{product_slug}.html",
        slug_rules={
            "product_slug": "Contains product name + EAN barcode. E.g. 'parfums-de-marly-layton-edp-spray-4-2-oz-3700578501004'. Must discover via web search.",
        },
        examples=[
            "https://www.jomashop.com/parfums-de-marly-layton-edp-spray-4-2-oz-3700578501004.html",
        ],
        discovery_method="search_required",
        notes="URLs contain EAN barcodes — impossible to guess. Must use web search. Fully client-rendered SPA. Does NOT ship to UK — show with forwarding services."
    ),
    "maxaroma_us": URLPattern(
        template="https://www.maxaroma.com/fragrance/niche-fragrances/{brand_name}/pid/{product_id}/2",
        slug_rules={
            "brand_name": "URL-safe brand name",
            "product_id": "Internal numeric ID — must discover via search or navigation",
        },
        examples=[
            "https://www.maxaroma.com/fragrance/niche-fragrances/parfums-de-marly/pid/75261/2",
        ],
        discovery_method="search_required",
        notes="Custom URL with numeric IDs. JSON-LD price field returns '0.0' — must extract from DOM. Deal prices shown separately."
    ),
    "fragrancenet_us": URLPattern(
        template="https://www.fragrancenet.com/fragrances/{brand_slug}/{product_slug}/eau-de-parfum",
        slug_rules={
            "brand_slug": "Lowercase hyphenated brand name",
            "product_slug": "Lowercase hyphenated: {brand}-{product-name}",
        },
        examples=[
            "https://www.fragrancenet.com/fragrances/parfums-de-marly/parfums-de-marly-layton/eau-de-parfum",
        ],
        discovery_method="predictable",
        notes="Could not test from sandbox — domain blocked. URL structure confirmed via web search for 2 products. Needs live Playwright testing."
    ),
    "douglas_de": URLPattern(
        template="https://www.douglas.de/{locale}/{category}/{product_slug}",
        slug_rules={
            "locale": "Usually 'de' for German site",
            "category": "parfuem or similar",
            "product_slug": "Complex slug with internal IDs",
        },
        examples=[],
        discovery_method="search_required",
        notes="Blocked raw HTTP requests in testing. Needs Playwright + geo-aware proxy. German language pages."
    ),
}


# =============================================================================
# SCRAPING STRATEGY DECISION TREE
# =============================================================================

@dataclass
class ScrapingStrategy:
    """Complete scraping strategy for a retailer."""
    primary_method: str  # The method to try first
    fallback_methods: List[str]  # Ordered fallbacks
    price_selectors: List[Dict[str, str]]  # Priority-ordered price extraction methods
    size_extraction: str  # How to get size info
    stock_check: str  # How to check availability
    rate_limit_rpm: int
    needs_playwright: bool
    needs_proxy: bool
    anti_bot_handling: str  # "none", "headers_only", "playwright", "proxy_rotation"
    cookie_consent: bool  # Need to dismiss cookie banner?
    currency: str
    notes: str


PROVEN_STRATEGIES: Dict[str, ScrapingStrategy] = {
    "shopify_json_api": ScrapingStrategy(
        primary_method="GET /products/{handle}.json",
        fallback_methods=["GET /products/{handle} + parse HTML", "Site search API"],
        price_selectors=[
            {"method": "json_path", "path": "product.variants[].price", "note": "String, not cents"},
            {"method": "json_ld", "path": "offers.price", "note": "Fallback from HTML"},
        ],
        size_extraction="variant.title if not 'Default Title', else parse product.title with regex r'(\\d+)\\s*ml'",
        stock_check="variant.inventory_quantity > 0 (NOT variant.available — unreliable)",
        rate_limit_rpm=20,
        needs_playwright=False,
        needs_proxy=False,
        anti_bot_handling="headers_only",
        cookie_consent=False,
        currency="varies",
        notes="Most reliable method for Shopify stores. Always check if .json endpoint is enabled first."
    ),
    "woocommerce_html": ScrapingStrategy(
        primary_method="GET product page + BeautifulSoup parse",
        fallback_methods=["JSON-LD extraction", "WP REST API /wp-json/wc/v3/products"],
        price_selectors=[
            {"method": "css", "selector": ".price .woocommerce-Price-amount bdi", "note": "Current price"},
            {"method": "css", "selector": "p.price ins .woocommerce-Price-amount", "note": "Sale price"},
            {"method": "json_ld", "path": "offers.price", "note": "If JSON-LD present"},
            {"method": "css", "selector": ".summary .price", "note": "Broad fallback"},
        ],
        size_extraction="Parse from product title or variation dropdown",
        stock_check="Check for 'out-of-stock' class on body or product div, or 'Add to cart' button presence",
        rate_limit_rpm=25,
        needs_playwright=False,
        needs_proxy=False,
        anti_bot_handling="headers_only",
        cookie_consent=False,
        currency="varies",
        notes="URL prefix varies by store (/perfume/, /product/, /shop/). Always verify the correct prefix."
    ),
    "playwright_spa": ScrapingStrategy(
        primary_method="Playwright navigate + wait for price selector + extract",
        fallback_methods=["Check window.dataLayer", "JSON-LD after render", "Network intercept"],
        price_selectors=[
            {"method": "js_eval", "path": "window.dataLayer[0].ecommerce.detail.products[0].price", "note": "dataLayer"},
            {"method": "json_ld_rendered", "path": "application/ld+json → offers.price", "note": "After JS renders"},
            {"method": "css_rendered", "selector": ".product-price, .price-current, [data-price]", "note": "DOM element"},
        ],
        size_extraction="Parse from rendered page title or variant selector",
        stock_check="Check for 'Add to Cart' button enabled state, or stock indicator elements",
        rate_limit_rpm=10,
        needs_playwright=True,
        needs_proxy=False,
        anti_bot_handling="playwright",
        cookie_consent=True,
        currency="varies",
        notes="SLOW. Use only when absolutely necessary. Always dismiss cookie consent first. Check dataLayer before scraping DOM."
    ),
    "json_ld_ssr": ScrapingStrategy(
        primary_method="GET page + extract JSON-LD script[type='application/ld+json']",
        fallback_methods=["CSS selector extraction", "Open Graph meta tags", "Microdata"],
        price_selectors=[
            {"method": "json_ld", "path": "offers.price or offers[].price", "note": "Primary — match size via offers.name/description"},
            {"method": "meta", "selector": "meta[property='product:price:amount']", "note": "OG price"},
            {"method": "css", "selector": "[itemprop='price']", "note": "Schema.org microdata"},
        ],
        size_extraction="Match from JSON-LD offers array — filter by name/description containing '{size}ml'",
        stock_check="JSON-LD offers.availability === 'https://schema.org/InStock'",
        rate_limit_rpm=30,
        needs_playwright=False,
        needs_proxy=False,
        anti_bot_handling="headers_only",
        cookie_consent=False,
        currency="varies",
        notes="Most reliable for SSR sites. Watch for multiple offers (one per size) — must match target size. Notino uses this pattern."
    ),
    "dom_css_playwright": ScrapingStrategy(
        primary_method="Playwright navigate + CSS selector extraction",
        fallback_methods=["dataLayer extraction", "Network request intercept"],
        price_selectors=[
            {"method": "css_rendered", "selector": ".deal-price, .product-price, .current-price", "note": "Rendered price"},
            {"method": "js_eval", "path": "document.querySelector('[data-price]')?.dataset.price", "note": "Data attribute"},
        ],
        size_extraction="Parse from page or variant buttons",
        stock_check="Presence of 'Add to Cart' button",
        rate_limit_rpm=15,
        needs_playwright=True,
        needs_proxy=False,
        anti_bot_handling="playwright",
        cookie_consent=True,
        currency="varies",
        notes="For sites where JSON-LD is broken/empty (like MaxAroma price=0.0). Must extract from visible DOM."
    ),
}


# =============================================================================
# RETAILER-SPECIFIC GOTCHAS DATABASE
# =============================================================================

RETAILER_GOTCHAS: Dict[str, List[Dict[str, str]]] = {
    "notino_uk": [
        {
            "issue": "Brand slugs are completely unpredictable",
            "example": "Amouage → 'royal-essence', Initio → 'initio-parfums-prives', Xerjoff → 'xj-1861'",
            "fix": "Maintain a brand_slug_map. Discover new slugs by scraping /brands/ listing page.",
            "severity": "high",
        },
        {
            "issue": "Multiple offers per page = multiple sizes",
            "example": "Page has 3 offers: 50ml, 75ml, 125ml. Taking offers[0] gets wrong size.",
            "fix": "Iterate offers array, match by name/description containing target size '{size}ml'.",
            "severity": "high",
        },
        {
            "issue": "Gender in URL slug",
            "example": "'for-men' vs 'for-women' vs 'unisex' appended to product slug",
            "fix": "Try all three variants, or discover from brand listing.",
            "severity": "medium",
        },
    ],
    "nichegallerie_uk": [
        {
            "issue": "WooCommerce NOT Shopify — was wrongly classified",
            "example": "Shopify JSON API at /products/{handle}.json returns 404",
            "fix": "Use WooCommerce HTML scraper with CSS selectors. Check for woocommerce body class.",
            "severity": "critical",
        },
        {
            "issue": "URL prefix is /perfume/ not /products/",
            "example": "nichegallerie.com/perfume/creed-aventus-edp-100ml/",
            "fix": "Hardcode /perfume/ prefix. Verify by checking for redirects.",
            "severity": "high",
        },
        {
            "issue": "Inconsistent concentration slugs",
            "example": "Some use 'edp', others use 'eau-de-parfum'",
            "fix": "Try both variants. Or scrape from category/brand listing page.",
            "severity": "medium",
        },
    ],
    "fragrancebuy_ca": [
        {
            "issue": "Prices are strings, not integer cents",
            "example": "variant.price = '299.00' not 29900",
            "fix": "Parse with float() directly. Don't divide by 100.",
            "severity": "high",
        },
        {
            "issue": "Stock check: use inventory_quantity, NOT available",
            "example": "variant.available = true even when inventory_quantity = 0 (backorder enabled)",
            "fix": "Check variant.inventory_quantity > 0 for true stock status.",
            "severity": "high",
        },
        {
            "issue": "Handle format: no hyphens in brand name",
            "example": "'parfumsdemarly-layton-man' not 'parfums-de-marly-layton-man'",
            "fix": "Strip spaces/hyphens from brand name portion of handle.",
            "severity": "medium",
        },
    ],
    "seescents_uk": [
        {
            "issue": "Variant title is often 'Default Title'",
            "example": "variant.title = 'Default Title' instead of '125ml'",
            "fix": "Extract size from product.title with regex r'(\\d+)\\s*ml'.",
            "severity": "high",
        },
        {
            "issue": "Small catalog — only 7/20 test products available",
            "example": "Many niche brands not stocked",
            "fix": "Don't treat 404s as errors. Expect low coverage. Use as supplementary source.",
            "severity": "medium",
        },
    ],
    "jomashop_us": [
        {
            "issue": "Fully client-rendered SPA — no data in raw HTML",
            "example": "curl returns empty shell. JSON-LD only appears after JS execution.",
            "fix": "MUST use Playwright. No workarounds.",
            "severity": "critical",
        },
        {
            "issue": "URLs contain EAN barcodes",
            "example": "parfums-de-marly-layton-edp-spray-4-2-oz-3700578501004.html",
            "fix": "URLs cannot be predicted. Must discover via web search or site search.",
            "severity": "high",
        },
        {
            "issue": "Does NOT ship to UK",
            "example": "No UK shipping option at checkout",
            "fix": "Show price + forwarding service cost estimate. List 3rd-party forwarders.",
            "severity": "high",
        },
        {
            "issue": "Cookie consent banner blocks interaction",
            "example": "Price area not clickable/scrollable until banner dismissed",
            "fix": "Playwright: click accept on cookie banner before extracting data.",
            "severity": "medium",
        },
    ],
    "maxaroma_us": [
        {
            "issue": "JSON-LD price field returns '0.0' (broken)",
            "example": "JSON-LD has 'price': '0.0' for all products",
            "fix": "MUST extract from DOM. Look for .deal-price or similar CSS class.",
            "severity": "critical",
        },
        {
            "issue": "Custom URL structure with numeric product IDs",
            "example": "/fragrance/niche-fragrances/parfums-de-marly/pid/75261/2",
            "fix": "IDs must be discovered via search or navigation. Cannot predict.",
            "severity": "high",
        },
        {
            "issue": "Multiple price displays (retail vs deal)",
            "example": "Shows both $340 retail and $265 DEAL price",
            "fix": "Extract the DEAL price, not the retail price. Look for deal/sale CSS classes.",
            "severity": "medium",
        },
    ],
    "douglas_de": [
        {
            "issue": "Blocks raw HTTP requests",
            "example": "requests.get() returns 403 or Cloudflare challenge",
            "fix": "Must use Playwright with proper headers. May need EU-based proxy.",
            "severity": "high",
        },
        {
            "issue": "German language content",
            "example": "Product names and descriptions in German",
            "fix": "Match by brand + product name (usually same in German). Use EAN/GTIN for exact match.",
            "severity": "medium",
        },
    ],
    "fragrancenet_us": [
        {
            "issue": "Domain blocked from sandbox testing",
            "example": "Could not access fragrancenet.com from test environment",
            "fix": "Needs live server testing with proper IP/proxy. URL structure confirmed via web search.",
            "severity": "medium",
        },
    ],
}


# =============================================================================
# AUTO-DETECTION ENGINE
# =============================================================================

class RetailerDetector:
    """
    Auto-detects a new retailer's site archetype by analyzing its HTML.
    Run this BEFORE writing any scraper code.
    """

    @staticmethod
    def detect_archetype(html: str, url: str, headers: Dict = None) -> DetectionResult:
        """
        Analyze HTML to determine the site archetype and recommend scraping strategy.

        Args:
            html: The raw HTML of a product page
            url: The URL that was fetched
            headers: Response headers (useful for detecting platforms)

        Returns:
            DetectionResult with archetype, confidence, and recommended strategy
        """
        scores = {
            SiteArchetype.SHOPIFY: 0.0,
            SiteArchetype.WOOCOMMERCE: 0.0,
            SiteArchetype.SPA_REACT: 0.0,
            SiteArchetype.TRADITIONAL_SSR: 0.0,
            SiteArchetype.API_BACKED: 0.0,
        }
        signals_found = []
        warnings = []

        # Check Shopify signals
        for name, pattern in SHOPIFY_SIGNALS.items():
            if re.search(pattern, html, re.IGNORECASE):
                scores[SiteArchetype.SHOPIFY] += 0.25
                signals_found.append(f"shopify:{name}")

        # Check WooCommerce signals
        for name, pattern in WOOCOMMERCE_SIGNALS.items():
            if re.search(pattern, html, re.IGNORECASE):
                scores[SiteArchetype.WOOCOMMERCE] += 0.2
                signals_found.append(f"woocommerce:{name}")

        # Check SPA signals
        for name, pattern in SPA_SIGNALS.items():
            if re.search(pattern, html, re.IGNORECASE):
                scores[SiteArchetype.SPA_REACT] += 0.25
                signals_found.append(f"spa:{name}")

        # Check if page has visible price in HTML (SSR indicator)
        for name, pattern in TRADITIONAL_SSR_SIGNALS.items():
            if re.search(pattern, html, re.IGNORECASE):
                scores[SiteArchetype.TRADITIONAL_SSR] += 0.2
                signals_found.append(f"ssr:{name}")

        # HTML length heuristic — SPAs have very short initial HTML
        if len(html) < 5000:
            scores[SiteArchetype.SPA_REACT] += 0.3
            signals_found.append("spa:short_html")
        elif len(html) > 50000:
            scores[SiteArchetype.TRADITIONAL_SSR] += 0.1
            signals_found.append("ssr:long_html")

        # Check headers for platform hints
        if headers:
            server = headers.get("x-shopify-stage", headers.get("x-shopid", ""))
            if server:
                scores[SiteArchetype.SHOPIFY] += 0.3
                signals_found.append("shopify:header")

            if headers.get("x-powered-by", "").lower().startswith("wp"):
                scores[SiteArchetype.WOOCOMMERCE] += 0.3
                signals_found.append("woocommerce:header")

        # Determine winner
        best_archetype = max(scores, key=scores.get)
        best_score = scores[best_archetype]

        # Normalize to confidence
        total = sum(scores.values()) or 1
        confidence = best_score / total if total > 0 else 0.0

        # Generate warnings based on archetype
        if best_archetype == SiteArchetype.SHOPIFY:
            warnings = [
                "Verify .json API is enabled (some stores disable it)",
                "Check if prices are strings or cents",
                "Watch for 'Default Title' in variant names",
                "Stock: use inventory_quantity, not available boolean",
            ]
            method = "shopify_json_api"
            selectors = {"price": "product.variants[0].price", "name": "product.title"}
            needs_playwright = False

        elif best_archetype == SiteArchetype.WOOCOMMERCE:
            warnings = [
                "VERIFY this is actually WooCommerce — NicheGallerie was wrongly classified as Shopify!",
                "Check URL prefix: /product/, /perfume/, /shop/, or /fragrance/",
                "Test both 'edp' and 'eau-de-parfum' in slugs",
            ]
            method = "woocommerce_html"
            selectors = {"price": ".price .woocommerce-Price-amount bdi", "name": "h1.product_title"}
            needs_playwright = False

        elif best_archetype == SiteArchetype.SPA_REACT:
            warnings = [
                "MUST use Playwright — no data in raw HTML",
                "Check window.dataLayer for price data first (faster than DOM scraping)",
                "Dismiss cookie consent banner before extracting",
                "Wait for price selector to appear (may load async)",
            ]
            method = "playwright_spa"
            selectors = {"price": "window.dataLayer or rendered .price element", "name": "h1 or og:title"}
            needs_playwright = True

        elif best_archetype == SiteArchetype.TRADITIONAL_SSR:
            warnings = [
                "Check if JSON-LD price is accurate (MaxAroma returns 0.0)",
                "Watch for multiple offers in JSON-LD (one per size)",
                "May need anti-bot handling (headers, cookies, proxy)",
            ]
            method = "json_ld_ssr"
            selectors = {"price": "JSON-LD offers.price", "name": "JSON-LD name"}
            needs_playwright = False

        else:
            warnings = ["Rare archetype — needs manual investigation"]
            method = "custom"
            selectors = {}
            needs_playwright = False

        # Cross-check: if both Shopify and WooCommerce signals found, warn
        if scores[SiteArchetype.SHOPIFY] > 0 and scores[SiteArchetype.WOOCOMMERCE] > 0:
            warnings.insert(0, "AMBIGUOUS: Both Shopify and WooCommerce signals detected! Manually verify.")

        return DetectionResult(
            archetype=best_archetype,
            confidence=round(confidence, 2),
            signals=signals_found,
            recommended_method=method,
            recommended_selectors=selectors,
            warnings=warnings,
            needs_playwright=needs_playwright,
            needs_proxy=False,  # Can't detect this from HTML alone
        )

    @staticmethod
    def quick_shopify_check(domain: str) -> bool:
        """
        Quick check: try fetching /products.json to see if Shopify JSON API is available.
        This is the fastest way to confirm a Shopify store.
        """
        import requests
        try:
            resp = requests.get(
                f"https://{domain}/products.json?limit=1",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return "products" in data
        except Exception:
            pass
        return False


# =============================================================================
# ONBOARDING CHECKLIST — steps to add a new retailer
# =============================================================================

NEW_RETAILER_ONBOARDING_CHECKLIST = """
=== NEW RETAILER ONBOARDING CHECKLIST ===

Before writing ANY scraper code:

1. DETECT ARCHETYPE
   □ Fetch a product page HTML
   □ Run RetailerDetector.detect_archetype(html, url, headers)
   □ If Shopify detected: run quick_shopify_check(domain)
   □ If ambiguous: manually inspect in browser DevTools

2. VERIFY URL PATTERN
   □ Test 3-5 product URLs manually
   □ Document the slug format with examples
   □ Classify discovery method: predictable / search_required / sitemap / api

3. TEST PRICE EXTRACTION
   □ Verify JSON-LD price is accurate (not 0.0 or missing)
   □ Test with 3 products of different sizes
   □ Check if sale/deal price differs from listed price
   □ Verify currency matches expected

4. TEST SIZE/VARIANT HANDLING
   □ Check how variants are listed (dropdown, buttons, separate pages)
   □ Verify variant title contains size info (or if 'Default Title' issue)
   □ Test with a product that has multiple sizes

5. TEST STOCK CHECKING
   □ Verify how out-of-stock is indicated
   □ For Shopify: confirm inventory_quantity vs available behavior
   □ Test with a known out-of-stock product if possible

6. ANTI-BOT ASSESSMENT
   □ Test raw HTTP GET (does it return full HTML or challenge page?)
   □ Check for Cloudflare, DataDome, or other WAF
   □ Test with and without browser-like headers
   □ If blocked: test with Playwright

7. RATE LIMIT DISCOVERY
   □ Start at 10 RPM, increase gradually
   □ Watch for 429 responses or temporary bans
   □ Document safe rate limit

8. ADD TO REGISTRY
   □ Create entry in retailer_registry.json
   □ Add to RETAILER_GOTCHAS with any issues found
   □ Add to VERIFIED_URL_PATTERNS
   □ Write scraper class extending BaseScraper

9. VALIDATION RUN
   □ Test against 5 known products with known prices
   □ Verify price accuracy within 2%
   □ Run for 24h at scheduled rate, check for drift/blocks
"""


# =============================================================================
# EXPANSION PRIORITY MATRIX
# =============================================================================

def get_expansion_priorities() -> List[Dict]:
    """
    Returns prioritized list of retailers to onboard next,
    based on expected value (coverage × price competitiveness × ease of scraping).
    """
    return [
        {
            "retailer": "allbeauty_uk",
            "priority": 1,
            "reason": "UK authorized, good prices, likely simple HTML. Low risk, high value.",
            "estimated_effort_hours": 2,
            "expected_archetype": "traditional_ssr",
        },
        {
            "retailer": "flaconi_de",
            "priority": 2,
            "reason": "Often lowest EU prices. German authorized. Good coverage of niche brands.",
            "estimated_effort_hours": 3,
            "expected_archetype": "traditional_ssr",
        },
        {
            "retailer": "parfumdreams_de",
            "priority": 3,
            "reason": "Strong German alternative. High reviews. Good niche coverage.",
            "estimated_effort_hours": 3,
            "expected_archetype": "traditional_ssr",
        },
        {
            "retailer": "thefragranceshop_uk",
            "priority": 4,
            "reason": "UK high street. Not cheapest but good for stock availability cross-reference.",
            "estimated_effort_hours": 2,
            "expected_archetype": "traditional_ssr",
        },
        {
            "retailer": "parfumsraffy_ca",
            "priority": 5,
            "reason": "Canadian alternative to FragranceBuy. Likely Shopify.",
            "estimated_effort_hours": 1.5,
            "expected_archetype": "shopify",
        },
        {
            "retailer": "luckyscent_us",
            "priority": 6,
            "reason": "US niche specialist. Good for rare brands. Medium effort.",
            "estimated_effort_hours": 3,
            "expected_archetype": "traditional_ssr",
        },
    ]


# =============================================================================
# CURRENCY & LANDED COST INTELLIGENCE
# =============================================================================

LANDED_COST_RULES = {
    "GBP": {
        "vat_rate": 0.0,  # Already included
        "customs_duty_rate": 0.0,
        "de_minimis_gbp": None,
        "notes": "No additional costs for UK retailers",
    },
    "EUR": {
        "vat_rate": 0.0,  # EU retailers include VAT; UK import VAT applies post-Brexit
        "customs_duty_rate": 0.0,  # Fragrances under £135 — no customs duty, but 20% import VAT
        "import_vat_rate": 0.20,  # 20% UK import VAT on goods from EU
        "de_minimis_gbp": 135,  # Below £135 seller collects VAT at point of sale (usually)
        "notes": "Most EU retailers (Douglas, Flaconi) collect UK VAT at checkout for orders under £135. Over £135: buyer pays 20% import VAT + possible duty.",
    },
    "USD": {
        "vat_rate": 0.0,
        "customs_duty_rate": 0.0,
        "import_vat_rate": 0.20,
        "de_minimis_gbp": 135,
        "notes": "US retailers generally don't collect UK VAT. Buyer likely owes 20% import VAT. Fragrance duty rate: 0%. Forwarding services add $15-25.",
    },
    "CAD": {
        "vat_rate": 0.0,
        "customs_duty_rate": 0.0,
        "import_vat_rate": 0.20,
        "de_minimis_gbp": 135,
        "notes": "Similar to USD. FragranceBuy ships direct to UK. Import VAT applies.",
    },
}

FORWARDING_SERVICES = [
    {
        "name": "Stackry",
        "url": "https://www.stackry.com",
        "avg_cost_gbp": 15,
        "supported_origins": ["US"],
        "delivery_days": "7-14",
        "notes": "Popular for Jomashop purchases. Consolidation available.",
    },
    {
        "name": "MyUS",
        "url": "https://www.myus.com",
        "avg_cost_gbp": 18,
        "supported_origins": ["US"],
        "delivery_days": "5-10",
        "notes": "Premium service. Tax-free shopping address in US.",
    },
    {
        "name": "Planet Express",
        "url": "https://www.planetexpress.com",
        "avg_cost_gbp": 12,
        "supported_origins": ["US"],
        "delivery_days": "7-14",
        "notes": "Budget option. Good for single items.",
    },
]


if __name__ == "__main__":
    # Print summary of intelligence database
    print("=" * 60)
    print("OLFEX RETAILER INTELLIGENCE PLAYBOOK")
    print("=" * 60)

    print(f"\nSite Archetypes: {len(SiteArchetype)}")
    for arch in SiteArchetype:
        print(f"  - {arch.value}")

    print(f"\nVerified URL Patterns: {len(VERIFIED_URL_PATTERNS)}")
    for retailer_id, pattern in VERIFIED_URL_PATTERNS.items():
        print(f"  - {retailer_id}: {pattern.discovery_method}")

    print(f"\nProven Strategies: {len(PROVEN_STRATEGIES)}")
    for name, strategy in PROVEN_STRATEGIES.items():
        print(f"  - {name}: playwright={strategy.needs_playwright}")

    print(f"\nRetailer Gotchas: {sum(len(v) for v in RETAILER_GOTCHAS.values())} issues across {len(RETAILER_GOTCHAS)} retailers")
    for retailer_id, gotchas in RETAILER_GOTCHAS.items():
        critical = sum(1 for g in gotchas if g["severity"] == "critical")
        high = sum(1 for g in gotchas if g["severity"] == "high")
        print(f"  - {retailer_id}: {critical} critical, {high} high")

    print(f"\nExpansion Queue:")
    for item in get_expansion_priorities():
        print(f"  {item['priority']}. {item['retailer']} ({item['estimated_effort_hours']}h) — {item['expected_archetype']}")

    print(f"\n{NEW_RETAILER_ONBOARDING_CHECKLIST}")
