"""
Retailer Intelligence System
=============================
Encodes hard-won knowledge about each retailer's platform, URL patterns,
price extraction methods, gotchas, and failure modes.

This is Olfex's MOAT — the knowledge base that makes scraping
work reliably across diverse e-commerce platforms.

Usage:
    intel = RetailerIntelligence()
    profile = intel.get_profile("fragrancebuy")
    strategy = intel.recommend_strategy("nichegallerie")
    url = intel.build_product_url("notino", brand="Parfums de Marly", name="Layton", size_ml=125)
"""

import re
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# PLATFORM TYPES — What kind of e-commerce platform is the retailer running?
# ============================================================================

class PlatformType(Enum):
    SHOPIFY = "shopify"               # FragranceBuy, SeeScents
    WOOCOMMERCE = "woocommerce"       # NicheGallerie
    CUSTOM_SSR = "custom_ssr"         # Notino (server-rendered, JSON-LD)
    CUSTOM_SPA = "custom_spa"         # Jomashop, MaxAroma (JS-rendered)
    MAGENTO = "magento"               # FragranceNet (likely)
    UNKNOWN = "unknown"


class ScrapingStrategy(Enum):
    SHOPIFY_JSON_API = "shopify_json"       # /products/{handle}.json
    WOOCOMMERCE_HTML = "woocommerce_html"   # Parse HTML + JSON-LD
    JSON_LD = "json_ld"                     # Schema.org structured data
    PLAYWRIGHT = "playwright"               # Full headless browser
    DOM_CSS = "dom_css"                     # CSS selector extraction
    API = "api"                             # Direct API (if available)


class PriceFormat(Enum):
    STRING_DECIMAL = "string_decimal"  # "149.00" — Shopify storefront
    INTEGER_CENTS = "integer_cents"    # 14900 — Shopify search/admin
    FLOAT = "float"                    # 149.0 — JSON-LD
    HTML_CURRENCY = "html_currency"    # "£149.00" — DOM text


# ============================================================================
# RETAILER PROFILE — Everything we know about scraping a retailer
# ============================================================================

@dataclass
class RetailerProfile:
    """Complete intelligence profile for a retailer"""
    id: str
    domain: str
    platform: PlatformType
    currency: str
    country: str

    # Scraping strategy
    primary_strategy: ScrapingStrategy
    fallback_strategy: Optional[ScrapingStrategy] = None

    # URL patterns
    url_pattern: str = ""                          # Template with {brand}, {name}, {size}
    url_slug_rules: Dict[str, str] = field(default_factory=dict)  # How to build slugs
    url_discovery_method: str = ""                 # How to find URLs for new products

    # Price extraction
    price_format: PriceFormat = PriceFormat.FLOAT
    price_selector: str = ""                       # CSS selector or JSON path
    price_gotchas: List[str] = field(default_factory=list)

    # Size/variant matching
    variant_strategy: str = ""                     # How variants work on this site
    variant_gotchas: List[str] = field(default_factory=list)

    # Stock detection
    stock_method: str = ""
    stock_gotchas: List[str] = field(default_factory=list)

    # Anti-bot / rate limiting
    rate_limit_rpm: int = 20
    needs_playwright: bool = False
    needs_proxy: bool = False
    bot_detection: str = "none"                    # none, cloudflare, custom

    # Brand coverage
    brands_available: List[str] = field(default_factory=list)   # Brands we know they carry
    brands_unavailable: List[str] = field(default_factory=list) # Brands confirmed NOT carried

    # Lessons learned
    lessons: List[str] = field(default_factory=list)
    last_verified: str = ""


# ============================================================================
# THE KNOWLEDGE BASE — Hard-won retailer intelligence
# ============================================================================

