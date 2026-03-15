# Olfex Design System
## Version 1.0 — 100K Download Edition

---

## 🎨 Philosophy

Olfex exists at the intersection of **luxury** and **savvy**. Our users love Creed, Le Labo, and Tom Ford—but hate paying full price. The design must feel like a premium shopping experience while delivering dopamine hits through deal discovery.

### Core Principles
1. **Instant Luxury** — Dark mode first, gold accents, premium feel in 3 seconds
2. **Addictive Clarity** — FOMO mechanics that don't feel manipulative
3. **Swipe-able Delight** — Tinder-style interactions for discovery
4. **Celebratory Moments** — Every deal found deserves confetti

---

## 🎨 Color Palette

### Primary Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `color-black` | `#0A0A0A` | rgb(10, 10, 10) | Primary background |
| `color-gold` | `#D4AF37` | rgb(212, 175, 55) | Primary accent, CTAs |
| `color-gold-light` | `#F4E4BC` | rgb(244, 228, 188) | Highlights, hover states |
| `color-gold-dark` | `#B8941F` | rgb(184, 148, 31) | Active states, pressed |

### Secondary Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `color-charcoal` | `#1A1A1A` | rgb(26, 26, 26) | Card backgrounds |
| `color-graphite` | `#2D2D2D` | rgb(45, 45, 45) | Elevated surfaces |
| `color-silver` | `#A0A0A0` | rgb(160, 160, 160) | Secondary text |
| `color-platinum` | `#E8E8E8` | rgb(232, 232, 232) | Primary text on dark |

### Semantic Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `color-success` | `#4CAF50` | rgb(76, 175, 80) | Price drops, savings |
| `color-warning` | `#FF9800` | rgb(255, 152, 0) | Urgency, expiring soon |
| `color-danger` | `#F44336` | rgb(244, 67, 54) | Errors, sold out |
| `color-info` | `#2196F3` | rgb(33, 150, 243) | Tips, new features |

### Gradient Definitions

```css
/* Gold Shimmer - Premium highlights */
gradient-gold-shimmer: linear-gradient(135deg, #D4AF37 0%, #F4E4BC 50%, #D4AF37 100%);

/* Dark Elevation - Card depth */
gradient-dark-elevation: linear-gradient(180deg, #1A1A1A 0%, #0A0A0A 100%);

/* Success Glow - Price drop celebration */
gradient-success-glow: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
```

---

## ✍️ Typography

### Font Families

| Token | Font | Fallback | Usage |
|-------|------|----------|-------|
| `font-display` | Playfair Display | Georgia, serif | Headers, brand moments |
| `font-body` | Inter | -apple-system, sans-serif | Body text, UI |
| `font-mono` | JetBrains Mono | Monaco, monospace | Prices, numbers |

### Type Scale

| Token | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| `text-hero` | 48px | 700 | 1.1 | -0.02em | Onboarding headlines |
| `text-h1` | 32px | 700 | 1.2 | -0.01em | Screen titles |
| `text-h2` | 24px | 600 | 1.3 | 0 | Section headers |
| `text-h3` | 20px | 600 | 1.4 | 0 | Card titles |
| `text-h4` | 18px | 500 | 1.4 | 0.01em | Subsection headers |
| `text-body-large` | 16px | 400 | 1.6 | 0 | Primary body |
| `text-body` | 14px | 400 | 1.5 | 0 | Secondary text |
| `text-small` | 12px | 500 | 1.4 | 0.02em | Labels, captions |
| `text-micro` | 10px | 600 | 1.3 | 0.03em | Badges, timestamps |
| `text-price` | 28px | 700 | 1 | 0 | Current prices |
| `text-price-small` | 18px | 600 | 1 | 0 | Original prices |

### Typography Patterns

```css
/* Section Header - Elegant gold accent */
.section-header {
  font-family: Playfair Display;
  font-size: 24px;
  font-weight: 600;
  color: #E8E8E8;
  letter-spacing: 0.5px;
}

/* Price Display - Mono for alignment */
.price-current {
  font-family: JetBrains Mono;
  font-size: 28px;
  font-weight: 700;
  color: #D4AF37;
}

/* FOMO Text - Urgency styling */
.fomo-text {
  font-family: Inter;
  font-size: 12px;
  font-weight: 600;
  color: #FF9800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
```

---

## 🧩 Component Library

### Buttons

