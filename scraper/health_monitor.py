#!/usr/bin/env python3
"""
Olfex Health Monitor
===========================
Tracks scraper health metrics and triggers self-healing when issues detected.

Monitors:
- Success/failure rate per retailer
- Price anomalies (sudden jumps/drops)
- Extraction method failures (JSON-LD broken, Shopify API changed, etc.)
- Response time trends
- Stock data consistency
- Circuit breaker states

Self-healing actions:
- Fallback to alternative extraction methods
- Temporary retailer disabling (circuit breaker)
- Alert generation for manual intervention

Usage:
    python health_monitor.py --dashboard              # Show health dashboard
    python health_monitor.py --diagnose notino        # Run diagnostics on retailer
    python health_monitor.py --anomalies              # Show recent anomalies
"""

import json
import logging
import statistics
import asyncio
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Overall health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    DISABLED = "disabled"


@dataclass
class RetailerHealth:
    """Health metrics for a single retailer"""
    retailer: str
    status: HealthStatus
    success_rate_1h: float  # 0-100%
    success_rate_24h: float  # 0-100%
    avg_response_time_ms: float
    median_response_time_ms: float
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    consecutive_failures: int
    price_anomalies_24h: int
    extraction_method: str  # current working method
    fallback_methods: List[str]  # available fallbacks
    circuit_breaker_until: Optional[datetime]
    total_requests: int = 0
    total_failures: int = 0

    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is currently active"""
        if not self.circuit_breaker_until:
            return False
        return datetime.utcnow() < self.circuit_breaker_until

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        d['status'] = self.status.value
        d['last_success'] = self.last_success.isoformat() if self.last_success else None
        d['last_failure'] = self.last_failure.isoformat() if self.last_failure else None
        d['circuit_breaker_until'] = self.circuit_breaker_until.isoformat() \
            if self.circuit_breaker_until else None
        return d


@dataclass
class PriceAnomaly:
    """Detected price anomaly for investigation"""
    product_id: str
    retailer: str
    previous_price: float
    current_price: float
    change_pct: float
    detected_at: datetime
    anomaly_type: str  # "spike", "drop", "disappeared", "new_listing"
    reason: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['detected_at'] = self.detected_at.isoformat()
        return d


@dataclass
class ScanResult:
    """Result from a single scan for tracking"""
    retailer: str
    product_id: str
    success: bool
    response_time_ms: float
    price: Optional[float] = None
    currency: Optional[str] = None
    in_stock: Optional[bool] = None
    error: Optional[str] = None
    extraction_method: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


class HealthMonitor:
    """Monitors and maintains scraper health"""

    # Thresholds for health status
    HEALTHY_SUCCESS_RATE_24H = 95.0
    DEGRADED_SUCCESS_RATE_24H = 80.0
    FAILING_SUCCESS_RATE_24H = 50.0

    HEALTHY_RESPONSE_TIME_MS = 3000
    DEGRADED_RESPONSE_TIME_MS = 8000

    MAX_CONSECUTIVE_FAILURES = 10
    PRICE_SPIKE_THRESHOLD_PCT = 30.0  # 30% change
    PRICE_DROP_THRESHOLD_PCT = 30.0
    PRICE_ANOMALY_THRESHOLD_7DAY = 50.0  # 50% from 7-day avg

    CIRCUIT_BREAKER_TIMEOUT = 600  # 10 minutes

    def __init__(self, data_dir: str = "data/health"):
        """Initialize health monitor"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.retailer_health: Dict[str, RetailerHealth] = {}
        self.anomalies: deque = deque(maxlen=1000)  # Keep last 1000 anomalies
        self.scan_history: deque = deque(maxlen=10000)  # Keep last 10k scans
        self.price_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)  # Keep last 100 prices per product
        )

        self._initialize_retailers()
        self.load_state()

    def _initialize_retailers(self) -> None:
        """Initialize health records for all known retailers"""
        retailers = [
            "notino", "nichegallerie", "fragrancebuy", "seescents",
            "maxaroma", "jomashop", "fragrancenet", "douglas_de"
        ]

        for retailer in retailers:
            self.retailer_health[retailer] = RetailerHealth(
                retailer=retailer,
                status=HealthStatus.HEALTHY,
                success_rate_1h=100.0,
                success_rate_24h=100.0,
                avg_response_time_ms=0.0,
                median_response_time_ms=0.0,
                last_success=None,
                last_failure=None,
                consecutive_failures=0,
                price_anomalies_24h=0,
                extraction_method="json_ld",
                fallback_methods=[],
                circuit_breaker_until=None,
            )

    def record_scan_result(self, result: ScanResult) -> None:
        """Record a single scan result and update metrics"""
        self.scan_history.append(result)

        retailer = result.retailer
        if retailer not in self.retailer_health:
            logger.warning(f"Unknown retailer: {retailer}")
            return

        health = self.retailer_health[retailer]

        if result.success:
            health.last_success = result.timestamp
            health.consecutive_failures = 0
            health.total_requests += 1

            if result.price is not None:
                key = f"{result.product_id}_{retailer}"
                self.price_history[key].append({
                    "price": result.price,
                    "currency": result.currency,
                    "timestamp": result.timestamp,
                    "in_stock": result.in_stock,
                })

        else:
            health.last_failure = result.timestamp
            health.consecutive_failures += 1
            health.total_failures += 1
            health.total_requests += 1

        # Update health status
        self._update_health_status(retailer)

        logger.debug(
            f"Recorded scan: {retailer}/{result.product_id} "
            f"success={result.success} time={result.response_time_ms:.0f}ms"
        )

    def check_price_anomaly(self, product_id: str, retailer: str,
                            new_price: float, currency: str = "GBP") -> Optional[PriceAnomaly]:
        """
        Check if a new price is anomalous compared to history.
        Returns PriceAnomaly if detected, None otherwise.
        """
        key = f"{product_id}_{retailer}"
        history = self.price_history.get(key, [])

        if not history:
            # New listing
            return PriceAnomaly(
                product_id=product_id,
                retailer=retailer,
                previous_price=0.0,
                current_price=new_price,
                change_pct=0.0,
                detected_at=datetime.utcnow(),
                anomaly_type="new_listing",
            )

        last_price = history[-1]["price"]
        change_pct = ((new_price - last_price) / last_price * 100) if last_price > 0 else 0

        # Check for spike
        if change_pct > self.PRICE_SPIKE_THRESHOLD_PCT:
            anomaly = PriceAnomaly(
                product_id=product_id,
                retailer=retailer,
                previous_price=last_price,
                current_price=new_price,
                change_pct=change_pct,
                detected_at=datetime.utcnow(),
                anomaly_type="spike",
                reason=f"Price increased {change_pct:.1f}%"
            )
            self.anomalies.append(anomaly)
            return anomaly

        # Check for drop
        if change_pct < -self.PRICE_DROP_THRESHOLD_PCT:
            anomaly = PriceAnomaly(
                product_id=product_id,
                retailer=retailer,
                previous_price=last_price,
                current_price=new_price,
                change_pct=change_pct,
                detected_at=datetime.utcnow(),
                anomaly_type="drop",
                reason=f"Price decreased {abs(change_pct):.1f}%"
            )
            self.anomalies.append(anomaly)
            return anomaly

        # Check 7-day trend
        if len(history) >= 7:
            prices_7d = [h["price"] for h in list(history)[-7:]]
            avg_7d = statistics.mean(prices_7d)
            trend_change = ((new_price - avg_7d) / avg_7d * 100) if avg_7d > 0 else 0

            if abs(trend_change) > self.PRICE_ANOMALY_THRESHOLD_7DAY:
                anomaly = PriceAnomaly(
                    product_id=product_id,
                    retailer=retailer,
                    previous_price=avg_7d,
                    current_price=new_price,
                    change_pct=trend_change,
                    detected_at=datetime.utcnow(),
                    anomaly_type="drop" if trend_change < 0 else "spike",
                    reason=f"Price deviates {abs(trend_change):.1f}% from 7-day average"
                )
                self.anomalies.append(anomaly)
                return anomaly

        return None

    def _update_health_status(self, retailer: str) -> None:
        """Update health status for a retailer based on metrics"""
        health = self.retailer_health[retailer]

        # Calculate success rates
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        recent_1h = [
            r for r in self.scan_history
            if r.retailer == retailer and r.timestamp > one_hour_ago
        ]
        recent_24h = [
            r for r in self.scan_history
            if r.retailer == retailer and r.timestamp > day_ago
        ]

        if recent_1h:
            successes_1h = sum(1 for r in recent_1h if r.success)
            health.success_rate_1h = (successes_1h / len(recent_1h)) * 100

        if recent_24h:
            successes_24h = sum(1 for r in recent_24h if r.success)
            health.success_rate_24h = (successes_24h / len(recent_24h)) * 100

            # Calculate response times
            response_times = [r.response_time_ms for r in recent_24h if r.success]
            if response_times:
                health.avg_response_time_ms = statistics.mean(response_times)
                health.median_response_time_ms = statistics.median(response_times)

        # Determine overall status
        if health.is_circuit_open():
            health.status = HealthStatus.DISABLED
        elif health.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
            health.status = HealthStatus.FAILING
            logger.error(f"Retailer {retailer} failing: {health.consecutive_failures} "
                         f"consecutive failures")
        elif health.success_rate_24h < self.FAILING_SUCCESS_RATE_24H:
            health.status = HealthStatus.FAILING
        elif health.success_rate_24h < self.DEGRADED_SUCCESS_RATE_24H:
            health.status = HealthStatus.DEGRADED
        else:
            health.status = HealthStatus.HEALTHY

        # Update anomaly count
        health.price_anomalies_24h = sum(
            1 for a in self.anomalies
            if a.retailer == retailer and a.detected_at > day_ago
        )

    def get_retailer_health(self, retailer: str) -> Optional[RetailerHealth]:
        """Get current health status for a retailer"""
        return self.retailer_health.get(retailer)

    def get_dashboard(self) -> Dict:
        """Get full health dashboard data for visualization"""
        overall_status = self._calculate_overall_status()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status.value,
            "retailers": {
                name: health.to_dict()
                for name, health in self.retailer_health.items()
            },
            "recent_anomalies": [
                a.to_dict() for a in list(self.anomalies)[-20:]
            ],
            "scan_stats_24h": self._calculate_scan_stats(),
            "extraction_methods": {
                name: health.extraction_method
                for name, health in self.retailer_health.items()
            },
        }

    def _calculate_overall_status(self) -> HealthStatus:
        """Calculate overall health status"""
        statuses = [h.status for h in self.retailer_health.values()]
        failed_count = sum(1 for s in statuses if s == HealthStatus.FAILING)
        disabled_count = sum(1 for s in statuses if s == HealthStatus.DISABLED)

        if disabled_count > len(statuses) / 2:
            return HealthStatus.FAILING
        if failed_count > 2 or disabled_count > 1:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def _calculate_scan_stats(self) -> Dict:
        """Calculate 24-hour scan statistics"""
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)

        recent = [r for r in self.scan_history if r.timestamp > day_ago]

        if not recent:
            return {
                "total_scans": 0,
                "successful_scans": 0,
                "failed_scans": 0,
                "success_rate": 0.0,
                "avg_response_time_ms": 0.0,
            }

        successful = sum(1 for r in recent if r.success)
        failed = len(recent) - successful
        response_times = [r.response_time_ms for r in recent if r.success]

        return {
            "total_scans": len(recent),
            "successful_scans": successful,
            "failed_scans": failed,
            "success_rate": (successful / len(recent) * 100) if recent else 0.0,
            "avg_response_time_ms": statistics.mean(response_times) if response_times else 0.0,
        }

    def should_skip_retailer(self, retailer: str) -> bool:
        """Check if retailer should be skipped (circuit breaker)"""
        health = self.retailer_health.get(retailer)
        if not health:
            return False

        # Skip if circuit breaker is open
        if health.is_circuit_open():
            logger.warning(f"Skipping {retailer}: circuit breaker active")
            return True

        # Skip if failing
        if health.status == HealthStatus.FAILING:
            logger.warning(f"Skipping {retailer}: status is FAILING")
            return True

        return False

    def suggest_extraction_method(self, retailer: str) -> Optional[str]:
        """
        Suggest best extraction method based on recent success rates.
        Returns None if no working method found.
        """
        health = self.retailer_health.get(retailer)
        if not health:
            return None

        # Return current method if it's working well
        if health.success_rate_24h > 90.0:
            return health.extraction_method

        # Try fallback methods
        for method in health.fallback_methods:
            logger.info(f"Suggesting fallback method for {retailer}: {method}")
            return method

        return None

    def trigger_circuit_breaker(self, retailer: str) -> None:
        """Temporarily disable retailer due to repeated failures"""
        health = self.retailer_health.get(retailer)
        if not health:
            return

        health.circuit_breaker_until = datetime.utcnow() + timedelta(
            seconds=self.CIRCUIT_BREAKER_TIMEOUT
        )
        health.status = HealthStatus.DISABLED

        logger.error(
            f"Circuit breaker triggered for {retailer} "
            f"until {health.circuit_breaker_until.isoformat()}"
        )

    def reset_circuit_breaker(self, retailer: str) -> None:
        """Manually reset circuit breaker"""
        health = self.retailer_health.get(retailer)
        if not health:
            return

        health.circuit_breaker_until = None
        health.consecutive_failures = 0
        health.status = HealthStatus.HEALTHY

        logger.info(f"Circuit breaker reset for {retailer}")

    def save_state(self) -> None:
        """Persist health data to disk"""
        try:
            # Save retailer health
            health_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "retailers": {
                    name: health.to_dict()
                    for name, health in self.retailer_health.items()
                },
                "recent_anomalies": [
                    a.to_dict() for a in list(self.anomalies)[-100:]
                ],
            }

            with open(self.data_dir / "health.json", 'w') as f:
                json.dump(health_data, f, indent=2)

            logger.debug("Saved health state to disk")

        except Exception as e:
            logger.error(f"Failed to save health state: {e}")

    def load_state(self) -> None:
        """Load health data from disk"""
        try:
            health_file = self.data_dir / "health.json"
            if not health_file.exists():
                logger.info("No previous health state found")
                return

            with open(health_file, 'r') as f:
                data = json.load(f)

            for name, health_dict in data.get("retailers", {}).items():
                if name in self.retailer_health:
                    health = self.retailer_health[name]
                    health.success_rate_1h = health_dict.get("success_rate_1h", 100.0)
                    health.success_rate_24h = health_dict.get("success_rate_24h", 100.0)
                    health.consecutive_failures = health_dict.get("consecutive_failures", 0)
                    health.total_requests = health_dict.get("total_requests", 0)
                    health.total_failures = health_dict.get("total_failures", 0)

            logger.info("Loaded health state from disk")

        except Exception as e:
            logger.error(f"Failed to load health state: {e}")

    def generate_alert(self, retailer: str, severity: str, message: str) -> Dict:
        """Generate an alert for notification"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "retailer": retailer,
            "severity": severity,  # "info", "warning", "error"
            "message": message,
            "health": self.retailer_health.get(retailer, {}).to_dict() if retailer else None,
        }


class SelfHealer:
    """Automatic recovery actions when issues detected"""

    # Fallback extraction methods per retailer
    EXTRACTION_FALLBACK_ORDER = {
        "notino": ["json_ld", "html_css", "playwright"],
        "nichegallerie": ["woocommerce_html", "site_search", "playwright"],
        "fragrancebuy": ["shopify_json", "html_css", "playwright"],
        "seescents": ["shopify_json", "html_css", "playwright"],
        "maxaroma": ["playwright", "json_ld", "html_css"],
        "jomashop": ["playwright", "html_css", "json_ld"],
        "fragrancenet": ["json_ld", "html_css", "playwright"],
        "douglas_de": ["json_ld", "playwright", "html_css"],
    }

    def __init__(self, monitor: HealthMonitor):
        """Initialize self-healer with monitor"""
        self.monitor = monitor

    def attempt_recovery(self, retailer: str) -> Dict:
        """
        Try to recover a failing retailer.
        Returns recovery result with status and recommended action.
        """
        health = self.monitor.retailer_health.get(retailer)
        if not health:
            return {"status": "error", "reason": "Unknown retailer"}

        logger.info(f"Attempting recovery for {retailer}")

        # Try fallback extraction methods
        fallback_methods = self.EXTRACTION_FALLBACK_ORDER.get(retailer, [])
        for method in fallback_methods:
            if method == health.extraction_method:
                continue  # Skip current method

            logger.info(f"Trying fallback method {method} for {retailer}")
            # In production, this would test the extraction method
            health.extraction_method = method
            health.fallback_methods = [
                m for m in fallback_methods if m != method
            ]

            return {
                "status": "recovery_attempted",
                "retailer": retailer,
                "action": "switched_extraction_method",
                "new_method": method,
                "next_fallback": health.fallback_methods[0] if health.fallback_methods else None,
            }

        # All fallback methods exhausted - trigger circuit breaker
        logger.error(f"All fallback methods exhausted for {retailer}")
        self.monitor.trigger_circuit_breaker(retailer)

        return {
            "status": "recovery_failed",
            "retailer": retailer,
            "action": "circuit_breaker_triggered",
            "timeout_seconds": self.monitor.CIRCUIT_BREAKER_TIMEOUT,
        }

    async def run_diagnostic(self, retailer: str) -> Dict:
        """
        Run diagnostic tests on a retailer.
        In production, would test each extraction method.
        """
        logger.info(f"Running diagnostics for {retailer}")

        methods = self.EXTRACTION_FALLBACK_ORDER.get(retailer, [])
        results = {}

        for method in methods:
            # In production, would actually test the method
            results[method] = {
                "status": "untested",
                "response_time_ms": None,
                "error": None,
            }

        return {
            "retailer": retailer,
            "timestamp": datetime.utcnow().isoformat(),
            "methods": results,
            "recommended": methods[0] if methods else None,
        }


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Olfex Health Monitor")
    parser.add_argument("--dashboard", action="store_true", help="Show health dashboard")
    parser.add_argument("--diagnose", type=str, help="Run diagnostics on a retailer")
    parser.add_argument("--anomalies", action="store_true", help="Show recent anomalies")
    parser.add_argument("--data-dir", default="data/health", help="Data directory")
    args = parser.parse_args()

    monitor = HealthMonitor(args.data_dir)

    if args.dashboard:
        dashboard = monitor.get_dashboard()
        print(json.dumps(dashboard, indent=2))

    elif args.diagnose:
        healer = SelfHealer(monitor)
        result = asyncio.run(healer.run_diagnostic(args.diagnose))
        print(json.dumps(result, indent=2))

    elif args.anomalies:
        anomalies = [a.to_dict() for a in list(monitor.anomalies)[-20:]]
        print(json.dumps({"anomalies": anomalies}, indent=2))

    else:
        parser.print_help()
