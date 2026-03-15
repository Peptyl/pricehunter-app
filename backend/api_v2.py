#!/usr/bin/env python3
"""
Olfex V2 API - Extended endpoints for product search, pricing, deals & alerts
Includes product catalog, retailer health, price history, and Fragrantica integration
"""

from fastapi import APIRouter, Query, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import os
from pathlib import Path
import httpx
import logging
from rapidfuzz import fuzz
from functools import lru_cache
import time

# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class PriceBreakdown(BaseModel):
    """Price breakdown for a product at a retailer"""
    base_price_gbp: float
    vat_gbp: float
    shipping_gbp: float
    total_gbp: float
    currency_code: str = "GBP"

    class Config:
        schema_extra = {
            "example": {
                "base_price_gbp": 85.00,
                "vat_gbp": 17.00,
                "shipping_gbp": 8.50,
                "total_gbp": 110.50,
                "currency_code": "GBP"
            }
        }


class RetailerPrice(BaseModel):
    """Current price from a retailer"""
    retailer_id: str
    retailer_name: str
    url: str
    price_breakdown: PriceBreakdown
    in_stock: bool
    last_updated: datetime
    tier: int

    class Config:
        schema_extra = {
            "example": {
                "retailer_id": "fragnet",
                "retailer_name": "FragranceBuy",
                "url": "https://example.com/product",
                "price_breakdown": {
                    "base_price_gbp": 85.00,
                    "vat_gbp": 17.00,
                    "shipping_gbp": 8.50,
                    "total_gbp": 110.50
                },
                "in_stock": True,
                "last_updated": "2024-03-15T10:30:00Z",
                "tier": 1
            }
        }


class FragmentaAccord(BaseModel):
    """Fragrantica accord data"""
    name: str
    percentage: float

    class Config:
        schema_extra = {
            "example": {"name": "Warm Spicy", "percentage": 45}
        }


class FragrantaNote(BaseModel):
    """Fragrance note"""
    name: str
    category: str  # top, middle, base

    class Config:
        schema_extra = {
            "example": {"name": "Bergamot", "category": "top"}
        }


class FragrantaProfile(BaseModel):
    """Fragrantica profile data"""
    product_id: str
    fragrantica_id: Optional[str] = None
    fragrantica_url: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None  # 1-10
    rating_count: Optional[int] = None
    accords: Optional[List[FragmentaAccord]] = []
    top_notes: Optional[List[FragrantaNote]] = []
    middle_notes: Optional[List[FragrantaNote]] = []
    base_notes: Optional[List[FragrantaNote]] = []
    description: Optional[str] = None
    longevity: Optional[str] = None
    sillage: Optional[str] = None
    last_synced: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "product_id": "prod_123",
                "fragrantica_id": "frag_456",
                "rating": 8.5,
                "rating_count": 1250,
                "accords": [{"name": "Warm Spicy", "percentage": 45}],
                "longevity": "8-10 hours",
                "sillage": "Excellent"
            }
        }


class Product(BaseModel):
    """Product listing with basic info"""
    product_id: str
    name: str
    brand: str
    volume_ml: int
    rrp_gbp: float
    lowest_price_gbp: Optional[float] = None
    lowest_retailer: Optional[str] = None
    fragrantica_rating: Optional[float] = None
    image_url: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "product_id": "prod_123",
                "name": "Aventus",
                "brand": "Creed",
                "volume_ml": 100,
                "rrp_gbp": 195.00,
                "lowest_price_gbp": 155.00,
                "lowest_retailer": "fragnet",
                "fragrantica_rating": 8.5
            }
        }


class ProductDetail(Product):
    """Full product details with prices and profile"""
    description: Optional[str] = None
    current_prices: List[RetailerPrice] = []
    fragrantica_profile: Optional[FragrantaProfile] = None
    price_history_7d: Optional[List[Dict]] = None
    discount_percentage: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "product_id": "prod_123",
                "name": "Aventus",
                "brand": "Creed",
                "volume_ml": 100,
                "rrp_gbp": 195.00,
                "lowest_price_gbp": 155.00,
                "discount_percentage": 20.5
            }
        }


class Deal(BaseModel):
    """Current deal/discount"""
    product_id: str
    product_name: str
    brand: str
    rrp_gbp: float
    current_price_gbp: float
    discount_percentage: float
    discount_amount_gbp: float
    best_retailer: str
    retailer_name: str
    url: str
    stock_status: bool
    fragrantica_rating: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "product_id": "prod_123",
                "product_name": "Aventus",
                "brand": "Creed",
                "rrp_gbp": 195.00,
                "current_price_gbp": 155.00,
                "discount_percentage": 20.5,
                "discount_amount_gbp": 40.00,
                "best_retailer": "fragnet"
            }
        }


