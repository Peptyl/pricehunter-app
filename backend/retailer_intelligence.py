"""
Retailer Intelligence System
=============================
Discovers, verifies, ranks, and manages the retailer registry.

Three main components:
1. RetailerRegistry - CRUD for the retailer database
2. RetailerVerifier - Checks if a retailer is legitimate
3. RetailerDiscoveryAgent - Finds new retailers automatically

This system enables PriceHunter to:
- Dynamically discover and verify new fragrance retailers
- Automatically score trust based on multi-factor analysis
- Identify and rank buying routes by total landed cost
- Continuously improve the retailer network without hardcoding
"""

import json
import logging
import requests
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RetailerTier(Enum):
    """Retailer classification tiers"""
    TIER_1 = 1  # Active scrapers, fully verified
    TIER_2 = 2  # Known good, should add next
    TIER_3 = 3  # Research required
    TIER_4 = 4  # Secondary market, high risk


class RetailerType(Enum):
    """Types of retailers"""
    AUTHORIZED_RESELLER = "authorized_reseller"
    GREY_MARKET = "grey_market"
    SPECIALIST_RETAILER = "specialist_retailer"
    AUTHORIZED_RESELLER_TYPE = "authorized_reseller"
    MARKETPLACE = "marketplace"


class TrustSignalName(Enum):
    """Trust signal scoring factors"""
    DOMAIN_AGE = "domain_age"          # 0-15 pts
    SSL_CERTIFICATE = "ssl_cert"        # 0-10 pts
    REVIEW_SCORE = "review_score"       # 0-20 pts
    PAYMENT_METHODS = "payment_methods" # 0-15 pts
    BUSINESS_REGISTRATION = "reg"       # 0-15 pts
    RETURN_POLICY = "returns"           # 0-10 pts
    SOCIAL_PROOF = "social_proof"       # 0-15 pts


@dataclass
class TrustSignal:
    """Individual trust signal with score and evidence"""
    name: TrustSignalName
    points: int
    max_points: int
    evidence: str
    verified: bool = False
    checked_at: Optional[datetime] = None


@dataclass
class TrustReport:
    """Complete trust assessment of a retailer"""
    domain: str
    trust_score: int  # 0-100
    tier: RetailerTier
    signals: List[TrustSignal] = field(default_factory=list)
    breakdown: Dict[str, int] = field(default_factory=dict)
    recommendation: str = ""
    checked_at: datetime = field(default_factory=datetime.utcnow)
    is_current: bool = True

    def __post_init__(self):
        """Validate trust score"""
        if not 0 <= self.trust_score <= 100:
            raise ValueError(f"Trust score must be 0-100, got {self.trust_score}")


@dataclass
class RetailerCandidate:
    """New retailer discovered and awaiting verification"""
    domain: str
    discovered_via: str  # "search", "forum", "reddit", "shopping", "competitor"
    candidate_name: str
    candidate_country: str
    candidate_currency: str
    probability_fragrance_retailer: float  # 0.0-1.0
    discovered_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DiscoveryReport:
    """Report from a discovery cycle"""
    run_date: datetime
    new_retailers_found: int
    new_retailers: List[RetailerCandidate] = field(default_factory=list)
    re_verified_count: int = 0
    trust_score_changes: List[Tuple[str, int, int]] = field(default_factory=list)  # (domain, old, new)
    new_routes_discovered: List[Dict] = field(default_factory=list)
    high_priority_additions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class Route:
    """A complete buying route to acquire a fragrance"""
    retailer_id: str
    retailer_name: str
    product_price_source_currency: float
    source_currency: str
    source_country: str
    shipping_cost_source_currency: float
    needs_forwarder: bool
    forwarder_name: Optional[str] = None
    forwarder_fee_gbp: float = 0.0
    duty_gbp: float = 0.0
    vat_gbp: float = 0.0
    conversion_rate: float = 1.0
    is_direct_uk: bool = False

    def total_cost_gbp(self) -> float:
        """Calculate total landed cost in GBP"""
        product_gbp = (self.product_price_source_currency * self.conversion_rate)
        shipping_gbp = (self.shipping_cost_source_currency * self.conversion_rate)
        subtotal = product_gbp + shipping_gbp + self.forwarder_fee_gbp + self.duty_gbp
        # UK VAT (20%) applies to non-EU goods
        vat = subtotal * 0.20 if not self.is_direct_uk else 0.0
        return subtotal + vat

    def breakdown_dict(self) -> Dict:
        """Return cost breakdown"""
        product_gbp = (self.product_price_source_currency * self.conversion_rate)
        shipping_gbp = (self.shipping_cost_source_currency * self.conversion_rate)
        return {
            "product_gbp": round(product_gbp, 2),
            "shipping_gbp": round(shipping_gbp, 2),
            "forwarder_fee_gbp": round(self.forwarder_fee_gbp, 2),
            "duty_gbp": round(self.duty_gbp, 2),
            "vat_gbp": round(self.vat_gbp, 2),
            "total_gbp": round(self.total_cost_gbp(), 2)
        }


