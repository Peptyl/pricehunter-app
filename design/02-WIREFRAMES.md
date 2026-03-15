# Olfex Wireframes
## Version 1.0 — 5 Key Screens

---

## 1. Home / Deal Feed
**Purpose:** Instant deal discovery with addictive swipe interaction
**Engagement Goal:** 3+ swipes per session

### Layout Structure

```
┌─────────────────────────────────────┐
│ STATUS BAR (time, battery, wifi)    │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ 🔍 Search perfumes...        ⚙️ │ │  ← Header (56px)
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ [Quick Filters: All | -50%+ | New]  │  ← Filter Pills (48px)
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐  │
│  │                               │  │
│  │     [PERFUME IMAGE]           │  │  ← Card (65% of screen)
│  │     375x420px                 │  │
│  │                               │  │
│  │     ┌──────┐                  │  │
│  │     │ -30% │ ← Badge          │  │
│  │     └──────┘                  │  │
│  │                               │  │
│  │  Gradient overlay             │  │
│  └───────────────────────────────┘  │
│                                     │
│  TOM FORD                    ⏱️ 4h  │
│  Oud Wood EDP                 left  │
│  👥 1,247 tracking                  │
│                                     │
│  £89.99 ~~£129.00~~          [♡]    │  ← Price + Track
│                                     │
│  ┌───────────────────────────────┐  │
│  │  [Similar: Tuscan Leather]    │  │
│  └───────────────────────────────┘  │
│                                     │
├─────────────────────────────────────┤
│     [← SWIPE]        [SWIPE →]      │
│       Skip            Track         │  ← Hint (32px)
├─────────────────────────────────────┤
│  🏠      🔍      🔔      👤         │  ← Tab Bar (64px)
│ Home   Search   Alerts  Profile     │
└─────────────────────────────────────┘
```

### Component Specifications

#### Deal Card (Swipeable)
```
Dimensions: 375px × 420px (portrait)
Border Radius: 24px
Background: #1A1A1A
Shadow: 0 8px 32px rgba(0,0,0,0.4)

Image Area: 100% × 65%
  - Object Fit: Cover
  - Gradient Overlay: linear-gradient(to top, #1A1A1A 0%, transparent 40%)

Content Area: 100% × 35%
  Padding: 20px
  
  Brand: Playfair Display, 14px, #A0A0A0, uppercase
  Name: Inter, 22px, #E8E8E8, 600 weight
  Tracking Badge: 12px, #FF9800
  
  Price Row:
    - Current: JetBrains Mono, 32px, #D4AF37, 700
    - Original: JetBrains Mono, 18px, #666, strikethrough
    - Track Button: 44px circle, gold outline
```

#### Empty State (No More Cards)
```
Center Content:
  Icon: 🎯 (64px, #D4AF37)
  Title: "All caught up!" (24px, #E8E8E8)
  Subtitle: "We'll notify you of new deals" (14px, #A0A0A0)
  Button: "Browse All Deals" (Primary CTA)
```

### Interactions

| Gesture | Action | Animation |
|---------|--------|-----------|
| Swipe Left | Skip deal | Card exits left, next card scales up |
| Swipe Right | Track deal | Card exits right, heart fills gold |
| Tap Card | View detail | Card expands to full screen |
| Pull Down | Refresh | Gold spinner, new deals load |
| Long Press | Quick peek | Card lifts, shows price history |

### Edge Cases

**No Internet:**
- Grey placeholder cards
- "You're offline" banner at top
- Cached deals still swipeable

**No Deals Available:**
- Empty state illustration
- "Set alerts for your favorites" CTA
- Trending search suggestions

**First Time User:**
- Overlay tutorial on first card
- "Swipe right to track" hint
- Highlight key UI elements

---

## 2. Perfume Detail
**Purpose:** Deep dive with price history and tracking setup
**Engagement Goal:** 40% add to tracker rate

### Layout Structure