class Retailer(BaseModel):
    """Retailer info with health status"""
    retailer_id: str
    name: str
    website: str
    tier: int
    country: str
    health_status: str  # healthy, degraded, down
    products_indexed: int
    last_scan: Optional[datetime] = None
    uptime_percentage: Optional[float] = None
    response_time_ms: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "retailer_id": "fragnet",
                "name": "FragranceBuy",
                "website": "https://fragrance.com",
                "tier": 1,
                "country": "GB",
                "health_status": "healthy",
                "products_indexed": 5234,
                "uptime_percentage": 99.9
            }
        }


class HealthMetrics(BaseModel):
    """Health status for a retailer"""
    retailer_id: str
    name: str
    status: str  # healthy, degraded, down
    uptime_percentage: float
    response_time_ms: float
    last_successful_scan: Optional[datetime] = None
    consecutive_failures: int
    products_available: int
    products_out_of_stock: int
    average_price_change_percentage: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "retailer_id": "fragnet",
                "name": "FragranceBuy",
                "status": "healthy",
                "uptime_percentage": 99.9,
                "response_time_ms": 245.5,
                "products_available": 5000,
                "products_out_of_stock": 234
            }
        }


class PriceAlert(BaseModel):
    """Price alert configuration"""
    alert_id: str
    product_id: str
    product_name: str
    brand: str
    target_price_gbp: float
    current_price_gbp: Optional[float] = None
    discount_to_target: Optional[float] = None
    email: Optional[str] = None
    created_at: datetime
    triggered_at: Optional[datetime] = None
    is_active: bool

    class Config:
        schema_extra = {
            "example": {
                "alert_id": "alert_123",
                "product_id": "prod_456",
                "product_name": "Aventus",
                "target_price_gbp": 150.00,
                "current_price_gbp": 155.00,
                "is_active": True
            }
        }


class PriceAlertCreate(BaseModel):
    """Request model for creating a price alert"""
    product_id: str
    target_price_gbp: float = Field(..., gt=0)
    email: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "product_id": "prod_123",
                "target_price_gbp": 150.00,
                "email": "user@example.com"
            }
        }


class ComparisonProduct(BaseModel):
    """Product in a price comparison"""
    product_id: str
    name: str
    brand: str
    volume_ml: int
    rrp_gbp: float
    lowest_price: float
    lowest_retailer: str
    price_difference_from_rrp: float
    discount_percentage: float

    class Config:
        schema_extra = {
            "example": {
                "product_id": "prod_123",
                "name": "Aventus",
                "brand": "Creed",
                "lowest_price": 155.00,
                "discount_percentage": 20.5
            }
        }


class SystemHealth(BaseModel):
    """System-wide health status"""
    timestamp: datetime
    status: str  # healthy, degraded, critical
    retailers_healthy: int
    retailers_degraded: int
    retailers_down: int
    total_products: int
    last_scan_cycle: Optional[datetime] = None
    next_scan_cycle: Optional[datetime] = None
    active_alerts: int
    recent_anomalies: List[str] = []

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "retailers_healthy": 15,
                "retailers_degraded": 2,
                "total_products": 12500,
                "active_alerts": 145
            }
        }


class ScanResult(BaseModel):
    """Result of a scan cycle"""
    scan_id: str
    timestamp: datetime
    duration_seconds: float
    products_scanned: int
    retailers_scanned: int
    errors: int
    price_updates: int
    new_products_found: int

    class Config:
        schema_extra = {
            "example": {
                "scan_id": "scan_123",
                "products_scanned": 12500,
                "retailers_scanned": 20,
                "price_updates": 3456
            }
        }


# ============================================================================
# DATA LOADING UTILITIES
# ============================================================================

