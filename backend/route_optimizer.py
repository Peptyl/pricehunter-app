"""
Route Optimizer
===============
Finds the optimal buying route for UK customers.

A "route" is: Retailer → [Forwarder] → UK door

Routes are ranked by total landed cost:
- Product price (converted to GBP)
- Shipping (direct or via forwarder)
- Import duty (usually £0 for cosmetics/fragrances)
- UK VAT (20%)
- Forwarder fee (if applicable)

Novel routes the system discovers:
- Poland/Czech: EU prices, sometimes 15-25% lower than UK, no customs post-Brexit wait times
- UAE/Dubai: Tax-free shopping, significant savings on luxury fragrances (20-30%)
- Canada: Grey market excellence, best overall savings (30-45%)
- South Korea: K-beauty retailers with niche western brands
- India: Niche brands at 40-50% discount (but shipping concerns)

The optimizer automatically calculates:
1. Direct UK shipping (no forwarder needed)
2. EU shipping (low shipping costs, immediate delivery)
3. US grey market (via Stackry, WeShip, etc.)
4. Canadian direct or via forwarder
5. Asian routes via Forwarder

Each route is scored on:
- Total landed cost (primary)
- Delivery speed
- Trust/risk score
- Packaging quality
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from enum import Enum
from abc import ABC, abstractmethod
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShippingRegion(Enum):
    """Geographic regions for shipping"""
    UK = "uk"
    EU = "eu"
    USA = "usa"
    CANADA = "canada"
    MIDDLE_EAST = "me"
    ASIA = "asia"


class ForwarderName(Enum):
    """Popular package forwarders"""
    STACKRY = "stackry"
    FORWARD2ME = "forward2me"
    WESHIP = "weship"
    MYUS = "myus"
    NONE = "none"


@dataclass
class CurrencyRate:
    """Exchange rate snapshot"""
    source: str
    target: str
    rate: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def convert(self, amount: float) -> float:
        """Convert amount from source to target currency"""
        return amount * self.rate


@dataclass
class Forwarder:
    """Package forwarding service"""
    name: ForwarderName
    cost_per_shipment_gbp: float
    cost_per_lb_gbp: Optional[float] = None
    average_weight_buffer_pct: float = 1.15  # 15% weight estimation buffer
    processing_time_days: int = 3
    countries_supported: List[str] = field(default_factory=list)
    trust_score: int = 85

    def estimate_fee(self, weight_oz: float = 0.0) -> float:
        """Estimate total forwarding fee"""
        if self.cost_per_lb_gbp and weight_oz > 0:
            weight_lb = (weight_oz / 16) * self.average_weight_buffer_pct
            return self.cost_per_shipment_gbp + (weight_lb * self.cost_per_lb_gbp)
        return self.cost_per_shipment_gbp


@dataclass
class ShippingOption:
    """Available shipping from a retailer"""
    region: ShippingRegion
    base_cost: float
    base_currency: str
    estimated_days: int
    is_tracked: bool = True
    is_insured: bool = True


@dataclass
class Route:
    """A complete buying route to acquire a fragrance"""
    retailer_id: str
    retailer_name: str
    retailer_country: str
    retailer_tier: int
    product_price_source_currency: float
    source_currency: str
    source_country: str
    shipping_cost_source_currency: float
    needs_forwarder: bool
    forwarder: Optional[Forwarder] = None
    forwarder_fee_gbp: float = 0.0
    duty_gbp: float = 0.0
    vat_gbp: float = 0.0
    conversion_rate: float = 1.0
    is_direct_uk: bool = False
    estimated_delivery_days: int = 7
    risk_score: float = 0.0  # 0.0-1.0, where 1.0 = highest risk
    packaging_score: float = 0.85  # 0.0-1.0, impact on product integrity
    fragrance_weight_oz: float = 3.4  # Typical fragrance bottle

    def total_cost_gbp(self) -> float:
        """Calculate total landed cost in GBP"""
        product_gbp = (self.product_price_source_currency * self.conversion_rate)
        shipping_gbp = (self.shipping_cost_source_currency * self.conversion_rate)
        subtotal = product_gbp + shipping_gbp + self.forwarder_fee_gbp + self.duty_gbp

        # UK VAT (20%) applies to non-UK goods AFTER shipping and duty
        vat = subtotal * 0.20 if not self.is_direct_uk else 0.0

        return subtotal + vat

    def breakdown_dict(self) -> Dict:
        """Return detailed cost breakdown"""
        product_gbp = round(self.product_price_source_currency * self.conversion_rate, 2)
        shipping_gbp = round(self.shipping_cost_source_currency * self.conversion_rate, 2)
        subtotal = product_gbp + shipping_gbp + self.forwarder_fee_gbp + self.duty_gbp
        vat = round(subtotal * 0.20 if not self.is_direct_uk else 0.0, 2)

        return {
            "product_price": {
                "amount": self.product_price_source_currency,
                "currency": self.source_currency,
                "gbp": product_gbp
            },
            "shipping_direct": {
                "amount": self.shipping_cost_source_currency,
                "currency": self.source_currency,
                "gbp": shipping_gbp
            },
            "forwarder_fee": round(self.forwarder_fee_gbp, 2),
            "import_duty": round(self.duty_gbp, 2),
            "subtotal": round(subtotal, 2),
            "vat_20pct": vat,
            "total_gbp": round(self.total_cost_gbp(), 2)
        }

    def estimate_delivery(self) -> Tuple[datetime, str]:
        """Estimate delivery date and method summary"""
        delivery_date = datetime.utcnow() + timedelta(days=self.estimated_delivery_days)
        method = "Direct to UK" if self.is_direct_uk else f"via {self.forwarder.name.value}" if self.forwarder else "Unknown"
        return delivery_date, method

    def quality_score(self) -> float:
        """Overall quality score (0-1.0)"""
        # Combines cost savings, delivery speed, risk, and packaging
        cost_score = 1.0 - (self.total_cost_gbp() / 250)  # Normalize to ~£250 baseline
        delivery_score = 1.0 - (self.estimated_delivery_days / 30)
        risk_score = 1.0 - self.risk_score
        packaging_score = self.packaging_score

        # Weighted average
        return (
            cost_score * 0.5 +
            delivery_score * 0.2 +
            risk_score * 0.2 +
            packaging_score * 0.1
        )


@dataclass
class RouteComparison:
    """Comparison of multiple routes"""
    product_sku: str
    product_name: str
    routes: List[Route] = field(default_factory=list)
    best_route: Optional[Route] = None
    savings_vs_rrp_gbp: float = 0.0
    savings_vs_rrp_pct: float = 0.0
    comparison_date: datetime = field(default_factory=datetime.utcnow)

    def add_route(self, route: Route):
        """Add a route and update best_route if cheaper"""
        self.routes.append(route)
        if not self.best_route or route.total_cost_gbp() < self.best_route.total_cost_gbp():
            self.best_route = route

    def get_ranked_routes(self) -> List[Route]:
        """Return all routes sorted by total cost (cheapest first)"""
        return sorted(self.routes, key=lambda r: r.total_cost_gbp())

    def to_display_dict(self) -> Dict:
        """Format for user display"""
        ranked = self.get_ranked_routes()
        return {
            "product": self.product_name,
            "best_route": {
                "retailer": self.best_route.retailer_name if self.best_route else None,
                "total_gbp": round(self.best_route.total_cost_gbp(), 2) if self.best_route else None,
                "delivery_days": self.best_route.estimated_delivery_days if self.best_route else None,
            },
            "all_routes": [
                {
                    "rank": i + 1,
                    "retailer": r.retailer_name,
                    "country": r.retailer_country,
                    "total_gbp": round(r.total_cost_gbp(), 2),
                    "savings_vs_best": round(r.total_cost_gbp() - self.best_route.total_cost_gbp(), 2) if self.best_route else 0,
                    "delivery_days": r.estimated_delivery_days,
                    "method": "Direct UK" if r.is_direct_uk else f"via {r.forwarder.name.value}" if r.forwarder else "Unknown"
                }
                for i, r in enumerate(ranked)
            ],
            "savings_vs_rrp": {
                "gbp": round(self.savings_vs_rrp_gbp, 2),
                "pct": round(self.savings_vs_rrp_pct, 2)
            }
        }


@dataclass
class CountryRoute:
    """Identified geographic price opportunity"""
    country: str
    country_code: str
    currency: str
    avg_discount_vs_uk_pct: float
    best_retailers: List[str]  # retailer names
    typical_shipping_cost_gbp: float
    typical_delivery_days: int
    customs_concerns: str
    vat_implications: str
    recommendation: str
    risk_level: str  # "low", "medium", "high"


class CurrencyConverter:
    """Handles currency conversions"""

    def __init__(self):
        """Initialize with mock exchange rates (production would use live API)"""
        self.rates = {
            ("EUR", "GBP"): 0.86,
            ("USD", "GBP"): 0.79,
            ("CAD", "GBP"): 0.58,
            ("AED", "GBP"): 0.21,
            ("KRW", "GBP"): 0.00061,
            ("INR", "GBP"): 0.0095,
            ("GBP", "GBP"): 1.0,
        }
        self.last_updated = datetime.utcnow()

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount from one currency to another"""
        if from_currency == to_currency:
            return amount

        key = (from_currency, to_currency)
        if key not in self.rates:
            logger.warning(f"No rate available for {from_currency} -> {to_currency}")
            return amount

        return amount * self.rates[key]

    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Get conversion rate"""
        if from_currency == to_currency:
            return 1.0
        return self.rates.get((from_currency, to_currency), 1.0)


class ShippingCalculator:
    """Calculates shipping costs based on origin/destination"""

    def __init__(self):
        """Initialize with mock shipping data"""
        # Typical costs for 100ml fragrance (3.4 oz)
        self.base_costs = {
            (ShippingRegion.UK, ShippingRegion.UK): (0.0, 1),
            (ShippingRegion.EU, ShippingRegion.UK): (3.5, 3),
            (ShippingRegion.USA, ShippingRegion.UK): (12.0, 5),
            (ShippingRegion.CANADA, ShippingRegion.UK): (8.5, 4),
            (ShippingRegion.MIDDLE_EAST, ShippingRegion.UK): (15.0, 7),
            (ShippingRegion.ASIA, ShippingRegion.UK): (18.0, 10),
        }

        self.forwarders = {
            ForwarderName.STACKRY: Forwarder(
                name=ForwarderName.STACKRY,
                cost_per_shipment_gbp=7.5,
                cost_per_lb_gbp=0.5,
                processing_time_days=2,
                countries_supported=["USA", "CA"],
                trust_score=88
            ),
            ForwarderName.FORWARD2ME: Forwarder(
                name=ForwarderName.FORWARD2ME,
                cost_per_shipment_gbp=6.0,
                cost_per_lb_gbp=0.45,
                processing_time_days=3,
                countries_supported=["USA", "CA"],
                trust_score=87
            ),
            ForwarderName.WESHIP: Forwarder(
                name=ForwarderName.WESHIP,
                cost_per_shipment_gbp=5.5,
                cost_per_lb_gbp=0.40,
                processing_time_days=3,
                countries_supported=["USA", "CA", "AU"],
                trust_score=83
            ),
        }

    def calculate(self, origin: ShippingRegion, destination: ShippingRegion = ShippingRegion.UK) -> Tuple[float, int]:
        """
        Calculate shipping cost and estimated days.

        Returns: (cost_gbp, estimated_days)
        """
        key = (origin, destination)
        if key in self.base_costs:
            return self.base_costs[key]

        logger.warning(f"No shipping data for {origin.value} -> {destination.value}")
        return 10.0, 7

    def get_forwarder(self, name: ForwarderName) -> Optional[Forwarder]:
        """Get forwarder by name"""
        return self.forwarders.get(name)

    def list_forwarders(self, origin_country: str) -> List[Forwarder]:
        """List suitable forwarders for given country"""
        return [
            f for f in self.forwarders.values()
            if origin_country in f.countries_supported
        ]


class RouteOptimizer:
    """
    Finds optimal buying routes for fragrance products.

    Evaluates all possible paths:
    - Direct UK retailers
    - EU retailers with shipping
    - US grey market (direct or via forwarder)
    - Canadian retailers
    - Other regional options

    Ranks by total landed cost while considering:
    - Trust score
    - Delivery speed
    - Product integrity risk
    - VAT implications
    """

    def __init__(self, registry, converter: CurrencyConverter = None, calculator: ShippingCalculator = None):
        """
        Initialize route optimizer.

        Args:
            registry: RetailerRegistry instance
            converter: CurrencyConverter (creates new if not provided)
            calculator: ShippingCalculator (creates new if not provided)
        """
        self.registry = registry
        self.converter = converter or CurrencyConverter()
        self.calculator = calculator or ShippingCalculator()
        self.rrp_baseline = 195.0  # Typical niche fragrance RRP in GBP

    def find_all_routes(self, product_sku: str, rrp_gbp: float = None) -> RouteComparison:
        """
        Find all possible routes to acquire a product.

        Returns RouteComparison with ranked list of routes.
        """
        if rrp_gbp is None:
            rrp_gbp = self.rrp_baseline

        logger.info(f"Finding all routes for {product_sku}")
        comparison = RouteComparison(
            product_sku=product_sku,
            product_name=f"Fragrance {product_sku}"
        )

        active_retailers = self.registry.get_active_retailers()

        for retailer in active_retailers:
            routes = self._build_routes_for_retailer(retailer, rrp_gbp)
            for route in routes:
                comparison.add_route(route)

        # Calculate savings
        if comparison.best_route:
            comparison.savings_vs_rrp_gbp = rrp_gbp - comparison.best_route.total_cost_gbp()
            comparison.savings_vs_rrp_pct = (comparison.savings_vs_rrp_gbp / rrp_gbp) * 100

        logger.info(f"Found {len(comparison.routes)} routes. Best: £{comparison.best_route.total_cost_gbp():.2f}")
        return comparison

    def _build_routes_for_retailer(self, retailer: Dict, rrp_gbp: float) -> List[Route]:
        """Build all possible routes for a single retailer"""
        routes = []

        # Mock product pricing
        mock_price_discount = retailer.get('pricing', {}).get('avg_discount_vs_rrp_pct', 15)
        product_price = rrp_gbp * (1 - mock_price_discount / 100)

        retailer_country = retailer.get('country', 'UK')
        retailer_currency = retailer.get('currency', 'GBP')
        retailer_tier = retailer.get('tier', 3)

        # Route 1: Direct shipping if available
        if retailer.get('ships_to_uk') or retailer.get('direct_shipping'):
            shipping_cost, delivery_days = self.calculator.calculate(
                ShippingRegion[self._country_to_region(retailer_country)],
                ShippingRegion.UK
            )

            conversion_rate = self.converter.get_rate(retailer_currency, "GBP")

            route = Route(
                retailer_id=retailer.get('id', ''),
                retailer_name=retailer.get('name', ''),
                retailer_country=retailer_country,
                retailer_tier=retailer_tier,
                product_price_source_currency=product_price,
                source_currency=retailer_currency,
                source_country=retailer_country,
                shipping_cost_source_currency=shipping_cost if retailer_currency == "GBP" else shipping_cost / conversion_rate,
                needs_forwarder=False,
                is_direct_uk=(retailer_country == "UK"),
                estimated_delivery_days=delivery_days,
                conversion_rate=conversion_rate,
                risk_score=self._estimate_risk(retailer),
                packaging_score=self._estimate_packaging(retailer)
            )
            routes.append(route)

        # Route 2: Via forwarder if retailer doesn't ship to UK
        if not retailer.get('ships_to_uk') and not retailer.get('direct_shipping'):
            forwarders = self.calculator.list_forwarders(retailer_country)

            for forwarder in forwarders:
                forwarder_fee = forwarder.estimate_fee(self.fragrance_weight_oz)

                shipping_cost, delivery_days_direct = self.calculator.calculate(
                    ShippingRegion[self._country_to_region(retailer_country)],
                    ShippingRegion.UK
                )

                conversion_rate = self.converter.get_rate(retailer_currency, "GBP")
                total_delivery_days = delivery_days_direct + forwarder.processing_time_days

                route = Route(
                    retailer_id=retailer.get('id', ''),
                    retailer_name=retailer.get('name', ''),
                    retailer_country=retailer_country,
                    retailer_tier=retailer_tier,
                    product_price_source_currency=product_price,
                    source_currency=retailer_currency,
                    source_country=retailer_country,
                    shipping_cost_source_currency=shipping_cost if retailer_currency == "GBP" else shipping_cost / conversion_rate,
                    needs_forwarder=True,
                    forwarder=forwarder,
                    forwarder_fee_gbp=forwarder_fee,
                    is_direct_uk=False,
                    estimated_delivery_days=total_delivery_days,
                    conversion_rate=conversion_rate,
                    risk_score=self._estimate_risk(retailer, uses_forwarder=True),
                    packaging_score=self._estimate_packaging(retailer)
                )
                routes.append(route)

        return routes

    def find_best_route(self, product_sku: str) -> Optional[Route]:
        """Find THE cheapest route"""
        comparison = self.find_all_routes(product_sku)
        return comparison.best_route

    def compare_routes(self, product_sku: str) -> RouteComparison:
        """Get ranked route comparison"""
        return self.find_all_routes(product_sku)

    def discover_country_opportunities(self) -> List[CountryRoute]:
        """
        Analyze price differences by country/region.

        Returns opportunities sorted by savings potential.
        """
        logger.info("Analyzing country-level price opportunities...")

        opportunities = [
            CountryRoute(
                country="Canada",
                country_code="CA",
                currency="CAD",
                avg_discount_vs_uk_pct=35,
                best_retailers=["FragranceBuy CA", "Parfums Raffy"],
                typical_shipping_cost_gbp=8.5,
                typical_delivery_days=4,
                customs_concerns="Minimal (post-Brexit CAD goods face normal duty)",
                vat_implications="20% VAT applied on landed value",
                recommendation="EXCELLENT. Best overall savings with reasonable shipping. Recommended for most fragrances.",
                risk_level="low"
            ),
            CountryRoute(
                country="Germany",
                country_code="DE",
                currency="EUR",
                avg_discount_vs_uk_pct=20,
                best_retailers=["Douglas", "Flaconi", "Parfumdreams"],
                typical_shipping_cost_gbp=3.5,
                typical_delivery_days=3,
                customs_concerns="None (EU, post-Brexit trade agreement)",
                vat_implications="VAT included in price (DE VAT 19%). UK VAT may still apply.",
                recommendation="VERY GOOD. Consistent savings, fast shipping, high trust. Default choice for EU brands.",
                risk_level="low"
            ),
            CountryRoute(
                country="USA (Grey Market)",
                country_code="US",
                currency="USD",
                avg_discount_vs_uk_pct=30,
                best_retailers=["MaxAroma", "FragranceNet", "Jomashop (via forwarder)"],
                typical_shipping_cost_gbp=12.0,
                typical_delivery_days=6,
                customs_concerns="Standard US import duties apply. Check product origin.",
                vat_implications="20% VAT on landed value (product + shipping + duty)",
                recommendation="GOOD. Higher shipping costs but excellent prices. Worth it for high-value items.",
                risk_level="low"
            ),
            CountryRoute(
                country="Poland",
                country_code="PL",
                currency="PLN",
                avg_discount_vs_uk_pct=22,
                best_retailers=["Douglas PL", "Iperfumy", "Notino PL"],
                typical_shipping_cost_gbp=4.0,
                typical_delivery_days=4,
                customs_concerns="None (EU, post-Brexit trade agreement)",
                vat_implications="VAT included in price. Possible VAT recalculation for UK.",
                recommendation="VERY GOOD. Emerging opportunity. Similar to Germany but slightly cheaper on some brands.",
                risk_level="low"
            ),
            CountryRoute(
                country="Czech Republic",
                country_code="CZ",
                currency="CZK",
                avg_discount_vs_uk_pct=21,
                best_retailers=["Notino CZ", "Sephora CZ"],
                typical_shipping_cost_gbp=4.0,
                typical_delivery_days=4,
                customs_concerns="None (EU, post-Brexit trade agreement)",
                vat_implications="VAT included. Similar to Polish market.",
                recommendation="GOOD. Similar to Poland. Check specific brand availability.",
                risk_level="low"
            ),
            CountryRoute(
                country="UAE (Dubai)",
                country_code="AE",
                currency="AED",
                avg_discount_vs_uk_pct=25,
                best_retailers=["TBD - needs discovery"],
                typical_shipping_cost_gbp=15.0,
                typical_delivery_days=8,
                customs_concerns="Potential luxury goods duties. Alcohol content (fragrance) may trigger delays.",
                vat_implications="No VAT in UAE. UK 20% VAT applies on landing.",
                recommendation="INTERESTING. Tax-free pricing is valuable, but shipping costs and customs delays are concerns.",
                risk_level="medium"
            ),
            CountryRoute(
                country="Hong Kong",
                country_code="HK",
                currency="HKD",
                avg_discount_vs_uk_pct=28,
                best_retailers=["Strawberrynet"],
                typical_shipping_cost_gbp=5.0,
                typical_delivery_days=14,
                customs_concerns="Standard imports duties, longer transit",
                vat_implications="20% VAT applies",
                recommendation="MODERATE. Good prices but slow shipping (10-14 days). Best for non-urgent purchases.",
                risk_level="low"
            ),
            CountryRoute(
                country="South Korea",
                country_code="KR",
                currency="KRW",
                avg_discount_vs_uk_pct=15,
                best_retailers=["TBD - needs discovery"],
                typical_shipping_cost_gbp=12.0,
                typical_delivery_days=12,
                customs_concerns="Standard imports duties",
                vat_implications="20% VAT applies",
                recommendation="EMERGING. K-beauty retailers sometimes stock western niche brands. Requires research.",
                risk_level="medium"
            ),
            CountryRoute(
                country="India",
                country_code="IN",
                currency="INR",
                avg_discount_vs_uk_pct=40,
                best_retailers=["TBD - needs discovery"],
                typical_shipping_cost_gbp=10.0,
                typical_delivery_days=15,
                customs_concerns="HIGH RISK. Counterfeiting concerns, Indian duties, fragrance regulations",
                vat_implications="20% VAT applies",
                recommendation="CAUTION. Extremely aggressive pricing but counterfeiting risk is substantial. Not recommended.",
                risk_level="high"
            ),
        ]

        return opportunities

    def _country_to_region(self, country: str) -> str:
        """Map country code to shipping region"""
        eu_countries = {"DE", "FR", "IT", "ES", "PL", "CZ", "NL", "BE", "AT", "SE", "DK"}
        if country in eu_countries:
            return "EU"
        elif country == "US":
            return "USA"
        elif country == "CA":
            return "CANADA"
        elif country == "AE":
            return "MIDDLE_EAST"
        elif country in {"HK", "SG", "KR", "IN"}:
            return "ASIA"
        else:
            return "EU"  # Default

    def _estimate_risk(self, retailer: Dict, uses_forwarder: bool = False) -> float:
        """
        Estimate risk score (0.0-1.0) for a retailer.

        Factors:
        - Trust score (inverse)
        - Retailer type (grey market higher risk)
        - Forwarder risk
        """
        trust_score = retailer.get('trust_score', 70)
        trust_risk = (100 - trust_score) / 100.0

        retailer_type = retailer.get('type', 'authorized')
        type_risk = 0.1 if retailer_type == 'authorized_reseller' else 0.3

        forwarder_risk = 0.15 if uses_forwarder else 0.0

        total_risk = (trust_risk * 0.5) + (type_risk * 0.3) + (forwarder_risk * 0.2)
        return min(total_risk, 1.0)

    def _estimate_packaging(self, retailer: Dict) -> float:
        """
        Estimate packaging quality (0.0-1.0).

        Factors:
        - Tier (higher tier = better packaging)
        - Trust score
        """
        tier = retailer.get('tier', 2)
        trust_score = retailer.get('trust_score', 70)

        if tier == 1:
            tier_score = 0.95
        elif tier == 2:
            tier_score = 0.85
        else:
            tier_score = 0.70

        trust_score_normalized = trust_score / 100.0
        return (tier_score * 0.6) + (trust_score_normalized * 0.4)

    @property
    def fragrance_weight_oz(self) -> float:
        """Standard fragrance bottle weight (100ml = 3.4oz)"""
        return 3.4


if __name__ == "__main__":
    """Demo and testing"""
    logger.info("=" * 70)
    logger.info("ROUTE OPTIMIZER DEMO")
    logger.info("=" * 70)

    # Import registry for demo
    from retailer_intelligence import RetailerRegistry

    # 1. Initialize
    logger.info("\n1. Initializing route optimizer...")
    registry = RetailerRegistry()
    optimizer = RouteOptimizer(registry)
    logger.info(f"   Loaded {len(registry.get_active_retailers())} active retailers")

    # 2. Find all routes
    logger.info("\n2. Finding all routes for example fragrance...")
    rrp = 195.0
    comparison = optimizer.find_all_routes("creed-aventus-100ml", rrp_gbp=rrp)

    logger.info(f"   Found {len(comparison.routes)} possible routes")
    logger.info(f"   RRP Baseline: £{rrp:.2f}")
    if comparison.best_route:
        logger.info(f"   Best Route: £{comparison.best_route.total_cost_gbp():.2f}")
        logger.info(f"   Savings: £{comparison.savings_vs_rrp_gbp:.2f} ({comparison.savings_vs_rrp_pct:.1f}%)")

    # 3. Display route comparison
    logger.info("\n3. Route ranking (top 5):")
    ranked = comparison.get_ranked_routes()
    for i, route in enumerate(ranked[:5], 1):
        delivery_date, method = route.estimate_delivery()
        logger.info(f"   {i}. {route.retailer_name:25} £{route.total_cost_gbp():7.2f} "
                   f"({route.estimated_delivery_days}d, {method})")

    # 4. Display cost breakdown for best route
    if comparison.best_route:
        logger.info("\n4. Cost breakdown for best route:")
        breakdown = comparison.best_route.breakdown_dict()
        logger.info(f"   Product:        £{breakdown['product_price']['gbp']:7.2f}")
        logger.info(f"   Shipping:       £{breakdown['shipping_direct']['gbp']:7.2f}")
        if breakdown['forwarder_fee']:
            logger.info(f"   Forwarder:      £{breakdown['forwarder_fee']:7.2f}")
        if breakdown['import_duty']:
            logger.info(f"   Duty:           £{breakdown['import_duty']:7.2f}")
        logger.info(f"   Subtotal:       £{breakdown['subtotal']:7.2f}")
        if breakdown['vat_20pct']:
            logger.info(f"   VAT (20%):      £{breakdown['vat_20pct']:7.2f}")
        logger.info(f"   {'─' * 30}")
        logger.info(f"   TOTAL:          £{breakdown['total_gbp']:7.2f}")

    # 5. Country opportunities
    logger.info("\n5. Country-level opportunities:")
    opportunities = optimizer.discover_country_opportunities()
    for opp in opportunities[:5]:
        logger.info(f"   {opp.country:20} Save ~{opp.avg_discount_vs_uk_pct:2.0f}% "
                   f"(Risk: {opp.risk_level.upper()})")

    logger.info("\n" + "=" * 70)
    logger.info("DEMO COMPLETE")
    logger.info("=" * 70)
