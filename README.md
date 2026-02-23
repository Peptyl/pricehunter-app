# PriceHunter

**Never overpay for niche perfumes again.**

PriceHunter tracks fragrance prices across 10+ retailers and alerts you when prices drop.

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/Peptyl/pricehunter-app.git
cd pricehunter-app

# Backend
docker-compose up -d

# Mobile
cd mobile && npm install && npx expo start
```

## ✨ Features

- **Real-time Price Tracking** — Monitor 10+ retailers (Notino, Douglas, FragranceNet, etc.)
- **Instant Deal Alerts** — Telegram notifications when prices drop
- **Price History** — Charts showing 30/90/365 day trends
- **Wishlist** — Track your favorite fragrances with target prices
- **Multi-platform** — iOS and Android apps

## 📱 Screenshots

![Deal Feed](./assets/screenshots/iphone-deal-feed.png)
![Price History](./assets/screenshots/iphone-price-history.png)
![Alerts](./assets/screenshots/iphone-alerts.png)

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Mobile** | React Native (Expo) |
| **Backend** | FastAPI, PostgreSQL |
| **Scraping** | Scrapling (anti-bot) |
| **Auth** | Clerk |
| **Payments** | RevenueCat |
| **Analytics** | Firebase |
| **Hosting** | Railway/Render |

## 📊 Status

- [x] Backend API
- [x] Database schema
- [x] Price scrapers
- [x] Mobile app scaffold
- [x] Telegram alerts
- [ ] App Store submission ← **Next**
- [ ] Play Store submission ← **Next**

## 💰 Revenue Model

- **Affiliate commissions** from retailer links
- **Pro subscription** (£4.99/month) — unlimited tracking
- **Target:** 100K downloads Year 1

## 📈 Metrics

| Metric | Target |
|--------|--------|
| Downloads | 100,000 (Year 1) |
| DAU | 20,000 |
| Retention (D7) | 35% |
| Revenue | £30,000/month |

## 📝 License

MIT © Peptyl Ltd

## 🔗 Links

- Website: https://pricehunter.app
- Support: support@pricehunter.app
- Twitter: @PriceHunterApp

---

**Built with ❤️ by the Peptyl team**
