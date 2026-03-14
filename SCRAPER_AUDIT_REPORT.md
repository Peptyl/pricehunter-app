# PriceHunter Scraper Audit Report
**Date:** 2026-03-14
**Auditor:** CTO (Claude)
**Scope:** All 8 scrapers × 20 products — code review + URL verification

---

## Executive Summary

The v2 scraper engine has **12 bugs**, of which **5 are critical** (would cause wrong prices or total failures in production). The validation layer and architecture are sound, but the implementation has issues that would drop us to ~30-40% accuracy rather than the 98-99% target.

**No live testing was possible** from this sandbox (egress proxy blocks all retail domains). All findings are from code review + web search URL verification.

---

## CRITICAL BUGS (will cause wrong prices or total failure)

### BUG #1: SeeScents domain is WRONG
- **File:** `data/retailer_registry.json`, `data/product_catalog_top20.json`, `scraper/engine.py`
- **Issue:** We have `seescents.co.uk` everywhere. The actual domain is **`seescents.com`**
- **Impact:** 100% failure rate for SeeScents. Every URL 404s.
- **Fix:** Replace all `seescents.co.uk` → `seescents.com`

### BUG #2: NicheGallerie Shopify price divided by 100 (WRONG)
- **File:** `scraper/engine.py` line 604
- **Code:** `price = float(variant.get('price', 0)) / 100`
- **Issue:** Shopify storefront `.json` API returns prices as **strings** like `"149.00"`, NOT in cents. Dividing by 100 turns a £149 bottle into £1.49.
- **Impact:** Every NicheGallerie price is 100× too low. Would show PDM Layton at £1.55 instead of £155.
- **Fix:** Remove the `/ 100` → `price = float(variant.get('price', '0'))`

### BUG #3: Catalog URLs are fabricated (4 of 8 retailers)
- **File:** `data/product_catalog_top20.json`
- **Issue:** URLs were generated from assumed patterns but don't match actual retailer URL structures:
  - **FragranceBuy CA:** Our URL: `/products/parfums-de-marly-layton-125ml-edp` → Real URL: `/products/parfumsdemarlylayton-man` (no hyphens in slug, appends `-man`)
  - **MaxAroma:** Our URL: `/parfums-de-marly/layton-edp-125ml` → Real URL: `/fragrance/niche-fragrances/parfums-de-marly-layton/pid/14225/2` (completely different structure with product IDs)
  - **Jomashop:** Our URL: `/parfums-de-marly-layton-edp-125ml.html` → Real URL: `/parfums-de-marly-mens-layton-edp-spray-4-2-oz-fragrances-3700578518002.html` (includes barcode/SKU number)
  - **FragranceNet:** Our URL: `/parfums-de-marly-layton-edp-125ml` → Real URL: `/fragrances/parfums-de-marly/parfums-de-marly-layton/eau-de-parfum` (hierarchical category path)
- **Impact:** All 20 products × 4 retailers = **80 broken URLs** (all will 404)
- **Fix:** Must crawl/search each retailer for correct product URLs. Can be semi-automated with search scraper.

### BUG #4: Currency conversion fallback rates are inverted
- **File:** `scraper/engine.py` lines 330-335
- **Issue:** The exchange rate API returns "units per 1 GBP" (e.g. USD: 1.27), and the code does `amount / rate`. But the fallback rates use "GBP per 1 unit" format (e.g. USD: 0.79). With division: `$100 / 0.79 = £126.58` instead of the correct `£78.74`.
- **Impact:** When the exchange rate API is down, ALL non-GBP prices are ~60% too high. A $200 Jomashop price would show as £253 instead of £157.
- **Fix:** Change fallback rates to match API format: `"USD": 1.27, "EUR": 1.17, "CAD": 1.70`

### BUG #5: VAT double-charged on UK domestic purchases
- **File:** `scraper/engine.py` lines 1034, and `ShippingCalculator.calculate_landed_cost`
- **Issue:** UK retailer prices (Notino UK, NicheGallerie, SeeScents) already INCLUDE 20% VAT. But the engine adds another 20% VAT on top: `vat = (price_gbp + shipping) * 0.20`
- **Impact:** All UK-retailer prices inflated by 20%. A £155 NicheGallerie price shows as £186.
- **Fix:** Only apply VAT on non-UK/non-EU imports. Add `country` field check.

---

## SIGNIFICANT BUGS (reduce accuracy or miss products)

### BUG #6: NicheGallerie takes first variant (wrong size)
- **File:** `scraper/engine.py` line 603
- **Code:** `variant = variants[0]`
- **Issue:** Takes the first Shopify variant without checking if it matches the target size. If variants are [50ml, 100ml, 125ml], we get 50ml price for a 125ml search.
- **Impact:** Wrong size → wrong price. Validation layer SHOULD catch this via size match, but only if the variant title contains "ml".
- **Fix:** Port the SeeScents variant-matching logic (which does try to match by size) to NicheGallerie too.

### BUG #7: SeeScents variant matching uses wrong target
- **File:** `scraper/engine.py` line 941
- **Code:** `target_size = sku.size_variants[0] if sku.size_variants else None`
- **Issue:** Uses `sku.size_variants[0]` (the first ALTERNATIVE size) instead of `sku.size_ml` (the TARGET size).
- **Impact:** For PDM Layton (target 125ml, variants [75, 125]), this would match against 75ml, returning the wrong size.
- **Fix:** Change to `target_size = sku.size_ml`