class DataLoader:
    """Centralized data loading with caching"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._product_catalog = None
        self._retailer_registry = None
        self._latest_prices = None
        self._fragrantica_cache = {}
        self._load_time = {}

    def load_product_catalog(self) -> Dict[str, Any]:
        """Load product catalog with caching"""
        if self._product_catalog is None:
            path = self.data_dir / "product_catalog_expanded.json"
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        self._product_catalog = json.load(f)
                        self._load_time['catalog'] = datetime.now()
                except Exception as e:
                    logger.error(f"Failed to load product catalog: {e}")
                    self._product_catalog = {}
            else:
                logger.warning(f"Product catalog not found at {path}")
                self._product_catalog = {}
        return self._product_catalog

    def load_retailer_registry(self) -> Dict[str, Any]:
        """Load retailer registry with caching"""
        if self._retailer_registry is None:
            path = self.data_dir / "retailer_registry.json"
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        self._retailer_registry = json.load(f)
                        self._load_time['retailers'] = datetime.now()
                except Exception as e:
                    logger.error(f"Failed to load retailer registry: {e}")
                    self._retailer_registry = {}
            else:
                logger.warning(f"Retailer registry not found at {path}")
                self._retailer_registry = {}
        return self._retailer_registry

    def load_latest_prices(self) -> Dict[str, Any]:
        """Load latest prices with caching"""
        if self._latest_prices is None:
            path = self.data_dir / "latest_prices.json"
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        self._latest_prices = json.load(f)
                        self._load_time['prices'] = datetime.now()
                except Exception as e:
                    logger.error(f"Failed to load latest prices: {e}")
                    self._latest_prices = {}
            else:
                logger.warning(f"Latest prices not found at {path}")
                self._latest_prices = {}
        return self._latest_prices

    def load_price_history(self, product_id: str, days: int = 30) -> List[Dict]:
        """Load price history for a product"""
        try:
            history_dir = self.data_dir / "price_history"
            history_file = history_dir / f"{product_id}.json"

            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    # Filter by date range
                    cutoff_date = datetime.now() - timedelta(days=days)
                    filtered = [
                        h for h in history
                        if datetime.fromisoformat(h.get('timestamp', '')) >= cutoff_date
                    ]
                    return sorted(filtered, key=lambda x: x.get('timestamp', ''))
            return []
        except Exception as e:
            logger.error(f"Failed to load price history for {product_id}: {e}")
            return []

    def load_fragrantica_profile(self, product_id: str) -> Optional[Dict]:
        """Load Fragrantica profile data"""
        if product_id in self._fragrantica_cache:
            return self._fragrantica_cache[product_id]

        try:
            profile_dir = self.data_dir / "fragrantica_cache"
            profile_file = profile_dir / f"{product_id}.json"

            if profile_file.exists():
                with open(profile_file, 'r') as f:
                    profile = json.load(f)
                    self._fragrantica_cache[product_id] = profile
                    return profile
            return None
        except Exception as e:
            logger.error(f"Failed to load Fragrantica profile for {product_id}: {e}")
            return None

    def load_health_data(self) -> Dict[str, Any]:
        """Load health monitoring data"""
        try:
            path = self.data_dir / "health_metrics.json"
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load health data: {e}")
            return {}

    def clear_cache(self):
        """Clear all cached data"""
        self._product_catalog = None
        self._retailer_registry = None
        self._latest_prices = None
        self._fragrantica_cache = {}
        self._load_time = {}


# ============================================================================
# INITIALIZE DATA LOADER
# ============================================================================

data_loader = DataLoader(data_dir=os.getenv("DATA_DIR", "data"))

# ============================================================================
# ROUTER DEFINITION
# ============================================================================

router = APIRouter(prefix="/api/v2", tags=["v2"])

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def fuzzy_search(query: str, items: List[Dict], fields: List[str], limit: int = 10) -> List[Dict]:
    """Fuzzy search across multiple fields"""
    scored = []
    query_lower = query.lower()

    for item in items:
        max_score = 0
        for field in fields:
            value = str(item.get(field, "")).lower()
            score = fuzz.partial_ratio(query_lower, value)
            max_score = max(max_score, score)

        if max_score > 50:  # Minimum threshold
            scored.append((item, max_score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    return [item for item, score in scored[:limit]]


def calculate_discount(rrp: float, current_price: float) -> tuple:
    """Calculate discount percentage and amount"""
    if rrp <= 0:
        return 0.0, 0.0
    discount_pct = ((rrp - current_price) / rrp) * 100
    discount_amount = rrp - current_price
    return max(0, discount_pct), max(0, discount_amount)


def get_retailer_by_id(retailer_id: str) -> Optional[Dict]:
    """Get retailer info by ID"""
    registry = data_loader.load_retailer_registry()
    return registry.get("retailers", {}).get(retailer_id)


def get_product_by_id(product_id: str) -> Optional[Dict]:
    """Get product info by ID"""
    catalog = data_loader.load_product_catalog()
    return catalog.get("products", {}).get(product_id)


# ============================================================================
# PRODUCT ENDPOINTS
# ============================================================================

@router.get("/products", response_model=List[Product])
async def list_products(
    brand: Optional[str] = Query(None, description="Filter by brand"),
    search: Optional[str] = Query(None, description="Fuzzy search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    List all products with optional brand filter and fuzzy search.

    Supports pagination and search across product names/brands.
    """
    try:
        catalog = data_loader.load_product_catalog()
        latest_prices = data_loader.load_latest_prices()
        products_list = catalog.get("products", {}).values()

        # Filter by brand
        if brand:
            products_list = [p for p in products_list if p.get("brand", "").lower() == brand.lower()]

        # Fuzzy search
        if search:
            products_list = fuzzy_search(search, list(products_list), ["name", "brand"])
        else:
            products_list = list(products_list)

        # Calculate lowest price for each product
        results = []
        for product in products_list:
            product_id = product.get("product_id")
            prices_for_product = latest_prices.get(product_id, [])

            lowest_price = None
            lowest_retailer = None
            if prices_for_product:
                sorted_prices = sorted(prices_for_product, key=lambda p: p.get("total_gbp", float('inf')))
                lowest = sorted_prices[0]
                lowest_price = lowest.get("total_gbp")
                lowest_retailer = lowest.get("retailer_id")

            # Load Fragrantica profile for rating
            frag_profile = data_loader.load_fragrantica_profile(product_id)
            frag_rating = frag_profile.get("rating") if frag_profile else None

            results.append(Product(
                product_id=product_id,
                name=product.get("name"),
                brand=product.get("brand"),
                volume_ml=product.get("volume_ml", 0),
                rrp_gbp=product.get("rrp_gbp", 0),
                lowest_price_gbp=lowest_price,
                lowest_retailer=lowest_retailer,
                fragrantica_rating=frag_rating,
                image_url=frag_profile.get("image_url") if frag_profile else None,
            ))

        # Pagination
        total = len(results)
        start = (page - 1) * limit
        end = start + limit
        paginated = results[start:end]

        return paginated

    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", response_model=ProductDetail)