RETAILER_PROFILES: Dict[str, RetailerProfile] = {

    # ========================================================================
    # FRAGRANCEBUY (Shopify — our most reliable scraper)
    # ========================================================================
    "fragrancebuy": RetailerProfile(
        id="fragrancebuy",
        domain="fragrancebuy.ca",
        platform=PlatformType.SHOPIFY,
        currency="CAD",
        country="CA",
        primary_strategy=ScrapingStrategy.SHOPIFY_JSON_API,

        url_pattern="https://fragrancebuy.ca/products/{handle}",
        url_slug_rules={
            "format": "lowercase, no spaces, brand+name concatenated",
            "examples": {
                "Parfums de Marly Layton": "parfumsdemarlylayton-man",
                "Creed Aventus": "creedaventus-man",
                "Tom Ford Tuscan Leather": "tomfordtuscanleather-man",
                "Tom Ford Oud Wood": "tomfordoudwood-man",
                "MFK Baccarat Rouge 540": "franciskurkdjian540baccaratrouge-man",
                "Le Labo Santal 33": "lelabosantal-man",
                "Byredo Mojave Ghost": "byredomojaveghost-man",
                "Initio Oud for Greatness": "initiooudforgreatness-man",
                "Xerjoff Naxos": "xerjoff1861naxos-man",
            },
            "pattern_notes": "Generally: brand+name (no spaces) + '-man' suffix for men's. "
                           "Some unisex have '-man' too. Check Shopify search API to discover.",
        },
        url_discovery_method="Shopify search API: /search/suggest.json?q={brand+name}&resources[type]=product",

        price_format=PriceFormat.STRING_DECIMAL,
        price_selector="variant.price (string like '299.00')",
        price_gotchas=[
            "Shopify storefront JSON returns prices as STRINGS like '299.00' — NOT cents",
            "Shopify SEARCH API returns prices in CENTS (e.g., 29900) — different format!",
            "Always use float(variant['price']), never divide by 100",
        ],

        variant_strategy="Variants have titles like '125ml / 4.2oz'. Match by extracting size from title.",
        variant_gotchas=[
            "Some products have only 1 variant — take it",
            "Variant titles may include oz AND ml — extract ml specifically",
        ],

        stock_method="inventory_quantity + inventory_policy",
        stock_gotchas=[
            "The 'available' field may be UNDEFINED on some variants",
            "Use: in_stock = inventory_quantity > 0 or inventory_policy == 'continue'",
            "DO NOT rely on variant.available — it can be missing",
        ],

        rate_limit_rpm=15,
        needs_playwright=False,
        bot_detection="none",

        brands_available=["Parfums de Marly", "Creed", "Tom Ford", "MFK", "Amouage",
                         "Initio", "Xerjoff", "Le Labo", "Byredo"],
        brands_unavailable=[],

        lessons=[
            "19/20 of our top products verified — excellent coverage",
            "Shopify JSON API is the most reliable extraction method",
            "2-second delay between requests is respectful and avoids blocks",
            "Handle slug format: generally brandname-man (no spaces in brand)",
        ],
        last_verified="2026-03-14",
    ),

    # ========================================================================
    # NICHEGALLERIE (WooCommerce — NOT Shopify!)
    # ========================================================================
    "nichegallerie": RetailerProfile(
        id="nichegallerie",
        domain="nichegallerie.com",
        platform=PlatformType.WOOCOMMERCE,
        currency="GBP",
        country="UK",
        primary_strategy=ScrapingStrategy.WOOCOMMERCE_HTML,
        fallback_strategy=ScrapingStrategy.JSON_LD,

        url_pattern="https://nichegallerie.com/perfume/{slug}/",
        url_slug_rules={
            "format": "lowercase, hyphens, brand-name-concentration-size",
            "examples": {
                "PDM Layton 125ml EDP": "parfums-de-marly-layton-eau-de-parfum-125ml",
                "PDM Carlisle 125ml EDP": "parfums-de-marly-carlisle-edp-125ml",
                "Creed Aventus 100ml EDP": "creed-aventus-edp-100ml",
                "Tom Ford Tuscan Leather 100ml": "tom-ford-tuscan-leather-edp-100ml",
                "Tom Ford Oud Wood 100ml": "tom-ford-oud-wood-eau-de-parfum-100ml",
                "MFK BR540 70ml": "maison-francis-kurkdjian-baccarat-rouge-540-edp-70ml",
                "Initio OFG 90ml": "initio-parfums-prives-oud-for-greatness-edp-90ml",
            },
            "pattern_notes": "URL uses /perfume/ prefix (NOT /products/). "
                           "Slug inconsistent: sometimes 'edp', sometimes 'eau-de-parfum'. "
                           "Always includes size in ml. Must probe multiple patterns.",
        },
        url_discovery_method="HEAD request probing with multiple slug variations. "
                            "Try: brand-name-edp-{size}ml, brand-name-eau-de-parfum-{size}ml",

        price_format=PriceFormat.HTML_CURRENCY,
        price_selector="JSON-LD Product.offers.price OR <p class='price'> OR regex £(\\d+)",
        price_gotchas=[
            "THIS IS NOT SHOPIFY — the /products/{handle}.json endpoint does NOT exist",
            "WooCommerce outputs JSON-LD structured data — use that first",
            "Fallback: parse <p class='price'> with £ regex",
            "Some products (Creed Aventus, Xerjoff Erba Pura) had price regex failures — "
            "may need WooCommerce-specific <span class='woocommerce-Price-amount'> selector",
            "MFK BR540 showed £96 which seems low — verify manually (may be sample/decant)",
        ],

        variant_strategy="WooCommerce may have variant dropdowns. Most products are single-variant.",
        variant_gotchas=[
            "Size is encoded in the URL/product title, not in variant selectors",
            "Extract size from URL slug or product title, not from variant data",
        ],

        stock_method="JSON-LD offers.availability contains 'InStock' or 'OutOfStock'",
        stock_gotchas=[],

        rate_limit_rpm=25,
        needs_playwright=False,
        bot_detection="none",

        brands_available=["Parfums de Marly", "Creed", "Tom Ford", "MFK", "Amouage",
                         "Initio", "Xerjoff", "Le Labo", "Byredo"],
        brands_unavailable=[],

        lessons=[
            "CRITICAL: Originally assumed Shopify — wasted hours before discovering it's WooCommerce",
            "WordPress/Elementor site with WooCommerce commerce layer",
            "17/20 products found — 3 missing (TF Tobacco Vanille, MFK Grand Soir, Xerjoff Naxos)",
            "URL slugs are inconsistent between 'edp' and 'eau-de-parfum' — must try both",
            "HEAD requests work for URL discovery — 200 = exists, 404 = not found",
            "Prices are in GBP, no currency conversion needed",
        ],
        last_verified="2026-03-14",
    ),

    # ========================================================================
    # SEESCENTS (Shopify — small inventory, "Default Title" gotcha)
    # ========================================================================
    "seescents": RetailerProfile(
        id="seescents",
        domain="seescents.com",
        platform=PlatformType.SHOPIFY,
        currency="GBP",
        country="UK",
        primary_strategy=ScrapingStrategy.SHOPIFY_JSON_API,

        url_pattern="https://seescents.com/products/{handle}",
        url_slug_rules={
            "format": "lowercase, hyphens, brand-name[-size]",
            "examples": {
                "PDM Layton": "parfums-de-marly-layton",
                "PDM Carlisle 125ml": "parfums-de-marly-carlisle-125ml",
                "PDM Herod 125ml": "parfums-de-marly-herod-125ml",
                "Creed Aventus": "creed-aventus",
                "Initio Side Effect 90ml": "initio-side-effect-90ml",
                "Xerjoff Naxos 100ml": "xerjoff-naxos-100ml",
                "TF Tobacco Vanille 100ml": "tom-ford-tobacco-vanille-100ml-eau-de-parfum-black-friday",
            },
            "pattern_notes": "Inconsistent: some have size, some don't, some have promo suffixes. "
                           "Use Shopify search API to discover correct handles.",
        },
        url_discovery_method="Shopify search API: /search/suggest.json?q={brand+name}",

        price_format=PriceFormat.STRING_DECIMAL,
        price_selector="variant.price (string like '225.00')",
        price_gotchas=[
            "Same Shopify format as FragranceBuy — prices are strings, NOT cents",
        ],

        variant_strategy="Often single variant. Variant title frequently 'Default Title'.",
        variant_gotchas=[
            "CRITICAL: SeeScents often uses 'Default Title' as variant title",
            "When variant title is 'Default Title', extract size from PRODUCT TITLE instead",
            "Fallback chain: variant title → product title → URL slug",
        ],

        stock_method="inventory_quantity + inventory_policy (same as FragranceBuy)",
        stock_gotchas=[
            "Same issue as FragranceBuy: 'available' field may be missing",
            "Use inventory_quantity > 0 || inventory_policy == 'continue'",
        ],

        rate_limit_rpm=25,
        needs_playwright=False,
        bot_detection="none",

        brands_available=["Parfums de Marly", "Creed", "Initio", "Xerjoff", "Tom Ford"],
        brands_unavailable=["MFK", "Amouage", "Le Labo", "Byredo"],

        lessons=[
            "Small inventory — only 7/20 of our products available",
            "Domain is seescents.com (NOT seescents.co.uk — that was wrong initially)",
            "Very competitive UK pricing on what they do carry",
            "Promo suffixes in handles (e.g., '-black-friday') make URL prediction unreliable",
            "Must use Shopify search API for URL discovery, not URL guessing",
        ],
        last_verified="2026-03-14",
    ),

    # ========================================================================
    # NOTINO (Custom SSR — JSON-LD works, tricky URL slugs)
    # ========================================================================
    "notino": RetailerProfile(
        id="notino",
        domain="notino.co.uk",
        platform=PlatformType.CUSTOM_SSR,
        currency="GBP",
        country="UK",
        primary_strategy=ScrapingStrategy.JSON_LD,

        url_pattern="https://www.notino.co.uk/{brand-slug}/{product-slug}/",
        url_slug_rules={
            "format": "/{brand-slug}/{product-name-gender-slug}/",
            "examples": {
                "PDM Layton": "parfums-de-marly/layton-royal-essence-eau-de-parfum-unisex",
                "PDM Carlisle": "parfums-de-marly/carlisle-eau-de-parfum-unisex",
                "PDM Pegasus": "parfums-de-marly/pegasus-royal-essence-eau-de-parfum-unisex",
                "PDM Herod": "parfums-de-marly/herod-royal-essence-eau-de-parfum-for-men",
                "Creed Aventus": "creed/aventus-eau-de-parfum-for-men",
                "Creed GIT": "creed/green-irish-tweed-eau-de-parfum-for-men",
                "TF Tuscan Leather": "tom-ford/tuscan-leather-eau-de-parfum-unisex",
                "Amouage Reflection": "amouage/reflection-eau-de-parfum-for-men",
                "Initio OFG": "initio-parfums-prives/oud-for-greatness-eau-de-parfum-unisex",
                "Xerjoff Naxos": "xerjoff/xj-1861-naxos-eau-de-parfum-unisex",
                "Xerjoff Erba Pura": "xerjoff/erba-pura-eau-de-parfum-unisex",
                "Byredo Mojave Ghost": "byredo/mojave-ghost-eau-de-parfum-unisex",
            },
            "pattern_notes": "URL slugs are UNPREDICTABLE. Key gotchas: "
                           "1) PDM uses 'royal-essence' in slug (not in product name) "
                           "2) Initio brand slug is 'initio-parfums-prives' (full legal name) "
                           "3) Xerjoff Naxos has 'xj-1861-' prefix "
                           "4) Gender suffix: '-for-men', '-unisex', '-for-women-and-men' varies "
                           "5) Some use 'eau-de-parfum', some don't. "
                           "BEST APPROACH: Navigate to brand page and extract product URLs from DOM.",
        },
        url_discovery_method="Navigate to brand page (e.g., /parfums-de-marly/) and extract product links. "
                            "Search page (/search/?q=...) is JS-rendered and may not work with fetch().",

        price_format=PriceFormat.FLOAT,
        price_selector="JSON-LD Product.offers[].price",
        price_gotchas=[
            "Multiple offers in JSON-LD = different sizes. MUST match target size.",
            "Old code took offers[0] which was the SMALLEST/CHEAPEST variant (e.g., 1ml sample)",
            "Match by: extracting size from offer.name/description, find closest to target_size",
            "If no size match, take the MOST EXPENSIVE offer (likely the largest full bottle)",
            "Tom Ford products show 'sorry' page when out of stock — JSON-LD returns £3.49 (sample)",
        ],

        variant_strategy="Size variants are in JSON-LD offers array, not in DOM selectors.",
        variant_gotchas=[
            "Each size is a separate 'offer' in the JSON-LD, not a variant selector",
            "Must parse offer.name or offer.description for size matching",
        ],

        stock_method="Page shows 'sorry that you haven't found' message when out of stock",
        stock_gotchas=[
            "Out-of-stock products return HTTP 200 but show apology message",
            "Check HTML for 'sorry that you haven' or 'We are sorry' to detect OOS",
            "JSON-LD may still return a price (sample/travel size) even when main size is OOS",
        ],

        rate_limit_rpm=30,
        needs_playwright=False,
        bot_detection="moderate",

        brands_available=["Parfums de Marly", "Creed", "Amouage", "Initio", "Xerjoff", "Byredo"],
        brands_unavailable=["MFK", "Le Labo", "Tom Ford (out of stock UK, March 2026)"],

        lessons=[
            "ALL original catalog URLs were wrong — URL format is completely non-standard",
            "PDM has 'royal-essence' in URL slugs that isn't in any product name",
            "Initio brand slug uses full legal name 'initio-parfums-prives'",
            "Xerjoff Naxos has 'xj-1861-' prefix in slug",
            "Notino UK doesn't carry MFK or Le Labo brands AT ALL",
            "Tom Ford was all showing 'sorry' (out of stock) at time of validation",
            "14/20 products verified with real prices — solid UK retailer for non-niche-exclusive brands",
            "Search page is JS-rendered — can't extract from fetch(), must use DOM after navigation",
        ],
        last_verified="2026-03-14",
    ),

    # ========================================================================
    # JOMASHOP (Custom SPA — Playwright required)
    # ========================================================================
    "jomashop": RetailerProfile(
        id="jomashop",
        domain="jomashop.com",
        platform=PlatformType.CUSTOM_SPA,
        currency="USD",
        country="US",
        primary_strategy=ScrapingStrategy.PLAYWRIGHT,
        fallback_strategy=ScrapingStrategy.JSON_LD,  # Available AFTER JS rendering

        url_pattern="https://www.jomashop.com/{product-slug}.html",
        url_slug_rules={
            "format": "brand-gender-name-type-size-barcode.html",
            "examples": {
                "PDM Layton 125ml": "parfums-de-marly-mens-layton-edp-spray-4-2-oz-fragrances-3700578518002",
                "PDM Carlisle 125ml": "parfums-de-marly-unisex-carlisle-edp-spray-4-2-oz-fragrances-3700578519009",
                "Creed Aventus 100ml": "creed-fragrances-cavmes33b-3-3oz",
                "Initio OFG 90ml": "initio-parfums-prives-oud-for-greatness-eau-de-parfum-spray-90ml-3701415900080",
            },
            "pattern_notes": "URL slugs include EAN/barcode numbers — completely unpredictable. "
                           "MUST use web search (site:jomashop.com + product name) to find URLs. "
                           "Two URL formats: old (product-code.html) and new (descriptive-barcode.html). "
                           "Same product can have multiple URLs (tester, event, etc.).",
        },
        url_discovery_method="Web search: site:jomashop.com '{brand}' '{name}' edp {size}ml",

        price_format=PriceFormat.FLOAT,
        price_selector="JSON-LD Product.offers.price (after JS render) OR dataLayer[].ecommerce.detail.products[].price",
        price_gotchas=[
            "Page is fully client-side rendered — fetch() returns empty shell with NO data",
            "JSON-LD and dataLayer are only available AFTER JavaScript execution",
            "Must use Playwright or equivalent headless browser",
            "Multiple size variants shown as clickable tabs (e.g., '4.2 oz / 125 ml $360.00')",
            "Prices in USD — need currency conversion for UK users",
        ],

        variant_strategy="Size variants are clickable tabs in the product page. "
                        "dataLayer contains the currently selected variant price.",
        variant_gotchas=[
            "Default selected variant may not be the target size",
            "Tester versions have different prices — watch for 'Tester' in product title",
        ],

        stock_method="'Add To Bag' button present = in stock",
        stock_gotchas=[
            "'Limited Quantity' badge shown when stock is low",
        ],

        rate_limit_rpm=15,
        needs_playwright=True,
        bot_detection="moderate",

        brands_available=["Parfums de Marly", "Creed", "Tom Ford", "MFK", "Amouage",
                         "Initio", "Xerjoff", "Le Labo", "Byredo"],
        brands_unavailable=[],

        lessons=[
            "All 20 products found — best coverage of any US retailer",
            "Must use web search to find URLs — slug format includes barcodes, unpredictable",
            "Playwright is mandatory — no data in raw HTML fetch",
            "Cookie banner blocks page — need to dismiss or wait",
            "JSON-LD appears after JS renders — use that for structured price extraction",
            "Does NOT ship to UK — requires freight forwarder",
            "PDM Layton verified at $360.00 (125ml) from rendered page",
        ],
        last_verified="2026-03-14",
    ),

    # ========================================================================
    # MAXAROMA (Custom SPA — JSON-LD broken, DOM required)
    # ========================================================================
    "maxaroma": RetailerProfile(
        id="maxaroma",
        domain="maxaroma.com",
        platform=PlatformType.CUSTOM_SPA,
        currency="USD",
        country="US",
        primary_strategy=ScrapingStrategy.DOM_CSS,

        url_pattern="https://www.maxaroma.com/fragrance/niche-fragrances/{brand-slug}/pid/{product-id}/2",
        url_slug_rules={
            "format": "/fragrance/niche-fragrances/{brand-name-hyphenated}/pid/{numeric-id}/2",
            "examples": {
                "PDM Layton": "parfums-de-marly-layton/pid/14225/2",
                "PDM Carlisle": "parfums-de-marly-carlisle/pid/14221/2",
                "PDM Pegasus": "parfums-de-marly-pegasus/pid/14226/2",
                "PDM Herod": "parfums-de-marly-herod/pid/14223/2",
            },
            "pattern_notes": "PDM products use /fragrance/niche-fragrances/ prefix with numeric IDs. "
                           "Other brands may use different URL structures. "
                           "Web search needed for non-PDM products.",
        },
        url_discovery_method="Web search: site:maxaroma.com '{brand}' '{name}' {size}ml",

        price_format=PriceFormat.HTML_CURRENCY,
        price_selector="DOM elements with class containing 'price' — look for 'DEAL: $XXX'",
        price_gotchas=[
            "JSON-LD Product.offers.price returns '0.0' — COMPLETELY BROKEN",
            "Must extract price from rendered DOM, not from structured data",
            "Multiple prices visible: RRP (strikethrough), deal price, other sizes",
            "Look for elements with 'DEAL:' prefix for the actual selling price",
            "PDM Layton showed $265 deal price (vs $380 RRP) on validation day",
        ],

        variant_strategy="Size variants listed with prices in the page",
        variant_gotchas=[],

        stock_method="Check for 'Add to Cart' or 'Sold Out' button",
        stock_gotchas=[],

        rate_limit_rpm=20,
        needs_playwright=True,  # DOM extraction needed
        bot_detection="low",

        brands_available=["Parfums de Marly", "Creed", "Tom Ford", "MFK", "Amouage",
                         "Initio", "Xerjoff", "Le Labo", "Byredo"],
        brands_unavailable=[],

        lessons=[
            "JSON-LD is BROKEN — always returns price: 0.0",
            "Must use DOM/CSS selectors or Playwright for price extraction",
            "Good product coverage but unreliable structured data",
            "URL structure varies by brand — some use /fragrance/niche-fragrances/, others don't",
        ],
        last_verified="2026-03-14",
    ),

    # ========================================================================
    # FRAGRANCENET (likely Magento — blocked from sandbox testing)
    # ========================================================================
    "fragrancenet": RetailerProfile(
        id="fragrancenet",
        domain="fragrancenet.com",
        platform=PlatformType.UNKNOWN,
        currency="USD",
        country="US",
        primary_strategy=ScrapingStrategy.JSON_LD,
        fallback_strategy=ScrapingStrategy.PLAYWRIGHT,

        url_pattern="https://www.fragrancenet.com/fragrances/{brand}/{product-name}/eau-de-parfum",
        url_slug_rules={
            "format": "/fragrances/{brand-slug}/{brand-product-name}/eau-de-parfum",
            "examples": {
                "PDM Layton": "parfums-de-marly/parfums-de-marly-layton/eau-de-parfum",
                "Creed Aventus": "creed/creed-aventus/eau-de-parfum",
            },
            "pattern_notes": "Brand name appears TWICE in URL for some products. "
                           "Could not verify from sandbox — domain blocked. "
                           "Need live testing to confirm patterns.",
        },
        url_discovery_method="Web search: site:fragrancenet.com '{brand}' '{name}'",

        price_format=PriceFormat.FLOAT,
        price_selector="JSON-LD (assumed) or DOM extraction",
        price_gotchas=[
            "Could not test from sandbox — domain blocked for fetch()",
            "Need live/Playwright testing to verify extraction method",
        ],

        variant_strategy="Unknown — needs live testing",
        variant_gotchas=[],

        stock_method="Unknown — needs live testing",
        stock_gotchas=[],

        rate_limit_rpm=18,
        needs_playwright=False,  # Assumed — needs verification
        bot_detection="unknown",

        brands_available=["Parfums de Marly", "Creed", "Tom Ford", "MFK", "Amouage",
                         "Initio", "Xerjoff", "Le Labo", "Byredo"],
        brands_unavailable=[],

        lessons=[
            "Domain blocked from sandbox testing — all validation via web search only",
            "URL pattern confirmed for PDM Layton and Creed Aventus via web search",
            "Need live Playwright testing to verify price extraction",
        ],
        last_verified="2026-03-14",
    ),

    # ========================================================================
    # DOUGLAS (Custom SSR — blocked from sandbox)
    # ========================================================================
    "douglas_de": RetailerProfile(
        id="douglas_de",
        domain="douglas.de",
        platform=PlatformType.CUSTOM_SSR,
        currency="EUR",
        country="DE",
        primary_strategy=ScrapingStrategy.JSON_LD,
        fallback_strategy=ScrapingStrategy.PLAYWRIGHT,

        url_pattern="https://www.douglas.de/de/p/{product-code}",
        url_slug_rules={},
        url_discovery_method="Web search: site:douglas.de '{brand}' '{name}'",

        price_format=PriceFormat.FLOAT,
        price_selector="JSON-LD (assumed)",
        price_gotchas=[
            "Could not test from sandbox — domain blocked",
            "EUR pricing — needs currency conversion",
        ],

        variant_strategy="Unknown — needs live testing",
        variant_gotchas=[],
        stock_method="Unknown",
        stock_gotchas=[],

        rate_limit_rpm=20,
        needs_playwright=False,
        bot_detection="unknown",

        brands_available=[],
        brands_unavailable=[],

        lessons=[
            "Domain completely blocked from sandbox — not even HEAD requests work",
            "Need live testing environment for full validation",
        ],
        last_verified="2026-03-14",
    ),
}


