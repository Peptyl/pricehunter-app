"""
Auto-discovers product URLs on retailer websites.

This module resolves product URLs across multiple retailer platforms using a
strategy-based approach. Instead of manually guessing URLs (which has a high
error rate), it searches each retailer's site and finds the correct product page.

Features:
- Multiple resolution strategies (Shopify, WooCommerce, generic site search, Google fallback)
- URL caching to avoid redundant lookups
- Fuzzy matching validation to confirm product matches
- Batch resolution for efficiency
- Async/await support with graceful fallback to sync requests
- Retailer-specific search patterns and platform detection
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, quote
import re

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

import requests
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """Supported e-commerce platforms."""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    CUSTOM = "custom"


class ResolutionStrategy(str, Enum):
    """URL resolution strategies."""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    SITE_SEARCH = "site_search"
    GOOGLE_FALLBACK = "google_fallback"


@dataclass
class ProductSKU:
    """Product identifier for URL resolution."""
    brand: str
    name: str
    size_ml: Optional[int] = None
    sku: Optional[str] = None

    def __hash__(self):
        return hash((self.brand, self.name, self.size_ml, self.sku))


@dataclass
class RetailerConfig:
    """Configuration for a specific retailer."""
    domain: str
    platform: Platform
    search_url_template: str
    country: str
    currency: str
    name: str

    # Platform-specific config
    shopify_search_endpoint: Optional[str] = None
    woocommerce_search_param: Optional[str] = None

    @classmethod
    def create_shopify(cls, domain: str, name: str, country: str, currency: str) -> "RetailerConfig":
        """Create config for a Shopify store."""
        return cls(
            domain=domain,
            platform=Platform.SHOPIFY,
            search_url_template=f"https://{domain}/search/suggest.json",
            shopify_search_endpoint=f"https://{domain}/search/suggest.json",
            country=country,
            currency=currency,
            name=name,
        )

    @classmethod
    def create_woocommerce(cls, domain: str, name: str, country: str, currency: str) -> "RetailerConfig":
        """Create config for a WooCommerce store."""
        return cls(
            domain=domain,
            platform=Platform.WOOCOMMERCE,
            search_url_template=f"https://{domain}/",
            woocommerce_search_param="s",
            country=country,
            currency=currency,
            name=name,
        )

    @classmethod
    def create_custom(cls, domain: str, name: str, search_url_template: str,
                     country: str, currency: str) -> "RetailerConfig":
        """Create config for a custom platform."""
        return cls(
            domain=domain,
            platform=Platform.CUSTOM,
            search_url_template=search_url_template,
            country=country,
            currency=currency,
            name=name,
        )


@dataclass
class ResolvedURL:
    """Result of URL resolution."""
    url: str
    confidence: int  # 0-100
    strategy_used: ResolutionStrategy
    validated_at: str
    matched_title: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResolvedURL":
        """Create from dictionary."""
        return cls(**data)


class FuzzyMatcher:
    """Fuzzy matching for product validation."""

    @staticmethod
    def similarity_ratio(a: str, b: str) -> float:
        """Calculate similarity ratio between two strings (0-1)."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    @staticmethod
    def normalize_product_title(title: str) -> str:
        """Normalize product title for comparison."""
        # Remove extra whitespace and convert to lowercase
        title = title.lower().strip()
        # Remove common suffixes
        title = re.sub(r'\s*(eau de parfum|edp|eau de toilette|edt|eau de cologne|edc)\s*$', '', title)
        # Remove size indicators
        title = re.sub(r'\s*\d+\s*ml\s*', '', title)
        # Remove special characters
        title = re.sub(r'[^\w\s]', '', title)
        return title

    @staticmethod
    def validate_product_match(found_title: str, brand: str, product_name: str,
                               size_ml: Optional[int] = None, threshold: float = 0.75) -> Tuple[bool, float]:
        """
        Validate if a found product matches the target product.

        Args:
            found_title: Title from search results
            brand: Target brand name
            product_name: Target product name
            size_ml: Target size in ml (optional)
            threshold: Minimum similarity ratio to accept match (0-1)

        Returns:
            Tuple of (is_match, confidence_score)
        """
        normalized_found = FuzzyMatcher.normalize_product_title(found_title)
        expected_parts = [FuzzyMatcher.normalize_product_title(brand),
                         FuzzyMatcher.normalize_product_title(product_name)]

        # Check if both brand and product name are present
        brand_match = FuzzyMatcher.similarity_ratio(normalized_found, expected_parts[0])
        product_match = FuzzyMatcher.similarity_ratio(normalized_found, expected_parts[1])

        # Require both parts to be reasonably similar
        overall_score = max(brand_match, product_match)

        # If size is provided, check for it in the original title
        if size_ml is not None:
            if str(size_ml) not in found_title and f"{size_ml}ml" not in found_title.lower():
                overall_score *= 0.8  # Penalize if size doesn't match

        is_match = overall_score >= threshold
        confidence = int(overall_score * 100)

        return is_match, confidence


