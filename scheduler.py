#!/usr/bin/env python3
"""
Olfex Scheduler
Runs price scans twice daily at 12:00 and 18:00 GMT
"""

import schedule
import time
import logging
from datetime import datetime
from scraper.engine import OlfexEngine
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OlfexScheduler:
    def __init__(self):
        self.scraper = OlfexEngine()
        self.running = False
        
    def run_price_scan(self):
        """Run full price scan"""
        logger.info("="*60)
        logger.info(f"STARTING PRICE SCAN - {datetime.now().isoformat()}")
        logger.info("="*60)
        
        # Load perfumes
        with open('/home/peptyl/.openclaw/workspace/olfex/data/perfumes.json') as f:
            data = json.load(f)
        
        perfumes = data['top_10_niche_perfumes']
        
        # Scan all
        results = self.scraper.scan_all(perfumes)
        
        # Save results
        with open('/home/peptyl/.openclaw/workspace/olfex/data/latest_scan.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Scan complete. Deals found: {results['deals_found']}")
        
        # Check for price drops on user alerts
        self.check_alerts(results)
        
        return results
    
    def check_alerts(self, results):
        """Check if any deals match user alerts"""
        # TODO: Query database for user alerts
        # TODO: Send notifications for matching deals
        logger.info("Checking user alerts...")
        
        # For now, just log
        for deal in results['deals']:
            logger.info(f"🎯 DEAL: {deal['perfume']} @ £{deal['best_price']}")
    
    def run_once(self):
        """Run scan once immediately"""
        return self.run_price_scan()
    
    def schedule_daily(self):
        """Schedule twice daily scans"""
        schedule.every().day.at("12:00").do(self.run_price_scan)
        schedule.every().day.at("18:00").do(self.run_price_scan)
        
        logger.info("Scheduler configured:")
        logger.info("  - 12:00 GMT")
        logger.info("  - 18:00 GMT")
        
        self.running = True
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        logger.info("Scheduler stopped")

if __name__ == '__main__':
    import sys
    
    scheduler = OlfexScheduler()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run once now
        print("Running price scan now...")
        results = scheduler.run_once()
        
        print(f"\n{'='*60}")
        print(f"SCAN COMPLETE")
        print(f"{'='*60}")
        print(f"Deals found: {results['deals_found']}")
        
        for deal in results['deals'][:5]:
            print(f"\n🎯 {deal['perfume']}")
            print(f"   £{deal['best_price']:.2f} @ {deal['retailer']}")
            print(f"   Save £{deal['savings']:.2f}")
    else:
        # Run scheduler
        print("Starting Olfex scheduler...")
        print("Scans at 12:00 and 18:00 GMT")
        print("Press Ctrl+C to stop")
        scheduler.schedule_daily()
