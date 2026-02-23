# PriceHunter Launch Checklist

**Goal:** Submit to App Store and Play Store within 48 hours

## Phase 1: Critical Integration (Hours 0-24) ✅ TRINITY Done

- [x] Privacy Policy — `legal/privacy-policy.md`
- [x] Terms of Service — `legal/terms-of-service.md`
- [x] App Store Description — `store/app-store-description.txt`
- [x] Short Subtitle — `store/short-subtitle.txt`

## Phase 1: Critical Integration (Hours 0-48) 🔄 IN PROGRESS

### Auth (MOUSE working on)
- [ ] Clerk account created
- [ ] @clerk/clerk-expo installed
- [ ] Email/password login
- [ ] Google Sign-In
- [ ] Apple Sign-In (mandatory for iOS)
- [ ] Auth flow tested

### Payments (MOUSE working on)
- [ ] RevenueCat account created
- [ ] react-native-purchases installed
- [ ] "Pro" offering configured
- [ ] Entitlements set up
- [ ] Test purchase working (sandbox)

### Analytics (MOUSE working on)
- [ ] Firebase project created
- [ ] @react-native-firebase/analytics installed
- [ ] Events tracking: app_open, search, deal_view
- [ ] Conversion funnels configured

## Phase 2: Store Assets (Hours 24-48) 🔄 IN PROGRESS

### Visual Assets (VISION working on)
- [ ] App Icon (1024x1024) — `assets/icon.png`
- [ ] iPhone 14 Pro Max screenshot — `assets/screenshots/iphone-14-pro-max.png`
- [ ] iPhone 14 screenshot — `assets/screenshots/iphone-14.png`
- [ ] iPad Pro screenshot — `assets/screenshots/ipad-pro.png`
- [ ] Pixel 7 Pro screenshot — `assets/screenshots/pixel-7-pro.png`
- [ ] Feature Graphic (1024x500) — `assets/feature-graphic.png`

## Phase 3: Testing (Hours 48-60)

- [ ] End-to-end testing
- [ ] Auth flow tested on device
- [ ] Purchase flow tested (sandbox)
- [ ] Analytics events verified
- [ ] Performance check (< 3s load time)

## Phase 4: Store Submission (Hours 60-72)

### App Store (iOS)
- [ ] Apple Developer account ($99/year)
- [ ] App Store Connect app created
- [ ] App icon uploaded
- [ ] Screenshots uploaded (all sizes)
- [ ] Description + subtitle entered
- [ ] Privacy policy URL linked
- [ ] Build uploaded (TestFlight)
- [ ] Test credentials provided
- [ ] Submitted for review

### Play Store (Android)
- [ ] Google Play Console account ($25 one-time)
- [ ] App listing created
- [ ] App icon uploaded
- [ ] Screenshots uploaded
- [ ] Feature graphic uploaded
- [ ] Description entered
- [ ] Privacy policy URL linked
- [ ] Content rating completed
- [ ] Build uploaded (Internal Testing)
- [ ] Submitted for review

## Post-Launch (Ongoing)

- [ ] Monitor crash reports
- [ ] Track analytics daily
- [ ] Respond to reviews
- [ ] Iterate based on feedback

## Accounts Needed

| Service | URL | Cost | Status |
|---------|-----|------|--------|
| Clerk | https://clerk.dev | Free (10K users) | ⏳ Waiting for CEO |
| RevenueCat | https://revenuecat.com | Free ($2.5K MRR) | ⏳ Waiting for CEO |
| Firebase | https://firebase.google.com | Free (Spark) | ⏳ Waiting for CEO |
| Apple Developer | https://developer.apple.com | $99/year | ⏳ Waiting for CEO |
| Google Play Console | https://play.google.com/console | $25 one-time | ⏳ Waiting for CEO |

## Status

**Current Phase:** Phase 1 (Critical Integration)  
**Completed:** Legal docs, app store copy  
**In Progress:** Auth, payments, analytics, visual assets  
**Blockers:** Waiting for CEO to create accounts (Clerk, RevenueCat, Firebase, Apple, Google)

---

**Last Updated:** 2026-02-23 22:00  
**Next Update:** When MOUSE and VISION complete (ETA: 6-12 hours)