async def get_product(product_id: str):
    """
    Get single product with latest prices from all retailers and Fragrantica profile.

    Returns full product details including current prices, price history preview, and fragrance profile.
    """
    try:
        product = get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        latest_prices = data_loader.load_latest_prices()
        prices_for_product = latest_prices.get(product_id, [])

        # Build current prices list
        current_prices = []
        for price_data in prices_for_product:
            retailer = get_retailer_by_id(price_data.get("retailer_id"))
            if retailer:
                current_prices.append(RetailerPrice(
                    retailer_id=price_data.get("retailer_id"),
                    retailer_name=retailer.get("name"),
                    url=price_data.get("url", ""),
                    price_breakdown=PriceBreakdown(
                        base_price_gbp=price_data.get("base_price_gbp", 0),
                        vat_gbp=price_data.get("vat_gbp", 0),
                        shipping_gbp=price_data.get("shipping_gbp", 0),
                        total_gbp=price_data.get("total_gbp", 0),
                    ),
                    in_stock=price_data.get("in_stock", True),
                    last_updated=datetime.fromisoformat(price_data.get("last_updated", datetime.now().isoformat())),
                    tier=retailer.get("tier", 3),
                ))

        # Sort by total price
        current_prices.sort(key=lambda p: p.price_breakdown.total_gbp)

        # Calculate discount
        rrp = product.get("rrp_gbp", 0)
        lowest_price = current_prices[0].price_breakdown.total_gbp if current_prices else None
        discount_pct, _ = calculate_discount(rrp, lowest_price) if lowest_price else (0, 0)

        # Load Fragrantica profile
        frag_data = data_loader.load_fragrantica_profile(product_id)
        frag_profile = None
        if frag_data:
            frag_profile = FragrantaProfile(
                product_id=product_id,
                fragrantica_id=frag_data.get("fragrantica_id"),
                fragrantica_url=frag_data.get("fragrantica_url"),
                image_url=frag_data.get("image_url"),
                rating=frag_data.get("rating"),
                rating_count=frag_data.get("rating_count"),
                accords=[FragmentaAccord(**a) for a in frag_data.get("accords", [])],
                top_notes=[FragrantaNote(**n) for n in frag_data.get("top_notes", [])],
                middle_notes=[FragrantaNote(**n) for n in frag_data.get("middle_notes", [])],
                base_notes=[FragrantaNote(**n) for n in frag_data.get("base_notes", [])],
                description=frag_data.get("description"),
                longevity=frag_data.get("longevity"),
                sillage=frag_data.get("sillage"),
                last_synced=datetime.fromisoformat(frag_data.get("last_synced")) if frag_data.get("last_synced") else None,
            )

        # Load price history (7 days preview)
        price_history = data_loader.load_price_history(product_id, days=7)

        return ProductDetail(
            product_id=product_id,
            name=product.get("name"),
            brand=product.get("brand"),
            volume_ml=product.get("volume_ml", 0),
            rrp_gbp=rrp,
            lowest_price_gbp=lowest_price,
            lowest_retailer=current_prices[0].retailer_id if current_prices else None,
            description=product.get("description"),
            current_prices=current_prices,
            fragrantica_profile=frag_profile,
            price_history_7d=price_history[:7] if price_history else None,
            discount_percentage=discount_pct,
            fragrantica_rating=frag_profile.rating if frag_profile else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}/prices", response_model=List[RetailerPrice])