```
┌─────────────────────────────────────┐
│ ← Back                      [♡] [↗] │  ← Nav (56px)
├─────────────────────────────────────┤
│                                     │
│     [PERFUME IMAGE GALLERY]         │
│     375px × 400px                   │
│                                     │
│     • ○ ○  ← Pagination dots        │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  CREED                              │
│  Aventus                            │
│  Eau de Parfum • 100ml              │
│  ⭐ 4.8 (2,847 reviews)             │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  💰 BEST DEAL                       │
│  £189.99                           │
│  Notino • Free delivery    [→]      │
│  ~~£295.00~~ You save £105!         │
│                                     │
│  ┌───────────────────────────────┐  │
│  │     [TRACK THIS DEAL]         │  │
│  │     Set your target price     │  │
│  └───────────────────────────────┘  │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  📈 PRICE HISTORY (90 days)         │
│                                     │
│     ╭─────────────────────╮         │
│    £│    ╱╲               │         │
│   250│   ╱  ╲    ╱╲       │         │
│     │  ╱    ╲  ╱  ╲      │         │
│   150│ ╱      ╲╱    ╲____│         │
│     ╰─────────────────────╯         │
│       Jan  Feb  Mar  Apr            │
│                                     │
│  Lowest: £175 (Feb 14)              │
│  Highest: £295 (Jan 3)              │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  🎯 SIMILAR DEALS                   │
│  ┌────────┐ ┌────────┐ ┌────────┐  │
│  │Img     │ │Img     │ │Img     │  │
│  │Green.. │ │Viking  │ │Spice.. │  │
│  │£165    │ │£142    │ │£89     │  │
│  └────────┘ └────────┘ └────────┘  │
│                                     │
└─────────────────────────────────────┘
```

### Component Specifications

#### Price History Chart
```
Height: 180px
Background: transparent
Grid: Horizontal lines, #2D2D2D

Line:
  - Color: #D4AF37
  - Width: 3px
  - Fill: Gradient below line (gold to transparent)
  
Points:
  - Current: 8px circle, gold fill
  - Lowest: Green diamond marker
  - Hover: Tooltip with exact price
  
Y-Axis: JetBrains Mono, 12px, #A0A0A0
X-Axis: Month abbreviations, 11px, #666
```

#### Deal Comparison Table
```
Retailer Row (72px):
  - Logo: 40px × 24px
  - Name: 14px, #E8E8E8
  - Price: 16px, #D4AF37, 600
  - Delivery: 12px, #4CAF50
  - CTA: "Shop →" button
```

#### Track Modal (Bottom Sheet)
```
Height: 400px (70% screen)
Background: #1A1A1A
Border Radius: 24px (top corners)

Content:
  - Handle bar at top (indicates draggable)
  - "Set your target price" header
  - Current price display (large)
  - Price slider (£50 - £300)
  - Quick select buttons:
    • -10% from current
    • -20% from current  
    • -30% from current
  - Notification preferences
  - "Start Tracking" CTA
```

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Image | Swipe left/right | Next/prev image |
| Track Button | Tap | Bottom sheet opens |
| Price Slider | Drag | Updates target, shows % off |
| Retailer Row | Tap | Opens browser to purchase |
| Share Icon | Tap | Native share sheet |
| Heart | Tap | Add/remove from favorites |

### Edge Cases

**No Price History:**
- "Just added!" badge
- "Be the first to track" messaging
- Predicted price range based on similar items

**Multiple Sizes:**
- Size selector tabs (30ml | 50ml | 100ml)
- Prices update with selection
- "Best value" badge on optimal size

**Out of Stock:**
- Greyed out image
- "Notify when back" CTA
- Estimated restock date if available

---

## 3. Tracker / Alerts
**Purpose:** Manage tracked items and celebrate savings
**Engagement Goal:** Daily check-ins, 50% notification CTR

### Layout Structure

```
┌─────────────────────────────────────┐
│ ← Back         My Tracker           │  ← Nav (56px)
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐  │
│  │  💰 TOTAL SAVED               │  │
│  │                               │  │
│  │     £247.50                   │  │
│  │     ━━━━━━                    │  │
│  │     🏆 Deal Hunter Pro        │  │
│  └───────────────────────────────┘  │
│                                     │
│  [Active ▼] [Price ↓] [Filter]      │  ← Sort/Filter
│                                     │
│  ┌───────────────────────────────┐  │
│  │ [Img]                         │  │
│  │ CREED                    🔔   │  │
│  │ Aventus                 🔴    │  │
│  │                               │  │
│  │ Target: £150         Current: │  │
│  │ ████████████░░░░░░░  £189.99  │  │
│  │ 75% to target!                │  │
│  │ Notino • Expires in 2 days    │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ [Img]  TOM FORD               │  │
│  │        Oud Wood          🎉   │  │
│  │                               │  │
│  │ TARGET HIT! £89.99            │  │
│  │ ✓ You saved £40!              │  │
│  │ [Shop Now] [Dismiss]          │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ [Img]  BYREDO                 │  │
│  │        Bal d'Afrique          │  │
│  │                               │  │
│  │ Waiting for deals...          │  │
│  │ 🔔 Notify when under £120     │  │
│  │ Last price: £145 (3 days ago) │  │
│  └───────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

### Component Specifications

#### Savings Hero Card
```
Height: 160px
Background: Gradient gold (subtle)
Border: 1px solid #D4AF37
Border Radius: 20px
Padding: 24px

