#!/usr/bin/env python3
"""
Olfex Scraper Engine
Scrapes perfume prices from major EU retailers
"""

import requests
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NicheGallerieScraper:
    """Scraper for NicheGallerie.com - UK niche specialist"""
    
    BASE_URL = "https://nichegallerie.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search(self, brand: str, name: str, size_ml: int) -> Optional[Dict]:
        """Search NicheGallerie - UK niche specialist"""
        query = f"{brand} {name}"
        search_url = f"{self.BASE_URL}/search?q={query.replace(' ', '+')}"
        
        try:
            logger.info(f"🔍 Searching NicheGallerie: {query}")
            resp = self.session.get(search_url, timeout=10)
            
            if resp.status_code != 200:
                return None
            
            # NicheGallerie uses Shopify - easier to scrape
            # Look for price in JSON-LD or HTML
            price_match = re.search(r'"price":\s*"([0-9.]+)"', resp.text)
            if not price_match:
                price_match = re.search(r'£([0-9,]+\.?\d{0,2})', resp.text)
            
            if price_match:
                price = float(price_match.group(1).replace(',', ''))
                
                in_stock = 'out of stock' not in resp.text.lower() and 'sold out' not in resp.text.lower()
                
                return {
                    'retailer': 'NicheGallerie',
                    'price_gbp': price,
                    'currency': 'GBP',
                    'url': search_url,
                    'in_stock': in_stock,
                    'scraped_at': datetime.now().isoformat(),
                    'match_confidence': 0.85,
                    'notes': 'UK niche specialist'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"NicheGallerie error: {e}")
            return None


