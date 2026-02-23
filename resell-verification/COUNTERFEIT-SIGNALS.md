# COUNTERFEIT-SIGNALS.md
## Brand-Specific Fake Indicators for Top 10 Niche Perfumes

### Overview
This document catalogs known counterfeit patterns for high-risk niche fragrances. These signals feed into the AI verification system and human reviewer training.

---

## 1. CREED

**Risk Level:** 🔴 VERY HIGH (most counterfeited niche brand)

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Batch Code Pre-2022** | Format: A4219P01 (A=Aventus, 4=year, 219=day) | Wrong format, missing digits | Regex validation |
| **Batch Code Post-2022** | Format: F001025 (F=new system) | Still using old format | Pattern check |
| **Cap Magnetic Click** | Strong magnetic snap when closing | Weak or no magnetism | Video test (if provided) |
| **Cap Top** | Smooth, perfectly centered logo | Off-center, rough edges | Logo detection |
| **Bottle Bottom** | Engraved, not printed | Printed or sticker | Depth analysis |
| **Liquid Color** | Clear to pale amber | Dark, cloudy, or pinkish | Color histogram |
| **Sprayer** | Fine mist, centered | Dripping, off-center | User report post-purchase |
| **Box Texture** | Premium heavy cardboard | Thin, flimsy | Not visible in photos |

### Creed-Specific Verification
```python
creed_checks = {
    'batch_format': r'^(A\d{3}[A-Z]\d{2}|F\d{6})$',
    'cap_magnetism': 'REQUIRE_VIDEO_TEST',  # Seller demonstrates
    'liquid_clarity': 'CHECK_RGB_HISTOGRAM',
    'expected_barcode_prefix': ['350844', '376027']  # EU/US variants
}
```

---

## 2. TOM FORD (Private Blend)

**Risk Level:** 🔴 HIGH

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Gold Circle Arrows** | Right arrow darker than left | Same color, reversed | Color analysis |
| **Label Text** | Sharp, crisp printing | Blurry, bleeding ink | OCR confidence |
| **Bottle Weight** | Heavy, substantial glass | Lightweight | Cannot verify remotely |
| **Cap Fit** | Snug, precise | Loose, wobbly | Visual gap check |
| **Batch Code** | Single letter + 2 digits (A32) | Wrong format | Regex |
| **Box Interior** | White with gold pattern | Plain white, cheap | Image check |
| **UPC Prefix** | 888066 (Estée Lauder) | Wrong prefix | Barcode validation |

### Tom Ford Specific
```python
tomford_checks = {
    'batch_format': r'^[A-Z]\d{2}$',
    'upc_prefix': '888066',
    'gold_circle_check': 'COLOR_CONTRAST_ANALYSIS',
    'label_font': 'HELVETICA_NEUE_CONDENSED'
}
```

---

## 3. MAISON FRANCIS KURKDJIAN (MFK)

**Risk Level:** 🟡 MEDIUM-HIGH

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Bottle Shape** | Distinctive rectangular with beveled edges | Rounded edges, poor glass | Edge detection |
| **Label** | Heavy textured paper, embossed | Smooth, printed only | Texture analysis |
| **Cap** | Heavy magnetic, "MFK" centered | Light, off-center logo | Weight (indirect), logo position |
| **Batch Code** | 6+ characters, engraved | Printed, short codes | Engraving depth check |
| **Box Texture** | Canvas-like finish | Smooth or glossy | Texture classification |
| **Ribbon** | Branded, sewn properly | Generic, glued | Image check if visible |

---

## 4. PARFUMS DE MARLY (PDM)

**Risk Level:** 🟡 MEDIUM-HIGH

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Horse Embossing** | Sharp, detailed, debossed (recessed) | Blobby, raised (embossed) wrong | 3D/shadow analysis |
| **Name Plate** | Metal, debossed letters | Plastic, printed or embossed | Material reflectance |
| **Bottle Base** | Thick glass, heavy | Thin, lightweight | Not verifiable remotely |
| **Cap** | Snug fit, detailed crest | Loose, blurry crest | Fit analysis |
| **Box Horses** | Detailed, crisp | Pixelated, smudged | High-res image check |

