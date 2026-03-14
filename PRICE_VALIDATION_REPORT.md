# PriceHunter — Live Price Validation Report

**Date:** 14 March 2026
**Method:** Browser-based validation using Chrome JavaScript fetch() against live retailer sites
**Scope:** All 20 products × 8 retailers

---

## Retailer Validation Summary

| Retailer | Platform | Scraper Strategy | Products Found | Currency | Status |
|----------|----------|-----------------|----------------|----------|--------|
| FragranceBuy | Shopify | JSON API (.json) | 19/20 | CAD | ✅ Verified |
| NicheGallerie | WooCommerce | HTML parser (rewritten) | 17/20 | GBP | ✅ Verified |
| Notino | Custom | JSON-LD structured data | 14/20 | GBP | ✅ Verified |
| SeeScents | Shopify | JSON API (.json) | 7/20 | GBP | ✅ Verified |
| Jomashop | Custom (Next.js) | Playwright required | 20/20 | USD | ✅ URLs verified |
| MaxAroma | Custom | HTML/DOM extraction | ~20 | USD | ⚠️ URLs verified, JSON-LD price=0 |
| FragranceNet | Custom | Blocked from sandbox | ~20 | USD | ⚠️ URLs found via search |
| Douglas | Custom | Blocked from sandbox | ~20 | EUR | ⚠️ Not reachable from sandbox |

---

## Verified Prices (Live Browser Extraction)

### Notino (GBP) — JSON-LD works perfectly
| Product | Price (GBP) | Size | Status |
|---------|-------------|------|--------|
| PDM Layton | £270.00 | 125ml | ✅ |
| PDM Carlisle | £330.00 | 125ml | ✅ |
| PDM Pegasus | £270.00 | 125ml | ✅ |
| PDM Herod | £270.00 | 125ml | ✅ |
| Creed Aventus | £261.50 | 100ml | ✅ |
| Creed GIT | £248.80 | 100ml | ✅ |
| Creed SMW | £248.80 | 100ml | ✅ |
| TF Tuscan Leather | — | — | ❌ Out of stock |
| TF Oud Wood | — | — | ❌ Out of stock |
| TF Tobacco Vanille | — | — | ❌ Out of stock |
| MFK BR540 | — | — | ❌ Not on Notino UK |
| MFK Grand Soir | — | — | ❌ Not on Notino UK |
| Amouage Reflection | £311.90 | 100ml | ✅ |
| Amouage Interlude | £311.90 | 100ml | ✅ |
| Initio OFG | £320.00 | 90ml | ✅ |
| Initio Side Effect | £275.00 | 90ml | ✅ |
| Xerjoff Naxos | £167.36 | 100ml | ✅ |
| Xerjoff Erba Pura | £155.55 | 100ml | ✅ |
| Le Labo Santal 33 | — | — | ❌ Not on Notino UK |
| Byredo Mojave Ghost | £213.50 | 100ml | ✅ |

### NicheGallerie (GBP) — WooCommerce HTML extraction
| Product | Price (GBP) | Status |
|---------|-------------|--------|
| PDM Layton 125ml | £202 | ✅ |
| PDM Carlisle 125ml | £229 | ✅ |
| PDM Pegasus 125ml | £199 | ✅ |
| PDM Herod 125ml | £192 | ✅ |
| Creed Aventus 100ml | Price regex failed | ⚠️ |
| Creed GIT 100ml | £215 | ✅ |
| Creed SMW 100ml | £171 | ✅ |
| TF Tuscan Leather 100ml | £266 | ✅ |
| TF Oud Wood 100ml | £246 | ✅ |
| TF Tobacco Vanille | — | ❌ Not found |
| MFK BR540 70ml | £96 | ✅ (suspiciously low?) |
| MFK Grand Soir | — | ❌ Not found |
| Amouage Reflection 100ml | £285 | ✅ |
| Amouage Interlude 100ml | £304 | ✅ |
| Initio OFG 90ml | £202 | ✅ |
| Initio Side Effect 90ml | £192 | ✅ |
| Xerjoff Naxos | — | ❌ Not found |
| Xerjoff Erba Pura 100ml | Price regex failed | ⚠️ |
| Le Labo Santal 33 100ml | £233 | ✅ |
| Byredo Mojave Ghost 100ml | £196 | ✅ |

### SeeScents (GBP) — Shopify JSON API
| Product | Price (GBP) | Status |
|---------|-------------|--------|
| PDM Layton | £225.00 | ✅ |
| PDM Carlisle 125ml | £245.00 | ✅ |
| PDM Herod 125ml | £225.00 | ✅ |
| Creed Aventus | £239.00 | ✅ |
| Initio Side Effect 90ml | £225.00 | ✅ |
| Xerjoff Naxos 100ml | £175.00 | ✅ |
| TF Tobacco Vanille 100ml | £277.00 | ✅ |