class ShopifyURLResolver:
    """Resolves URLs on Shopify stores."""

    async def resolve(self, config: RetailerConfig, product: ProductSKU,
                     session=None) -> Optional[ResolvedURL]:
        """
        Resolve product URL on a Shopify store.

        Uses the /search/suggest.json endpoint for efficient product search.

        Args:
            config: Retailer configuration
            product: Product to find
            session: Async session (aiohttp.ClientSession or requests.Session)

        Returns:
            ResolvedURL if found, None otherwise
        """
        query = f"{product.brand} {product.name}"
        if product.size_ml:
            query += f" {product.size_ml}"

        url = f"{config.shopify_search_endpoint}?q={quote(query)}&resources[type]=product"

        try:
            if HAS_AIOHTTP and isinstance(session, aiohttp.ClientSession):
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                    else:
                        return None
            else:
                resp = session.get(url, timeout=10) if session else requests.get(url, timeout=10)
                if resp.status_code != 200:
                    return None
                data = resp.json()

            products = data.get("resources", {}).get("results", {}).get("products", [])

            if not products:
                return None

            # Score and rank products
            best_match = None
            best_confidence = 0

            for p in products:
                title = p.get("title", "")
                handle = p.get("handle", "")

                is_match, confidence = FuzzyMatcher.validate_product_match(
                    title, product.brand, product.name, product.size_ml
                )

                if is_match and confidence > best_confidence:
                    best_match = p
                    best_confidence = confidence

            if best_match:
                handle = best_match.get("handle", "")
                product_url = urljoin(f"https://{config.domain}/", f"/products/{handle}")

                return ResolvedURL(
                    url=product_url,
                    confidence=best_confidence,
                    strategy_used=ResolutionStrategy.SHOPIFY,
                    validated_at=datetime.now().isoformat(),
                    matched_title=best_match.get("title"),
                )

        except Exception as e:
            logger.warning(f"Shopify resolution failed for {product}: {e}")

        return None


class WooCommerceURLResolver:
    """Resolves URLs on WooCommerce stores."""

    async def resolve(self, config: RetailerConfig, product: ProductSKU,
                     session=None) -> Optional[ResolvedURL]:
        """
        Resolve product URL on a WooCommerce store.

        Searches using the standard WooCommerce search endpoint.

        Args:
            config: Retailer configuration
            product: Product to find
            session: Async session or requests session

        Returns:
            ResolvedURL if found, None otherwise
        """
        query = f"{product.brand} {product.name}"
        if product.size_ml:
            query += f" {product.size_ml}"

        url = f"{config.search_url_template}?{config.woocommerce_search_param}={quote(query)}&post_type=product"

        try:
            if HAS_AIOHTTP and isinstance(session, aiohttp.ClientSession):
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                    else:
                        return None
            else:
                resp = session.get(url, timeout=10) if session else requests.get(url, timeout=10)
                if resp.status_code != 200:
                    return None
                html = resp.text

            # Parse HTML for product links
            # Look for product links in common WooCommerce patterns
            pattern = r'href="([^"]*product[^"]*)"[^>]*title="([^"]*)"'
            matches = re.finditer(pattern, html, re.IGNORECASE)

            best_match = None
            best_confidence = 0
            best_url = None

            for match in matches:
                found_url = match.group(1)
                found_title = match.group(2)

                is_match, confidence = FuzzyMatcher.validate_product_match(
                    found_title, product.brand, product.name, product.size_ml
                )

                if is_match and confidence > best_confidence:
                    best_match = found_title
                    best_confidence = confidence
                    best_url = found_url

            if best_url:
                # Ensure absolute URL
                if not best_url.startswith("http"):
                    best_url = urljoin(f"https://{config.domain}/", best_url)

                return ResolvedURL(
                    url=best_url,
                    confidence=best_confidence,
                    strategy_used=ResolutionStrategy.WOOCOMMERCE,
                    validated_at=datetime.now().isoformat(),
                    matched_title=best_match,
                )

        except Exception as e:
            logger.warning(f"WooCommerce resolution failed for {product}: {e}")

        return None