# ============================================================================
# PLATFORM DETECTION — Automatically identify what a retailer is running
# ============================================================================

class PlatformDetector:
    """Detect e-commerce platform from HTML response"""

    SIGNATURES = {
        PlatformType.SHOPIFY: [
            'cdn.shopify.com',
            'Shopify.theme',
            '/products/{handle}.json',
            'shopify-section',
            'myshopify.com',
        ],
        PlatformType.WOOCOMMERCE: [
            'woocommerce',
            'wp-content',
            'wordpress',
            'elementor',
            'wc-product',
            'add_to_cart_button',
        ],
        PlatformType.MAGENTO: [
            'Magento',
            'mage-',
            'catalogsearch',
            'checkout/cart',
        ],
    }

    @classmethod
    def detect(cls, html: str, url: str = "") -> Tuple[PlatformType, float]:
        """Detect platform type from HTML. Returns (platform, confidence 0-1)"""
        html_lower = html.lower()

        best_platform = PlatformType.UNKNOWN
        best_score = 0.0

        for platform, signatures in cls.SIGNATURES.items():
            matches = sum(1 for sig in signatures if sig.lower() in html_lower)
            score = matches / len(signatures)
            if score > best_score:
                best_score = score
                best_platform = platform

        # Additional heuristic: check for .json API availability
        if best_platform == PlatformType.SHOPIFY and best_score > 0.3:
            best_score = min(best_score + 0.2, 1.0)

        return best_platform, best_score

    @classmethod
    def detect_from_url(cls, url: str) -> Optional[PlatformType]:
        """Quick detection from URL patterns alone"""
        if 'myshopify.com' in url or '/products/' in url:
            return PlatformType.SHOPIFY
        if '/perfume/' in url or 'wp-content' in url:
            return PlatformType.WOOCOMMERCE
        return None