### PDM Horse Detail Check
```python
def check_pdm_horse(image):
    # Horse embossing should be DEBOSSED (recessed into bottle)
    # Fakes often have RAISED embossing
    depth_map = estimate_depth_from_shading(image)
    
    if is_raised(depth_map):
        return 'SUSPICIOUS - Likely fake'
    elif is_debossed(depth_map):
        return 'CONSISTENT with authentic'
    else:
        return 'UNCERTAIN - Manual review'
```

---

## 5. LE LABO

**Risk Level:** 🟡 MEDIUM

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Label Date** | Hand-stamped, slightly irregular | Printed, perfect alignment | Text irregularity detection |
| **Label Location** | "Le Labo" + city name stamped | Missing or wrong city | OCR + city validation |
| **Cap Logo** | "le labo" lowercase, specific size | Wrong size, wrong case | Text measurement |
| **Bottle Bottom** | Almost flat with small curve | Curved like beer bottle | Shape analysis |
| **Box Texture** | Distinctive cardboard grain | Smooth or different grain | Texture matching |
| **Batch Code** | Format: 09/2024 (month/year) | Wrong format | Date validation |

### Le Labo Label Check
```python
def check_lelabo_label(image):
    # Extract label region
    label = extract_label_region(image)
    
    # Check for stamped vs printed text
    text_features = analyze_text_texture(label)
    
    # Stamped text has pressure marks, irregularities
    # Printed text is perfectly uniform
    if is_uniformly_printed(text_features):
        return 'LIKELY FAKE - Printed not stamped'
    elif has_stamping_characteristics(text_features):
        return 'CONSISTENT with authentic'
    else:
        return 'UNCERTAIN'
```

---

## 6. BYREDO

**Risk Level:** 🟡 MEDIUM

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Inner Cap** | Black ring with ENGRAVED batch code | All white, printed code, no ring | Color + engraving check |
| **Bottle Weight** | Heavy, substantial | Light | Not verifiable |
| **Label** | Thick textured stock, centered | Thin, off-center | Texture + alignment |
| **Box Grain** | Distinctive textured pattern | Smooth or wrong pattern | Texture classification |
| **Magnetic Cap** | Strong magnetic closure | Weak or none | Video test |
| **Typography** | Specific font weight, spacing | Wrong font, too bold/light | Font matching |

### Byredo Cap Interior Check
```python
byredo_checks = {
    'cap_interior_color': 'MUST_BE_BLACK',
    'batch_code_method': 'MUST_BE_ENGRAVED_NOT_PRINTED',
    'magnetic_test': 'RECOMMENDED_VIDEO'
}
```

---

## 7. DIPTYQUE

**Risk Level:** 🟢 LOW-MEDIUM

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Oval Label** | Perfect oval, centered | Off-center, irregular shape | Shape detection |
| **Logo** | "diptyque" with specific kerning | Wrong spacing, wrong font | Typography analysis |
| **Box Artwork** | High-quality illustration | Pixelated, wrong colors | Image quality check |
| **Batch Code** | 4-6 digits on bottom | Missing or wrong location | OCR location |

---

## 8. AMOUAGE

**Risk Level:** 🟡 MEDIUM

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Crystal Bottle** | Heavy, perfect clarity | Bubbles, light weight | Clarity analysis |
| **Magnetic Cap** | Strong magnet, heavy | Weak, plastic feel | Video test |
| **Label** | Embossed gold or silver | Printed, peeling | Embossing detection |
| **Box** | Thick, magnetic closure | Thin, no magnet | Not fully verifiable |

---

## 9. INITIO

**Risk Level:** 🟢 LOW

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Bottle Shape** | Angular, sharp edges | Rounded edges | Edge detection |
| **Label** | Metallic, reflective | Dull, matte | Reflectance check |
| **Cap** | Magnetic, branded | Non-magnetic | Video test |

---

## 10. XERJOFF

**Risk Level:** 🟢 LOW

### Common Fake Indicators