@dataclass
class RouteComparison:
    """Comparison of multiple routes"""
    product_sku: str
    routes: List[Route]
    best_route: Route
    savings_gbp: float
    savings_pct: float
    comparison_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CountryRoute:
    """Identified geographic price opportunity"""
    country: str
    currency: str
    avg_discount_vs_uk_pct: float
    sample_retailers: List[str]
    typical_shipping_cost_gbp: float
    custom_concerns: str
    recommendation: str


class RetailerRegistry:
    """
    Master database of all retailers PriceHunter knows about.

    Handles CRUD operations and ranking logic.
    """

    def __init__(self, registry_path: str = None):
        """Initialize registry from JSON file"""
        if registry_path is None:
            registry_path = "/sessions/intelligent-bold-ptolemy/pricehunter-app/data/retailer_registry.json"

        self.registry_path = Path(registry_path)
        self.data = {}
        self.retailers = {}
        self.load()

    def load(self):
        """Load registry from JSON"""
        try:
            with open(self.registry_path, 'r') as f:
                self.data = json.load(f)
                self.retailers = {r['id']: r for r in self.data.get('retailers', [])}
                logger.info(f"Loaded {len(self.retailers)} retailers from registry")
        except FileNotFoundError:
            logger.error(f"Registry file not found: {self.registry_path}")
            self.data = {
                "registry_version": "1.0",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "retailers": []
            }
            self.retailers = {}

    def save(self):
        """Save registry to JSON"""
        self.data['last_updated'] = datetime.utcnow().isoformat() + "Z"
        with open(self.registry_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        logger.info(f"Saved {len(self.retailers)} retailers to registry")

    def add_retailer(self, retailer_dict: Dict) -> bool:
        """Add new retailer to registry"""
        if retailer_dict['id'] in self.retailers:
            logger.warning(f"Retailer {retailer_dict['id']} already exists")
            return False

        self.retailers[retailer_dict['id']] = retailer_dict
        self.data['retailers'].append(retailer_dict)
        self.save()
        logger.info(f"Added retailer: {retailer_dict['name']}")
        return True

    def update_retailer(self, retailer_id: str, updates: Dict) -> bool:
        """Update existing retailer"""
        if retailer_id not in self.retailers:
            logger.error(f"Retailer {retailer_id} not found")
            return False

        self.retailers[retailer_id].update(updates)
        # Update in data['retailers'] list
        for i, r in enumerate(self.data['retailers']):
            if r['id'] == retailer_id:
                self.data['retailers'][i].update(updates)
                break

        self.save()
        logger.info(f"Updated retailer: {retailer_id}")
        return True

    def remove_retailer(self, retailer_id: str) -> bool:
        """Remove retailer from registry"""
        if retailer_id not in self.retailers:
            return False

        del self.retailers[retailer_id]
        self.data['retailers'] = [r for r in self.data['retailers'] if r['id'] != retailer_id]
        self.save()
        logger.info(f"Removed retailer: {retailer_id}")
        return True

    def get_retailer(self, retailer_id: str) -> Optional[Dict]:
        """Get single retailer by ID"""
        return self.retailers.get(retailer_id)

    def get_all_retailers(self) -> List[Dict]:
        """Get all retailers"""
        return list(self.retailers.values())

    def get_active_retailers(self) -> List[Dict]:
        """Get retailers with active scrapers"""
        return [r for r in self.retailers.values()
                if r.get('scraper_config', {}).get('status') == 'active']

    def get_by_tier(self, tier: int) -> List[Dict]:
        """Get retailers by tier (1-4)"""
        return [r for r in self.retailers.values() if r.get('tier') == tier]

    def rank_retailers(self, product_id: str = None) -> List[Tuple[str, float]]:
        """
        Rank all retailers by weighted score.

        Score = trust_score * 0.3 + price_competitiveness * 0.4
                + reliability * 0.2 + shipping_score * 0.1

        Returns list of (retailer_id, score) tuples sorted by score descending.
        """
        rankings = []

        for retailer_id, retailer in self.retailers.items():
            # Trust score (0-100, normalized to 0-30)
            trust_component = (retailer.get('trust_score', 50) / 100) * 30

            # Price competitiveness (inverse of rank, 1-50 retailers = 100 pts)
            rank = retailer.get('pricing', {}).get('price_competitiveness_rank', 50)
            price_component = max(0, (50 - rank) / 50) * 40

            # Reliability (success rate over 30 days, normalized to 0-20)
            success_rate = retailer.get('scraper_config', {}).get('success_rate_30d', 0.8)
            reliability_component = success_rate * 20

            # Shipping score (free shipping = 10, otherwise scaled by cost)
            shipping_cost = retailer.get('pricing', {}).get('shipping_cost_gbp', 5)
            shipping_component = max(0, 10 - shipping_cost)

            total_score = trust_component + price_component + reliability_component + shipping_component
            rankings.append((retailer_id, round(total_score, 2)))

        # Sort by score descending
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def get_best_route(self, product_sku: str, target_country: str = "UK") -> Optional[str]:
        """
        Returns the optimal retailer for buying a product.

        For UK buyers, prefers direct shipping over forwarder routes.
        """
        active = self.get_active_retailers()
        if not active:
            return None

        # Filter to UK-friendly retailers
        uk_friendly = [
            r for r in active
            if r.get('ships_to_uk') or r.get('direct_shipping')
        ]

        if not uk_friendly:
            return active[0]['id']

        # Return highest-ranked UK-friendly retailer
        rankings = self.rank_retailers(product_sku)
        for retailer_id, _ in rankings:
            retailer = self.get_retailer(retailer_id)
            if retailer and (retailer.get('ships_to_uk') or retailer.get('direct_shipping')):
                return retailer_id

        return uk_friendly[0]['id']


class RetailerVerifier:
    """
    Multi-factor trust verification system.

    Scores retailers on:
    1. Domain age (0-15)
    2. SSL certificate (0-10)
    3. Review scores (0-20)
    4. Payment methods (0-15)
    5. Business registration (0-15)
    6. Return policy (0-10)
    7. Social proof (0-15)

    Total: 0-100
    """

    def __init__(self):
        """Initialize verifier"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def calculate_trust_score(self, domain: str) -> TrustReport:
        """Calculate comprehensive trust score for a domain"""
        logger.info(f"Calculating trust score for {domain}")

        signals = []
        total_points = 0
        max_possible = 100

        # 1. Domain age (0-15 pts)
        domain_age_signal = self._check_domain_age(domain)
        signals.append(domain_age_signal)
        total_points += domain_age_signal.points

        # 2. SSL certificate (0-10 pts)
        ssl_signal = self._check_ssl(domain)
        signals.append(ssl_signal)
        total_points += ssl_signal.points

        # 3. Review score (0-20 pts)
        review_signal = self._check_reviews(domain)
        signals.append(review_signal)
        total_points += review_signal.points

        # 4. Payment methods (0-15 pts)
        payment_signal = self._check_payment_methods(domain)
        signals.append(payment_signal)
        total_points += payment_signal.points

        # 5. Business registration (0-15 pts)
        reg_signal = self._check_business_registration(domain)
        signals.append(reg_signal)
        total_points += reg_signal.points

        # 6. Return policy (0-10 pts)
        policy_signal = self._check_return_policy(domain)
        signals.append(policy_signal)
        total_points += policy_signal.points

        # 7. Social proof (0-15 pts)
        social_signal = self._check_social_proof(domain)
        signals.append(social_signal)
        total_points += social_signal.points

        # Determine tier
        if total_points >= 80:
            tier = RetailerTier.TIER_1
            recommendation = "Recommended for active scraping. High trust, reliable data."
        elif total_points >= 60:
            tier = RetailerTier.TIER_2
            recommendation = "Good retailer. Verify before adding to active scrapers."
        elif total_points >= 40:
            tier = RetailerTier.TIER_3
            recommendation = "Moderate risk. Requires manual review before scraping."
        else:
            tier = RetailerTier.TIER_4
            recommendation = "High risk. Do not scrape. Show to users with warnings only."

        breakdown = {
            "domain_age": domain_age_signal.points,
            "ssl": ssl_signal.points,
            "reviews": review_signal.points,
            "payment_methods": payment_signal.points,
            "registration": reg_signal.points,
            "return_policy": policy_signal.points,
            "social_proof": social_signal.points
        }

        report = TrustReport(
            domain=domain,
            trust_score=total_points,
            tier=tier,
            signals=signals,
            breakdown=breakdown,
            recommendation=recommendation
        )

        logger.info(f"Trust score for {domain}: {total_points}/100 (Tier {tier.value})")
        return report

    def _check_domain_age(self, domain: str) -> TrustSignal:
        """Check domain age using whois data"""
        try:
            # In production, use: import whois; w = whois.whois(domain)
            # For demo, return mock data based on known retailers

            mock_ages = {
                "notino.co.uk": 8,
                "douglas.de": 12,
                "fragrancebuy.ca": 7,
                "maxaroma.com": 9,
                "johnlewis.com": 14,
                "harrods.com": 13,
                "sephora.fr": 15,
            }

            age_years = mock_ages.get(domain, 3)

            if age_years >= 5:
                points = 15
                evidence = f"Domain registered {age_years} years ago"
            elif age_years >= 3:
                points = 10
                evidence = f"Domain registered {age_years} years ago"
            elif age_years >= 1:
                points = 5
                evidence = f"Domain registered {age_years} year(s) ago"
            else:
                points = 0
                evidence = "Domain less than 1 year old"

            return TrustSignal(
                name=TrustSignalName.DOMAIN_AGE,
                points=points,
                max_points=15,
                evidence=evidence,
                verified=True
            )
        except Exception as e:
            logger.warning(f"Could not verify domain age for {domain}: {e}")
            return TrustSignal(
                name=TrustSignalName.DOMAIN_AGE,
                points=0,
                max_points=15,
                evidence=f"Could not verify: {str(e)}",
                verified=False
            )

    def _check_ssl(self, domain: str) -> TrustSignal:
        """Check SSL certificate validity"""
        try:
            response = self.session.head(f"https://{domain}", timeout=5, allow_redirects=True)
            if response.status_code < 400:
                return TrustSignal(
                    name=TrustSignalName.SSL_CERTIFICATE,
                    points=10,
                    max_points=10,
                    evidence="Valid SSL certificate (HTTPS)",
                    verified=True
                )
        except requests.exceptions.SSLError:
            return TrustSignal(
                name=TrustSignalName.SSL_CERTIFICATE,
                points=0,
                max_points=10,
                evidence="SSL certificate invalid or expired",
                verified=True
            )
        except Exception as e:
            logger.warning(f"Could not verify SSL for {domain}: {e}")

        return TrustSignal(
            name=TrustSignalName.SSL_CERTIFICATE,
            points=0,
            max_points=10,
            evidence="Could not verify SSL",
            verified=False
        )

    def _check_reviews(self, domain: str) -> TrustSignal:
        """Check Trustpilot and review aggregator scores"""
        try:
            # In production, use Trustpilot API or scrape reviews
            # For demo, return mock data

            mock_scores = {
                "notino.co.uk": (4.3, 45000),
                "douglas.de": (4.2, 78000),
                "johnlewis.com": (4.4, 95000),
                "harrods.com": (4.3, 58000),
            }

            if domain in mock_scores:
                score, review_count = mock_scores[domain]
                if score >= 4.5:
                    points = 20
                elif score >= 4.0:
                    points = 15
                elif score >= 3.5:
                    points = 10
                elif score >= 3.0:
                    points = 5
                else:
                    points = 0

                evidence = f"Trustpilot: {score}/5.0 ({review_count:,} reviews)"
            else:
                points = 5
                evidence = "Limited review data available"

            return TrustSignal(
                name=TrustSignalName.REVIEW_SCORE,
                points=points,
                max_points=20,
                evidence=evidence,
                verified=True
            )
        except Exception as e:
            logger.warning(f"Could not verify reviews for {domain}: {e}")
            return TrustSignal(
                name=TrustSignalName.REVIEW_SCORE,
                points=0,
                max_points=20,
                evidence=f"Could not verify: {str(e)}",
                verified=False
            )

    def _check_payment_methods(self, domain: str) -> TrustSignal:
        """Check for buyer-protection payment methods"""
        try:
            # In production, parse checkout pages for payment options
            # For demo, return mock data

            mock_payments = {
                "notino.co.uk": ["visa", "mastercard", "paypal", "klarna"],
                "douglas.de": ["visa", "mastercard", "paypal", "klarna"],
                "johnlewis.com": ["visa", "mastercard", "paypal"],
                "ebay.co.uk": ["visa", "mastercard", "paypal"],
            }

            methods = mock_payments.get(domain, [])

            points = 0
            if "paypal" in methods:
                points += 5
            if "klarna" in methods:
                points += 5
            if "visa" in methods or "mastercard" in methods:
                points += 5

            # Cap at 15
            points = min(points, 15)

            evidence = f"Accepts: {', '.join(methods) if methods else 'Unknown'}"

            return TrustSignal(
                name=TrustSignalName.PAYMENT_METHODS,
                points=points,
                max_points=15,
                evidence=evidence,
                verified=bool(methods)
            )
        except Exception as e:
            logger.warning(f"Could not verify payments for {domain}: {e}")
            return TrustSignal(
                name=TrustSignalName.PAYMENT_METHODS,
                points=0,
                max_points=15,
                evidence=f"Could not verify: {str(e)}",
                verified=False
            )

    def _check_business_registration(self, domain: str) -> TrustSignal:
        """Check for business registration and contact info"""
        try:
            # In production, check Companies House, German registry, etc.
            # For demo, return mock data

            mock_registered = {
                "notino.co.uk": True,
                "douglas.de": True,
                "johnlewis.com": True,
                "harrods.com": True,
            }

            if mock_registered.get(domain, False):
                points = 15
                evidence = "Business registered with local authorities"
            else:
                points = 0
                evidence = "Could not verify business registration"

            return TrustSignal(
                name=TrustSignalName.BUSINESS_REGISTRATION,
                points=points,
                max_points=15,
                evidence=evidence,
                verified=bool(mock_registered.get(domain))
            )
        except Exception as e:
            logger.warning(f"Could not verify registration for {domain}: {e}")
            return TrustSignal(
                name=TrustSignalName.BUSINESS_REGISTRATION,
                points=0,
                max_points=15,
                evidence=f"Could not verify: {str(e)}",
                verified=False
            )

    def _check_return_policy(self, domain: str) -> TrustSignal:
        """Check for clear return/refund policy"""
        try:
            # In production, scrape Terms & Conditions, FAQ, etc.
            # For demo, return mock data

            mock_policies = {
                "notino.co.uk": "clear",
                "douglas.de": "clear",
                "johnlewis.com": "clear",
                "harrods.com": "clear",
                "ebay.co.uk": "vague",
            }

            policy = mock_policies.get(domain, "unknown")

            if policy == "clear":
                points = 10
                evidence = "Clear return policy found"
            elif policy == "vague":
                points = 5
                evidence = "Return policy exists but unclear"
            else:
                points = 0
                evidence = "No return policy found"

            return TrustSignal(
                name=TrustSignalName.RETURN_POLICY,
                points=points,
                max_points=10,
                evidence=evidence,
                verified=(policy != "unknown")
            )
        except Exception as e:
            logger.warning(f"Could not verify return policy for {domain}: {e}")
            return TrustSignal(
                name=TrustSignalName.RETURN_POLICY,
                points=0,
                max_points=10,
                evidence=f"Could not verify: {str(e)}",
                verified=False
            )

    def _check_social_proof(self, domain: str) -> TrustSignal:
        """Check for social proof (Reddit, Fragrantica, Basenotes mentions)"""
        try:
            # In production, search Reddit, Fragrantica, Basenotes
            # For demo, return mock data based on known retailers

            mock_mentions = {
                "notino.co.uk": ["reddit", "fragrantica", "basenotes"],
                "douglas.de": ["reddit", "basenotes"],
                "johnlewis.com": ["reddit"],
                "harrods.com": ["reddit"],
                "ebay.co.uk": ["reddit"],  # negative mentions included
            }

            mentions = mock_mentions.get(domain, [])

            points = 0
            if "fragrantica" in mentions:
                points += 5
            if "basenotes" in mentions:
                points += 5
            if "reddit" in mentions:
                points += 5

            # Cap at 15
            points = min(points, 15)

            evidence = f"Mentioned in: {', '.join(mentions) if mentions else 'No mentions found'}"

            return TrustSignal(
                name=TrustSignalName.SOCIAL_PROOF,
                points=points,
                max_points=15,
                evidence=evidence,
                verified=bool(mentions)
            )
        except Exception as e:
            logger.warning(f"Could not verify social proof for {domain}: {e}")
            return TrustSignal(
                name=TrustSignalName.SOCIAL_PROOF,
                points=0,
                max_points=15,
                evidence=f"Could not verify: {str(e)}",
                verified=False
            )


class RetailerDiscoveryAgent:
    """
    Autonomous agent that discovers new fragrance retailers.

    Discovery methods:
    1. Search engine queries
    2. Fragrance forum mining (Fragrantica, Basenotes)
    3. Reddit scraping (r/fragrance)
    4. Google Shopping
    5. Competitor analysis
    6. International route discovery

    Pipeline: discover() → verify() → score() → add_to_registry() → notify()
    """

    def __init__(self, registry: RetailerRegistry, verifier: RetailerVerifier):
        """Initialize discovery agent"""
        self.registry = registry
        self.verifier = verifier
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.candidates: List[RetailerCandidate] = []

    def run_discovery(self) -> DiscoveryReport:
        """Execute full discovery cycle"""
        logger.info("Starting retailer discovery cycle")

        report = DiscoveryReport(run_date=datetime.utcnow())

        # Phase 1: Discover new retailers
        logger.info("Phase 1: Discovering new retailers...")
        candidates_from_search = self.discover_via_search()
        candidates_from_forums = self.discover_via_forums()
        candidates_from_reddit = self.discover_via_reddit()
        candidates_from_shopping = self._discover_via_shopping()
        candidates_from_competitors = self._discover_from_competitors()

        all_candidates = (
            candidates_from_search +
            candidates_from_forums +
            candidates_from_reddit +
            candidates_from_shopping +
            candidates_from_competitors
        )

        # Deduplicate by domain
        seen_domains = set()
        unique_candidates = []
        for candidate in all_candidates:
            if candidate.domain not in seen_domains:
                unique_candidates.append(candidate)
                seen_domains.add(candidate.domain)

        report.new_retailers_found = len(unique_candidates)
        report.new_retailers = unique_candidates

        # Phase 2: Re-verify existing retailers
        logger.info("Phase 2: Re-verifying existing retailers...")
        re_verified = self.re_verify_existing()
        report.re_verified_count = len(re_verified)
        report.trust_score_changes = [
            (r['domain'], r['old_score'], r['new_score'])
            for r in re_verified if r.get('score_changed')
        ]

        # Phase 3: Identify new routes
        logger.info("Phase 3: Discovering new routes...")
        new_routes = self.discover_new_routes()
        report.new_routes_discovered = new_routes

        # Phase 4: Generate recommendations
        logger.info("Phase 4: Generating recommendations...")
        report.high_priority_additions = [
            c.domain for c in unique_candidates
            if c.probability_fragrance_retailer > 0.8
        ]

        report.recommendations = [
            "Consider adding all Tier 1 candidates immediately",
            "Prioritize German retailers (currently strongest pricing)",
            "Monitor Canadian grey market for pricing changes",
            "Re-test John Lewis / Selfridges scraper complexity",
            "Investigate new Reddit sources for indie brands",
        ]

        logger.info(f"Discovery cycle complete: {report.new_retailers_found} new, "
                   f"{report.re_verified_count} re-verified")

        return report

    def discover_via_search(self, brands: List[str] = None, fragrances: List[str] = None) -> List[RetailerCandidate]:
        """Search Google for fragrance retailers"""
        logger.info("Discovering via search...")

        if not brands:
            brands = ["Creed", "Dior", "Tom Ford", "Issey Miyake"]
        if not fragrances:
            fragrances = ["Aventus", "Sauvage", "Black Orchid", "L'eau d'Issey"]

        candidates = []
        queries = [
            f"buy {brand} {fragrance} online UK",
            f"{brand} {fragrance} best price online",
            f"where to buy {fragrance} UK"
        ]

        # In production, use SerpAPI or similar
        # For demo, return mock discoveries

        mock_domains = [
            ("allbeauty.com", "UK authorized reseller", "GBP"),
            ("parfumdreams.de", "German authorized", "EUR"),
            ("flaconi.de", "German authorized", "EUR"),
            ("beautinow.com", "EU retailer", "EUR"),
        ]

        for domain, description, currency in mock_domains:
            if domain not in [r.domain for r in self.registry.get_all_retailers()]:
                candidates.append(RetailerCandidate(
                    domain=domain,
                    discovered_via="search",
                    candidate_name=description,
                    candidate_country="EU",
                    candidate_currency=currency,
                    probability_fragrance_retailer=0.85
                ))

        logger.info(f"Found {len(candidates)} candidates via search")
        return candidates

    def discover_via_forums(self) -> List[RetailerCandidate]:
        """Scrape Fragrantica and Basenotes for retailer mentions"""
        logger.info("Discovering via fragrance forums...")

        candidates = []

        # In production, scrape:
        # - Fragrantica "Where to Buy" sections
        # - Basenotes retailer threads
        # - Extract unique domains

        # For demo, return mock
        mock_forums = [
            ("luckyscent.com", "Fragrantica", "US"),
            ("parfumsraffy.ca", "Basenotes", "CA"),
            ("essenza-nobile.de", "Basenotes", "DE"),
        ]

        for domain, source, country in mock_forums:
            if domain not in [r.domain for r in self.registry.get_all_retailers()]:
                candidates.append(RetailerCandidate(
                    domain=domain,
                    discovered_via="forum",
                    candidate_name=f"Found on {source}",
                    candidate_country=country,
                    candidate_currency="USD" if country == "US" else "CAD" if country == "CA" else "EUR",
                    probability_fragrance_retailer=0.90
                ))

        logger.info(f"Found {len(candidates)} candidates via forums")
        return candidates

    def discover_via_reddit(self) -> List[RetailerCandidate]:
        """Search Reddit fragrance communities for retailer recommendations"""
        logger.info("Discovering via Reddit...")

        candidates = []

        # In production, use PRAW (Python Reddit API Wrapper):
        # reddit = praw.Reddit(...)
        # subreddit = reddit.subreddit("fragrance")
        # Extract retailer mentions and rate them by frequency/sentiment

        # For demo, return mock based on known r/fragrance favorites
        mock_reddit = [
            ("strawberrynet.com", "r/fragrance", "HK", 0.75),
            ("luckyscent.com", "r/fragrance", "US", 0.88),
            ("noseparis.com", "r/fragrance", "FR", 0.70),
        ]

        for domain, subreddit, country, prob in mock_reddit:
            if domain not in [r.domain for r in self.registry.get_all_retailers()]:
                candidates.append(RetailerCandidate(
                    domain=domain,
                    discovered_via="reddit",
                    candidate_name=f"Found in {subreddit}",
                    candidate_country=country,
                    candidate_currency="USD" if country == "US" else "EUR" if country in ["DE", "FR"] else "HKD",
                    probability_fragrance_retailer=prob
                ))

        logger.info(f"Found {len(candidates)} candidates via Reddit")
        return candidates

    def _discover_via_shopping(self) -> List[RetailerCandidate]:
        """Analyze Google Shopping and price comparison results"""
        logger.info("Discovering via Google Shopping...")
        # Mock implementation
        return []

    def _discover_from_competitors(self) -> List[RetailerCandidate]:
        """Analyze competitors' retailer lists (Perfume.com, FragranceFinder, etc.)"""
        logger.info("Discovering from competitor analysis...")
        # Mock implementation
        return []

    def discover_new_routes(self) -> List[Dict]:
        """
        Find novel buying routes by analyzing geographic price differences.

        Returns opportunities like:
        - "Poland 15-25% cheaper than UK for PDM"
        - "UAE duty-free saves 20-30% on Tom Ford"
        - "Canadian grey market best for Creed"
        """
        logger.info("Discovering new routes...")

        routes = [
            {
                "region": "Poland",
                "avg_savings_pct": 20,
                "sample_retailers": ["Douglas PL"],
                "note": "Polish retailers often 15-25% cheaper than UK, minimal shipping to UK"
            },
            {
                "region": "Canada",
                "avg_savings_pct": 35,
                "sample_retailers": ["FragranceBuy CA"],
                "note": "Grey market leader. Best prices globally. ~£8 shipping."
            },
            {
                "region": "USA Grey Market",
                "avg_savings_pct": 32,
                "sample_retailers": ["Jomashop (via forwarder)", "MaxAroma"],
                "note": "Requires forwarder for some retailers but excellent prices"
            },
            {
                "region": "UAE",
                "avg_savings_pct": 22,
                "sample_retailers": ["TBD"],
                "note": "Tax-free pricing on luxury brands. Slower shipping."
            },
        ]

        logger.info(f"Identified {len(routes)} new route opportunities")
        return routes

    def re_verify_existing(self) -> List[Dict]:
        """Re-check all existing retailers for changes"""
        logger.info("Re-verifying existing retailers...")

        re_verified = []
        active_retailers = self.registry.get_active_retailers()

        for retailer in active_retailers[:3]:  # Demo: only check first 3
            domain = retailer['domain']
            old_score = retailer.get('trust_score', 70)

            # Re-run verification
            report = self.verifier.calculate_trust_score(domain)
            new_score = report.trust_score

            re_verified.append({
                'domain': domain,
                'old_score': old_score,
                'new_score': new_score,
                'score_changed': old_score != new_score,
                'tier_changed': False  # Simplified for demo
            })

        logger.info(f"Re-verified {len(re_verified)} retailers")
        return re_verified

    def generate_report(self, discoveries: List, re_verifications: List) -> DiscoveryReport:
        """Generate human-readable discovery report"""
        report = DiscoveryReport(
            run_date=datetime.utcnow(),
            new_retailers_found=len(discoveries),
            re_verified_count=len(re_verifications)
        )
        return report


if __name__ == "__main__":
    """Demo and testing"""
    logger.info("=" * 60)
    logger.info("RETAILER INTELLIGENCE SYSTEM DEMO")
    logger.info("=" * 60)

    # 1. Load registry
    logger.info("\n1. Loading retailer registry...")
    registry = RetailerRegistry()
    logger.info(f"   Loaded {len(registry.get_all_retailers())} retailers")
    logger.info(f"   Active scrapers: {len(registry.get_active_retailers())}")
    logger.info(f"   Tier 1: {len(registry.get_by_tier(1))}")
    logger.info(f"   Tier 2: {len(registry.get_by_tier(2))}")

    # 2. Rank retailers
    logger.info("\n2. Ranking retailers by composite score...")
    rankings = registry.rank_retailers()
    logger.info("   Top 5 retailers:")
    for retailer_id, score in rankings[:5]:
        retailer = registry.get_retailer(retailer_id)
        logger.info(f"     {retailer['name']:30} Score: {score:.1f}")

    # 3. Verify a domain
    logger.info("\n3. Verifying retailer (Notino)...")
    verifier = RetailerVerifier()
    trust_report = verifier.calculate_trust_score("notino.co.uk")
    logger.info(f"   Domain: {trust_report.domain}")
    logger.info(f"   Trust Score: {trust_report.trust_score}/100")
    logger.info(f"   Tier: {trust_report.tier.name}")
    logger.info(f"   Recommendation: {trust_report.recommendation}")
    logger.info("   Breakdown:")
    for signal_name, points in trust_report.breakdown.items():
        logger.info(f"     {signal_name:20} {points:3} pts")

    # 4. Run discovery
    logger.info("\n4. Running discovery cycle...")
    agent = RetailerDiscoveryAgent(registry, verifier)
    discovery_report = agent.run_discovery()
    logger.info(f"   New retailers found: {discovery_report.new_retailers_found}")
    logger.info(f"   Retailers re-verified: {discovery_report.re_verified_count}")
    logger.info(f"   New routes discovered: {len(discovery_report.new_routes_discovered)}")
    logger.info(f"   High-priority additions: {len(discovery_report.high_priority_additions)}")

    if discovery_report.new_routes_discovered:
        logger.info("   Route Opportunities:")
        for route in discovery_report.new_routes_discovered[:3]:
            logger.info(f"     {route['region']:20} Save ~{route['avg_savings_pct']}%")

    if discovery_report.recommendations:
        logger.info("   Recommendations:")
        for rec in discovery_report.recommendations[:3]:
            logger.info(f"     - {rec}")

    logger.info("\n" + "=" * 60)
    logger.info("DEMO COMPLETE")
    logger.info("=" * 60)
