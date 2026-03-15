#!/usr/bin/env python3
"""
Olfex Production Scheduler
=================================
Runs automated price scans on a configurable schedule.
Default: 2x/day (06:00 and 18:00 GMT)

Features:
- APScheduler-based with cron triggers for reliability
- Redis-backed job queue for distributed workers
- Scan prioritization (popular products first)
- Staggered retailer requests to avoid rate limits
- Health check integration
- Slack/webhook notifications for failures
- Graceful shutdown handling with SIGTERM/SIGINT
- Comprehensive logging and metrics

Usage:
    python scheduler.py --run-now              # Run one cycle immediately
    python scheduler.py --start                # Start daemon scheduler
    python scheduler.py --catalog path/to.json # Use custom catalog
"""

import asyncio
import signal
import logging
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from contextlib import asynccontextmanager

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScanJob:
    """A single scan job for one product × one retailer"""
    job_id: str
    product_id: str
    retailer: str
    priority: int  # 1=high, 5=low
    created_at: datetime
    status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        d['created_at'] = self.created_at.isoformat()
        d['started_at'] = self.started_at.isoformat() if self.started_at else None
        d['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'ScanJob':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['created_at'] = datetime.fromisoformat(data_copy['created_at'])
        if data_copy.get('started_at'):
            data_copy['started_at'] = datetime.fromisoformat(data_copy['started_at'])
        if data_copy.get('completed_at'):
            data_copy['completed_at'] = datetime.fromisoformat(data_copy['completed_at'])
        return cls(**data_copy)


class ScanQueue:
    """Redis-backed job queue for scan jobs with in-memory fallback"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize queue with Redis backend or in-memory fallback"""
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory_queue: List[ScanJob] = []
        self.in_memory_results: Dict[str, ScanJob] = {}

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory queue.")
                self.redis_client = None
        else:
            logger.warning("redis-py not installed. Using in-memory queue.")

    async def enqueue(self, job: ScanJob) -> None:
        """Add job to queue (higher priority = earlier execution)"""
        if self.redis_client:
            try:
                key = f"job:{job.job_id}"
                self.redis_client.hset(key, mapping=job.to_dict())
                self.redis_client.zadd("job_queue", {job.job_id: job.priority})
                logger.debug(f"Enqueued job {job.job_id} with priority {job.priority}")
                return
            except Exception as e:
                logger.error(f"Redis enqueue failed: {e}. Falling back to in-memory.")

        # In-memory fallback
        self.in_memory_queue.append(job)
        self.in_memory_queue.sort(key=lambda j: (j.priority, j.created_at))

    async def dequeue(self) -> Optional[ScanJob]:
        """Get next job from queue (highest priority first)"""
        if self.redis_client:
            try:
                result = self.redis_client.zrange("job_queue", 0, 0)
                if result:
                    job_id = result[0].decode() if isinstance(result[0], bytes) else result[0]
                    key = f"job:{job_id}"
                    job_data = self.redis_client.hgetall(key)
                    if job_data:
                        job_dict = {
                            k.decode() if isinstance(k, bytes) else k:
                            v.decode() if isinstance(v, bytes) else v
                            for k, v in job_data.items()
                        }
                        job = ScanJob.from_dict(job_dict)
                        self.redis_client.zrem("job_queue", job_id)
                        logger.debug(f"Dequeued job {job_id}")
                        return job
            except Exception as e:
                logger.error(f"Redis dequeue failed: {e}. Falling back to in-memory.")

        # In-memory fallback
        if self.in_memory_queue:
            job = self.in_memory_queue.pop(0)
            logger.debug(f"Dequeued job {job.job_id} (in-memory)")
            return job

        return None

    async def complete(self, job_id: str, result: dict) -> None:
        """Mark job as completed with result"""
        if self.redis_client:
            try:
                key = f"job:{job_id}"
                self.redis_client.hset(key, "status", JobStatus.COMPLETED.value)
                self.redis_client.hset(key, "result", json.dumps(result))
                self.redis_client.hset(key, "completed_at", datetime.utcnow().isoformat())
                self.redis_client.zadd("completed_jobs", {job_id: time.time()})
                logger.debug(f"Marked job {job_id} as completed")
                return
            except Exception as e:
                logger.error(f"Redis complete failed: {e}")

        # In-memory fallback
        if job_id in self.in_memory_results:
            job = self.in_memory_results[job_id]
            job.status = JobStatus.COMPLETED.value
            job.result = result
            job.completed_at = datetime.utcnow()

    async def fail(self, job_id: str, error: str) -> None:
        """Mark job as failed with error message"""
        if self.redis_client:
            try:
                key = f"job:{job_id}"
                self.redis_client.hset(key, "status", JobStatus.FAILED.value)
                self.redis_client.hset(key, "error", error)
                self.redis_client.hset(key, "completed_at", datetime.utcnow().isoformat())
                self.redis_client.zadd("failed_jobs", {job_id: time.time()})
                logger.debug(f"Marked job {job_id} as failed")
                return
            except Exception as e:
                logger.error(f"Redis fail failed: {e}")

        # In-memory fallback
        if job_id in self.in_memory_results:
            job = self.in_memory_results[job_id]
            job.status = JobStatus.FAILED.value
            job.error = error
            job.completed_at = datetime.utcnow()

    async def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        stats = {"pending": 0, "completed": 0, "failed": 0}

        if self.redis_client:
            try:
                stats["pending"] = self.redis_client.zcard("job_queue")
                stats["completed"] = self.redis_client.zcard("completed_jobs")
                stats["failed"] = self.redis_client.zcard("failed_jobs")
                return stats
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")

        # In-memory stats
        stats["pending"] = len(self.in_memory_queue)
        return stats


class OlfexScheduler:
    """Main scheduler that orchestrates scan cycles"""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize scheduler with configuration"""
        self.config = config or self._default_config()
        self.queue = ScanQueue(self.config.get("redis_url", "redis://localhost:6379"))
        self.running = False
        self.scheduler = None
        self.workers = []

        if APSCHEDULER_AVAILABLE:
            self.scheduler = AsyncIOScheduler()
        else:
            logger.warning("APScheduler not installed. Using manual scheduling.")

    def _default_config(self) -> Dict:
        """Default configuration for scheduler"""
        return {
            "scan_times": ["06:00", "18:00"],  # GMT
            "timezone": "Europe/London",
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "max_concurrent_scrapers": int(os.getenv("MAX_CONCURRENT_SCRAPERS", 5)),
            "retailer_rate_limits": {
                "notino": 30,  # requests per minute
                "nichegallerie": 20,
                "fragrancebuy": 10,
                "seescents": 15,
                "maxaroma": 20,
                "jomashop": 15,
                "fragrancenet": 20,
                "douglas_de": 15,
            },
            "webhook_url": os.getenv("SCHEDULER_WEBHOOK_URL"),
            "stagger_delay_seconds": 2,
            "catalog_path": "data/product_catalog_expanded.json",
            "data_dir": "data/scheduler",
        }

    async def create_scan_cycle(self, catalog_path: str) -> List[ScanJob]:
        """
        Create all scan jobs for one full cycle.
        Prioritizes popular products and reliable retailers.
        """
        if not os.path.exists(catalog_path):
            logger.error(f"Catalog not found at {catalog_path}")
            return []

        try:
            with open(catalog_path, 'r') as f:
                catalog = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            return []

        jobs = []
        retailers = self.config["retailer_rate_limits"].keys()

        # Sort products by popularity (if available)
        products = catalog.get("products", [])
        if not isinstance(products, list):
            products = list(products.values()) if isinstance(products, dict) else []

        for idx, product in enumerate(products):
            product_id = product.get("id", f"product_{idx}")
            popularity = product.get("popularity", 1)  # Lower is more popular
            priority = min(5, max(1, popularity))  # Clamp between 1-5

            # Create job for each retailer
            for retailer in retailers:
                job_id = f"{product_id}_{retailer}_{int(time.time())}"
                job = ScanJob(
                    job_id=job_id,
                    product_id=product_id,
                    retailer=retailer,
                    priority=priority,
                    created_at=datetime.utcnow(),
                )
                jobs.append(job)
                await self.queue.enqueue(job)

        logger.info(f"Created {len(jobs)} scan jobs for cycle")
        return jobs

    async def run_scan_cycle(self) -> Dict:
        """
        Execute one complete scan cycle with worker pool.
        Returns summary statistics.
        """
        logger.info("Starting scan cycle")
        cycle_start = datetime.utcnow()

        # Create jobs
        catalog_path = self.config.get("catalog_path", "data/product_catalog_expanded.json")
        jobs = await self.create_scan_cycle(catalog_path)

        if not jobs:
            logger.warning("No jobs created for cycle")
            return {"status": "failed", "reason": "No jobs created"}

        # Run worker pool
        max_workers = self.config["max_concurrent_scrapers"]
        completed = 0
        failed = 0

        worker_tasks = [
            asyncio.create_task(self.run_worker(i))
            for i in range(max_workers)
        ]

        try:
            await asyncio.gather(*worker_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Worker pool error: {e}")

        # Collect stats
        queue_stats = await self.queue.get_stats()
        cycle_end = datetime.utcnow()
        duration = (cycle_end - cycle_start).total_seconds()

        result = {
            "status": "completed",
            "cycle_start": cycle_start.isoformat(),
            "cycle_end": cycle_end.isoformat(),
            "duration_seconds": duration,
            "jobs_created": len(jobs),
            "queue_stats": queue_stats,
        }

        logger.info(f"Scan cycle completed in {duration:.1f}s: {result}")
        await self.notify(f"Scan cycle completed: {json.dumps(result)}", "info")
        return result

    async def run_worker(self, worker_id: int) -> None:
        """
        Worker that processes scan jobs from queue.
        Implements retry logic and rate limiting per retailer.
        """
        logger.info(f"Worker {worker_id} started")
        retailer_delays = {}  # Track last request time per retailer

        while self.running or await self.queue.dequeue() is not None:
            job = await self.queue.dequeue()
            if not job:
                await asyncio.sleep(0.5)
                continue

            # Apply retailer rate limiting
            retailer = job.retailer
            rate_limit = self.config["retailer_rate_limits"].get(retailer, 15)
            min_delay = 60.0 / rate_limit

            if retailer in retailer_delays:
                elapsed = time.time() - retailer_delays[retailer]
                if elapsed < min_delay:
                    await asyncio.sleep(min_delay - elapsed)

            retailer_delays[retailer] = time.time()

            # Execute job
            logger.info(f"Worker {worker_id} processing {job.job_id}")
            job.status = JobStatus.RUNNING.value
            job.started_at = datetime.utcnow()
            job.retry_count += 1

            try:
                # Simulate scraping (in production, call actual scraper)
                result = await self._execute_scan(job)
                await self.queue.complete(job.job_id, result)
                logger.info(f"Worker {worker_id} completed {job.job_id}")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Worker {worker_id} failed {job.job_id}: {error_msg}")

                if job.retry_count < job.max_retries:
                    job.status = JobStatus.PENDING.value
                    await self.queue.enqueue(job)
                else:
                    await self.queue.fail(job.job_id, error_msg)
                    await self.notify(
                        f"Job {job.job_id} failed after {job.max_retries} retries: {error_msg}",
                        "error"
                    )

    async def _execute_scan(self, job: ScanJob) -> Dict:
        """
        Execute actual scan for a job.
        This is where the scraper engine integration happens.
        """
        # In production, this would call the actual scraper engine
        # For now, return mock result
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "job_id": job.job_id,
            "product_id": job.product_id,
            "retailer": job.retailer,
            "price": 99.99,
            "currency": "GBP",
            "in_stock": True,
            "scraped_at": datetime.utcnow().isoformat(),
        }

    def start(self) -> None:
        """Start the scheduler daemon"""
        if not self.scheduler:
            logger.error("APScheduler not available. Cannot start daemon.")
            return

        self.running = True
        logger.info("Starting Olfex scheduler")

        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, f: asyncio.create_task(self.stop()))

        try:
            # Schedule scan cycles
            for scan_time in self.config["scan_times"]:
                hour, minute = map(int, scan_time.split(":"))
                self.scheduler.add_job(
                    self.run_scan_cycle,
                    CronTrigger(hour=hour, minute=minute, timezone=self.config["timezone"]),
                    id=f"scan_{hour}_{minute}",
                )
                logger.info(f"Scheduled scan at {scan_time} {self.config['timezone']}")

            self.scheduler.start()
            logger.info("Scheduler running. Press Ctrl+C to stop.")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            self.running = False

    async def stop(self) -> None:
        """Graceful shutdown"""
        logger.info("Stopping scheduler...")
        self.running = False

        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)

        # Cancel all worker tasks
        for task in asyncio.all_tasks():
            if task != asyncio.current_task():
                task.cancel()

        logger.info("Scheduler stopped")

    async def notify(self, message: str, level: str = "info") -> None:
        """Send notification via webhook (Slack, Discord, etc)"""
        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            return

        payload = {
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=5) as resp:
                    if resp.status != 200:
                        logger.warning(f"Webhook returned {resp.status}")
        except ImportError:
            logger.warning("aiohttp not installed. Cannot send webhook notification.")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def load_config(self, config_path: str) -> None:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.config.update(config)
            logger.info(f"Loaded config from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")

    def save_metrics(self) -> None:
        """Save cycle metrics to disk"""
        data_dir = Path(self.config.get("data_dir", "data/scheduler"))
        data_dir.mkdir(parents=True, exist_ok=True)

        metrics_file = data_dir / "metrics.json"
        try:
            metrics = {
                "last_cycle": datetime.utcnow().isoformat(),
                "scheduler_config": self.config,
            }
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            logger.debug(f"Saved metrics to {metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Olfex Production Scheduler")
    parser.add_argument("--run-now", action="store_true", help="Run a scan cycle immediately")
    parser.add_argument("--start", action="store_true", help="Start the scheduler daemon")
    parser.add_argument("--catalog", default="data/product_catalog_expanded.json",
                        help="Path to product catalog JSON")
    parser.add_argument("--config", default=None, help="Path to config JSON")
    args = parser.parse_args()

    # Initialize scheduler
    scheduler = OlfexScheduler()
    if args.config:
        scheduler.load_config(args.config)

    # Execute requested action
    if args.run_now:
        logger.info(f"Running scan cycle now (catalog: {args.catalog})")
        try:
            result = asyncio.run(scheduler.run_scan_cycle())
            print(json.dumps(result, indent=2))
            sys.exit(0 if result["status"] == "completed" else 1)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            sys.exit(130)
        except Exception as e:
            logger.error(f"Scan cycle failed: {e}")
            sys.exit(1)

    elif args.start:
        logger.info("Starting scheduler daemon")
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            asyncio.run(scheduler.stop())
            sys.exit(130)

    else:
        parser.print_help()
        sys.exit(0)