### Jomashop (USD) — Playwright required
| Product | Price (USD) | Status |
|---------|-------------|--------|
| PDM Layton 125ml | $360.00 | ✅ Verified from rendered page |
| All others | URLs verified via web search | ⚠️ Needs Playwright for prices |

---

## Critical Bugs Found & Fixed This Session

### 1. NicheGallerie is WooCommerce, NOT Shopify (CRITICAL)
- **Discovery:** Shopify JSON API calls to `/products/{handle}.json` were returning 404
- **Root cause:** NicheGallerie uses WordPress/WooCommerce/Elementor
- **URL pattern:** `/perfume/{slug}/` not `/products/{handle}/`
- **Fix:** Complete scraper rewrite from `ShopifyJSONScraper` to `WooCommerceHTMLParser`
- **Impact:** 17 out of 20 products now extractable

### 2. Notino URLs were ALL wrong
- **Issue:** Catalog had URLs like `/parfums-de-marly/layton-eau-de-parfum-for-men/` → 404
- **Real URLs:** `/parfums-de-marly/layton-royal-essence-eau-de-parfum-unisex/`
- **Fix:** All 14 active Notino URLs verified and updated
- **Notino variant bug:** Was taking `offers[0]` (smallest/cheapest size). Now matches target size.

### 3. SeeScents "Default Title" variant bug
- **Issue:** SeeScents uses "Default Title" as variant title → size extraction fails
- **Fix:** Fallback to extract size from product title when variant title is useless

### 4. FragranceBuy stock check broken
- **Issue:** Using `variant.available` which is undefined on some products
- **Root cause:** FragranceBuy uses `inventory_quantity` + `inventory_policy` instead
- **Fix:** Check `inventory_quantity > 0 || inventory_policy == 'continue'`

### 5. Tom Ford out of stock on Notino UK
- **Issue:** All 3 TF products show "sorry" page, JSON-LD returns £3.49 (sample price)
- **Fix:** Removed Notino URLs for these products; scraper won't waste time

### 6. MFK & Le Labo not sold on Notino UK
- **Discovery:** Notino UK doesn't carry MFK or Le Labo brands at all
- **Fix:** Removed these URLs from catalog

---

## Scraper Architecture Per Retailer

| Retailer | Strategy | Data Source | Size Matching | Notes |
|----------|----------|-------------|---------------|-------|
| FragranceBuy | Shopify JSON API | `/products/{handle}.json` | Variant title regex | CAD prices, stock via inventory_quantity |
| NicheGallerie | WooCommerce HTML | JSON-LD + `<p class="price">` + regex | Product title/URL | NEW: Complete rewrite from Shopify |
| SeeScents | Shopify JSON API | `/products/{handle}.json` | Product title fallback | "Default Title" variant workaround |
| Notino | HTTP + JSON-LD | Schema.org structured data | Offer name/description | Size-matched variant selection |
| Jomashop | Playwright (headless) | JSON-LD after JS render | dataLayer object | Full JS rendering required |
| MaxAroma | HTTP + DOM | CSS selectors (JSON-LD price=0) | N/A | JSON-LD is broken, need DOM |
| FragranceNet | HTTP + JSON-LD | Schema.org structured data | TBD | Blocked from sandbox testing |
| Douglas | HTTP + JSON-LD | Schema.org structured data | TBD | Blocked from sandbox testing |

---

## Remaining Gaps

1. **MaxAroma price extraction:** JSON-LD returns `price: "0.0"`. Need DOM/CSS selector approach.
2. **FragranceNet & Douglas:** Couldn't be tested from sandbox (blocked). Need live testing.
3. **NicheGallerie 2 price failures:** Creed Aventus and Xerjoff Erba Pura — regex didn't match their price format. May need WooCommerce-specific price selector.
4. **MFK BR540 on NicheGallerie:** Price shows £96 which seems suspiciously low for a 70ml MFK. May be a smaller decant or pricing error — needs manual verification.
5. **Jomashop prices:** Only Layton ($360) verified from rendered page. All URLs confirmed but need Playwright deployment for bulk price extraction.

---

## Git Commits This Session

| Hash | Description |
|------|-------------|
| `a35d4f5d` | Add SeeScents as Tier 1 retailer |
| `10984945` | Fix 5 critical scraper bugs found during audit |
| `7becbced` | Production-grade scraper: Playwright, Shopify APIs, retry, circuit breaker |
| `21eda277` | Remove node_modules from git (63,051 files) |
| `5e6efc9c` | Fix all retailer URLs and scraper bugs from live browser validation |