#### Primary Button (Gold)
```
Height: 56px
Border Radius: 28px (pill shape)
Background: #D4AF37
Text: #0A0A0A
Font: Inter 16px 600
Padding: 0 32px
Shadow: 0 4px 20px rgba(212, 175, 55, 0.3)

States:
- Default: #D4AF37
- Pressed: #B8941F
- Disabled: #2D2D2D (text: #666)
- Loading: Shimmer animation
```

#### Secondary Button (Outline)
```
Height: 48px
Border Radius: 24px
Border: 2px solid #D4AF37
Background: transparent
Text: #D4AF37
Font: Inter 14px 600

States:
- Default: transparent
- Pressed: rgba(212, 175, 55, 0.1)
- Disabled: #2D2D2D border, #666 text
```

#### Icon Button (Ghost)
```
Size: 44px
Border Radius: 22px
Background: rgba(255, 255, 255, 0.05)
Icon: 24px, #E8E8E8

States:
- Default: rgba(255, 255, 255, 0.05)
- Pressed: rgba(255, 255, 255, 0.1)
- Active: #D4AF37 background, #0A0A0A icon
```

### Cards

#### Deal Card (Full Bleed)
```
Width: 100%
Height: 420px (portrait images)
Border Radius: 24px
Background: #1A1A1A
Overflow: hidden

Structure:
┌─────────────────────────┐
│  [Image - 65% height]   │
│  Gradient overlay       │
│  "-30%" Badge           │
├─────────────────────────┤
│  Brand Name (silver)    │
│  Perfume Name (white)   │
│  Price + Original       │
│  ┌────┐  [Track Btn]    │
│  │👥847│                 │
│  └────┘                 │
└─────────────────────────┘
```

#### Compact Card (List View)
```
Height: 80px
Border Radius: 16px
Background: #1A1A1A
Padding: 16px

Structure:
┌─────────────────────────┐
│ [Img] Brand             │
│       Name          £XX │
│       Progress bar      │
└─────────────────────────┘
```

### Input Fields

#### Text Input
```
Height: 56px
Border Radius: 12px
Background: #1A1A1A
Border: 1px solid #2D2D2D
Padding: 0 16px
Font: Inter 16px
Text: #E8E8E8
Placeholder: #666

States:
- Default: #2D2D2D border
- Focus: #D4AF37 border, glow shadow
- Error: #F44336 border
- Success: #4CAF50 border
```

#### Price Target Slider
```
Track Height: 8px
Track Radius: 4px
Track: #2D2D2D
Fill: #D4AF37
Thumb: 24px circle, gold gradient
Thumb Shadow: 0 2px 8px rgba(0,0,0,0.3)
Value Display: Float above thumb
```

### Badges & Chips

| Type | Background | Text | Border | Icon |
|------|------------|------|--------|------|
| Discount | #4CAF50 | #0A0A0A | none | -XX% |
| Trending | #F44336 | #FFF | none | 🔥 |
| Tracking | #D4AF37 | #0A0A0A | none | 👥 |
| New | #2196F3 | #FFF | none | ✨ |
| Filter | transparent | #D4AF37 | 1px gold | ✕ |

### Progress Indicators

#### Deal Urgency Bar
```
Height: 4px
Background: #2D2D2D
Fill Gradient: #FF9800 → #F44336
Animation: Pulse when < 2 hours
```

#### Target Price Progress
```
Height: 6px
Border Radius: 3px
Background: #2D2D2D
Fill: #4CAF50
Label: "£45 / £60 target"
```

---

## 🎯 FOMO Components

### Live Counter Badge
```
Background: rgba(244, 67, 54, 0.15)
Border: 1px solid #F44336
Border Radius: 12px
Padding: 6px 12px

Content:
- Icon: 👥 (16px)
- Text: "847 tracking" (12px, #F44336, 600)
- Pulse animation on icon
```

### Countdown Timer
```
Background: rgba(255, 152, 0, 0.1)
Border: 1px solid #FF9800
Border Radius: 8px
Padding: 8px 12px

Content:
- Icon: ⏱️
- Time: "04:23:17" (JetBrains Mono, 14px, #FF9800)
- Label: "Deal ends" (10px, #A0A0A0)
```

### Social Proof Toast
```
Position: Bottom of screen
Animation: Slide up, pause 3s, fade out
Background: #1A1A1A
Border: 1px solid #2D2D2D
Border Radius: 16px
Padding: 12px 20px

Content:
- Avatar: 32px circle
- Text: "Sarah just saved £89 on Creed Aventus"
- Time: "2 min ago"
```

