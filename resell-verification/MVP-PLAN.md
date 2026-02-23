# MVP-PLAN.md
## Safer Niche Perfume Resale Platform with AI Verification

### Product Overview
A specialized marketplace for niche perfume enthusiasts that reduces counterfeit risk through standardized photo capture and AI-powered authenticity verification before listings go live.

**Key Differentiator:** Unlike Reddit/Facebook/Vinted where verification is absent or crowdsourced, this platform requires AI + optional human verification before a listing can receive buyer funds.

---

## User Flows

### 1. Seller Journey

```
┌─────────────────────────────────────────────────────────────────┐
│  SIGNUP → VERIFY IDENTITY → REQUEST TO SELL → CAPTURE PHOTOS   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI ANALYSIS (30-60s) → VERDICT → IF PASS: LIST LIVE          │
│                       → IF REVIEW: QUEUE FOR HUMAN             │
│                       → IF FAIL: REJECT WITH REASONS           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SALE → SHIP TO BUYER → DELIVERY CONFIRM → FUNDS RELEASED      │
│  (Escrow holds funds until delivery + verification)            │
└─────────────────────────────────────────────────────────────────┘
```

**Seller Onboarding Steps:**
1. Email/phone verification
2. ID verification (KYC - passport/driver's license)
3. Payout method setup (Stripe Connect / PayPal)
4. First listing requires photo template training (interactive guide)

### 2. Verifier Journey (Human Reviewers)

```
┌─────────────────────────────────────────────────────────────────┐
│  REVIEW QUEUE → SIDE-BY-SIDE COMPARISON → DECISION              │
│  (AI-flagged items + random audits)                            │
└─────────────────────────────────────────────────────────────────┘
```

**Verifier Actions:**
- Approve (Legit)
- Request more photos
- Reject with specific reason codes
- Flag for admin review

**Verifier Compensation:** Per-review payment or revenue share

### 3. Buyer Journey

```
┌─────────────────────────────────────────────────────────────────┐
│  BROWSE → VIEW VERIFICATION BADGE → PURCHASE → ESCROW PAYMENT  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RECEIVE → 48HR AUTHENTICATION WINDOW → RELEASE / DISPUTE      │
└─────────────────────────────────────────────────────────────────┘
```

**Buyer Trust Indicators:**
- AI Confidence Score (0-100)
- Verification Badge: ✅ Legit / ⚠️ Manual Review / ❌ Suspicious
- Checklist of verified elements (batch code, packaging, etc.)
- Seller reputation tier
- "Authenticity Guarantee" badge for high-confidence listings

---

## Trust Model & Fraud Prevention Layers

### Layer 1: Identity Verification (Pre-Listing)
- Government ID verification (Stripe Identity / Onfido)
- Phone/email verification
- Address verification
- First-time seller deposit (£20-50) - refunded after 3 successful sales

### Layer 2: AI Photo Verification (Per-Listing)
- Mandatory 10-photo template (see IMAGE-TEMPLATE-SPEC.md)
- Real-time quality checks (blur, lighting, angles)
- Multi-stage CV pipeline (see AI-VERIFICATION-SYSTEM.md)
- Confidence scoring with explainable results

### Layer 3: Human Review (Escalation)
- All 60-84 confidence scores → human review
- Random 5% sampling of 85+ scores for quality audit
- Community-expert verifiers with track records

### Layer 4: Escrow Protection (Transaction)
- Funds held until delivery confirmed
- 48-hour buyer authentication window
- Dispute resolution with photo evidence

### Layer 5: Post-Transaction Reputation
- Buyer "confirmed authentic" ratings
- Seller tier system based on history
- Ban escalation for confirmed fakes

---

## UK/FR First Rollout Strategy

### Why UK/FR First?
1. **Market Size:** UK = £2.1B fragrance market; FR = €4.5B (Europe's largest)
2. **Niche Density:** High concentration of Creed, Le Labo, Byredo, PDM enthusiasts
3. **Regulatory:** Strong consumer protection laws legitimize verification claims
4. **Shipping:** Royal Mail/La Poste integration for tracked delivery
5. **Payment:** Stripe + PayPal widely adopted

### Geographic Expansion Phases
| Phase | Markets | Timeline |
|-------|---------|----------|
| 1 | UK + France | Months 1-6 |
| 2 | Germany + Netherlands | Months 7-12 |
| 3 | US + Canada | Months 13-18 |

### Localization Requirements
- **UK:** GBP, Royal Mail tracking, English UI, UKCA compliance
- **FR:** EUR, La Poste tracking, French UI, CE marking checks

---

## Key Metrics for Success

| Metric | Target (6 months) |
|--------|-------------------|
| Counterfeit Rate | <2% (vs 15-20% on unverified platforms) |
| AI Accuracy | >90% on validation set |
| Time to Verify | <60 seconds (AI) / <24 hours (human) |
| Dispute Rate | <3% of transactions |
| GMV | £500K |
| Seller NPS | >50 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AI false positives | Human review pipeline; seller appeal process |
| Empty bottle refills | Require sealed/unopened OR fill line verification |
| Account takeover | 2FA; device fingerprinting; anomaly detection |
| Chargebacks | Escrow holds; clear T&Cs; evidence collection |
| Platform liability | "Verification assistant, not guarantee" disclaimer; insurance option |

---

## Legal/Risk Notes

### Counterfeit Handling
- **Never** knowingly allow counterfeit sales
- Immediate account ban for confirmed fakes
- Cooperation with brand IP teams (voluntary reporting)
- Clear T&Cs: Platform is "authentication assistant" not legal guarantor

### Buyer Claims
- 14-day cooling-off period (UK Consumer Rights Act)
- 48-hour authenticity verification window post-delivery
- "Not as described" disputes handled through escrow
- Optional insurance upgrade for high-value items (£500+)

### Data Protection
- GDPR compliance (UK/EU)
- Photo retention: 90 days post-transaction, then purge
- ID verification data: Encrypted, retained per KYC requirements

### Insurance Partner (Recommended)
- Partner with Hiscox or similar for "Authentication Guarantee" insurance
- Platform pays premium; buyer gets peace of mind
- Covers refund if item proven fake post-purchase

---

## Tech Stack Overview

| Layer | Technology |
|-------|------------|
| Mobile App | React Native (iOS/Android) |
| Backend | Node.js / Python FastAPI |
| Database | PostgreSQL + Redis |
| CV/AI | Python + OpenCV + TensorFlow/PyTorch |
| OCR | Tesseract + AWS Textract |
| Storage | AWS S3 / Cloudflare R2 |
| Payments | Stripe Connect + PayPal |
| Hosting | AWS / GCP / Hetzner |

See AI-VERIFICATION-SYSTEM.md for detailed CV pipeline.

---

## Competitive Positioning

| Platform | Verification | Counterfeit Risk | Our Advantage |
|----------|--------------|------------------|---------------|
| Reddit (r/fragranceswap) | None | Very High | AI + escrow protection |
| Facebook Marketplace | None | High | Standardized verification |
| Vinted | Basic | Medium | Niche-specific AI + human review |
| eBay | Authenticity Guarantee* | Medium | Faster, cheaper, niche-focused |
| StockX | Human only | Low | Faster verification, lower fees |

*eBay's guarantee is limited to select categories and values.

---

## Go-to-Market

1. **Seed Community:** Partner with r/fragrance and Fragrantica forums
2. **Influencer:** Send verified sellers to perfume YouTubers (Demi Rawling, etc.)
3. **Referral:** £10 credit for sellers who bring verified buyers
4. **Guarantee:** "First fake is on us" - platform refunds if AI fails

---

*Document Version: 1.0*
*Last Updated: 2026-02-22*