class NotinoScraper:
    """Scraper for Notino (EU coverage)"""
    
    BASE_URL = "https://www.notino.co.uk"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search(self, brand: str, name: str, size_ml: int) -> Optional[Dict]:
        """
        Search for perfume on Notino
        Returns: {price, currency, url, in_stock} or None
        """
        query = f"{brand} {name} {size_ml}ml"
        search_url = f"{self.BASE_URL}/search?q={query.replace(' ', '+')}"
        
        try:
            logger.info(f"Searching Notino: {query}")
            resp = self.session.get(search_url, timeout=10)
            
            if resp.status_code != 200:
                logger.warning(f"Notino returned {resp.status_code}")
                return None
            
            # Extract price (simplified - would need proper HTML parsing)
            # Looking for patterns like "£149.00" or "149.00 £"
            price_match = re.search(r'£([0-9,]+\.?\d{0,2})', resp.text)
            
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                price = float(price_str)
                
                # Check stock
                in_stock = 'out of stock' not in resp.text.lower() and 'unavailable' not in resp.text.lower()
                
                return {
                    'retailer': 'Notino',
                    'price_gbp': price,
                    'currency': 'GBP',
                    'url': search_url,
                    'in_stock': in_stock,
                    'scraped_at': datetime.now().isoformat(),
                    'match_confidence': 0.85  # Would need better matching
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Notino error: {e}")
            return None

class DouglasScraper:
    """Scraper for Douglas (DE/FR/UK)"""
    
    DOMAINS = {
        'UK': 'https://www.douglas.co.uk',
        'DE': 'https://www.douglas.de',
        'FR': 'https://www.douglas.fr'
    }
    
    def __init__(self, country='UK'):
        self.country = country
        self.base_url = self.DOMAINS.get(country, self.DOMAINS['UK'])
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search(self, brand: str, name: str, size_ml: int) -> Optional[Dict]:
        """Search Douglas"""
        query = f"{brand} {name}"
        # Douglas search URL structure
        search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"
        
        try:
            logger.info(f"Searching Douglas {self.country}: {query}")
            resp = self.session.get(search_url, timeout=10)
            
            if resp.status_code != 200:
                return None
            
            # Price extraction (simplified)
            # Douglas uses data attributes or JSON-LD
            price_match = re.search(r'"price":\s*"?([0-9.]+)"?', resp.text)
            
            if price_match:
                price = float(price_match.group(1))
                
                return {
                    'retailer': f'Douglas {self.country}',
                    'price_gbp': price if self.country == 'UK' else price * 0.85,  # Approx conversion
                    'currency': 'GBP' if self.country == 'UK' else 'EUR',
                    'url': search_url,
                    'in_stock': 'out-of-stock' not in resp.text.lower(),
                    'scraped_at': datetime.now().isoformat(),
                    'match_confidence': 0.80
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Douglas error: {e}")
            return None

class SeesScentsScraper:
    """Scraper for SeesScents.com - testers and unboxed specialist"""
    
    BASE_URL = "https://seesscents.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search(self, brand: str, name: str, size_ml: int) -> Optional[Dict]:
        """Search Sees Scents - testers and unboxed deals"""
        query = f"{brand} {name}"
        search_url = f"{self.BASE_URL}/search?q={query.replace(' ', '+')}"
        
        try:
            logger.info(f"🔍 Searching Sees Scents: {query}")
            resp = self.session.get(search_url, timeout=10)
            
            if resp.status_code != 200:
                return None
            
            # Shopify store - look for price
            price_match = re.search(r'"price":\s*([0-9.]+)', resp.text)
            if not price_match:
                price_match = re.search(r'\\$([0-9,]+\.?\d{0,2})', resp.text)
            
            if price_match:
                price_usd = float(price_match.group(1).replace(',', ''))
                price_gbp = price_usd * 0.79  # USD to GBP
                
                in_stock = 'sold out' not in resp.text.lower() and 'unavailable' not in resp.text.lower()
                
                # Check if tester/unboxed
                is_tester = 'tester' in resp.text.lower() or 'unboxed' in resp.text.lower()
                
                return {
                    'retailer': 'Sees Scents',
                    'price_gbp': round(price_gbp, 2),
                    'price_local': price_usd,
                    'currency_local': 'USD',
                    'url': search_url,
                    'in_stock': in_stock,
                    'scraped_at': datetime.now().isoformat(),
                    'match_confidence': 0.80,
                    'notes': 'Tester/Unboxed' if is_tester else 'Retail',
                    'is_tester': is_tester
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Sees Scents error: {e}")
            return None


class FragranceBuyScraper:
    """Scraper for FragranceBuy.ca - BEST prices but aggressive anti-bot"""
    
    BASE_URL = "https://fragrancebuy.ca"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        })
    
    def search(self, brand: str, name: str, size_ml: int) -> Optional[Dict]:
        """Search FragranceBuy - most aggressive pricing"""
        query = f"{brand} {name}"
        search_url = f"{self.BASE_URL}/search?q={query.replace(' ', '+')}"
        
        try:
            logger.info(f"🔥 Searching FragranceBuy.ca: {query}")
            
            # Add delay to be respectful
            time.sleep(2)
            
            resp = self.session.get(search_url, timeout=15)
            
            if resp.status_code == 403:
                logger.warning("FragranceBuy blocked (403) - may need proxy rotation")
                return None
            
            if resp.status_code != 200:
                return None
            
            # Look for price patterns - FragranceBuy uses CAD
            # Convert to GBP (approx 0.59 CAD = 1 GBP)
            cad_match = re.search(r'C\$([0-9,]+\.?\d{0,2})', resp.text)
            if not cad_match:
                cad_match = re.search(r'\\$([0-9,]+\.?\d{0,2})', resp.text)
            
            if cad_match:
                price_cad = float(cad_match.group(1).replace(',', ''))
                price_gbp = price_cad * 0.59  # Approx conversion
                
                # Check stock
                in_stock = 'sold out' not in resp.text.lower() and 'unavailable' not in resp.text.lower()
                
                # Estimate shipping (CAD $20-30 = ~£12-18)
                total_gbp = price_gbp + 15  # Avg shipping
                
                return {
                    'retailer': 'FragranceBuy.ca ⭐',
                    'price_gbp': round(total_gbp, 2),
                    'price_local': price_cad,
                    'currency_local': 'CAD',
                    'url': search_url,
                    'in_stock': in_stock,
                    'scraped_at': datetime.now().isoformat(),
                    'match_confidence': 0.90,
                    'notes': 'Add ~£15 for shipping to UK'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"FragranceBuy error: {e}")
            return None


class MaxAromaScraper:
    """Scraper for MaxAroma - good prices, reliable shipping"""
    
    BASE_URL = "https://maxaroma.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
        })
    
    def search(self, brand: str, name: str, size_ml: int) -> Optional[Dict]:
        """Search MaxAroma"""
        query = f"{brand} {name}"
        search_url = f"{self.BASE_URL}/search?q={query.replace(' ', '+')}"
        
        try:
            logger.info(f"🔥 Searching MaxAroma: {query}")
            time.sleep(1.5)
            
            resp = self.session.get(search_url, timeout=10)
            
            if resp.status_code != 200:
                return None
            
            # MaxAroma uses USD
            usd_match = re.search(r'\\$([0-9,]+\.?\d{0,2})', resp.text)
            
            if usd_match:
                price_usd = float(usd_match.group(1).replace(',', ''))
                price_gbp = price_usd * 0.79  # USD to GBP
                
                in_stock = 'out of stock' not in resp.text.lower()
                
                # Shipping: Free over $75, else $6-10
                shipping = 0 if price_usd > 75 else 6
                total_gbp = (price_usd + shipping) * 0.79
                
                return {
                    'retailer': 'MaxAroma',
                    'price_gbp': round(total_gbp, 2),
                    'price_local': price_usd,
                    'currency_local': 'USD',
                    'url': search_url,
                    'in_stock': in_stock,
                    'scraped_at': datetime.now().isoformat(),
                    'match_confidence': 0.85,
                    'notes': 'Free US ship over $75'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"MaxAroma error: {e}")
            return None