# ============================================================================
# URL PATTERN ENGINE — Build URLs for new products
# ============================================================================

class URLPatternEngine:
    """Generate probable URLs for new products based on learned patterns"""

    @staticmethod
    def generate_shopify_handle_guesses(brand: str, name: str, size_ml: int = None) -> List[str]:
        """Generate likely Shopify product handles"""
        b = brand.lower().replace("'", "").replace(" ", "")
        n = name.lower().replace("'", "").replace(" ", "")
        b_hyph = brand.lower().replace("'", "").replace(" ", "-")
        n_hyph = name.lower().replace("'", "").replace(" ", "-")

        handles = [
            f"{b}{n}-man",                    # parfumsdemarlylayton-man
            f"{b}{n}",                         # parfumsdemarlylayton
            f"{b_hyph}-{n_hyph}",             # parfums-de-marly-layton
            f"{b_hyph}-{n_hyph}-man",         # parfums-de-marly-layton-man
        ]

        if size_ml:
            handles.extend([
                f"{b_hyph}-{n_hyph}-{size_ml}ml",
                f"{b_hyph}-{n_hyph}-{size_ml}ml-man",
            ])

        return handles

    @staticmethod
    def generate_woocommerce_slug_guesses(brand: str, name: str, size_ml: int,
                                           concentration: str = "edp") -> List[str]:
        """Generate likely WooCommerce slugs (NicheGallerie style)"""
        b = brand.lower().replace("'", "").replace(" ", "-")
        n = name.lower().replace("'", "").replace(" ", "-")
        conc = concentration.lower()

        return [
            f"{b}-{n}-{conc}-{size_ml}ml",              # parfums-de-marly-layton-edp-125ml
            f"{b}-{n}-eau-de-parfum-{size_ml}ml",        # parfums-de-marly-layton-eau-de-parfum-125ml
            f"{b}-{n}-{size_ml}ml",                       # parfums-de-marly-layton-125ml
            f"{b}-{n}-{conc}",                            # parfums-de-marly-layton-edp
        ]

    @staticmethod
    def generate_notino_slug_guesses(brand: str, name: str, gender: str = "unisex") -> List[str]:
        """Generate likely Notino URL patterns"""
        b = brand.lower().replace("'", "").replace(" ", "-")
        n = name.lower().replace("'", "").replace(" ", "-")

        gender_suffixes = {
            "male": ["for-men", "for-men-and-women"],
            "female": ["for-women", "for-women-and-men"],
            "unisex": ["unisex", "for-women-and-men", "for-men"],
        }

        slugs = []
        for suffix in gender_suffixes.get(gender, ["unisex"]):
            slugs.extend([
                f"{b}/{n}-eau-de-parfum-{suffix}",
                f"{b}/{n}-royal-essence-eau-de-parfum-{suffix}",  # PDM pattern
                f"{b}/{n}-edp-{suffix}",
            ])

        return slugs


