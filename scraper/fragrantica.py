"""
Fragrantica scraper module for enriching fragrance product catalogs.

This module extracts fragrance metadata from Fragrantica including:
- Images, accords, scent pyramid, ratings, longevity, sillage, season ratings
- Rate-limited with caching to avoid blocking
- Supports both simple requests and Playwright for JS-heavy pages
"""

import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Optional Playwright import for JS-rendered content
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class FragranticaProfile:
    """Complete fragrance profile scraped from Fragrantica."""

    fragrantica_url: str
    image_url: Optional[str] = None
    accords: List[Dict[str, float]] = field(default_factory=list)
    top_notes: List[str] = field(default_factory=list)
    heart_notes: List[str] = field(default_factory=list)
    base_notes: List[str] = field(default_factory=list)
    rating: Optional[float] = None
    votes: Optional[int] = None
    longevity: Optional[str] = None
    sillage: Optional[str] = None
    season_ratings: Dict[str, float] = field(default_factory=dict)
    day_night: Dict[str, float] = field(default_factory=dict)
    similar_fragrances: List[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FragranticaProfile":
        """Create instance from dictionary."""
        return cls(**data)


class FragranticaScraper:
    """Scrapes Fragrantica for fragrance metadata and images."""

    BASE_URL = "https://www.fragrantica.com"
    SEARCH_URL = f"{BASE_URL}/search/"
    PERFUME_URL = f"{BASE_URL}/perfume"

    # User agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]

    REQUEST_DELAY_SECONDS = 3.0

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        cache_dir: str = "data/fragrantica_cache",
        use_playwright: bool = False,
    ):
        """
        Initialize the Fragrantica scraper.

        Args:
            session: Optional requests.Session for connection pooling
            cache_dir: Directory for caching profiles
            use_playwright: Use Playwright for JS-heavy pages
        """
        self.session = session or requests.Session()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_playwright = use_playwright and PLAYWRIGHT_AVAILABLE
        self._last_request_time = 0.0
        self._ua_index = 0

        logger.info(
            f"Initialized FragranticaScraper (cache_dir={cache_dir}, "
            f"playwright={'enabled' if self.use_playwright else 'disabled'})"
        )

    def _rotate_user_agent(self) -> str:
        """Get next user agent in rotation."""
        ua = self.USER_AGENTS[self._ua_index % len(self.USER_AGENTS)]
        self._ua_index += 1
        return ua

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY_SECONDS:
            sleep_time = self.REQUEST_DELAY_SECONDS - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _get_cache_path(self, slug: str) -> Path:
        """Get cache file path for a fragrance slug."""
        safe_slug = re.sub(r'[^\w\-]', '_', slug)
        return self.cache_dir / f"{safe_slug}.json"

    def _load_cache(self, slug: str) -> Optional[FragranticaProfile]:
        """Load profile from cache if available."""
        cache_path = self._get_cache_path(slug)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded {slug} from cache")
                    return FragranticaProfile.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load cache for {slug}: {e}")
        return None

    def _save_cache(self, slug: str, profile: FragranticaProfile) -> None:
        """Save profile to cache."""
        cache_path = self._get_cache_path(slug)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2)
                logger.debug(f"Cached {slug}")
        except Exception as e:
            logger.warning(f"Failed to cache {slug}: {e}")

    def build_url(self, fragrantica_slug: str) -> str:
        """
        Build Fragrantica URL from slug.

        Args:
            fragrantica_slug: Slug like "Parfums-de-Marly/Layton-42736"

        Returns:
            Full URL to fragrance page
        """
        return f"{self.PERFUME_URL}/{fragrantica_slug}.html"

    def search_fragrance(self, brand: str, name: str) -> Optional[str]:
        """
        Search for a fragrance and return the slug if found.

        Args:
            brand: Fragrance brand
            name: Fragrance name

        Returns:
            Fragrantica slug or None if not found
        """
        logger.info(f"Searching for {brand} {name}")
        self._rate_limit()

        query = f"{brand} {name}"
        params = {"query": query}
        headers = {"User-Agent": self._rotate_user_agent()}

        try:
            resp = self.session.get(
                self.SEARCH_URL,
                params=params,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Search request failed: {e}")
            return None

        soup = BeautifulSoup(resp.content, 'html.parser')

        # Look for perfume search results
        # Fragrantica typically returns results in a specific format
        result_links = soup.select('a[href*="/perfume/"]')

        if not result_links:
            logger.warning(f"No search results found for {brand} {name}")
            return None

        # Get the first result's href and extract slug
        href = result_links[0].get('href', '')
        # Extract slug from URL like /perfume/Brand/Name-123.html
        match = re.search(r'/perfume/(.+?)\.html', href)
        if match:
            slug = match.group(1)
            logger.info(f"Found: {slug}")
            return slug

        return None

    def _parse_accords(self, soup: BeautifulSoup) -> List[Dict[str, float]]:
        """Parse accords from soup."""
        accords = []

        # Look for accord bars
        accord_bars = soup.select('div.accord-bar, .accord-bar')

        for bar in accord_bars:
            # Get accord name
            name_elem = bar.find(class_='accord-name') or bar.find('span')
            if not name_elem:
                continue

            name = name_elem.get_text(strip=True).lower()

            # Get strength percentage from style width or data attribute
            strength = 0.0
            style = bar.get('style', '')
            width_match = re.search(r'width:\s*(\d+(?:\.\d+)?)%', style)
            if width_match:
                strength = float(width_match.group(1))
            else:
                # Try data attribute
                strength_str = bar.get('data-strength') or bar.get('data-percent')
                if strength_str:
                    try:
                        strength = float(strength_str)
                    except ValueError:
                        pass

            if name and strength > 0:
                accords.append({"name": name, "strength": strength})

        return accords

    def _parse_notes(self, soup: BeautifulSoup) -> tuple[List[str], List[str], List[str]]:
        """Parse fragrance notes pyramid."""
        top_notes = []
        heart_notes = []
        base_notes = []

        # Find notes sections by common class/id patterns
        note_sections = soup.select('.note-section, .notes-section, [data-section="notes"]')

        for section in note_sections:
            section_text = section.get_text(lower=True)

            # Identify section type
            is_top = 'top' in section_text or 'head' in section_text
            is_heart = 'middle' in section_text or 'heart' in section_text
            is_base = 'base' in section_text or 'bottom' in section_text

            # Extract note elements
            notes = []
            note_elements = section.select('span.note, .note, li[data-type="note"]')

            for elem in note_elements:
                note = elem.get_text(strip=True)
                if note:
                    notes.append(note)

            if is_top and notes:
                top_notes = notes
            elif is_heart and notes:
                heart_notes = notes
            elif is_base and notes:
                base_notes = notes

        return top_notes, heart_notes, base_notes

    def _parse_rating(self, soup: BeautifulSoup) -> tuple[Optional[float], Optional[int]]:
        """Parse rating and vote count."""
        rating = None
        votes = None

        # Look for rating value
        rating_elem = soup.select_one('[itemprop="ratingValue"]')
        if rating_elem:
            try:
                rating = float(rating_elem.get_text(strip=True))
            except ValueError:
                pass

        # Look for vote count
        votes_elem = soup.select_one('[itemprop="reviewCount"]')
        if votes_elem:
            try:
                votes_text = votes_elem.get_text(strip=True)
                votes = int(votes_text.replace(',', ''))
            except ValueError:
                pass

        return rating, votes

    def _parse_longevity_sillage(self, soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
        """Parse longevity and sillage ratings."""
        longevity = None
        sillage = None

        # Common patterns for longevity/sillage
        labels = {
            'poor': 'poor',
            'weak': 'weak',
            'moderate': 'moderate',
            'long': 'long-lasting',
            'very long': 'eternal',
            'eternal': 'eternal',
            'intimate': 'intimate',
            'strong': 'strong',
            'enormous': 'enormous',
        }

        text = soup.get_text(lower=True)

        # Find longevity
        for label_key in ['poor', 'weak', 'moderate', 'long', 'very long', 'eternal']:
            if f'longevity' in text and label_key in text:
                longevity = labels.get(label_key)
                break

        # Find sillage
        for label_key in ['intimate', 'moderate', 'strong', 'enormous']:
            if 'sillage' in text and label_key in text:
                sillage = labels.get(label_key)
                break

        return longevity, sillage

    def _parse_season_ratings(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Parse season ratings (Spring/Summer/Fall/Winter)."""
        season_ratings = {}

        seasons = ['spring', 'summer', 'fall', 'autumn', 'winter']

        # Look for season indicators
        for season in seasons:
            # Try various patterns
            patterns = [
                f'[data-season="{season}"] [data-percent]',
                f'.season-{season} [data-value]',
                f'span:contains("{season}") + *',
            ]

            for pattern in patterns:
                elem = soup.select_one(pattern)
                if elem:
                    try:
                        value_str = elem.get('data-percent') or elem.get('data-value') or elem.get_text()
                        value = float(value_str.replace('%', '').strip())
                        season_key = 'autumn' if season == 'fall' else season
                        season_ratings[season_key] = value
                        break
                    except (ValueError, AttributeError):
                        pass

        return season_ratings

    def _parse_day_night(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Parse day/night preference ratings."""
        day_night = {}

        # Look for day/night preferences
        day_elem = soup.select_one('[data-day], .day-percent, [data-period="day"]')
        night_elem = soup.select_one('[data-night], .night-percent, [data-period="night"]')

        if day_elem:
            try:
                day_value = float(
                    day_elem.get('data-day') or
                    day_elem.get('data-percent') or
                    day_elem.get_text().replace('%', '')
                )
                day_night['day'] = day_value
            except (ValueError, AttributeError):
                pass

        if night_elem:
            try:
                night_value = float(
                    night_elem.get('data-night') or
                    night_elem.get('data-percent') or
                    night_elem.get_text().replace('%', '')
                )
                day_night['night'] = night_value
            except (ValueError, AttributeError):
                pass

        return day_night

    def _parse_similar_fragrances(self, soup: BeautifulSoup) -> List[str]:
        """Parse similar fragrance links."""
        similar = []

        # Look for similar fragrances section
        similar_section = soup.select_one(
            '.similar-perfumes, [data-section="similar"], .recommendations'
        )

        if not similar_section:
            return similar

        # Extract perfume links
        for link in similar_section.select('a[href*="/perfume/"]'):
            href = link.get('href', '')
            match = re.search(r'/perfume/(.+?)\.html', href)
            if match:
                similar.append(match.group(1))

        return similar[:10]  # Limit to 10

    def _parse_image_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Parse main product image URL."""
        # Try various common patterns
        img_patterns = [
            'img[itemprop="image"]',
            'img.product-image',
            '.image-container img',
            '[data-image-main] img',
            'img[alt*="bottle"]',
        ]

        for pattern in img_patterns:
            img = soup.select_one(pattern)
            if img:
                src = img.get('src') or img.get('data-src')
                if src:
                    # Convert relative to absolute URL
                    return urljoin(base_url, src)

        return None

    def _fetch_page_requests(self, url: str) -> Optional[str]:
        """Fetch page using requests library."""
        self._rate_limit()

        headers = {
            "User-Agent": self._rotate_user_agent(),
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            resp = self.session.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            logger.debug(f"Fetched {url}")
            return resp.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _fetch_page_playwright(self, url: str) -> Optional[str]:
        """Fetch page using Playwright for JS rendering."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available, falling back to requests")
            return self._fetch_page_requests(url)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                content = page.content()
                browser.close()
                logger.debug(f"Fetched {url} with Playwright")
                return content
        except Exception as e:
            logger.warning(f"Playwright fetch failed for {url}, trying requests: {e}")
            return self._fetch_page_requests(url)

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content."""
        if self.use_playwright:
            return self._fetch_page_playwright(url)
        else:
            return self._fetch_page_requests(url)

    def get_profile(self, fragrantica_slug: str) -> Optional[FragranticaProfile]:
        """
        Get full fragrance profile from Fragrantica.

        Args:
            fragrantica_slug: Slug like "Parfums-de-Marly/Layton-42736"

        Returns:
            FragranticaProfile or None if scraping fails
        """
        # Check cache first
        cached = self._load_cache(fragrantica_slug)
        if cached:
            return cached

        url = self.build_url(fragrantica_slug)
        logger.info(f"Fetching profile: {url}")

        html = self._fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Parse all data
        image_url = self._parse_image_url(soup, url)
        accords = self._parse_accords(soup)
        top_notes, heart_notes, base_notes = self._parse_notes(soup)
        rating, votes = self._parse_rating(soup)
        longevity, sillage = self._parse_longevity_sillage(soup)
        season_ratings = self._parse_season_ratings(soup)
        day_night = self._parse_day_night(soup)
        similar_fragrances = self._parse_similar_fragrances(soup)

        profile = FragranticaProfile(
            fragrantica_url=url,
            image_url=image_url,
            accords=accords,
            top_notes=top_notes,
            heart_notes=heart_notes,
            base_notes=base_notes,
            rating=rating,
            votes=votes,
            longevity=longevity,
            sillage=sillage,
            season_ratings=season_ratings,
            day_night=day_night,
            similar_fragrances=similar_fragrances,
        )

        # Cache it
        self._save_cache(fragrantica_slug, profile)

        logger.info(f"Successfully scraped profile for {fragrantica_slug}")
        return profile

    def get_image_url(self, fragrantica_slug: str) -> Optional[str]:
        """
        Get just the bottle image URL.

        Args:
            fragrantica_slug: Fragrance slug

        Returns:
            Image URL or None
        """
        profile = self.get_profile(fragrantica_slug)
        return profile.image_url if profile else None

    def download_image(
        self,
        fragrantica_slug: str,
        output_dir: str,
    ) -> Optional[str]:
        """
        Download bottle image to local storage.

        Args:
            fragrantica_slug: Fragrance slug
            output_dir: Directory to save image

        Returns:
            Local path to saved image or None
        """
        image_url = self.get_image_url(fragrantica_slug)
        if not image_url:
            logger.warning(f"No image URL found for {fragrantica_slug}")
            return None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename from slug
        safe_slug = re.sub(r'[^\w\-]', '_', fragrantica_slug)
        ext = Path(urlparse(image_url).path).suffix or '.jpg'
        filename = f"{safe_slug}{ext}"
        filepath = output_path / filename

        logger.info(f"Downloading image: {image_url} -> {filepath}")

        self._rate_limit()

        try:
            resp = self.session.get(image_url, timeout=15)
            resp.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(resp.content)

            logger.info(f"Saved image to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None

    def enrich_catalog(
        self,
        catalog_path: str,
        output_path: str,
        image_output_dir: Optional[str] = None,
    ) -> None:
        """
        Enrich a product catalog JSON with Fragrantica data.

        Args:
            catalog_path: Path to input catalog JSON
            output_path: Path to output enriched catalog
            image_output_dir: Optional directory to download images
        """
        logger.info(f"Enriching catalog: {catalog_path}")

        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            return

        products = catalog.get('products', [])
        enriched = []

        for i, product in enumerate(products):
            logger.info(f"Processing {i+1}/{len(products)}: {product.get('name')}")

            # Look for fragrantica_slug in product
            slug = product.get('fragrantica_slug')
            if not slug:
                # Try to search for it
                brand = product.get('brand')
                name = product.get('name')
                if brand and name:
                    slug = self.search_fragrance(brand, name)
                    if slug:
                        product['fragrantica_slug'] = slug

            if slug:
                profile = self.get_profile(slug)
                if profile:
                    # Enrich product with profile data
                    product['fragrantica_profile'] = profile.to_dict()

                    # Download image if requested
                    if image_output_dir and profile.image_url:
                        local_image_path = self.download_image(slug, image_output_dir)
                        if local_image_path:
                            product['fragrantica_image_local'] = local_image_path

            enriched.append(product)

        # Save enriched catalog
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {'products': enriched},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            logger.info(f"Saved enriched catalog to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save enriched catalog: {e}")


def setup_logging(level=logging.INFO) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Fragrantica scraper for fragrance enrichment"
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Scrape single fragrance
    scrape_parser = subparsers.add_parser('scrape', help='Scrape single fragrance')
    scrape_parser.add_argument('brand', help='Brand name')
    scrape_parser.add_argument('name', help='Fragrance name')
    scrape_parser.add_argument('--download-image', help='Directory to save image')
    scrape_parser.add_argument('--use-playwright', action='store_true')
    scrape_parser.add_argument('--cache-dir', default='data/fragrantica_cache')

    # Enrich catalog
    enrich_parser = subparsers.add_parser('enrich', help='Enrich product catalog')
    enrich_parser.add_argument('catalog', help='Input catalog JSON')
    enrich_parser.add_argument('output', help='Output catalog JSON')
    enrich_parser.add_argument('--image-dir', help='Directory to save images')
    enrich_parser.add_argument('--use-playwright', action='store_true')
    enrich_parser.add_argument('--cache-dir', default='data/fragrantica_cache')
    enrich_parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()

    setup_logging(level=logging.DEBUG if getattr(args, 'verbose', False) else logging.INFO)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'scrape':
        scraper = FragranticaScraper(
            cache_dir=args.cache_dir,
            use_playwright=args.use_playwright,
        )

        # Search for fragrance
        slug = scraper.search_fragrance(args.brand, args.name)
        if not slug:
            logger.error(f"Could not find {args.brand} {args.name}")
            sys.exit(1)

        # Get profile
        profile = scraper.get_profile(slug)
        if not profile:
            logger.error("Failed to get profile")
            sys.exit(1)

        # Print profile
        print(json.dumps(profile.to_dict(), indent=2))

        # Download image if requested
        if args.download_image:
            scraper.download_image(slug, args.download_image)

    elif args.command == 'enrich':
        scraper = FragranticaScraper(
            cache_dir=args.cache_dir,
            use_playwright=args.use_playwright,
        )

        scraper.enrich_catalog(
            args.catalog,
            args.output,
            image_output_dir=args.image_dir,
        )