---

## 🎬 Animations & Micro-interactions

### Duration Standards

| Type | Duration | Easing |
|------|----------|--------|
| Instant | 100ms | ease-out |
| Quick | 200ms | ease-out |
| Standard | 300ms | cubic-bezier(0.4, 0, 0.2, 1) |
| Emphasis | 400ms | cubic-bezier(0.0, 0, 0.2, 1) |
| Celebration | 600ms | cubic-bezier(0.34, 1.56, 0.64, 1) |

### Key Animations

#### Swipe Card (Tinder-style)
```
Swipe Left (Skip):
- Card rotates -15°
- Translates X -120%
- Opacity → 0
- Duration: 300ms

Swipe Right (Track):
- Card rotates +15°
- Translates X +120%
- Scale: 1.05
- Background flash: #4CAF50
- Duration: 300ms
```

#### Price Drop Celebration
```
Trigger: Price drops on tracked item
Sequence:
1. Card border flashes gold (200ms)
2. Price number counts up/down (800ms)
3. Confetti burst from price (600ms)
4. "You saved £XX" toast slides in
```

#### Pull to Refresh
```
Pull Threshold: 80px
Animation:
- Gold spinner rotates
- Speed increases with pull distance
- Release: Spinner continues, content fades
- Success: Checkmark morph, content slides down
```

#### Achievement Unlock
```
Sequence:
1. Dark overlay fades in (200ms)
2. Badge scales from 0.5 → 1.2 → 1 (400ms, bounce)
3. Particles burst from badge
4. Text types in character by character
5. "Share" button slides up
```

---

## 📱 Responsive Behavior

### Breakpoints

| Device | Width | Adjustments |
|--------|-------|-------------|
| Phone SE | 375px | Compact cards, smaller hero |
| Phone Standard | 390px | Default specs |
| Phone Plus | 428px | Larger images, more padding |
| Tablet | 768px | 2-column grid |

### Scaling Rules
- Typography scales 1:1 (fixed px)
- Cards maintain aspect ratios
- Touch targets minimum 44x44pt
- Safe areas respected (notch, home indicator)

---

## 🌓 Dark Mode (Default)

Olfex is **dark mode first**. The luxury aesthetic demands it.

### Why Dark Default?
1. Premium feel (Creed/Tom Ford vibes)
2. Battery savings on OLED
3. Fragrance photography pops
4. Gold accents shine

### Light Mode (Optional Future)
If implemented:
- Background: #FAFAFA
- Cards: #FFFFFF
- Text: #1A1A1A
- Accent: #B8941F (darker gold for contrast)

---

## 📋 Design Tokens (JSON)

```json
{
  "colors": {
    "black": "#0A0A0A",
    "gold": "#D4AF37",
    "goldLight": "#F4E4BC",
    "goldDark": "#B8941F",
    "charcoal": "#1A1A1A",
    "graphite": "#2D2D2D",
    "silver": "#A0A0A0",
    "platinum": "#E8E8E8",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "danger": "#F44336",
    "info": "#2196F3"
  },
  "fonts": {
    "display": "Playfair Display",
    "body": "Inter",
    "mono": "JetBrains Mono"
  },
  "spacing": {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "xxl": 48
  },
  "radius": {
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "pill": 999
  },
  "shadows": {
    "sm": "0 2px 8px rgba(0,0,0,0.2)",
    "md": "0 4px 16px rgba(0,0,0,0.3)",
    "lg": "0 8px 32px rgba(0,0,0,0.4)",
    "gold": "0 4px 20px rgba(212,175,55,0.3)"
  }
}
```

---

## 🔗 Figma Setup Instructions

1. **Create Variables:**
   - Import color tokens as Figma variables
   - Set up dark mode variable modes
   - Create spacing tokens

2. **Typography Styles:**
   - Import Playfair Display, Inter, JetBrains Mono
   - Create text styles matching token names
   - Set up responsive type scales

3. **Component Library:**
   - Build atoms (buttons, inputs, badges)
   - Compose molecules (cards, headers)
   - Create organisms (full screens)

4. **Prototyping:**
   - Link screens with smart animate
   - Set up swipe gestures
   - Add micro-interactions

---

*Version 1.0 | VISION Agent | Olfex Design System*
