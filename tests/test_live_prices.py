#!/usr/bin/env python3
"""
PriceHunter Live Price Validation Test
========================================
Run this on YOUR machine (not sandbox) to validate real scraping.

Usage:
    python tests/test_live_prices.py              # Test first 3 products
    python tests/test_live_prices.py --full       # Test all 20 products
    python tests/test_live_prices.py --retailer notino  # Test one retailer only
    python tests/test_live_prices.py --product pdm-layton-125-edp  # Test one product

Prerequisites:
    pip install beautifulsoup4 rapidfuzz lxml requests
    pip install playwright && playwright install chromium  # Optional: for JS sites
"""

import json
import sys
import os
import time
import argparse
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.engine import (
    ProductSKU, PriceHunterEngine, MatchValidator, PlaywrightScraper
)


def load_catalog():
    catalog_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "product_catalog_top20.json"
    )
    with open(catalog_path) as f:
        data = json.load(f)

    products = []
    for p in data["products"]:
        products.append(ProductSKU(
            id=p["id"],
            brand=p["brand"],
            name=p["name"],
            size_ml=p["size_ml"],
            concentration=p["concentration"],
            typical_retail_gbp=p["typical_retail_gbp"],
            aliases=p.get("aliases", []),
            retailer_urls=p.get("retailer_urls", {}),
            size_variants=p.get("size_variants_ml", []),
        ))
    return products


def main():
    parser = argparse.ArgumentParser(description="PriceHunter Live Price Validation")
    parser.add_argument("--full", action="store_true", help="Test all 20 products")
    parser.add_argument("--retailer", type=str, help="Test only this retailer")
    parser.add_argument("--product", type=str, help="Test only this product ID")
    args = parser.parse_args()

    products = load_catalog()
    engine = PriceHunterEngine()

    # Filter products
    if args.product:
        products = [p for p in products if p.id == args.product]
        if not products:
            print(f"Product '{args.product}' not found in catalog")
            sys.exit(1)
    elif not args.full:
        products = products[:3]

    # Filter scrapers
    if args.retailer:
        if args.retailer not in engine.scrapers:
            print(f"Retailer '{args.retailer}' not found. Available: {list(engine.scrapers.keys())}")
            sys.exit(1)
        engine.scrapers = {args.retailer: engine.scrapers[args.retailer]}

    print("=" * 90)
    print("PRICEHUNTER LIVE PRICE VALIDATION")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Products: {len(products)}")
    print(f"Retailers: {list(engine.scrapers.keys())}")
    print(f"Playwright: {'YES' if PlaywrightScraper.is_available() else 'NO (install: pip install playwright && playwright install chromium)'}")
    print("=" * 90)

    # Stats
    stats = defaultdict(lambda: {"success": 0, "fail": 0, "no_url": 0, "total_response_ms": 0})
    all_results = []

    for pi, sku in enumerate(products):
        print(f"\n{'─' * 90}")
        print(f"[{pi+1}/{len(products)}] {sku.brand} {sku.name} ({sku.size_ml}ml {sku.concentration})")
        print(f"  RRP: £{sku.typical_retail_gbp}  |  Good deal: £{sku.typical_retail_gbp * 0.80:.0f}  |  Hot deal: £{sku.typical_retail_gbp * 0.72:.0f}")

        report = engine.scan_product(sku)

        if not report.prices:
            print(f"  ⚠️  NO PRICES FOUND from {report.retailers_attempted} retailers")
        else:
            # Sort by total price
            sorted_prices = sorted(report.prices, key=lambda p: p.total_gbp)

            for i, price_opt in enumerate(sorted_prices):
                rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "

                # Show local price + currency, then GBP total
                if price_opt.currency == "GBP":
                    local_str = f"£{price_opt.price_local:.2f}"
                else:
                    local_str = f"{price_opt.currency} {price_opt.price_local:.2f} (£{price_opt.price_gbp:.2f})"

                route_str = f"via {price_opt.forwarder}" if price_opt.forwarder else "direct"

                print(f"  {rank} {price_opt.retailer:18s} | {local_str:28s} | ship £{price_opt.shipping_gbp:.2f} | VAT £{price_opt.vat_gbp:.2f} | TOTAL £{price_opt.total_gbp:.2f} | conf: {price_opt.confidence:.0f}% | {route_str}")

                all_results.append({
                    "product": sku.id,
                    "retailer": price_opt.retailer,
                    "local_price": price_opt.price_local,
                    "currency": price_opt.currency,
                    "total_gbp": price_opt.total_gbp,
                    "confidence": price_opt.confidence,
                    "in_stock": price_opt.in_stock,
                })

            print(f"  ───")
            print(f"  Best price: £{sorted_prices[0].total_gbp:.2f} from {sorted_prices[0].retailer}")
            savings = sku.typical_retail_gbp - sorted_prices[0].total_gbp
            savings_pct = (savings / sku.typical_retail_gbp) * 100
            print(f"  Saving: £{savings:.2f} ({savings_pct:.0f}% off RRP)")

        # Rate limit
        time.sleep(0.5)

    # SUMMARY
    print(f"\n{'=' * 90}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 90}")

    total_products = len(products)
    products_with_prices = len(set(r["product"] for r in all_results))
    total_price_points = len(all_results)
    avg_confidence = sum(r["confidence"] for r in all_results) / len(all_results) if all_results else 0

    print(f"\nProducts tested:     {total_products}")
    print(f"Products with data:  {products_with_prices}/{total_products}")
    print(f"Total price points:  {total_price_points}")
    print(f"Avg confidence:      {avg_confidence:.1f}%")

    # Retailer breakdown
    retailer_counts = defaultdict(int)
    for r in all_results:
        retailer_counts[r["retailer"]] += 1

    print(f"\nRetailer success rates:")
    for retailer in sorted(retailer_counts.keys()):
        count = retailer_counts[retailer]
        print(f"  {retailer:18s}: {count}/{total_products} products scraped successfully")

    # Save results
    results_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests", "live_validation_results.json"
    )
    with open(results_path, 'w') as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "total_products": total_products,
            "total_price_points": total_price_points,
            "avg_confidence": avg_confidence,
            "results": all_results,
        }, f, indent=2, default=str)

    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    main()