# ============================================================================
# EXPANSION STRATEGY — How to onboard new products/retailers efficiently
# ============================================================================

EXPANSION_PLAYBOOK = {
    "new_product_onboarding": {
        "description": "Steps to add a new fragrance to the catalog",
        "steps": [
            "1. Add product to product_catalog_top20.json with basic info",
            "2. For each active retailer, discover the URL:",
            "   - Shopify: Try /search/suggest.json?q={brand+name} to find handle",
            "   - WooCommerce: HEAD request probe with slug variations",
            "   - Notino: Navigate to brand page, extract links from DOM",
            "   - Jomashop: Web search site:jomashop.com '{brand}' '{name}'",
            "   - Others: Web search site:{domain} '{brand}' '{name}'",
            "3. Validate each URL returns 200 and contains expected product",
            "4. Extract a test price and compare against known retail (sanity check)",
            "5. Add verified URLs to catalog",
        ],
        "time_estimate": "10-15 min per product across all retailers",
    },

    "new_retailer_onboarding": {
        "description": "Steps to add a new retailer to the scraper",
        "steps": [
            "1. DETECT PLATFORM: Fetch homepage, run PlatformDetector.detect(html)",
            "2. If Shopify: Try /products/{any-known-handle}.json to confirm",
            "3. If WooCommerce: Check for /wp-content/ or /wc-api/ in page source",
            "4. CHECK STRUCTURED DATA: Look for JSON-LD <script type='application/ld+json'>",
            "5. TEST URL PATTERNS: Try 3-5 known products to learn URL structure",
            "6. VERIFY PRICE FORMAT: Extract price, compare to known retail (within 30%?)",
            "7. CHECK VARIANT HANDLING: Test a product with multiple sizes",
            "8. CHECK STOCK DETECTION: Find an OOS product, verify detection works",
            "9. ADD TO REGISTRY: Create RetailerProfile with all findings",
            "10. WRITE SCRAPER: Based on detected platform and price format",
        ],
        "time_estimate": "30-60 min per retailer",
        "priority_retailers_to_add": [
            "allbeauty.com (UK, Shopify likely, Tier 2)",
            "parfumdreams.de (DE, EUR, similar to Douglas)",
            "flaconi.de (DE, EUR, good pricing)",
        ],
    },

    "scaling_from_20_to_100": {
        "description": "Strategy to expand from 20 to 100 products",
        "approach": [
            "1. Add products in batches of 10 by brand (all PDM, all Creed, etc.)",
            "2. Brand batching is efficient because URL patterns are consistent per brand",
            "3. For Shopify retailers: Use bulk search API to find all handles at once",
            "4. For WooCommerce: Probe URL variations in parallel",
            "5. For Notino: Scrape entire brand pages (all products listed)",
            "6. For Jomashop: Bulk web search (can search 10 products in one query)",
            "7. VALIDATE: Run price sanity checks against known typical retail prices",
        ],
        "estimated_coverage": {
            "FragranceBuy": "95%+ (Shopify, excellent catalog)",
            "NicheGallerie": "85%+ (WooCommerce, good niche selection)",
            "Notino": "70% (missing some niche-exclusive brands)",
            "SeeScents": "35% (small, curated inventory)",
            "Jomashop": "90%+ (huge catalog, grey market)",
            "MaxAroma": "85%+ (good niche selection)",
        },
    },
}


