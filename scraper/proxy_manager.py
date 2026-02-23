#!/usr/bin/env python3
"""
PriceHunter Proxy Manager
Rotates proxies to avoid blocks on aggressive sites
"""

import requests
import random
import logging
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyManager:
    """
    Manages proxy rotation for aggressive scraping
    """
    
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.failed_proxies = set()
    
    def load_free_proxies(self) -> List[str]:
        """
        Load free proxies from public lists
        Note: Free proxies are unreliable but good for testing
        """
        try:
            # Fetch from free-proxy-list.net
            resp = requests.get(
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                timeout=10
            )
            
            proxy_list = []
            for line in resp.text.strip().split('\n')[:20]:  # Top 20
                if ':' in line:
                    proxy_list.append(f"http://{line.strip()}")
            
            logger.info(f"Loaded {len(proxy_list)} free proxies")
            return proxy_list
            
        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")
            return []
    
    def get_proxy(self) -> Optional[str]:
        """Get next working proxy"""
        available = [p for p in self.proxies if p not in self.failed_proxies]
        
        if not available:
            return None
        
        proxy = random.choice(available)
        return proxy
    
    def mark_failed(self, proxy: str):
        """Mark proxy as failed"""
        self.failed_proxies.add(proxy)
        logger.warning(f"Proxy failed: {proxy}")
    
    def test_proxy(self, proxy: str) -> bool:
        """Test if proxy is working"""
        try:
            resp = requests.get(
                'https://httpbin.org/ip',
                proxies={'http': proxy, 'https': proxy},
                timeout=10
            )
            return resp.status_code == 200
        except:
            return False


class SmartScraper:
    """
    Smart scraper with fallback strategies
    """
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.session = requests.Session()
    
    def scrape_with_fallback(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Try scraping with multiple strategies:
        1. Direct request
        2. Different User-Agent
        3. Proxy rotation
        4. Delay and retry
        """
        
        # Strategy 1: Direct
        for i in range(max_retries):
            try:
                headers = {
                    'User-Agent': self._get_random_ua(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                resp = self.session.get(url, headers=headers, timeout=15)
                
                if resp.status_code == 200:
                    return resp.text
                
                if resp.status_code == 403:
                    logger.warning(f"Blocked (403), attempt {i+1}")
                    time.sleep(2 ** i)  # Exponential backoff
                    continue
                    
            except Exception as e:
                logger.error(f"Request failed: {e}")
                time.sleep(2 ** i)
        
        return None
    
    def _get_random_ua(self) -> str:
        """Get random user agent"""
        uas = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]
        return random.choice(uas)


# Production recommendations
PRODUCTION_STRATEGY = """
## For Production Scraping (Reliable)

### Option 1: Residential Proxies (Recommended)
- BrightData (formerly Luminati)
- SmartProxy
- Oxylabs
- Cost: ~$10-15/GB
- Success rate: 95%+

### Option 2: Scraping APIs
- ScraperAPI
- ScrapingBee
- ScrapingAnt
- Cost: ~$50-100/mo
- Handles proxies, CAPTCHAs, JS rendering

### Option 3: Headless Browsers
- Playwright with stealth
- Puppeteer with puppeteer-extra-plugin-stealth
- More resource intensive but higher success

### Option 4: Manual Data Entry (MVP)
- User-submitted prices (community)
- Affiliate API feeds where available
- Slower but 100% reliable
"""

if __name__ == '__main__':
    print("PriceHunter Proxy Manager")
    print("="*50)
    print(PRODUCTION_STRATEGY)
