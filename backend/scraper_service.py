#!/usr/bin/env python3
"""
PriceHunter Scraper Service
Integration layer between FastAPI backend and v2 scraper engine.
Handles product catalog, caching, and price discovery.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import os

try:
    import redis
except ImportError:
    redis = None

from rapidfuzz import fuzz

# Setup logging
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

CATALOG_PATH = Path(__file__).parent.parent / 'data' / 'product_catalog_top20.json'
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
CACHE_TTL_FREE = 6 * 3600  # 6 hours for free users
CACHE_TTL_PRO = 300  # 5 minutes for pro users (near real-time)

# ============================================================================
# SCRAPER SERVICE
# ============================================================================

class ScraperService:
    """Integration layer for scraper engine with caching and product discovery."""

    def __init__(self):
        """Initialize scraper service with catalog and Redis connection."""
        self.catalog = self._load_catalog()
        self.redis_client = self._init_redis()
        self.scraper = None  # Lazy-loaded on first use

    def _load_catalog(self) -> Dict[str, Any]:
        """Load product catalog from JSON file."""
        try:
            if not CATALOG_PATH.exists():
                logger.error(f"Catalog not found at {CATALOG_PATH}")
                return {"products": []}

            with open(CATALOG_PATH, 'r') as f:
                data = json.load(f)
                logger.info(f"✅ Loaded {len(data.get('products', []))} products from catalog")
                return data
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            return {"products": []}

    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection for caching."""
        if redis is None:
            logger.warning("Redis client not installed, caching disabled")
            return None

        try:
            r = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=5
            )
            r.ping()
            logger.info("✅ Connected to Redis")
            return r
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
            return None

    def _get_scraper(self):
        """Lazy-load scraper engine."""
        if self.scraper is None:
            try:
                from scraper.engine import PriceHunterScraper
                self.scraper = PriceHunterScraper()
                logger.info("✅ Scraper engine loaded")
            except Exception as e:
                logger.error(f"Failed to load scraper engine: {e}")
                return None
        return self.scraper

    def _get_cache_key(self, key: str) -> str:
        """Generate Redis cache key."""
        return f"pricehunter:{key}"

    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get value from Redis cache."""
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(self._get_cache_key(key))
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.debug(f"Cache get error: {e}")

        return None

    def _set_cache(self, key: str, value: Dict, ttl: int) -> None:
        """Set value in Redis cache."""
        if not self.redis_client:
            return

        try:
            self.redis_client.setex(
                self._get_cache_key(key),
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.debug(f"Cache set error: {e}")

    def _get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get product from catalog by ID."""
        for product in self.catalog.get('products', []):
            if product['id'] == product_id:
                return product
        return None

    def _rank_deals(self, deals: List[Dict]) -> List[Dict]:
        """Rank deals by savings percentage, then by absolute savings."""
        return sorted(
            deals,
            key=lambda d: (
                -d.get('savings_percent', 0),
                -d.get('savings', 0)
            )
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def get_all_deals(self, user_tier: str = 'free') -> Dict[str, Any]:
        """
        Get all current best deals across catalog.

        Args:
            user_tier: 'free', 'premium', or 'pro'

        Returns:
            Dict with scan_time, tier, and ranked deals
        """
        cache_key = f"deals:{user_tier}"
        cached = self._get_cached(cache_key)
        if cached:
            logger.info(f"Returning cached deals for {user_tier}")
            return cached

        logger.info("Fetching fresh deals from scraper")
        scraper = self._get_scraper()
        if not scraper:
            return {
                'scan_time': datetime.now().isoformat(),
                'tier': user_tier,
                'deals': [],
                'error': 'Scraper unavailable'
            }

        all_deals = []

        # Scan all products in catalog
        for product in self.catalog.get('products', []):
            try:
                deals = self._scan_product(product, scraper)
                all_deals.extend(deals)
            except Exception as e:
                logger.error(f"Error scanning {product.get('id')}: {e}")
                continue

        # Rank deals
        ranked_deals = self._rank_deals(all_deals)

        result = {
            'scan_time': datetime.now().isoformat(),
            'tier': user_tier,
            'deals': ranked_deals,
            'total': len(ranked_deals)
        }

        # Cache based on tier
        ttl = CACHE_TTL_PRO if user_tier in ['premium', 'pro'] else CACHE_TTL_FREE
        self._set_cache(cache_key, result, ttl)

        return result

    def _scan_product(self, product: Dict, scraper) -> List[Dict]:
        """
        Scan a single product across retailers.
        Returns list of deals for this product.
        """
        deals = []
        product_id = product['id']
        brand = product['brand']
        name = product['name']
        size_ml = product['size_ml']
        typical_retail = product['typical_retail_gbp']

        logger.info(f"Scanning {brand} {name} {size_ml}ml")

        # Try to scrape from each retailer URL
        for retailer_name, url in product.get('retailer_urls', {}).items():
            try:
                result = scraper.scrape_product(url, product)

                if result and result.get('found'):
                    price = result.get('price')
                    in_stock = result.get('in_stock', True)

                    if price:
                        savings = typical_retail - price
                        savings_pct = (savings / typical_retail * 100) if typical_retail > 0 else 0

                        deal = {
                            'product_id': product_id,
                            'perfume': f"{brand} {name} {size_ml}ml",
                            'brand': brand,
                            'name': name,
                            'size_ml': size_ml,
                            'retailer': retailer_name,
                            'price': price,
                            'currency': 'GBP',
                            'typical_retail': typical_retail,
                            'savings': round(savings, 2),
                            'savings_percent': round(savings_pct, 1),
                            'in_stock': in_stock,
                            'url': url,
                            'scraped_at': datetime.now().isoformat()
                        }

                        # Only include if price is reasonable (good deal)
                        if savings_pct >= 5:  # At least 5% discount
                            deals.append(deal)
                            logger.info(f"  ✓ {retailer_name}: £{price} (-{savings_pct:.1f}%)")

            except Exception as e:
                logger.debug(f"Error scraping {retailer_name} for {product_id}: {e}")
                continue

        return deals

    def get_product_prices(self, product_id: str) -> Dict[str, Any]:
        """
        Get current prices for a specific product across retailers.

        Args:
            product_id: Product ID from catalog

        Returns:
            Dict with product info and current prices from each retailer
        """
        product = self._get_product_by_id(product_id)
        if not product:
            return {'error': f'Product {product_id} not found'}

        cache_key = f"prices:{product_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        scraper = self._get_scraper()
        if not scraper:
            return {
                'product_id': product_id,
                'brand': product.get('brand'),
                'name': product.get('name'),
                'prices': {},
                'error': 'Scraper unavailable'
            }

        prices_by_retailer = {}

        for retailer_name, url in product.get('retailer_urls', {}).items():
            try:
                result = scraper.scrape_product(url, product)
                if result and result.get('found'):
                    prices_by_retailer[retailer_name] = {
                        'price': result.get('price'),
                        'currency': 'GBP',
                        'in_stock': result.get('in_stock', True),
                        'url': url
                    }
            except Exception as e:
                logger.debug(f"Error getting price from {retailer_name}: {e}")

        result = {
            'product_id': product_id,
            'brand': product.get('brand'),
            'name': product.get('name'),
            'size_ml': product.get('size_ml'),
            'typical_retail': product.get('typical_retail_gbp'),
            'prices': prices_by_retailer,
            'updated_at': datetime.now().isoformat()
        }

        self._set_cache(cache_key, result, CACHE_TTL_FREE)
        return result

    def get_price_history(self, product_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get price history for a product.
        Note: This requires database integration for historical data.

        Args:
            product_id: Product ID from catalog
            days: Number of days of history (30, 90, 365)

        Returns:
            Dict with price history (requires DB integration)
        """
        product = self._get_product_by_id(product_id)
        if not product:
            return {'error': f'Product {product_id} not found'}

        return {
            'product_id': product_id,
            'brand': product.get('brand'),
            'name': product.get('name'),
            'size_ml': product.get('size_ml'),
            'days': days,
            'message': 'Price history requires database integration',
            'history': []
        }

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """
        Fuzzy search products in catalog.

        Args:
            query: Search query (brand, name, etc.)

        Returns:
            List of matching products ranked by relevance
        """
        if not query or len(query) < 2:
            return []

        query_lower = query.lower()
        results = []

        for product in self.catalog.get('products', []):
            # Build searchable text
            searchable = f"{product['brand']} {product['name']} {' '.join(product.get('aliases', []))}"

            # Fuzzy match
            score = fuzz.token_set_ratio(query_lower, searchable.lower())

            if score >= 60:  # Threshold
                results.append({
                    'score': score,
                    'product_id': product['id'],
                    'brand': product['brand'],
                    'name': product['name'],
                    'size_ml': product['size_ml'],
                    'typical_retail': product['typical_retail_gbp']
                })

        # Sort by score descending
        return sorted(results, key=lambda x: x['score'], reverse=True)

    def refresh_prices(self, product_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Manually trigger price refresh for products.

        Args:
            product_ids: Optional list of product IDs. If None, refresh all.

        Returns:
            Dict with refresh status and count
        """
        logger.info("Starting manual price refresh")

        # Clear relevant cache
        if self.redis_client:
            if product_ids:
                for product_id in product_ids:
                    keys_to_delete = self.redis_client.keys(f"pricehunter:prices:{product_id}")
                    if keys_to_delete:
                        self.redis_client.delete(*keys_to_delete)
            else:
                # Clear all deal and price caches
                keys = self.redis_client.keys("pricehunter:deals:*") + \
                       self.redis_client.keys("pricehunter:prices:*")
                if keys:
                    self.redis_client.delete(*keys)

        # Get deals (this triggers new scrape)
        deals = self.get_all_deals('pro')

        return {
            'success': True,
            'refreshed_at': datetime.now().isoformat(),
            'deals_found': len(deals.get('deals', [])),
            'cache_cleared': True
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_service_instance = None

def get_scraper_service() -> ScraperService:
    """Get or create scraper service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ScraperService()
    return _service_instance