Content:
  - Label: "TOTAL SAVED" (12px, uppercase, #D4AF37)
  - Amount: JetBrains Mono, 48px, #D4AF37, 700
  - Progress line: 80px wide, 2px, gold
  - Badge: Current achievement level
```

#### Tracked Item Card (Active)
```
Height: 140px
Background: #1A1A1A
Border Radius: 16px
Padding: 16px

States:
  - Default: #1A1A1A
  - Alert (price drop): Gold border pulse
  - Target hit: Green gradient background

Progress Bar:
  - Height: 8px
  - Background: #2D2D2D
  - Fill: #4CAF50 (current to target)
  - Label: "75% to target!" (12px, #A0A0A0)
```

#### Tracked Item Card (Hit Target)
```
Background: Linear gradient (success glow)
Border: 1px solid #4CAF50

Content:
  - "TARGET HIT!" badge (gold, uppercase)
  - Final price (large)
  - Savings amount (green, celebratory)
  - Action buttons: Shop / Dismiss
```

### Interactions

| Gesture | Action | Result |
|---------|--------|--------|
| Card Swipe Left | Delete | Confirm dialog, then remove |
| Card Swipe Right | Edit | Open target price editor |
| Tap Card | View | Go to perfume detail |
| Pull Down | Refresh | Sync latest prices |
| Tap Filter | Sort | Dropdown with options |

### Sort Options
1. **Active First** (default) — Items close to target
2. **Price Drop** — Biggest recent drops
3. **Newest Added** — Recently tracked
4. **Target Proximity** — Closest to hitting target
5. **Alphabetical** — A-Z by name

### Empty States

**No Tracked Items:**
- Illustration: Empty perfume bottle
- Title: "Start tracking deals"
- Subtitle: "Swipe right on any perfume to save"
- CTA: "Browse Deals" button

**All Targets Hit:**
- Celebration animation
- "You've cleaned up!" message
- "Find more deals" suggestion

---

## 4. Search / Discovery
**Purpose:** Find perfumes with visual search and trending
**Engagement Goal:** 2+ searches per session

### Layout Structure

```
┌─────────────────────────────────────┐
│ 🔍 Search perfumes...           📷  │  ← Search Bar (56px)
├─────────────────────────────────────┤
│                                     │
│  📸 VISUAL SEARCH                   │
│  Take a photo of any perfume bottle │
│  ┌───────────────────────────────┐  │
│  │                               │  │
│  │     [CAMERA PREVIEW]          │  │
│  │                               │  │
│  │   ┌─────────────────────┐     │  │
│  │   │   Point at bottle   │     │  │
│  │   └─────────────────────┘     │  │
│  │                               │  │
│  └───────────────────────────────┘  │
│                                     │
│  🔥 TRENDING NOW                    │
│  ┌────────┐ ┌────────┐ ┌────────┐  │
│  │Img     │ │Img     │ │Img     │  │
│  │Creed   │ │Le Labo │ │Byredo  │  │
│  │Aventus │ │Santal  │ │Blanche │  │
│  │£189    │ │£165    │ │£142    │  │
│  └────────┘ └────────┘ └────────┘  │
│                                     │
│  💎 LUXURY UNDER £100               │
│  ┌────────┐ ┌────────┐ ┌────────┐  │
│  │Img     │ │Img     │ │Img     │  │
│  │Montblanc│ │Carolina│ │Versace │  │
│  │£89     │ │£75     │ │£65     │  │
│  └────────┘ └────────┘ └────────┘  │
│                                     │
│  📚 BROWSE BY BRAND                 │
│  ┌────┬────┬────┬────┬────┐        │
│  │ A  │ B  │ C  │ D  │ E  │ ...    │
│  └────┴────┴────┴────┴────┘        │
│                                     │
│  [Acqua di Parma] [Amouage] ...     │  ← Brand pills
│                                     │
│  🏷️ QUICK FILTERS                   │
│  [Under £50] [50% off+] [New] [EDP] │
│                                     │
└─────────────────────────────────────┘
```

### Component Specifications

#### Visual Search Camera
```
Height: 200px
Border Radius: 20px
Background: #1A1A1A
Border: 2px dashed #D4AF37 (when active)

Camera Overlay:
  - Corner brackets (gold) for alignment
  - "Point camera at perfume bottle" text
  - Shutter button (80px circle, gold)
  
Result State:
  - Matching products appear in carousel
  - Confidence score per match (%)
  - "Not quite right?" feedback option
```

#### Trending Carousel
```
Card Size: 120px × 160px
Border Radius: 16px
Spacing: 12px between cards

Content:
  - Image: 120px × 120px
  - Brand: 11px, #A0A0A0
  - Name: 13px, #E8E8E8 (truncated)
  - Price: 14px, #D4AF37, 600
```

#### Brand Alphabet Index
```
Button Size: 48px × 48px
Border Radius: 12px
Background: #2D2D2D (default), #D4AF37 (selected)
Text: 16px, #E8E8E8 (default), #0A0A0A (selected)

Scroll Behavior:
  - Horizontal scroll with momentum
  - Selected letter snaps to center
  - Brand list updates below
```

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Search Input | Type | Real-time suggestions appear |
| Camera Button | Tap | Camera view opens |
| Camera Shutter | Tap | Capture, then AI search |
| Trending Card | Tap | Go to perfume detail |
| Brand Letter | Tap | Filter to that letter |
| Quick Filter | Tap | Apply filter, results update |

### Search States

**Typing (Active):**
```
Search Bar expanded
├─ Recent Searches
│  ├─ "Creed Aventus"
│  ├─ "oud perfumes"
│  └─ "under £100"
├─ Suggested
│  ├─ 🔥 Creed Aventus
│  ├─ ✨ Le Labo Santal 33
│  └─ 🆕 Byredo Mojave Ghost
└─ Matching Brands
   ├─ "Cre" → Creed, Cremo, Carolina Herrera
```

**Visual Search Results:**
```
┌─────────────────────────────────────┐
│ 📸 "We found these matches:"        │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ [IMG] Creed Aventus      94%  │  │
│  │ £189.99 - Best Match          │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ [IMG] Creed Green Irish  87%  │  │
│  │ £165.00 - Similar bottle      │  │
│  └───────────────────────────────┘  │
│                                     │
│  [❌ That's not it]                 │
└─────────────────────────────────────┘
```

---

## 5. Profile / Gamification
**Purpose:** Retention through achievements and referrals
**Engagement Goal:** 30% referral rate, daily check-ins

### Layout Structure

```
┌─────────────────────────────────────┐
│ ⚙️ Settings                    [↗] │  ← Nav (56px)
├─────────────────────────────────────┤
│                                     │
│  ┌──────┐                           │
│  │ 👤   │  Sarah Chen               │
│  │      │  Deal Hunter Pro 🏆       │
│  └──────┘  Member since Jan 2026    │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  💰 LIFETIME SAVINGS          │  │
│  │                               │  │
│  │     £1,247                    │  │
│  │                               │  │
│  │  ┌────────┐ ┌────────┐        │  │
│  │  │ Deals  │ │ Tracked│        │  │
│  │  │   23   │ │   12   │        │  │
│  │  └────────┘ └────────┘        │  │
│  └───────────────────────────────┘  │
│                                     │
│  🏆 ACHIEVEMENTS                    │
│  ┌───────────────────────────────┐  │
│  │ 🎯 Deal Hunter     │██████│  │  │
│  │ Track 5 deals      │ 5/5 ✓ │  │  │
│  ├───────────────────────────────┤  │
│  │ 💰 Money Saver     │████░░│  │  │
│  │ Save £100+         │75/100│  │  │
│  ├───────────────────────────────┤  │
│  │ 🔥 Trending        │░░░░░░│  │  │
│  │ Share 3 deals      │0/3   │  │  │
│  └───────────────────────────────┘  │
│                                     │
│  💎 EARN REWARDS                    │
│  ┌───────────────────────────────┐  │
│  │ 👥 Invite Friends             │  │
│  │ Give £5, Get £5               │  │
│  │ 3 of 5 invites sent           │  │
│  │ ████████░░░░░░░ 60%           │  │
│  │ [Share Your Link]             │  │
│  └───────────────────────────────┘  │
│                                     │
│  🔔 NOTIFICATIONS                   │
│  ┌───────────────────────────────┐  │
│  │ Price alerts           [ON]   │  │
│  │ Deal of the day        [ON]   │  │
│  │ Friend activity        [OFF]  │  │
│  └───────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

### Component Specifications

#### Stats Hero Card
```
Height: 140px
Background: Gradient (charcoal to black)
Border: 1px solid #2D2D2D
Border Radius: 20px
Padding: 20px

Content:
  - Label: "LIFETIME SAVINGS" (11px, uppercase, #A0A0A0)
  - Amount: JetBrains Mono, 40px, #D4AF37, 700
  - Divider: 1px #2D2D2D
  - Stats Row: 2 columns, centered
    • Deals Found: Count + label
    • Tracked: Count + label
```

#### Achievement Item
```
Height: 72px
Background: #1A1A1A
Border Radius: 12px
Padding: 16px

Content:
  - Icon: 32px emoji + circle background
  - Title: 14px, #E8E8E8, 600
  - Description: 12px, #A0A0A0
  - Progress: Small bar or checkmark
  
States:
  - Locked: Greyscale icon, progress empty
  - In Progress: Color icon, partial progress
  - Unlocked: Gold border, checkmark, confetti
```

#### Referral Card
```
Height: 120px
Background: Linear gradient (gold subtle)
Border: 1px solid #D4AF37
Border Radius: 16px
Padding: 20px

Content:
  - Icon: 👥 (group)
  - Title: "Invite Friends" (16px, #E8E8E8, 600)
  - Subtitle: "Give £5, Get £5" (14px, #D4AF37)
  - Progress: X of Y invites sent
  - Progress bar: Shows completion %
  - CTA: "Share Your Link" button
```

### Achievement System

| Badge | Name | Requirement | Reward |
|-------|------|-------------|--------|
| 🎯 | Deal Hunter | Track 5 perfumes | Bronze badge |
| 💰 | Money Saver | Save £100 total | Silver badge |
| 🔥 | Trending | Share 3 deals | Gold badge |
| 🏆 | VIP Hunter | Save £500 total | Pro badge + early access |
| 👑 | Master Nose | Track 50 perfumes | Crown badge + referral bonus |
| ⭐ | Early Bird | First 1,000 users | Lifetime Pro |
| 🎁 | Sharer | 5 friends join | £25 credit |
| 💎 | Loyalist | 30-day streak | Exclusive deals |

### Share Sheet
```
When user taps "Share a deal":
┌─────────────────────────────────────┐
│  Share This Deal                    │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ [IMG] Creed Aventus           │  │
│  │ £189.99 (was £295)            │  │
│  │ I saved £105 with Olfex!│  │
│  └───────────────────────────────┘  │
│                                     │
│  [Copy Link] [More Options]         │
│                                     │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│  │📱  │ │💬  │ │📧  │ │𝕏   │       │
│  │SMS │ │WA  │ │Email│ │X   │       │
│  └────┘ └────┘ └────┘ └────┘       │
│                                     │
└─────────────────────────────────────┘
```

### Interactions

| Element | Action | Result |
|---------|--------|--------|
| Achievement | Tap | View details, share unlocked |
| Share Button | Tap | Native share sheet opens |
| Settings | Tap | Navigate to settings |
| Stat Number | Tap | View detailed breakdown |
| Avatar | Tap | Change profile photo |

### Empty/New User State

```
┌─────────────────────────────────────┐
│                                     │
│  ┌───────────────────────────────┐  │
│  │        🎯                     │  │
│  │                               │  │
│  │   Welcome to Olfex!     │  │
│  │                               │  │
│  │   Start tracking deals to     │  │
│  │   unlock achievements         │  │
│  │                               │  │
│  │   [Browse Deals]              │  │
│  │                               │  │
│  └───────────────────────────────┘  │
│                                     │
│  🏆 Locked Achievements (5)         │
│  ┌───────────────────────────────┐  │
│  │ 🔒 Deal Hunter     │░░░░░░│  │  │
│  │ Track 5 deals      │0/5   │  │  │
│  ├───────────────────────────────┤  │
│  │ 🔒 Money Saver     │░░░░░░│  │  │
│  │ Save £100+         │0/100 │  │  │
│  └───────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

---

## Wireframe Summary

| Screen | Primary Goal | Key Metric |
|--------|--------------|------------|
| Home/Feed | Deal discovery | 3+ swipes/session |
| Detail | Conversion to tracker | 40% track rate |
| Tracker | Retention | Daily check-ins |
| Search | Catalog exploration | 2+ searches/session |
| Profile | Referrals & retention | 30% referral rate |

---

*Version 1.0 | VISION Agent | Olfex Wireframes*