async def get_product_prices(product_id: str):
    """
    Get all current prices for a product across all retailers.

    Returns prices sorted by total landed cost (GBP) including VAT and shipping.
    """
    try:
        product = get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        latest_prices = data_loader.load_latest_prices()
        prices_for_product = latest_prices.get(product_id, [])

        current_prices = []
        for price_data in prices_for_product:
            retailer = get_retailer_by_id(price_data.get("retailer_id"))
            if retailer:
                current_prices.append(RetailerPrice(
                    retailer_id=price_data.get("retailer_id"),
                    retailer_name=retailer.get("name"),
                    url=price_data.get("url", ""),
                    price_breakdown=PriceBreakdown(
                        base_price_gbp=price_data.get("base_price_gbp", 0),
                        vat_gbp=price_data.get("vat_gbp", 0),
                        shipping_gbp=price_data.get("shipping_gbp", 0),
                        total_gbp=price_data.get("total_gbp", 0),
                    ),
                    in_stock=price_data.get("in_stock", True),
                    last_updated=datetime.fromisoformat(price_data.get("last_updated", datetime.now().isoformat())),
                    tier=retailer.get("tier", 3),
                ))

        # Sort by total price ascending
        current_prices.sort(key=lambda p: p.price_breakdown.total_gbp)

        return current_prices

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prices for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}/history", response_model=List[Dict])
async def get_price_history(
    product_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    retailer: Optional[str] = Query(None, description="Filter by retailer ID"),
):
    """
    Get price history for a product over time.

    Returns time series data suitable for charting. Optional retailer filter.
    """
    try:
        product = get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        history = data_loader.load_price_history(product_id, days=days)

        # Filter by retailer if specified
        if retailer:
            history = [h for h in history if h.get("retailer_id") == retailer]

        return history

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price history for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RETAILER ENDPOINTS
# ============================================================================

@router.get("/retailers", response_model=List[Retailer])
async def list_retailers(tier: Optional[int] = Query(None, description="Filter by tier (1=primary, 2=secondary, 3=tertiary)")):
    """
    List all retailers with current health status.

    Tiers: 1 = Primary (high priority), 2 = Secondary, 3 = Tertiary.
    """
    try:
        registry = data_loader.load_retailer_registry()
        health_data = data_loader.load_health_data()

        retailers = registry.get("retailers", {}).values()

        # Filter by tier
        if tier:
            retailers = [r for r in retailers if r.get("tier") == tier]
        else:
            retailers = list(retailers)

        results = []
        for retailer in retailers:
            retailer_id = retailer.get("retailer_id")
            health = health_data.get(retailer_id, {})

            results.append(Retailer(
                retailer_id=retailer_id,
                name=retailer.get("name"),
                website=retailer.get("website"),
                tier=retailer.get("tier", 3),
                country=retailer.get("country", "GB"),
                health_status=health.get("status", "unknown"),
                products_indexed=health.get("products_indexed", 0),
                last_scan=datetime.fromisoformat(health.get("last_scan")) if health.get("last_scan") else None,
                uptime_percentage=health.get("uptime_percentage"),
                response_time_ms=health.get("response_time_ms"),
            ))

        return results

    except Exception as e:
        logger.error(f"Error listing retailers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retailers/{retailer_id}/health", response_model=HealthMetrics)
