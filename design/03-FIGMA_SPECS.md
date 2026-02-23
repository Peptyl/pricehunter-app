# PriceHunter Figma-Ready Specifications
## Complete Design Specs for Development Handoff

---

## 📐 Layout Specifications

### Screen Dimensions

| Device | Width | Height | Safe Area Top | Safe Area Bottom | Scale |
|--------|-------|--------|---------------|------------------|-------|
| iPhone SE | 375px | 667px | 20px | 20px | 1x |
| iPhone 14 | 390px | 844px | 47px | 34px | 1x |
| iPhone 14 Pro Max | 428px | 926px | 47px | 34px | 1x |
| Android (compact) | 360px | 760px | 24px | 48px | 1x |
| Android (large) | 412px | 915px | 24px | 48px | 1x |

### Grid System
```
Base Grid: 8px
Columns: 4 (mobile)
Gutter: 16px
Margin: 16px (20px on Plus devices)

Visual:
┌─────────────────────────────┐
│ M |   C1   |   C2   |   C3   |   C4   | M │
│ 16│  80px  │  80px  │  80px  │  80px  │ 16│
└─────────────────────────────┘
```

### Spacing Scale (8px Base)

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Micro gaps, icon padding |
| `space-2` | 8px | Tight spacing, inline elements |
| `space-3` | 12px | Small gaps, card internal |
| `space-4` | 16px | Default padding, section gaps |
| `space-5` | 20px | Card padding, comfortable spacing |
| `space-6` | 24px | Section separation |
| `space-8` | 32px | Large sections, hero spacing |
| `space-10` | 40px | Major section breaks |
| `space-12` | 48px | Screen padding, major gaps |
| `space-16` | 64px | Hero elements, large CTAs |

---

## 🎨 Color Specifications

### CSS Variables

```css
:root {
  /* Primary Palette */
  --color-black: #0A0A0A;
  --color-gold: #D4AF37;
  --color-gold-light: #F4E4BC;
  --color-gold-dark: #B8941F;
  
  /* Secondary Palette */
  --color-charcoal: #1A1A1A;
  --color-graphite: #2D2D2D;
  --color-silver: #A0A0A0;
  --color-platinum: #E8E8E8;
  
  /* Semantic Colors */
  --color-success: #4CAF50;
  --color-success-light: rgba(76, 175, 80, 0.15);
  --color-warning: #FF9800;
  --color-warning-light: rgba(255, 152, 0, 0.1);
  --color-danger: #F44336;
  --color-danger-light: rgba(244, 67, 54, 0.15);
  --color-info: #2196F3;
  
  /* Opacity Variants */
  --color-white-5: rgba(255, 255, 255, 0.05);
  --color-white-10: rgba(255, 255, 255, 0.1);
  --color-white-50: rgba(255, 255, 255, 0.5);
  --color-black-50: rgba(0, 0, 0, 0.5);
}
```

### Figma Variables Setup

```
Collection: PriceHunter Colors
Mode: Dark (default)

Primitives:
├── black: #0A0A0A
├── gold: #D4AF37
├── gold-light: #F4E4BC
├── gold-dark: #B8941F
├── charcoal: #1A1A1A
├── graphite: #2D2D2D
├── silver: #A0A0A0
├── platinum: #E8E8E8
├── success: #4CAF50
├── warning: #FF9800
├── danger: #F44336
└── info: #2196F3

Semantic:
├── background-primary: $black
├── background-secondary: $charcoal
├── background-elevated: $graphite
├── text-primary: $platinum
├── text-secondary: $silver
├── accent-primary: $gold
├── accent-hover: $gold-light
├── accent-active: $gold-dark
├── status-success: $success
├── status-warning: $warning
└── status-danger: $danger
```

---

## ✍️ Typography Specifications

### Font Stack

```css
/* Display - Luxury feel */
--font-display: 'Playfair Display', Georgia, 'Times New Roman', serif;

/* Body - Clean readability */
--font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Numbers - Monospace for alignment */
--font-mono: 'JetBrains Mono', 'SF Mono', Monaco, 'Cascadia Code', monospace;
```

### Google Fonts Import
```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Figma Text Styles

| Style Name | Font | Size | Weight | Line Height | Letter Spacing |
|------------|------|------|--------|-------------|----------------|
| Hero/Display | Playfair Display | 48px | 700 | 52px | -0.96px |
| H1/Screen Title | Playfair Display | 32px | 700 | 38px | -0.32px |
| H2/Section | Playfair Display | 24px | 600 | 31px | 0 |
| H3/Card Title | Inter | 20px | 600 | 28px | 0 |
| H4/Subtitle | Inter | 18px | 500 | 25px | 0.18px |
| Body Large | Inter | 16px | 400 | 26px | 0 |
| Body | Inter | 14px | 400 | 21px | 0 |
| Small/Label | Inter | 12px | 500 | 17px | 0.24px |
| Micro/Caption | Inter | 10px | 600 | 13px | 0.3px |
| Price Large | JetBrains Mono | 28px | 700 | 28px | 0 |
| Price | JetBrains Mono | 18px | 600 | 18px | 0 |
| Price Strikethrough | JetBrains Mono | 14px | 400 | 14px | 0 |

---

## 🧩 Component Specifications

### Button Component

#### Primary Button (CTA)
```
Height: 56px
Min Width: 120px
Max Width: 100%
Padding: 0 32px
Border Radius: 28px

