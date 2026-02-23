# PriceHunter

**AI-powered fragrance price tracking app**

Track niche perfume prices across retailers, get instant alerts when prices drop.

## Quick Start

```bash
# Start backend
docker-compose up -d

# Run scrapers
python3 -m scrapers.run_all

# Deploy mobile app
cd mobile && expo build:ios
```

## Features

- Real-time price monitoring (10+ retailers)
- Deal alerts via Telegram
- Wishlist with target prices
- Price history charts
- Mobile apps (iOS/Android)

## Tech Stack

- **Backend:** FastAPI, PostgreSQL, Redis
- **Mobile:** React Native (Expo)
- **Scraping:** Scrapling (anti-bot)
- **Hosting:** Railway/Render

## Status

✅ 80% complete — ready for deployment

## Revenue Model

- Affiliate commissions from retailers
- Freemium subscriptions
- Target: 100K downloads Year 1

## Links

- Main repo: https://github.com/Peptyl/pricehunter-app
- Workspace: https://github.com/Peptyl/peptyl-workspace