async def get_retailer_health(retailer_id: str):
    """
    Get detailed health metrics for a specific retailer.

    Includes uptime, response times, stock status, and recent performance.
    """
    try:
        retailer = get_retailer_by_id(retailer_id)
        if not retailer:
            raise HTTPException(status_code=404, detail=f"Retailer {retailer_id} not found")

        health_data = data_loader.load_health_data()
        health = health_data.get(retailer_id, {})

        return HealthMetrics(
            retailer_id=retailer_id,
            name=retailer.get("name"),
            status=health.get("status", "unknown"),
            uptime_percentage=health.get("uptime_percentage", 0),
            response_time_ms=health.get("response_time_ms", 0),
            last_successful_scan=datetime.fromisoformat(health.get("last_successful_scan")) if health.get("last_successful_scan") else None,
            consecutive_failures=health.get("consecutive_failures", 0),
            products_available=health.get("products_available", 0),
            products_out_of_stock=health.get("products_out_of_stock", 0),
            average_price_change_percentage=health.get("average_price_change_percentage"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting retailer health for {retailer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DEALS & ALERTS
# ============================================================================

@router.get("/deals", response_model=List[Deal])
async def get_deals(
    min_discount_pct: float = Query(15.0, ge=0, le=100, description="Minimum discount percentage"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
):
    """
    Get current best deals across all products.

    Compares current prices to RRP and returns products with discounts above minimum threshold.
    """
    try:
        catalog = data_loader.load_product_catalog()
        latest_prices = data_loader.load_latest_prices()

        products_list = catalog.get("products", {}).values()

        # Filter by brand if specified
        if brand:
            products_list = [p for p in products_list if p.get("brand", "").lower() == brand.lower()]

        deals = []
        for product in products_list:
            product_id = product.get("product_id")
            prices_for_product = latest_prices.get(product_id, [])

            if not prices_for_product:
                continue

            # Find lowest price
            sorted_prices = sorted(prices_for_product, key=lambda p: p.get("total_gbp", float('inf')))
            lowest_price_data = sorted_prices[0]
            current_price = lowest_price_data.get("total_gbp")

            rrp = product.get("rrp_gbp", 0)
            if rrp <= 0:
                continue

            discount_pct, discount_amount = calculate_discount(rrp, current_price)

            # Only include if discount meets threshold
            if discount_pct >= min_discount_pct:
                retailer = get_retailer_by_id(lowest_price_data.get("retailer_id"))
                frag_profile = data_loader.load_fragrantica_profile(product_id)

                deals.append(Deal(
                    product_id=product_id,
                    product_name=product.get("name"),
                    brand=product.get("brand"),
                    rrp_gbp=rrp,
                    current_price_gbp=current_price,
                    discount_percentage=discount_pct,
                    discount_amount_gbp=discount_amount,
                    best_retailer=lowest_price_data.get("retailer_id"),
                    retailer_name=retailer.get("name") if retailer else "Unknown",
                    url=lowest_price_data.get("url", ""),
                    stock_status=lowest_price_data.get("in_stock", True),
                    fragrantica_rating=frag_profile.get("rating") if frag_profile else None,
                ))

        # Sort by discount percentage descending
        deals.sort(key=lambda d: d.discount_percentage, reverse=True)

        return deals[:limit]

    except Exception as e:
        logger.error(f"Error getting deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deals/hot", response_model=List[Deal])
async def get_hot_deals():
    """
    Get products currently below hot deal threshold (extreme discounts).

    Returns only products with exceptional deals (typically 30%+ discount).
    """
    try:
        # Use high threshold for "hot" deals
        return await get_deals(min_discount_pct=30.0, limit=10)
    except Exception as e:
        logger.error(f"Error getting hot deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts", response_model=PriceAlert)
async def create_alert(alert_data: PriceAlertCreate):
    """
    Create a price alert for a product.

    Alert will be triggered when product price drops below target price.
    """
    try:
        product = get_product_by_id(alert_data.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {alert_data.product_id} not found")

        # Generate alert ID
        alert_id = f"alert_{int(time.time() * 1000)}"

        # Get current price
        latest_prices = data_loader.load_latest_prices()
        prices_for_product = latest_prices.get(alert_data.product_id, [])

        current_price = None
        if prices_for_product:
            sorted_prices = sorted(prices_for_product, key=lambda p: p.get("total_gbp", float('inf')))
            current_price = sorted_prices[0].get("total_gbp")

        discount_to_target = None
        if current_price:
            discount_to_target = max(0, current_price - alert_data.target_price_gbp)

        return PriceAlert(
            alert_id=alert_id,
            product_id=alert_data.product_id,
            product_name=product.get("name"),
            brand=product.get("brand"),
            target_price_gbp=alert_data.target_price_gbp,
            current_price_gbp=current_price,
            discount_to_target=discount_to_target,
            email=alert_data.email,
            created_at=datetime.now(),
            is_active=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[PriceAlert])
async def list_alerts(user_id: Optional[str] = Query(None, description="Filter by user ID")):
    """
    List active price alerts.

    Optionally filter by user ID. In production, this would verify user ownership.
    """
    try:
        # Mock implementation - in production would load from database
        # For now, return empty list as placeholder
        return []

    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMPARISON & SEARCH
# ============================================================================

@router.get("/compare", response_model=List[ComparisonProduct])
async def compare_prices(
    product_ids: str = Query(..., description="Comma-separated product IDs"),
):
    """
    Compare prices across multiple products.

    Takes comma-separated product IDs and returns side-by-side price comparison.
    """
    try:
        ids = [pid.strip() for pid in product_ids.split(",")]

        if not ids or len(ids) > 10:
            raise HTTPException(status_code=400, detail="Provide 1-10 comma-separated product IDs")

        catalog = data_loader.load_product_catalog()
        latest_prices = data_loader.load_latest_prices()

        results = []
        for product_id in ids:
            product = get_product_by_id(product_id)
            if not product:
                continue

            prices_for_product = latest_prices.get(product_id, [])

            if not prices_for_product:
                continue

            sorted_prices = sorted(prices_for_product, key=lambda p: p.get("total_gbp", float('inf')))
            lowest = sorted_prices[0]

            rrp = product.get("rrp_gbp", 0)
            lowest_price = lowest.get("total_gbp")
            discount_pct, _ = calculate_discount(rrp, lowest_price)

            results.append(ComparisonProduct(
                product_id=product_id,
                name=product.get("name"),
                brand=product.get("brand"),
                volume_ml=product.get("volume_ml", 0),
                rrp_gbp=rrp,
                lowest_price=lowest_price,
                lowest_retailer=lowest.get("retailer_id"),
                price_difference_from_rrp=rrp - lowest_price,
                discount_percentage=discount_pct,
            ))

        # Sort by lowest price
        results.sort(key=lambda p: p.lowest_price)

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[Product])
async def search_fragrances(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """
    Full-text search across all products.

    Uses fuzzy matching on product names, brands, and notes.
    """
    try:
        catalog = data_loader.load_product_catalog()
        latest_prices = data_loader.load_latest_prices()

        products_list = list(catalog.get("products", {}).values())

        # Fuzzy search across name, brand, description
        search_fields = ["name", "brand", "description"]
        matched = fuzzy_search(q, products_list, search_fields, limit=limit)

        results = []
        for product in matched:
            product_id = product.get("product_id")
            prices_for_product = latest_prices.get(product_id, [])

            lowest_price = None
            lowest_retailer = None
            if prices_for_product:
                sorted_prices = sorted(prices_for_product, key=lambda p: p.get("total_gbp", float('inf')))
                lowest = sorted_prices[0]
                lowest_price = lowest.get("total_gbp")
                lowest_retailer = lowest.get("retailer_id")

            frag_profile = data_loader.load_fragrantica_profile(product_id)
            frag_rating = frag_profile.get("rating") if frag_profile else None

            results.append(Product(
                product_id=product_id,
                name=product.get("name"),
                brand=product.get("brand"),
                volume_ml=product.get("volume_ml", 0),
                rrp_gbp=product.get("rrp_gbp", 0),
                lowest_price_gbp=lowest_price,
                lowest_retailer=lowest_retailer,
                fragrantica_rating=frag_rating,
                image_url=frag_profile.get("image_url") if frag_profile else None,
            ))

        return results

    except Exception as e:
        logger.error(f"Error searching fragrances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ADMIN / SYSTEM ENDPOINTS
# ============================================================================

@router.get("/admin/health", response_model=SystemHealth)
async def system_health():
    """
    System-wide health dashboard.

    Shows overall system status, retailer health breakdown, and recent anomalies.
    """
    try:
        registry = data_loader.load_retailer_registry()
        health_data = data_loader.load_health_data()

        retailers = registry.get("retailers", {}).values()

        healthy = 0
        degraded = 0
        down = 0

        for retailer in retailers:
            retailer_id = retailer.get("retailer_id")
            health = health_data.get(retailer_id, {})
            status = health.get("status", "unknown")

            if status == "healthy":
                healthy += 1
            elif status == "degraded":
                degraded += 1
            elif status == "down":
                down += 1

        catalog = data_loader.load_product_catalog()
        total_products = len(catalog.get("products", {}))

        # Determine overall status
        overall_status = "healthy"
        if down > 0:
            overall_status = "critical"
        elif degraded > 0:
            overall_status = "degraded"

        return SystemHealth(
            timestamp=datetime.now(),
            status=overall_status,
            retailers_healthy=healthy,
            retailers_degraded=degraded,
            retailers_down=down,
            total_products=total_products,
            last_scan_cycle=datetime.now() - timedelta(hours=1),
            next_scan_cycle=datetime.now() + timedelta(hours=1),
            active_alerts=0,
            recent_anomalies=[],
        )

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/scan/trigger", response_model=Dict[str, str])
async def trigger_scan(product_id: Optional[str] = Query(None, description="Optional: scan specific product")):
    """
    Manually trigger a scan cycle.

    Optionally target a specific product. Otherwise scans all products.
    """
    try:
        scan_id = f"scan_{int(time.time() * 1000)}"

        return {
            "scan_id": scan_id,
            "status": "initiated",
            "message": f"Scan {scan_id} has been queued. Check status with /admin/scan/history",
        }

    except Exception as e:
        logger.error(f"Error triggering scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/scan/history", response_model=List[ScanResult])
async def scan_history(limit: int = Query(10, ge=1, le=50, description="Number of recent scans")):
    """
    Get history of recent scan cycles.

    Returns scan execution times, product counts, and error summary.
    """
    try:
        # Mock implementation - in production would load from database
        results = []

        for i in range(limit):
            results.append(ScanResult(
                scan_id=f"scan_{int(time.time() * 1000) - i * 3600000}",
                timestamp=datetime.now() - timedelta(hours=i),
                duration_seconds=245.3 + (i * 10),
                products_scanned=12500 - (i * 50),
                retailers_scanned=18,
                errors=i * 2,
                price_updates=3456 - (i * 100),
                new_products_found=12 - i,
            ))

        return results

    except Exception as e:
        logger.error(f"Error getting scan history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FRAGRANTICA DATA ENDPOINTS
# ============================================================================

@router.get("/products/{product_id}/profile", response_model=FragrantaProfile)
async def get_fragrance_profile(product_id: str):
    """
    Get Fragrantica profile data for a product.

    Returns accords, notes, ratings, and fragrance image.
    """
    try:
        product = get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        frag_data = data_loader.load_fragrantica_profile(product_id)

        if not frag_data:
            raise HTTPException(status_code=404, detail=f"Fragrantica profile not found for {product_id}")

        return FragrantaProfile(
            product_id=product_id,
            fragrantica_id=frag_data.get("fragrantica_id"),
            fragrantica_url=frag_data.get("fragrantica_url"),
            image_url=frag_data.get("image_url"),
            rating=frag_data.get("rating"),
            rating_count=frag_data.get("rating_count"),
            accords=[FragmentaAccord(**a) for a in frag_data.get("accords", [])],
            top_notes=[FragrantaNote(**n) for n in frag_data.get("top_notes", [])],
            middle_notes=[FragrantaNote(**n) for n in frag_data.get("middle_notes", [])],
            base_notes=[FragrantaNote(**n) for n in frag_data.get("base_notes", [])],
            description=frag_data.get("description"),
            longevity=frag_data.get("longevity"),
            sillage=frag_data.get("sillage"),
            last_synced=datetime.fromisoformat(frag_data.get("last_synced")) if frag_data.get("last_synced") else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fragrance profile for {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}/similar", response_model=List[Product])
async def get_similar_fragrances(
    product_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum similar products"),
):
    """
    Get fragrances similar to a given product.

    Based on Fragrantica accord and note data.
    """
    try:
        product = get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        source_profile = data_loader.load_fragrantica_profile(product_id)
        if not source_profile:
            raise HTTPException(status_code=404, detail=f"Fragrantica profile not found for {product_id}")

        # Get all products and find similar ones based on accords
        catalog = data_loader.load_product_catalog()
        latest_prices = data_loader.load_latest_prices()

        source_accords = {a.get("name") for a in source_profile.get("accords", [])}

        similar_matches = []
        for other_product in catalog.get("products", {}).values():
            if other_product.get("product_id") == product_id:
                continue

            other_profile = data_loader.load_fragrantica_profile(other_product.get("product_id"))
            if not other_profile:
                continue

            other_accords = {a.get("name") for a in other_profile.get("accords", [])}

            # Calculate Jaccard similarity
            if source_accords or other_accords:
                intersection = len(source_accords & other_accords)
                union = len(source_accords | other_accords)
                similarity = intersection / union if union > 0 else 0

                if similarity > 0:
                    similar_matches.append((other_product, similarity))

        # Sort by similarity
        similar_matches.sort(key=lambda x: x[1], reverse=True)
        similar_matches = similar_matches[:limit]

        results = []
        for match_product, _ in similar_matches:
            product_id = match_product.get("product_id")
            prices_for_product = latest_prices.get(product_id, [])

            lowest_price = None
            lowest_retailer = None
            if prices_for_product:
                sorted_prices = sorted(prices_for_product, key=lambda p: p.get("total_gbp", float('inf')))
                lowest = sorted_prices[0]
                lowest_price = lowest.get("total_gbp")
                lowest_retailer = lowest.get("retailer_id")

            frag_profile = data_loader.load_fragrantica_profile(product_id)
            frag_rating = frag_profile.get("rating") if frag_profile else None

            results.append(Product(
                product_id=product_id,
                name=match_product.get("name"),
                brand=match_product.get("brand"),
                volume_ml=match_product.get("volume_ml", 0),
                rrp_gbp=match_product.get("rrp_gbp", 0),
                lowest_price_gbp=lowest_price,
                lowest_retailer=lowest_retailer,
                fragrantica_rating=frag_rating,
                image_url=frag_profile.get("image_url") if frag_profile else None,
            ))

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting similar fragrances for {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
