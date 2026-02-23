# PriceHunter Build Plan — 100K Downloads Target

## Mission
Build a world-class fragrance price tracking app with exceptional UI/UX that achieves 100,000 downloads in Year 1.

## Agent Team Assignment

### MOUSE (Mobile Specialist) — LEAD
**Current Role:** Mobile app development
**Skills:** React Native, iOS/Android, Expo
**Task:** Lead mobile development, app architecture

### New Agent: VISION (UI/UX Specialist) — TO BE CREATED
**Role:** UI/UX design, user research, conversion optimization
**Skills:** Figma, user psychology, A/B testing, app store optimization
**Mission:** Design addictive UX that drives 100k downloads

### TANK (Backend) — SUPPORT
**Current Role:** Backend systems
**Skills:** Python, FastAPI, databases
**Task:** API optimization, scraper integration with Scrapling

### TRINITY (Content/Growth) — MARKETING
**Current Role:** Content creation
**Skills:** Marketing copy, viral content, community building
**Task:** App store optimization, launch campaign, user acquisition

---

## 100K Download Strategy

### Phase 1: Product-Market Fit (Month 1-2)
- **Target:** 1,000 beta users
- **Tactics:**
  - Reddit r/fragrance community seeding
  - Fragrantica forum partnerships
  - 50 influencer outreach (perfume YouTubers)
  - "First 1,000 get lifetime Pro" campaign

### Phase 2: Viral Growth (Month 3-6)
- **Target:** 25,000 downloads
- **Tactics:**
  - TikTok perfume deal alerts (viral format)
  - "Deal of the day" notifications
  - Referral: £5 credit for each friend
  - ASO (App Store Optimization) — top 10 "perfume" keyword

### Phase 3: Scale (Month 7-12)
- **Target:** 100,000 downloads
- **Tactics:**
  - US expansion (FragranceNet, FragranceX)
  - Paid UA: £0.50 CPI target
  - Partnerships: Retailer affiliate programs
  - Feature in App Store "Apps We Love"

---

## UI/UX Requirements (VISION Agent Scope)

### Core UX Principles
1. **Instant Gratification:** Show deals within 3 seconds of opening
2. **FOMO Mechanics:** "24 deals expiring today" counters
3. **Social Proof:** "847 people tracking this perfume"
4. **Swipe Addiction:** Tinder-style swipe to track/skip perfumes
5. **Smart Notifications:** "Your tracked perfume just dropped 30%!"

### Key Screens
1. **Home (Deal Feed)**
   - Card-based layout (like TikTok/Reels)
   - Pull-to-refresh
   - Infinite scroll
   - Filter: By brand, price drop %, retailer

2. **Perfume Detail**
   - Price history graph (30/90/365 days)
   - "Best deal" badge
   - "Track" button with target price input
   - Similar perfumes carousel
   - Reviews from community

3. **Tracker/Alerts**
   - List view of tracked items
   - Target price progress bars
   - Price drop notifications
   - "Almost there" animations

4. **Search/Discovery**
   - Visual search (upload perfume bottle photo)
   - Trending perfumes
   - "Deals under £50" quick filters
   - Brand alphabet index

5. **Profile/Gamification**
   - Money saved tracker ("You've saved £247!")
   - Achievement badges ("Deal Hunter", "Nose Expert")
   - Referral progress
   - Settings & notifications

### Design System
- **Colors:** Luxury black/gold palette (Creed, Tom Ford vibes)
- **Typography:** Elegant serif for headers, clean sans-serif for body
- **Icons:** Custom perfume bottle icons
- **Animations:** Smooth price drop animations, confetti on deal found
- **Dark Mode:** Essential (default for luxury feel)

---

## Technical Stack (Updated with Scrapling)

### Backend
- **API:** FastAPI (already built)
- **Database:** PostgreSQL (migrations from SQLite)
- **Scraping:** Scrapling (anti-bot, adaptive)
  - Notino, Douglas, FragranceNet, FragranceX
  - Real-time price monitoring
- **Scheduler:** Celery + Redis (2x daily scans)
- **Hosting:** Railway/Render

### Mobile
- **Framework:** React Native (Expo)
- **Navigation:** React Navigation v6
- **State:** Redux Toolkit + RTK Query
- **UI:** React Native Paper + Custom components
- **Charts:** react-native-chart-kit
- **Notifications:** Expo Notifications
- **Analytics:** Firebase Analytics + Mixpanel

### Scrapling Integration
```python
from scrapling.fetchers import StealthyFetcher

fetcher = StealthyFetcher(adaptive=True)

# Scrape retailer with anti-bot protection
page = fetcher.fetch('https://www.notino.co.uk')
price = page.css('.price').text
currency = page.css('.currency').text
```

---

## Development Phases

### Week 1: Foundation
- [ ] VISION agent: Design system + wireframes
- [ ] MOUSE: React Native setup, navigation
- [ ] TANK: PostgreSQL migration, Scrapling integration

### Week 2: Core Features
- [ ] Deal feed with card UI
- [ ] Search + filter
- [ ] Price tracking (backend)
- [ ] Push notifications

### Week 3: Polish
- [ ] Animations + micro-interactions
- [ ] Dark mode
- [ ] Onboarding flow
- [ ] Analytics integration

### Week 4: Launch Prep
- [ ] App Store submission
- [ ] Play Store submission
- [ ] Landing page
- [ ] Beta testing (50 users)

### Week 5: Launch
- [ ] Reddit/Fragrantica announcement
- [ ] Influencer outreach
- [ ] Paid UA testing
- [ ] Monitor + iterate

---

## Success Metrics

| Metric | Month 1 | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|---------|----------|
| Downloads | 1,000 | 10,000 | 25,000 | 100,000 |
| DAU | 200 | 2,000 | 5,000 | 20,000 |
| Retention (D7) | 20% | 25% | 30% | 35% |
| Deal Alerts Sent | 5,000 | 50,000 | 150,000 | 500,000 |
| Revenue (affiliate) | £500 | £2,500 | £7,500 | £30,000 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Retailers block scraping | Scrapling anti-bot + rotating proxies |
| Low initial downloads | Heavy Reddit/fragrance community seeding |
| Poor retention | Gamification + push notification optimization |
| Competition | First-mover advantage, community building |

---

**Next Step:** Create VISION agent (UI/UX specialist) and begin Week 1 sprint.