class OlfexEngine:
    """Main scraper coordinator"""
    
    def __init__(self):
        self.scrapers = [
            SeesScentsScraper(),        # 🔥 TESTERS & UNBOXED (great value)
            FragranceBuyScraper(),      # 🔥 BEST PRICES (needs proxy)
            MaxAromaScraper(),          # 🔥 GREAT PRICES (needs proxy)
            NicheGallerieScraper(),     # 🔥 UK Niche Specialist
            NotinoScraper(),
            DouglasScraper('UK'),
            DouglasScraper('DE'),
        ]
        self.results = []
    
    def scan_perfume(self, perfume: Dict) -> List[Dict]:
        """
        Scan all retailers for a single perfume
        Returns list of price results
        """
        brand = perfume['brand']
        name = perfume['name']
        
        all_results = []
        
        for size in perfume['sizes_ml']:
            logger.info(f"Scanning {brand} {name} {size}ml...")
            
            for scraper in self.scrapers:
                try:
                    result = scraper.search(brand, name, size)
                    if result:
                        result['perfume'] = f"{brand} {name}"
                        result['size_ml'] = size
                        all_results.append(result)
                        
                        # Check if it's a deal
                        threshold = perfume.get('good_deal_threshold_gbp', 9999)
                        if result['price_gbp'] <= threshold:
                            logger.info(f"  🎯 DEAL FOUND: {result['retailer']} @ £{result['price_gbp']}")
                        
                except Exception as e:
                    logger.error(f"Scraper failed: {e}")
                
                # Be nice to servers
                time.sleep(1)
        
        return all_results
    
    def scan_all(self, perfumes: List[Dict]) -> Dict:
        """Scan all perfumes - AGGRESSIVE deal finding"""
        all_deals = []
        hot_deals = []  # Extra good deals
        
        for perfume in perfumes:
            results = self.scan_perfume(perfume)
            
            if results:
                # Sort by price
                results_sorted = sorted(results, key=lambda x: x['price_gbp'])
                best = results_sorted[0]
                
                # Check against thresholds
                threshold = perfume.get('good_deal_threshold_gbp', 9999)
                high_alert = perfume.get('high_alert_threshold_gbp', threshold * 0.85)
                
                savings = threshold - best['price_gbp']
                
                deal_info = {
                    'perfume': f"{perfume['brand']} {perfume['name']}",
                    'size_ml': best['size_ml'],
                    'best_price': best['price_gbp'],
                    'retailer': best['retailer'],
                    'threshold': threshold,
                    'savings': round(savings, 2),
                    'savings_percent': round((savings / threshold) * 100, 1),
                    'url': best['url'],
                    'timestamp': datetime.now().isoformat(),
                    'all_prices': [{r['retailer']: r['price_gbp']} for r in results_sorted[:3]]
                }
                
                # Categorize deal
                if best['price_gbp'] <= high_alert:
                    # 🔥 HOT DEAL - 15%+ below threshold
                    deal_info['hot'] = True
                    hot_deals.append(deal_info)
                    logger.info(f"🔥🔥 HOT DEAL: {deal_info['perfume']} @ £{deal_info['best_price']}")
                elif best['price_gbp'] <= threshold:
                    # ✅ Good deal
                    all_deals.append(deal_info)
                    logger.info(f"✅ DEAL: {deal_info['perfume']} @ £{deal_info['best_price']}")
        
        # Combine: hot deals first
        all_deals = hot_deals + all_deals
        
        return {
            'scan_time': datetime.now().isoformat(),
            'deals_found': len(all_deals),
            'hot_deals': len(hot_deals),
            'deals': sorted(all_deals, key=lambda x: x.get('savings', 0), reverse=True)
        }

if __name__ == '__main__':
    # Test
    hunter = OlfexEngine()
    
    # Load perfume database
    with open('/home/peptyl/.openclaw/workspace/olfex/data/perfumes.json') as f:
        data = json.load(f)
    
    # Scan top 3
    test_perfumes = data['top_10_niche_perfumes'][:3]
    results = hunter.scan_all(test_perfumes)
    
    print(f"\n{'='*60}")
    print(f"Olfex Scan Results")
    print(f"{'='*60}")
    print(f"Deals found: {results['deals_found']}")
    
    for deal in results['deals']:
        print(f"\n🎯 {deal['perfume']} ({deal['size_ml']}ml)")
        print(f"   Price: £{deal['best_price']:.2f} @ {deal['retailer']}")
        print(f"   Threshold: £{deal['threshold']:.2f}")
        print(f"   Savings: £{deal['savings']:.2f}")