# ============================================================================
# MAIN INTELLIGENCE CLASS
# ============================================================================

class RetailerIntelligence:
    """Main interface for retailer intelligence system"""

    def __init__(self):
        self.profiles = RETAILER_PROFILES
        self.detector = PlatformDetector()
        self.url_engine = URLPatternEngine()

    def get_profile(self, retailer_id: str) -> Optional[RetailerProfile]:
        """Get full intelligence profile for a retailer"""
        return self.profiles.get(retailer_id)

    def get_strategy(self, retailer_id: str) -> Optional[ScrapingStrategy]:
        """Get recommended scraping strategy"""
        profile = self.profiles.get(retailer_id)
        return profile.primary_strategy if profile else None

    def get_url_guesses(self, retailer_id: str, brand: str, name: str,
                        size_ml: int = None, gender: str = "unisex") -> List[str]:
        """Generate probable URLs for a product at a retailer"""
        profile = self.profiles.get(retailer_id)
        if not profile:
            return []

        if profile.platform == PlatformType.SHOPIFY:
            handles = self.url_engine.generate_shopify_handle_guesses(brand, name, size_ml)
            return [f"https://{profile.domain}/products/{h}" for h in handles]

        elif profile.platform == PlatformType.WOOCOMMERCE:
            slugs = self.url_engine.generate_woocommerce_slug_guesses(
                brand, name, size_ml or 100)
            return [f"https://{profile.domain}/perfume/{s}/" for s in slugs]

        elif retailer_id == "notino":
            slugs = self.url_engine.generate_notino_slug_guesses(brand, name, gender)
            return [f"https://www.notino.co.uk/{s}/" for s in slugs]

        return []

    def get_lessons(self, retailer_id: str) -> List[str]:
        """Get lessons learned for a retailer"""
        profile = self.profiles.get(retailer_id)
        return profile.lessons if profile else []

    def get_gotchas(self, retailer_id: str) -> Dict[str, List[str]]:
        """Get all gotchas for a retailer"""
        profile = self.profiles.get(retailer_id)
        if not profile:
            return {}
        return {
            "price": profile.price_gotchas,
            "variant": profile.variant_gotchas,
            "stock": profile.stock_gotchas,
        }

    def detect_platform(self, html: str) -> Tuple[PlatformType, float]:
        """Auto-detect platform from HTML"""
        return self.detector.detect(html)

    def get_expansion_playbook(self) -> dict:
        """Get the expansion strategy playbook"""
        return EXPANSION_PLAYBOOK

    def summarize(self) -> str:
        """Print a summary of all retailer intelligence"""
        lines = ["=== Retailer Intelligence Summary ===\n"]
        for rid, profile in self.profiles.items():
            lines.append(f"\n{rid.upper()} ({profile.domain})")
            lines.append(f"  Platform: {profile.platform.value}")
            lines.append(f"  Strategy: {profile.primary_strategy.value}")
            lines.append(f"  Currency: {profile.currency}")
            lines.append(f"  Playwright needed: {profile.needs_playwright}")
            lines.append(f"  Lessons: {len(profile.lessons)}")
            lines.append(f"  Last verified: {profile.last_verified}")
        return "\n".join(lines)


# Quick test
if __name__ == "__main__":
    intel = RetailerIntelligence()
    print(intel.summarize())

    print("\n\n=== URL Guesses for 'Parfums de Marly Layton' ===")
    for retailer_id in ["fragrancebuy", "nichegallerie", "seescents", "notino"]:
        urls = intel.get_url_guesses(retailer_id, "Parfums de Marly", "Layton", 125)
        print(f"\n{retailer_id}:")
        for u in urls:
            print(f"  {u}")
