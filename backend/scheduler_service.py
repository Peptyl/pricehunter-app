#!/usr/bin/env python3
"""
Olfex Scheduler Service
Runs price scans on schedule and manages the pipeline:
  1. Scan prices (6:00, 12:00, 18:00 GMT)
  2. Store results in PostgreSQL
  3. Trigger alert checks
  4. Log metrics
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import psycopg2
import psycopg2.extras

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:
    BackgroundScheduler = None

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'olfex')
DB_USER = os.getenv('DB_USER', 'olfex')
DB_PASS = os.getenv('DB_PASS', 'olfex123')

SCAN_TIMES = os.getenv('SCHEDULER_SCAN_TIMES', '06:00,12:00,18:00').split(',')
TIMEZONE = os.getenv('SCHEDULER_TIMEZONE', 'UTC')
ENABLED = os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'true'

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_conn():
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# ============================================================================
# SCHEDULER SERVICE
# ============================================================================

class SchedulerService:
    """Manages scheduled price scans and alert pipeline."""

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = None
        self.is_running = False
        self._init_scheduler()

    def _init_scheduler(self):
        """Initialize APScheduler."""
        if not BackgroundScheduler:
            logger.error("APScheduler not installed")
            return

        self.scheduler = BackgroundScheduler()

    def start(self):
        """Start the scheduler."""
        if not ENABLED:
            logger.info("Scheduler disabled via SCHEDULER_ENABLED")
            return

        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return

        try:
            # Schedule scans at specified times
            for scan_time in SCAN_TIMES:
                hour, minute = scan_time.strip().split(':')
                logger.info(f"Scheduling scan at {scan_time} {TIMEZONE}")

                self.scheduler.add_job(
                    self.run_scan,
                    'cron',
                    hour=hour,
                    minute=minute,
                    timezone=TIMEZONE,
                    id=f'price_scan_{scan_time}',
                    name=f'Price Scan {scan_time}'
                )

            self.scheduler.start()
            self.is_running = True
            logger.info("✅ Scheduler started")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")

    def run_scan(self) -> Dict:
        """
        Execute price scan for all products in catalog.

        Returns:
            Dict with scan results and metrics
        """
        scan_start = datetime.now()
        logger.info("=" * 70)
        logger.info(f"STARTING PRICE SCAN - {scan_start.isoformat()}")
        logger.info("=" * 70)

        try:
            # Import here to avoid circular imports
            from backend.scraper_service import get_scraper_service

            scraper_svc = get_scraper_service()

            # Get all deals
            deals_result = scraper_svc.get_all_deals('pro')
            deals = deals_result.get('deals', [])

            # Store in database
            stored_count = self._store_prices(deals)

            # Check alerts and send notifications
            alerts_triggered = self._check_alerts(deals)

            # Calculate metrics
            metrics = {
                'scan_time': scan_start.isoformat(),
                'duration_seconds': (datetime.now() - scan_start).total_seconds(),
                'products_scanned': len(scraper_svc.catalog.get('products', [])),
                'deals_found': len(deals),
                'prices_stored': stored_count,
                'alerts_triggered': alerts_triggered
            }

            self._log_metrics(metrics)

            return {
                'success': True,
                'metrics': metrics
            }

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _store_prices(self, deals: List[Dict]) -> int:
        """
        Store price data in PostgreSQL price_history table.

        Args:
            deals: List of deal dicts from scraper

        Returns:
            Number of prices stored
        """
        if not deals:
            return 0

        try:
            conn = get_db_conn()
            c = conn.cursor()

            stored = 0

            for deal in deals:
                try:
                    c.execute('''
                        INSERT INTO price_history
                        (perfume_id, retailer, price, currency, size_ml, in_stock, scraped_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        deal.get('product_id'),
                        deal.get('retailer'),
                        deal.get('price'),
                        deal.get('currency', 'GBP'),
                        deal.get('size_ml'),
                        deal.get('in_stock', True),
                        datetime.now()
                    ))
                    stored += 1
                except Exception as e:
                    logger.debug(f"Error storing price for {deal.get('product_id')}: {e}")

            conn.commit()
            conn.close()

            logger.info(f"✅ Stored {stored} prices in database")
            return stored

        except Exception as e:
            logger.error(f"Failed to store prices: {e}")
            return 0

    def _check_alerts(self, deals: List[Dict]) -> int:
        """
        Check if any deals match user alerts and send notifications.

        Args:
            deals: List of deal dicts

        Returns:
            Number of alerts triggered
        """
        if not deals:
            return 0

        try:
            conn = get_db_conn()
            c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Get all active alerts
            c.execute('''
                SELECT id, user_id, perfume_id, target_price
                FROM price_alerts
                WHERE status = 'active'
            ''')

            alerts = c.fetchall()
            triggered = 0

            for alert in alerts:
                # Find matching deals
                matching_deals = [
                    d for d in deals
                    if d.get('product_id') == alert['perfume_id']
                       and d.get('price', float('inf')) <= alert['target_price']
                ]

                if matching_deals:
                    for deal in matching_deals:
                        # Send notification (stub - implement Telegram/email)
                        self._send_alert_notification(alert, deal)
                        triggered += 1

                        logger.info(
                            f"🚨 ALERT TRIGGERED: {alert['user_id']} - "
                            f"{deal.get('perfume')} at £{deal.get('price')}"
                        )

            conn.close()
            return triggered

        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")
            return 0

    def _send_alert_notification(self, alert: Dict, deal: Dict) -> None:
        """
        Send notification to user (stub for Telegram/email integration).

        Args:
            alert: Alert dict with user_id, perfume_id, target_price
            deal: Deal dict with price, retailer, etc.
        """
        user_id = alert['user_id']
        perfume = deal.get('perfume', 'Unknown')
        price = deal.get('price')
        retailer = deal.get('retailer')
        url = deal.get('url', '')

        message = (
            f"🎯 Price Alert!\n"
            f"{perfume}\n"
            f"Price: £{price}\n"
            f"Retailer: {retailer}\n"
            f"Target: £{alert['target_price']}"
        )

        logger.info(f"[NOTIFICATION STUB] {user_id}: {message}")

        # TODO: Implement actual notifications
        # - Telegram: send_telegram_notification(user_id, message)
        # - Email: send_email_notification(user_id, message)

    def _log_metrics(self, metrics: Dict) -> None:
        """
        Log scan metrics for monitoring.

        Args:
            metrics: Dict with scan statistics
        """
        logger.info("=" * 70)
        logger.info("SCAN COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Products scanned: {metrics['products_scanned']}")
        logger.info(f"Deals found: {metrics['deals_found']}")
        logger.info(f"Prices stored: {metrics['prices_stored']}")
        logger.info(f"Alerts triggered: {metrics['alerts_triggered']}")
        logger.info(f"Duration: {metrics['duration_seconds']:.1f}s")
        logger.info("=" * 70)

    def get_status(self) -> Dict:
        """
        Get scheduler status.

        Returns:
            Dict with scheduler state and next run time
        """
        if not self.scheduler:
            return {'running': False, 'error': 'Scheduler not initialized'}

        jobs = []
        if self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                })

        return {
            'running': self.is_running,
            'enabled': ENABLED,
            'scan_times': SCAN_TIMES,
            'timezone': TIMEZONE,
            'scheduled_jobs': jobs
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_scheduler_instance = None

def get_scheduler_service() -> SchedulerService:
    """Get or create scheduler service singleton."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerService()
    return _scheduler_instance