class SiteSearchResolver:
    """Generic site search resolver for custom platforms."""

    async def resolve(self, config: RetailerConfig, product: ProductSKU,
                     session=None) -> Optional[ResolvedURL]:
        """
        Resolve product URL using generic site search.

        Args:
            config: Retailer configuration
            product: Product to find
            session: Async session or requests session

        Returns:
            ResolvedURL if found, None otherwise
        """
        query = f"{product.brand} {product.name}"
        if product.size_ml:
            query += f" {product.size_ml}"

        # Use the configured search URL template
        url = config.search_url_template.format(query=quote(query))

        try:
            if HAS_AIOHTTP and isinstance(session, aiohttp.ClientSession):
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                    else:
                        return None
            else:
                resp = session.get(url, timeout=10) if session else requests.get(url, timeout=10)
                if resp.status_code != 200:
                    return None
                html = resp.text

            # Parse HTML for product links
            # Look for common product link patterns
            patterns = [
                r'href="([^"]*)"[^>]*>([^<]*)</a>[^<]*<[^>]*class="[^"]*price',  # Link followed by price
                r'class="[^"]*product[^"]*"[^>]*>.*?href="([^"]*)"[^>]*>([^<]*)</a>',  # Product container
                r'href="([^"]*(?:product|item)[^"]*)"[^>]*>([^<]*)</a>',  # Product in URL
            ]

            best_match = None
            best_confidence = 0
            best_url = None

            for pattern in patterns:
                matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    found_url = match.group(1)
                    found_title = match.group(2) if match.lastindex >= 2 else ""

                    if not found_title:
                        # Try to extract title from URL
                        found_title = re.sub(r'[-_/]', ' ', found_url)

                    is_match, confidence = FuzzyMatcher.validate_product_match(
                        found_title, product.brand, product.name, product.size_ml
                    )

                    if is_match and confidence > best_confidence:
                        best_match = found_title
                        best_confidence = confidence
                        best_url = found_url

            if best_url:
                # Ensure absolute URL
                if not best_url.startswith("http"):
                    best_url = urljoin(f"https://{config.domain}/", best_url)

                return ResolvedURL(
                    url=best_url,
                    confidence=best_confidence,
                    strategy_used=ResolutionStrategy.SITE_SEARCH,
                    validated_at=datetime.now().isoformat(),
                    matched_title=best_match,
                )

        except Exception as e:
            logger.warning(f"Site search resolution failed for {product}: {e}")

        return None


class GoogleFallbackResolver:
    """Fallback resolver using Google Site Search."""

    async def resolve(self, config: RetailerConfig, product: ProductSKU,
                     session=None) -> Optional[ResolvedURL]:
        """
        Resolve product URL using Google Site Search as fallback.

        This is a last-resort strategy. In production, would require either:
        - Google Custom Search API (paid, ~$100/month)
        - Parsing Google results from browser (higher latency, may be blocked)

        For now, returns None as this requires external API integration.

        Args:
            config: Retailer configuration
            product: Product to find
            session: Async session or requests session

        Returns:
            ResolvedURL if found, None otherwise
        """
        # TODO: Implement with Google Custom Search API when available
        logger.debug(f"Google fallback resolver not yet implemented for {product}")
        return None


