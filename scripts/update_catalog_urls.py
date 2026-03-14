"""
Update product catalog with verified real retailer URLs.
All URLs discovered via web search on 2026-03-14.
"""
import json
import os

catalog_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "product_catalog_top20.json")

with open(catalog_path, 'r') as f:
    catalog = json.load(f)

# ============================================================================
# VERIFIED URLs — discovered via site: searches on 2026-03-14
# ============================================================================

VERIFIED_URLS = {
    # ===================
    # FRAGRANCEBUY.CA (Shopify store — all confirmed via site:fragrancebuy.ca)
    # ===================
    "fragrancebuy": {
        "pdm-layton-125-edp": "https://fragrancebuy.ca/products/parfumsdemarlylayton-man",
        "pdm-carlisle-125-edp": "https://fragrancebuy.ca/products/carlislemarly-man",
        "pdm-pegasus-125-edp": "https://fragrancebuy.ca/products/pegasusmarly-man",
        "pdm-herod-125-edp": "https://fragrancebuy.ca/products/herodmarly-man",
        "creed-aventus-100-edp": "https://fragrancebuy.ca/products/creedaventus-man",
        "creed-git-100-edp": "https://fragrancebuy.ca/products/creedgreenirish-man",
        "creed-smw-100-edp": "https://fragrancebuy.ca/products/creedsilvermountain-man",
        "tf-tuscan-leather-100-edp": "https://fragrancebuy.ca/products/tomfordtuscanleather-man",
        "tf-oud-wood-100-edp": "https://fragrancebuy.ca/products/tomfordoudwood-man",
        "tf-tobacco-vanille-100-edp": "https://fragrancebuy.ca/products/tomfordtobaccovanille-man",
        "mfk-br540-70-edp": "https://fragrancebuy.ca/products/franciskurkdjian540baccaratrouge-man",
        # mfk-grand-soir: NOT FOUND on fragrancebuy.ca
        "amouage-reflection-100-edp": "https://fragrancebuy.ca/products/amouagereflectioncologne-man",
        "amouage-interlude-100-edp": "https://fragrancebuy.ca/products/amouageinterlude-man",
        "initio-ofg-90-edp": "https://fragrancebuy.ca/products/initiooudforgreatness-man",
        "initio-side-effect-90-edp": "https://fragrancebuy.ca/products/initiosideeffect-man",
        "xerjoff-naxos-100-edp": "https://fragrancebuy.ca/products/xerjoff1861naxos-man",
        "xerjoff-erba-pura-100-edp": "https://fragrancebuy.ca/products/xerjofferbapura-man",
        "le-labo-santal33-100-edp": "https://fragrancebuy.ca/products/lelabosantal-man",
        "byredo-mojave-ghost-100-edp": "https://fragrancebuy.ca/products/byredomojaveghost-man",
    },

    # ===================
    # JOMASHOP (React SPA — all confirmed via site:jomashop.com)
    # ===================
    "jomashop": {
        "pdm-layton-125-edp": "https://www.jomashop.com/parfums-de-marly-mens-layton-edp-spray-4-2-oz-fragrances-3700578518002.html",
        "pdm-carlisle-125-edp": "https://www.jomashop.com/parfums-de-marly-unisex-carlisle-edp-spray-4-2-oz-fragrances-3700578519009.html",
        "pdm-pegasus-125-edp": "https://www.jomashop.com/parfums-de-marly-mens-pegasus-edp-spray-4-2-oz-fragrances-3700578506009.html",
        "pdm-herod-125-edp": "https://www.jomashop.com/herod-by-parfums-de-marly-for-men-4-2-oz-edp-spray-3700578507006.html",
        "creed-aventus-100-edp": "https://www.jomashop.com/creed-fragrances-cavmes33b-3-3oz.html",
        "creed-git-100-edp": "https://www.jomashop.com/creed-fragrances-cgimes33b-3-3oz.html",
        "creed-smw-100-edp": "https://www.jomashop.com/creed-perfume-csmes33.html",
        "tf-tuscan-leather-100-edp": "https://www.jomashop.com/tom-ford-unisex-tuscan-leather-edp-spray-3-4-oz-fragrances-888066004459.html",
        "tf-oud-wood-100-edp": "https://www.jomashop.com/tom-ford-unisex-oud-wood-edp-spray-3-4-oz-fragrances-888066024099.html",
        "tf-tobacco-vanille-100-edp": "https://www.jomashop.com/tom-ford-unisex-tobacco-vanille-edp-spray-3-4-oz-fragrances-888066004503.html",
        "mfk-br540-70-edp": "https://www.jomashop.com/maison-francis-kurkdjian-unisex-baccarat-rouge-540-white-edp-spray-2-4-oz-fragrances-3700559603116.html",
        # mfk-grand-soir: need to search separately
        "amouage-reflection-100-edp": "https://www.jomashop.com/amouage-mens-reflection-edp-spray-3-4-oz-fragrances-701666410058.html",
        "amouage-interlude-100-edp": "https://www.jomashop.com/amouage-mens-interlude-edp-spray-3-4-oz-fragrances-701666410195.html",
        "initio-ofg-90-edp": "https://www.jomashop.com/initio-parfums-prives-oud-for-greatness-eau-de-parfum-spray-90ml-3701415900080.html",
        "initio-side-effect-90-edp": "https://www.jomashop.com/initio-unisex-the-carnal-blend-side-effect-edp-spray-3-oz-fragrances-3701415900073.html",
        # xerjoff-naxos, xerjoff-erba-pura, le-labo-santal33, byredo-mojave-ghost: need separate search
    },

    # ===================
    # FRAGRANCENET (hierarchical URLs — confirmed via site:fragrancenet.com)
    # ===================
    "fragrancenet": {
        "pdm-layton-125-edp": "https://www.fragrancenet.com/fragrances/parfums-de-marly/parfums-de-marly-layton/eau-de-parfum",
        "creed-aventus-100-edp": "https://www.fragrancenet.com/fragrances/creed/creed-aventus/eau-de-parfum",
        # Remaining need individual searches
    },
}

# Apply all verified URLs
fixes_applied = 0
products_updated = set()

for product in catalog['products']:
    for retailer, url_map in VERIFIED_URLS.items():
        if product['id'] in url_map:
            old_url = product['retailer_urls'].get(retailer, '')
            new_url = url_map[product['id']]
            if old_url != new_url:
                product['retailer_urls'][retailer] = new_url
                fixes_applied += 1
                products_updated.add(product['id'])

catalog['last_updated'] = '2026-03-14'

with open(catalog_path, 'w') as f:
    json.dump(catalog, f, indent=2)

print(f"Applied {fixes_applied} URL fixes across {len(products_updated)} products")
print(f"\nVerified URLs by retailer:")
for retailer, urls in VERIFIED_URLS.items():
    print(f"  {retailer}: {len(urls)} products verified")

# Report gaps
print(f"\nGaps remaining:")
all_products = [p['id'] for p in catalog['products']]
all_retailers = list(VERIFIED_URLS.keys())
for retailer in all_retailers:
    missing = [pid for pid in all_products if pid not in VERIFIED_URLS[retailer]]
    if missing:
        print(f"  {retailer}: {len(missing)} products still need URL verification")
        for pid in missing:
            print(f"    - {pid}")