Background:
  Default: #D4AF37
  Pressed: #B8941F
  Disabled: #2D2D2D
  Loading: Animated shimmer

Text:
  Font: Inter
  Size: 16px
  Weight: 600
  Color: #0A0A0A
  
Shadow:
  Default: 0 4px 20px rgba(212, 175, 55, 0.3)
  Pressed: 0 2px 10px rgba(212, 175, 55, 0.2)
  Disabled: none

Icon (optional):
  Size: 20px
  Position: left of text, 8px gap

Animation:
  Press: scale(0.98), 100ms ease-out
  Release: scale(1), 200ms ease-out
```

#### Secondary Button (Outline)
```
Height: 48px
Padding: 0 24px
Border Radius: 24px
Border: 2px solid #D4AF37
Background: transparent

Text:
  Font: Inter
  Size: 14px
  Weight: 600
  Color: #D4AF37

States:
  Default: transparent bg, gold border
  Pressed: rgba(212, 175, 55, 0.1) bg
  Disabled: #2D2D2D border, #666 text
```

#### Icon Button (Ghost)
```
Size: 44px × 44px
Border Radius: 22px
Background: rgba(255, 255, 255, 0.05)
Icon: 24px, #E8E8E8

States:
  Default: rgba(255, 255, 255, 0.05)
  Pressed: rgba(255, 255, 255, 0.1)
  Active: #D4AF37 bg, #0A0A0A icon

Animation:
  Tap: scale(0.9), 100ms
```

### Card Component

#### Deal Card (Home Feed)
```
Width: 100% (343px on 390px screen)
Height: 420px
Border Radius: 24px
Background: #1A1A1A
Overflow: hidden
Shadow: 0 8px 32px rgba(0, 0, 0, 0.4)