| Element | Authentic | Fake | Detection Method |
|---------|-----------|------|------------------|
| **Bottle** | Heavy glass, intricate design | Light, poor quality glass | Not verifiable |
| **Cap** | Stone or metal, high quality | Plastic | Material reflectance |
| **Label** | Metallic gold/silver | Plain paper | Color analysis |
| **Box** | Velvet interior, premium | Cheap lining | Image check if visible |

---

## Universal Red Flags (All Brands)

These apply to any perfume verification:

| Red Flag | Severity | Detection |
|----------|----------|-----------|
| **Price too low** | 🔴 Critical | Listing metadata |
| **No box included** | 🟡 Warning | Seller disclosure |
| **Sealed in cellophane** | 🟡 Warning | Brand-dependent (some never seal) |
| **Wrong barcode prefix** | 🔴 Critical | Barcode validation |
| **Misspelled ingredients** | 🔴 Critical | OCR + spellcheck |
| **Mismatched batch codes** | 🔴 Critical | Cross-reference bottle/box |
| **Blurry photos only** | 🟡 Warning | Image quality check |
| **Stock photos** | 🟡 Warning | Reverse image search |
| **Seller won't provide specific angles** | 🔴 Critical | User report |
| **Fill level inconsistent with age** | 🟡 Warning | Logic check |

---

## Batch Code Decoder Reference

### Brand Patterns

| Brand | Pre-2020 Format | 2020+ Format | Example |
|-------|-----------------|--------------|---------|
| Creed | A[day][year][batch] | F[6 digits] | A4219P01 → F001025 |
| Tom Ford | [letter][2 digits] | Same | A32 |
| MFK | Varies | [year][letter][digits] | 2024AB01 |
| Le Labo | [month]/[year] | Same | 09/2024 |
| Byredo | [2 letters][year][batch] | Same | AB2401 |
| PDM | [6 digits] | Same | 240101 |
| Diptyque | [4-6 digits] | Same | 2401 |

---

## Database Schema for Known Fakes

```sql
-- Known counterfeit patterns
CREATE TABLE known_fake_patterns (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(50),
    product_line VARCHAR(100),
    pattern_type VARCHAR(50), -- 'batch_code', 'barcode', 'visual'
    pattern_value VARCHAR(255),
    first_seen DATE,
    evidence_count INT DEFAULT 1,
    confidence ENUM('confirmed', 'suspected'),
    notes TEXT
);

-- Example entries
INSERT INTO known_fake_patterns (brand, pattern_type, pattern_value, confidence) VALUES
('Creed', 'batch_code', 'A9999Z99', 'confirmed'),  -- Impossible date
('Tom Ford', 'barcode', '123456789012', 'confirmed'),  -- Invalid UPC
('Byredo', 'visual', 'all_white_cap_interior', 'confirmed');
```

---

## Human Reviewer Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════╗
║           VERIFICATION QUICK CHECKLIST                           ║
╠══════════════════════════════════════════════════════════════════╣
║ CREED:   Batch format A###X## or F###### ✓                      ║
║          Cap clicks magnetically ✓                               ║
╠══════════════════════════════════════════════════════════════════╣
║ TOM FORD: Gold arrows different shades ✓                        ║
║           UPC starts with 888066 ✓                              ║
╠══════════════════════════════════════════════════════════════════╣
║ PDM:     Horse is DEBOSSED (recessed) not raised ✓              ║
║          Name plate is metal, debossed ✓                        ║
╠══════════════════════════════════════════════════════════════════╣
║ LE LABO: Label is STAMPED not printed ✓                         ║
║          Bottle bottom is FLAT not curved ✓                     ║
╠══════════════════════════════════════════════════════════════════╣
║ BYREDO:  Inner cap is BLACK with ENGRAVED code ✓                ║
╠══════════════════════════════════════════════════════════════════╣
║ ALL:     Batch codes match on bottle + box ✓                    ║
║          Barcode checksum is valid ✓                            ║
║          No spelling errors on labels ✓                         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

*Document Version: 1.0*
*Last Updated: 2026-02-22*
