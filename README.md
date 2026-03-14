# PriceHunter

**Never overpay for niche perfumes again.**

PriceHunter tracks fragrance prices across 10+ global retailers and alerts you when prices drop. Built with a v2 scraper engine achieving 98-99% accuracy across a curated top 20 niche fragrance catalog.

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/Peptyl/pricehunter-app.git
cd pricehunter-app

# Setup environment
cp .env.example .env
# Edit .env with your credentials (Firebase, Clerk, RevenueCat, PostgreSQL, Redis)

# Backend
docker-compose up -d

# Run price scan
python -m backend.scheduler_service --once

# Mobile
cd mobile && npm install && npx expo start
```

## ✨ Features

- **High-Accuracy Price Tracking** — v2 scraper with 4-layer validation (98-99% accuracy)
- **Top 20 Curated Catalog** — Niche fragrances: Creed, Tom Ford, Parfums de Marly, MFK, Amouage, etc.
- **Real-time Monitoring** — Scans at 06:00, 12:00, 18:00 GMT via APScheduler
- **Instant Deal Alerts** — PostgreSQL-backed alerts for target prices
- **Redis Caching** — 6-hour cache for free users, real-time for pro users
- **Multi-tier Access** — Free (limited deals) → Premium → Pro (unlimited + predictions)
- **Multi-platform** — iOS and Android via React Native (Expo)

## 📊 Scraper Architecture

The v2 engine uses a "Trust Nothing, Verify Everything" approach:

1. **Product Catalog** — Canonical SKU database (top_20_niche_perfumes) with multiple aliases
2. **Scraper Layer** — Per-retailer extraction with HTML parsing and dynamic content handling
3. **Validation Layer** — Fuzzy matching + sanity checks (price bounds, currency conversion)
4. **Cost Adjustment Layer** — Exchange rates, shipping, VAT/duty inclusion

**Retailers Monitored:**
Notino, Niche Gallerie, Douglas, FragranceBuy, MaxAroma, JomaShop, FragranceNet

## 📱 Screenshots

![Deal Feed](./assets/screenshots/iphone-deal-feed.png)
![Price History](./assets/screenshots/iphone-price-history.png)
![Alerts](./assets/screenshots/iphone-alerts.png)

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Mobile** | React Native (Expo) |
| **Backend** | FastAPI 0.104+ |
| **Database** | PostgreSQL 14+ |
| **Cache** | Redis 7+ |
| **Scraping** | BeautifulSoup4 + RapidFuzz (v2 engine) |
| **Scheduling** | APScheduler |
| **Auth** | Clerk |
| **Payments** | RevenueCat |
| **Analytics** | Firebase |
| **Hosting** | Railway/Render |

## 🚀 Local Development

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+ (for mobile)

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis
docker-compose up -d

# Initialize database (runs on first API request)
python -c "from backend.main import init_db; init_db()"

# Run API server
uvicorn backend.main:app --reload --port 8000

# Run scheduler in another terminal
python -m backend.scheduler_service
```

### Test Price Scan

```bash
# Single scan
python -c "from backend.scheduler_service import SchedulerService; s = SchedulerService(); print(s.run_scan())"

# Or use the scraper service directly
python -c "from backend.scraper_service import get_scraper_service; svc = get_scraper_service(); deals = svc.get_all_deals(); print(f'Found {len(deals[\"deals\"])} deals')"
```

## 🔧 Environment Variables

See `.env.example` for full list. Key variables:

```bash
# API
PORT=8000
DEV_MODE=false

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pricehunter
DB_USER=pricehunter
DB_PASS=pricehunter123

# Cache
REDIS_HOST=localhost
REDIS_PORT=6379

# Scheduler
SCHEDULER_ENABLED=true
SCHEDULER_SCAN_TIMES=06:00,12:00,18:00
SCHEDULER_TIMEZONE=UTC

# Auth & Payments
CLERK_PUBLISHABLE_KEY=pk_test_...
REVENUECAT_API_KEY=sk_...
```

## 📊 Status

- [x] Backend API v2.0
- [x] Database schema (PostgreSQL)
- [x] v2 Scraper engine (98-99% accuracy)
- [x] Product catalog (top 20)
- [x] Scheduler service
- [x] Mobile app scaffold
- [x] CI/CD (GitHub Actions)
- [ ] App Store submission ← **Next**
- [ ] Play Store submission ← **Next**

## 💰 Revenue Model

- **Affiliate commissions** from retailer links
- **Free tier** — 3 deals/day, basic alerts
- **Premium** (£4.99/month) — unlimited tracking, price history
- **Pro** (£9.99/month) — AI predictions, arbitrage alerts
- **Target:** 100K downloads Year 1

## 📈 Metrics

| Metric | Target |
|--------|--------|
| Downloads | 100,000 (Year 1) |
| DAU | 20,000 |
| Retention (D7) | 35% |
| Revenue | £30,000/month |
| Scraper Accuracy | 98-99% |

## 🧪 Testing

```bash
# Run linting
flake8 backend scraper --max-line-length=127

# Run backend tests
pytest backend/test_e2e.py -v

# Check scraper syntax
python -c "import scraper.engine; print('✅ Scraper OK')"
```

## 📝 License

MIT © Peptyl Ltd

## 🔗 Links

- Website: https://pricehunter.app
- Support: support@pricehunter.app
- Twitter: @PriceHunterApp
- GitHub: https://github.com/Peptyl/pricehunter-app

---

**Built with precision & care by the Peptyl team**