### BUG #8: SeeScents missing from ShippingCalculator
- **File:** `scraper/engine.py` lines 342-350
- **Issue:** `RETAILER_SHIPPING` dict doesn't include `seescents`. Will return £0 shipping by default.
- **Impact:** Shipping cost missing from landed cost calculation.
- **Fix:** Add `"seescents": {"base_gbp": 3.95, "free_over_gbp": 50, "delivery_days": "1-3", "ships_to_uk": True}`

### BUG #9: Orchestrator variable reference error
- **File:** `scraper/engine.py` line 1023 (FIXED during this audit)
- **Code:** Was `scrapers[retailer_name]` → now `self.scrapers[retailer_name]`
- **Impact:** Would crash on every single scan attempt with NameError.
- **Status:** FIXED

---

## MODERATE ISSUES (affect edge cases)

### BUG #10: Stock check false positives
- **File:** `scraper/engine.py` line 476-492
- **Issue:** Searches entire page text for "out of stock". Many pages have this in footers, sidebars, or newsletter prompts like "Never miss an out of stock item".
- **Fix:** Limit stock check to product-specific elements (e.g., add-to-cart button area).

### BUG #11: Notino JSON-LD offers format assumption
- **File:** `scraper/engine.py` line 524
- **Code:** `data['offers'][0]` assumes offers is always a list
- **Issue:** Schema.org allows `offers` to be either a list OR a single object.
- **Fix:** Add type check: `offers = data['offers'] if isinstance(data['offers'], list) else [data['offers']]`

### BUG #12: FragranceBuy CSS class selectors likely wrong
- **File:** `scraper/engine.py` lines 713-718
- **Issue:** Uses regex `product.*title` for h1 class and `price|sale` for price span. FragranceBuy is a Shopify store — their classes are typically `product-single__title` and `product__price`.
- **Fix:** Need to inspect actual HTML or use Shopify `.json` API instead.

---

## ARCHITECTURAL GAPS

### GAP #1: No URL auto-discovery
All 20 products × 8 retailers = 160 URLs that were manually guessed. At least 80 are wrong. Need an automated URL finder that:
1. Searches retailer site for product name
2. Validates the found URL matches the product
3. Stores verified URLs

### GAP #2: No headless browser fallback
5 of 8 retailers use JavaScript-rendered content or have bot protection. `requests + BeautifulSoup` will fail on:
- Jomashop (React SPA, heavy JS rendering)
- MaxAroma (likely JS-rendered prices)
- Douglas DE (Cloudflare protection)
Need Playwright/Puppeteer as fallback for JS-heavy sites.

### GAP #3: No retry/circuit breaker logic
A temporary 429 or 503 from a retailer kills that entire scan. Need:
- Exponential backoff retry (3 attempts)
- Circuit breaker (if retailer fails 5× in a row, skip for 1 hour)

### GAP #4: FragranceBuy should use Shopify JSON API
FragranceBuy.ca is a Shopify store. Our scraper uses HTML parsing with CSS class guessing. Should use the `.json` API endpoint like we do for NicheGallerie/SeeScents — far more reliable.

### GAP #5: No proxy rotation
Many retailers will block repeated requests from the same IP. Need rotating proxy support for production scraping.

---

## RETAILER-BY-RETAILER STATUS

| Retailer | URLs Valid? | Scraper Logic | Critical Bugs | Production Ready? |
|----------|-------------|---------------|---------------|-------------------|
| Notino UK | ⚠️ Unverified | JSON-LD ✓ | offers format | MAYBE |
| NicheGallerie | ⚠️ Unverified | Shopify API ✓ | price/100, wrong variant | NO |
| Douglas DE | ⚠️ Unverified | JSON-LD ✓ | Cloudflare blocking | NO |
| FragranceBuy CA | ❌ Wrong URLs | HTML parse ⚠️ | Wrong URLs, wrong selectors | NO |
| MaxAroma | ❌ Wrong URLs | JSON-LD ✓ | Wrong URLs | NO |
| Jomashop | ❌ Wrong URLs | HTML parse ⚠️ | Wrong URLs, JS rendering | NO |
| FragranceNet | ❌ Wrong URLs | JSON-LD ✓ | Wrong URLs | NO |
| SeeScents | ❌ Wrong domain | Shopify API ✓ | Wrong domain, wrong target | NO |

**Current estimated accuracy: ~15-20%** (only Notino has a chance of working)
**After fixing all bugs: ~85-90%** (with correct URLs + code fixes)
**After adding headless browser: ~95-98%** (JS-rendered sites covered)
**After adding proxy rotation: ~98-99%** (target achieved)

---

## PRIORITY FIX ORDER

1. **Fix all 5 critical code bugs** (30 mins) — immediate accuracy improvement
2. **Discover and verify all 160 real URLs** (2-3 hours) — semi-automated with search
3. **Convert FragranceBuy to Shopify JSON API** (30 mins) — reliability improvement
4. **Add Playwright fallback for JS sites** (2 hours) — covers Jomashop, MaxAroma, Douglas
5. **Add retry/circuit breaker** (1 hour) — resilience
6. **Add proxy rotation** (1 hour) — anti-blocking