Image Section: 273px height (65%)
  - Object Fit: cover
  - Gradient Overlay: linear-gradient(to top, #1A1A1A 0%, transparent 40%)
  
Content Section: 147px height (35%)
  Padding: 20px
  
  Brand Label:
    Font: Playfair Display, 14px, #A0A0A0, uppercase, 500 weight
    Letter Spacing: 1px
    Margin Bottom: 4px
  
  Perfume Name:
    Font: Inter, 22px, #E8E8E8, 600 weight
    Line Height: 28px
    Max Lines: 2
    Ellipsis: tail
  
  Tracking Badge:
    Margin Top: 8px
    Icon: 👥 (16px)
    Text: "1,247 tracking" (12px, #FF9800, 600)
  
  Price Row:
    Margin Top: 12px
    Flex: space-between, center
    
    Current Price:
      Font: JetBrains Mono, 32px, #D4AF37, 700
    
    Original Price:
      Font: JetBrains Mono, 18px, #666, 400
      Text Decoration: line-through
      Margin LEFT: 12px
    
    Track Button:
      Size: 44px circle
      Border: 2px solid #D4AF37
      Icon: Heart (24px, #D4AF37)
      Background: transparent
      
      Active State:
        Background: #D4AF37
        Icon: Heart fill (#0A0A0A)
```

#### Compact Card (Tracker List)
```
Height: 80px
Border Radius: 16px
Background: #1A1A1A
Padding: 16px
Flex: row, center, 12px gap

Thumbnail:
  Size: 48px × 48px
  Border Radius: 8px
  Object Fit: cover

Content:
  Flex: 1
  
  Brand: 12px, #A0A0A0, uppercase
  Name: 14px, #E8E8E8, 500, truncate
  
Progress Section:
  Width: 120px
  
  Progress Bar:
    Height: 6px
    Border Radius: 3px
    Background: #2D2D2D
    Fill: #4CAF50
    
  Label: 11px, #A0A0A0, "75% to target"
```

### Input Component

#### Search Input
```
Height: 48px
Border Radius: 12px
Background: #1A1A1A
Border: 1px solid #2D2D2D
Padding: 0 16px 0 44px (for icon)

Search Icon:
  Position: absolute left 16px
  Size: 20px
  Color: #A0A0A0

Text:
  Font: Inter, 16px, #E8E8E8
  Placeholder: #666

Clear Button (when text present):
  Position: absolute right 12px
  Size: 20px circle
  Background: #2D2D2D
  Icon: X (12px, #A0A0A0)

Focus State:
  Border: 1px solid #D4AF37
  Shadow: 0 0 0 3px rgba(212, 175, 55, 0.1)
```

#### Price Target Slider
```
Track:
  Height: 8px
  Border Radius: 4px
  Background: #2D2D2D
  
Fill:
  Height: 8px
  Border Radius: 4px
  Background: #D4AF37

Thumb:
  Size: 24px circle
  Background: linear-gradient(135deg, #D4AF37, #F4E4BC)
  Border: 2px solid #0A0A0A
  Shadow: 0 2px 8px rgba(0, 0, 0, 0.3)
  
Value Tooltip:
  Position: above thumb
  Background: #1A1A1A
  Border: 1px solid #D4AF37
  Border Radius: 8px
  Padding: 8px 12px
  Text: "Target: £150" (14px, #D4AF37)
```

### Badge Component

#### Discount Badge
```
Height: 28px
Padding: 0 12px
Border Radius: 8px
Background: #4CAF50

Text: "-30%" (13px, #0A0A0A, 700)
Position: absolute top 16px, left 16px
```

#### Tracking Badge
```
Height: 28px
Padding: 0 12px
Border Radius: 8px
Background: rgba(244, 67, 54, 0.15)
Border: 1px solid #F44336

Icon: 👥 (14px)
Text: "847" (13px, #F44336, 600)
Gap: 4px
```

#### Urgency Countdown
```
Height: 32px
Padding: 0 12px
Border Radius: 8px
Background: rgba(255, 152, 0, 0.1)
Border: 1px solid #FF9800

Icon: ⏱️ (14px)
Time: "04:23:17" (14px, #FF9800, JetBrains Mono, 600)
Gap: 6px

Animation: Icon pulse 1.5s infinite
```

---

## 📱 Screen Specifications

### Navigation Bar
```
Height: 56px (including safe area)
Background: #0A0A0A
Border Bottom: 1px solid #1A1A1A
Padding Horizontal: 16px

Left Icon (Back): 44px tap target
Center Title: 20px, #E8E8E8, 600
Right Icons: 44px each, max 2
```

### Tab Bar
```
Height: 64px (including safe area bottom)
Background: #0A0A0A
Border Top: 1px solid #1A1A1A

Tab Item:
  Flex: 1
  Height: 48px (above safe area)
  
  Icon: 24px
    Inactive: #A0A0A0
    Active: #D4AF37
    
  Label: 11px
    Inactive: #A0A0A0
    Active: #D4AF37
    
  Active Indicator (optional):
    Top border: 2px solid #D4AF37
```

### Home Screen Layout
```
Total Height: 844px (iPhone 14)
Safe Area Top: 47px
Safe Area Bottom: 34px

Structure:
┌─────────────────────────────┐ ← 0px
│ Status Bar                  │ ← 47px
├─────────────────────────────┤
│ Search Header      (56px)   │ ← 103px
├─────────────────────────────┤
│ Filter Pills       (48px)   │ ← 151px
├─────────────────────────────┤
│                             │
│ Deal Card          (420px)  │ ← Centered
│                             │
├─────────────────────────────┤
│ Swipe Hint         (32px)   │
├─────────────────────────────┤
│                             │
│ Tab Bar            (64px)   │ ← 780px
├─────────────────────────────┤
│ Safe Area Bottom   (34px)   │ ← 814px
└─────────────────────────────┘
```

---

## 🎬 Animation Specifications

### Swipe Card Animation
```javascript
// Swipe Right (Track)
{
  trigger: "swipeRight",
  duration: 300,
  easing: "cubic-bezier(0.4, 0, 0.2, 1)",
  properties: {
    translateX: "+120%",
    rotate: "+15deg",
    scale: 1.05,
    opacity: 0
  },
  backgroundFlash: {
    color: "rgba(76, 175, 80, 0.2)",
    duration: 200
  }
}

// Next Card
{
  trigger: "cardExit",
  delay: 100,
  duration: 300,
  properties: {
    scale: [0.95, 1],
    translateY: [20, 0],
    opacity: [0.8, 1]
  }
}
```

### Price Counter Animation
```javascript
// Number counting animation
{
  trigger: "priceUpdate",
  duration: 800,
  easing: "ease-out",
  properties: {
    // Count from oldValue to newValue
  },
  celebration: {
    confetti: {
      particleCount: 50,
      spread: 60,
      origin: { y: 0.6 },
      colors: ['#D4AF37', '#F4E4BC', '#4CAF50']
    },
    duration: 600
  }
}
```

### Pull to Refresh
```javascript
{
  trigger: "pullDown",
  threshold: 80,
  properties: {
    spinner: {
      color: "#D4AF37",
      rotation: "continuous during pull",
      speed: "proportional to pull distance"
    }
  },
  release: {
    success: {
      iconMorph: "spinner -> checkmark",
      duration: 300
    }
  }
}
```

### Achievement Unlock
```javascript
{
  trigger: "achievementUnlock",
  sequence: [
    { // 1. Dark overlay
      duration: 200,
      overlay: "rgba(0, 0, 0, 0.8)"
    },
    { // 2. Badge scale in with bounce
      duration: 400,
      easing: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      scale: [0.5, 1.2, 1]
    },
    { // 3. Particle burst
      duration: 600,
      particles: {
        count: 100,
        colors: ["#D4AF37", "#F4E4BC", "#4CAF50"],
        spread: 360
      }
    },
    { // 4. Text type in
      duration: 800,
      textAnimation: "character-by-character",
      delay: 200
    },
    { // 5. Share button slide up
      duration: 300,
      translateY: [50, 0],
      opacity: [0, 1]
    }
  ]
}
```

---

## 🖼️ Asset Specifications

### Icons

| Icon Name | Size | Format | Usage |
|-----------|------|--------|-------|
| logo_mark | 1024×1024 | SVG | App icon, splash |
| logo_wordmark | 400×80 | SVG | Header branding |
| icon_home | 24×24 | SVG | Tab bar |
| icon_search | 24×24 | SVG | Tab bar, input |
| icon_bell | 24×24 | SVG | Tab bar, alerts |
| icon_user | 24×24 | SVG | Tab bar, profile |
| icon_heart | 24×24 | SVG | Track button |
| icon_heart_filled | 24×24 | SVG | Tracked state |
| icon_share | 24×24 | SVG | Share actions |
| icon_camera | 24×24 | SVG | Visual search |
| icon_arrow_right | 20×20 | SVG | Navigation |
| icon_chevron_down | 16×16 | SVG | Dropdowns |
| icon_settings | 24×24 | SVG | Profile |
| icon_fire | 20×20 | SVG | Trending badge |
| icon_clock | 20×20 | SVG | Countdown |
| icon_users | 16×16 | SVG | Tracking count |
| icon_check | 20×20 | SVG | Success states |
| icon_confetti | 48×48 | SVG | Celebrations |

### Illustrations

| Asset | Dimensions | Format | Usage |
|-------|------------|--------|-------|
| empty_state_deals | 200×200 | SVG | No deals found |
| empty_state_tracking | 200×200 | SVG | No tracked items |
| onboarding_1 | 390×500 | PNG | Tutorial swipe |
| onboarding_2 | 390×500 | PNG | Tutorial track |
| onboarding_3 | 390×500 | PNG | Tutorial save |
| achievement_bronze | 80×80 | SVG | Badge asset |
| achievement_silver | 80×80 | SVG | Badge asset |
| achievement_gold | 80×80 | SVG | Badge asset |
| achievement_crown | 80×80 | SVG | Badge asset |

### App Icon

```
Platform: iOS + Android
Shape: Rounded square
Background: #0A0A0A

Design:
  - Gold perfume bottle silhouette
  - "PH" monogram or full bottle
  - Subtle gradient on bottle
  
Sizes:
  - iOS: 1024×1024 (App Store), 180×180 (home), 120×120 (spotlight)
  - Android: 512×512 (Play Store), 192×192 (launcher), 144×144 (xxhdpi)
  
Export:
  - Provide PSD/AI source
  - Export PNGs at all sizes
  - Include dark mode variant
```

---

## 📱 Export Specifications

### Figma Export Settings

```
Screens:
  - Format: PNG
  - Scale: 2x (for retina)
  - Include: "iPhone 14" frame only
  
Components:
  - Format: SVG (icons)
  - Format: PNG @2x (illustrations)
  
Assets:
  - Create "Export" page
  - Organize by category
  - Use consistent naming: category_element_state
  
Example Names:
  - button_primary_default
  - button_primary_pressed
  - card_deal_default
  - icon_heart_outline
  - icon_heart_filled
```

### Naming Convention

```
Format: [category]_[element]_[state]@[scale].[ext]

category:
  - button
  - card
  - icon
  - input
  - badge
  - screen
  - illustration

element:
  - primary, secondary, ghost (buttons)
  - deal, compact, hero (cards)
  - heart, share, search (icons)
  - text, search, slider (inputs)
  - discount, tracking, countdown (badges)

state:
  - default, pressed, disabled, active
  - empty, loading, success, error

scale:
  - @1x, @2x, @3x

Examples:
  - button_primary_default@2x.png
  - card_deal_default@2x.png
  - icon_heart_filled@3x.png
  - input_search_focus@2x.png
```

---

*Version 1.0 | VISION Agent | Figma Specifications for PriceHunter*
