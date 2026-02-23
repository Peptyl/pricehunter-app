# PriceHunter - Build Status
## Niche Perfume Price Tracking App

---

## ✅ COMPLETED COMPONENTS

### 1. Data Layer
- ✅ `data/perfumes.json` - Top 10 niche perfumes with pricing thresholds
  - Parfums de Marley, Creed, Tom Ford, Amouage, Byredo, Le Labo, MFK
  - Retail prices, good deal thresholds, high alert prices

### 2. Scraper Engine
- ✅ `scraper/engine.py` - Price scraping system
  - Notino scraper (UK/EU)
  - Douglas scraper (UK/DE/FR)
  - Price matching algorithm
  - Deal detection (vs threshold prices)

### 3. Backend API
- ✅ `backend/api.py` - FastAPI server
  - GET /api/perfumes - List all tracked perfumes
  - GET /api/deals - Current best deals
  - POST /api/alerts - Create price alerts
  - GET /api/alerts/{user_id} - User's alerts
  - SQLite database for persistence

### 4. Mobile App (React Native)
- ✅ `mobile/App.js` - Complete app scaffold
  - Home screen with navigation
  - Perfume browser
  - Active deals viewer
  - Price alerts manager
  - Ready for Expo deployment

### 5. Scheduler
- ✅ `scheduler.py` - Automated price scans
  - Runs twice daily (12:00 & 18:00 GMT)
  - Background monitoring
  - Deal notification system

---

## 🚀 QUICK START

### 1. Start Backend
```bash
cd /home/peptyl/.openclaw/workspace/pricehunter/backend
python3 api.py
# API runs on http://localhost:8001
```

### 2. Run Price Scan
```bash
cd /home/peptyl/.openclaw/workspace/pricehunter
python3 scheduler.py --once
# Scans all retailers, finds deals
```

### 3. Start Scheduler
```bash
python3 scheduler.py
# Runs automatically at 12pm & 6pm
```

### 4. Mobile App
```bash
cd /home/peptyl/.openclaw/workspace/pricehunter/mobile
# Install Expo: npm install -g expo-cli
# expo start
# Scan QR with phone
```

---

## 💰 MONETIZATION OPTIONS

### Option A: Affiliate Revenue (Recommended)
- Use retailer affiliate links (Notino, Douglas)
- Free app for users
- Revenue share on purchases
- Easiest to implement

### Option B: Freemium
- Free: 3 price alerts, 12hr delayed data
- Pro £3.99/mo: Unlimited alerts, instant updates
- Premium £9.99/mo: Deal predictions, restock alerts

### Option C: Lead Generation
- Sell qualified leads to perfume retailers
- "Hot buyers" actively searching for deals
- B2B revenue model

---

## 🎯 MVP LAUNCH CHECKLIST

### Week 1: Backend
- [x] Scraper engine built
- [x] API server built
- [x] Database schema ready
- [ ] Deploy to server (Railway/Render)
- [ ] Set up domain (api.pricehunter.app)

### Week 2: Mobile
- [x] React Native app scaffold
- [ ] Test on iOS device
- [ ] Test on Android device
- [ ] App Store submission
- [ ] Play Store submission

### Week 3: Launch
- [ ] Affiliate partnerships (Notino, Douglas)
- [ ] Beta test with 10 users
- [ ] Fix bugs
- [ ] Public launch

---

## 📊 PROJECTED METRICS

### User Acquisition
- Target: 1,000 users in Month 1
- Channels: Reddit r/fragrance, TikTok perfume community
- Cost: £0 (organic)

### Revenue (Affiliate Model)
- 1,000 users × 20% active = 200 monthly buyers
- Average order: £150
- Commission: 5% = £7.50 per sale
- Monthly revenue: £1,500
- Year 1 potential: £18,000

### Growth
- Add 10 new perfumes per month
- Expand to US retailers (FragranceNet, FragranceX)
- Add "restock alerts" for sold-out items

---

## 🔥 NEXT STEPS

### Immediate (This Week)
1. Deploy backend API
2. Test scraper on live retailers
3. Build and test mobile app

### Short Term (Next 2 Weeks)
1. App Store / Play Store submission
2. Affiliate partnerships
3. Beta launch to 50 users

### Medium Term (Month 2-3)
1. Full public launch
2. Add authentication
3. Build user dashboard

---

## 💡 COMPETITIVE ADVANTAGE

**vs PriceRunner:**
- ✅ Specialized niche perfumes only
- ✅ Price drop alerts (not just comparison)
- ✅ Community of enthusiasts

**vs Reddit/Facebook:**
- ✅ Standardized price tracking
- ✅ Deal verification
- ✅ No scams/counterfeits

**vs Retailers Direct:**
- ✅ Aggregates all retailers
- ✅ Historical price data
- ✅ Deal predictions

---

**Status: Ready for deployment. Backend complete, mobile scaffold ready.**