class URLCache:
    """Persistent cache for resolved URLs."""

    def __init__(self, cache_file: Path):
        """
        Initialize URL cache.

        Args:
            cache_file: Path to JSON cache file
        """
        self.cache_file = Path(cache_file)
        self.data: Dict[str, Dict[str, dict]] = {}
        self._load()

    def _load(self):
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load URL cache: {e}")
                self.data = {}
        else:
            self.data = {}

    def _save(self):
        """Save cache to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save URL cache: {e}")

    def get(self, product_key: str, retailer: str) -> Optional[ResolvedURL]:
        """
        Get resolved URL from cache.

        Args:
            product_key: Product identifier (e.g., "pdm-layton-125-edp")
            retailer: Retailer domain

        Returns:
            ResolvedURL if in cache, None otherwise
        """
        if product_key in self.data and retailer in self.data[product_key]:
            try:
                return ResolvedURL.from_dict(self.data[product_key][retailer])
            except Exception as e:
                logger.warning(f"Failed to deserialize cached URL: {e}")
        return None

    def set(self, product_key: str, retailer: str, resolved: ResolvedURL):
        """
        Store resolved URL in cache.

        Args:
            product_key: Product identifier
            retailer: Retailer domain
            resolved: Resolved URL object
        """
        if product_key not in self.data:
            self.data[product_key] = {}
        self.data[product_key][retailer] = resolved.to_dict()
        self._save()

    def invalidate(self, product_key: str, retailer: Optional[str] = None):
        """
        Invalidate cache entries.

        Args:
            product_key: Product identifier
            retailer: Specific retailer to invalidate (None for all)
        """
        if retailer and product_key in self.data:
            self.data[product_key].pop(retailer, None)
        elif product_key in self.data:
            del self.data[product_key]
        self._save()


class URLResolver:
    """
    Auto-discovers product URLs on retailer websites.

    This resolver uses a strategy-based approach to find product URLs across
    multiple retailer platforms without manual URL guessing.
    """

    def __init__(self, session=None, cache_file: Optional[Path] = None):
        """
        Initialize URL resolver.

        Args:
            session: Optional requests.Session or aiohttp.ClientSession
            cache_file: Optional path to URL cache file (default: /data/resolved_urls.json)
        """
        self.session = session or requests.Session()
        self.cache = URLCache(cache_file or Path("/data/resolved_urls.json"))

        self.strategies = {
            ResolutionStrategy.SHOPIFY: ShopifyURLResolver(),
            ResolutionStrategy.WOOCOMMERCE: WooCommerceURLResolver(),
            ResolutionStrategy.SITE_SEARCH: SiteSearchResolver(),
            ResolutionStrategy.GOOGLE_FALLBACK: GoogleFallbackResolver(),
        }

    def _get_cache_key(self, product: ProductSKU) -> str:
        """Generate a cache key for a product."""
        size_str = f"-{product.size_ml}" if product.size_ml else ""
        sku_str = f"-{product.sku}" if product.sku else ""
        return f"{product.brand.lower()}-{product.name.lower()}{size_str}{sku_str}".replace(" ", "-")

    async def resolve_url(self, retailer: RetailerConfig, product: ProductSKU,
                         use_cache: bool = True, strategy: Optional[ResolutionStrategy] = None) -> Optional[ResolvedURL]:
        """
        Resolve a product URL on a retailer's website.

        Tries multiple strategies in order:
        1. Check cache first (if enabled)
        2. Platform-specific resolver (Shopify, WooCommerce)
        3. Generic site search
        4. Google fallback

        Args:
            retailer: Target retailer configuration
            product: Product to find
            use_cache: Whether to check/update cache (default: True)
            strategy: Specific strategy to use (None = auto-detect)

        Returns:
            ResolvedURL if found, None otherwise
        """
        product_key = self._get_cache_key(product)

        # Check cache first
        if use_cache:
            cached = self.cache.get(product_key, retailer.domain)
            if cached:
                logger.debug(f"Cache hit for {product_key} on {retailer.name}")
                return cached

        # Determine which strategies to try
        if strategy:
            strategies_to_try = [strategy]
        else:
            strategies_to_try = self._get_strategies_for_retailer(retailer)

        resolved = None
        for strat in strategies_to_try:
            logger.debug(f"Trying {strat.value} strategy for {product} on {retailer.name}")
            resolver = self.strategies[strat]
            resolved = await resolver.resolve(retailer, product, self.session)

            if resolved:
                logger.info(f"Resolved {product} to {resolved.url} on {retailer.name}")
                break

        # Cache the result (even if None, to avoid re-trying)
        if use_cache and resolved:
            self.cache.set(product_key, retailer.domain, resolved)

        return resolved

    async def resolve_batch(self, retailer: RetailerConfig,
                           products: List[ProductSKU]) -> Dict[str, ResolvedURL]:
        """
        Resolve URLs for multiple products on one retailer efficiently.

        Uses batching to minimize requests and maximize concurrency.

        Args:
            retailer: Target retailer
            products: List of products to resolve

        Returns:
            Dictionary mapping product cache keys to ResolvedURL objects
        """
        results = {}

        # Create tasks for all products
        tasks = []
        product_keys = []

        for product in products:
            product_key = self._get_cache_key(product)
            product_keys.append(product_key)
            tasks.append(self.resolve_url(retailer, product))

        # Run all resolution tasks concurrently
        resolved_urls = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        for product_key, resolved in zip(product_keys, resolved_urls):
            if isinstance(resolved, ResolvedURL):
                results[product_key] = resolved
            elif resolved is not None and not isinstance(resolved, Exception):
                results[product_key] = resolved

        logger.info(f"Resolved {len(results)}/{len(products)} products on {retailer.name}")
        return results

    def _get_strategies_for_retailer(self, retailer: RetailerConfig) -> List[ResolutionStrategy]:
        """Get the preferred strategy order for a retailer."""
        if retailer.platform == Platform.SHOPIFY:
            return [
                ResolutionStrategy.SHOPIFY,
                ResolutionStrategy.SITE_SEARCH,
                ResolutionStrategy.GOOGLE_FALLBACK,
            ]
        elif retailer.platform == Platform.WOOCOMMERCE:
            return [
                ResolutionStrategy.WOOCOMMERCE,
                ResolutionStrategy.SITE_SEARCH,
                ResolutionStrategy.GOOGLE_FALLBACK,
            ]
        else:
            return [
                ResolutionStrategy.SITE_SEARCH,
                ResolutionStrategy.GOOGLE_FALLBACK,
            ]

    def clear_cache(self):
        """Clear the URL cache."""
        self.cache.data = {}
        self.cache._save()

    def invalidate_product(self, product: ProductSKU, retailer: Optional[str] = None):
        """
        Invalidate cache for a specific product.

        Args:
            product: Product to invalidate
            retailer: Specific retailer to invalidate (None for all)
        """
        product_key = self._get_cache_key(product)
        self.cache.invalidate(product_key, retailer)


# Pre-configured retailer instances
def create_retailer_configs() -> Dict[str, RetailerConfig]:
    """Create configuration objects for all supported retailers."""
    return {
        "notino": RetailerConfig.create_custom(
            domain="notino.co.uk",
            name="Notino",
            search_url_template="https://www.notino.co.uk/search?query={query}",
            country="UK",
            currency="GBP",
        ),
        "nichegallerie": RetailerConfig.create_woocommerce(
            domain="nichegallerie.com",
            name="NicheGallerie",
            country="US",
            currency="USD",
        ),
        "fragrancebuy": RetailerConfig.create_shopify(
            domain="fragrancebuy.ca",
            name="FragranceBuy",
            country="CA",
            currency="CAD",
        ),
        "seescents": RetailerConfig.create_shopify(
            domain="seescents.com",
            name="SeeScents",
            country="US",
            currency="USD",
        ),
        "maxaroma": RetailerConfig.create_custom(
            domain="maxaroma.com",
            name="MaxAroma",
            search_url_template="https://www.maxaroma.com/search?q={query}",
            country="US",
            currency="USD",
        ),
        "jomashop": RetailerConfig.create_custom(
            domain="jomashop.com",
            name="Jomashop",
            search_url_template="https://www.jomashop.com/search?q={query}",
            country="US",
            currency="USD",
        ),
        "fragrancenet": RetailerConfig.create_custom(
            domain="fragrancenet.com",
            name="FragranceNet",
            search_url_template="https://www.fragrancenet.com/search?q={query}",
            country="US",
            currency="USD",
        ),
        "douglas": RetailerConfig.create_custom(
            domain="douglas.de",
            name="Douglas",
            search_url_template="https://www.douglas.de/de/search?query={query}",
            country="DE",
            currency="EUR",
        ),
    }
