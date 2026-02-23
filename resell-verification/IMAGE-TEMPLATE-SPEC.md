# IMAGE-TEMPLATE-SPEC.md
## Standardized Photo Capture Specification for Perfume Verification

### Overview
This document defines the mandatory photo template that sellers must complete for AI verification. The template is enforced via the mobile app's guided capture flow.

---

## Required Photo Angles (10 Photos)

| # | Angle | Description | Why It Matters |
|---|-------|-------------|----------------|
| 1 | **Bottle Front** | Full front label, centered | Typography, logo quality, alignment |
| 2 | **Bottle Back** | Full back label, centered | Ingredients list, distributor info |
| 3 | **Bottle Bottom** | Batch code / engraved markings | Production date, authenticity tracking |
| 4 | **Cap Top** | Cap from above | Logo embossing, material quality |
| 5 | **Cap Underside** | Inside cap showing nozzle seat | Molding marks, fit quality |
| 6 | **Atomizer** | Close-up of spray mechanism | Stem construction, alignment |
| 7 | **Box Front** | Front of original packaging | Artwork quality, color accuracy |
| 8 | **Box Back/Barcode** | Barcode and text panel | UPC verification, printing quality |
| 9 | **Ingredients Panel** | Close-up of ingredients list | Font consistency, spelling accuracy |
| 10 | **Fill Level** | Side view showing liquid level | Verifies volume, detects refills |

---

## Technical Requirements

### Image Specifications
| Parameter | Requirement |
|-----------|-------------|
| **Resolution** | Minimum 1920x1080 (1080p) |
| **Format** | JPEG, quality ≥ 85% |
| **File Size** | 500KB - 5MB per image |
| **Aspect Ratio** | 4:3 or 16:9 (auto-cropped if needed) |
| **Color Space** | sRGB |

### Capture Environment
| Parameter | Requirement |
|-----------|-------------|
| **Lighting** | Natural daylight OR 5000K+ LED, no harsh shadows |
| **Background** | Solid white, gray, or black (neutral) |
| **Distance** | 15-30cm for details, 50cm for full shots |
| **Focus** | Sharp on text/markings; no motion blur |
| **Glare** | Avoid reflective hotspots on glass/metal |

---

## App-Guided Capture Flow

The mobile app enforces template compliance through real-time feedback:

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Position bottle in frame                               │
│  □ Show bottle front label                                      │
│  [CAMERA PREVIEW]                                               │
│  ✓ Label detected    ✓ Good lighting    ✗ Too blurry          │
│           [CAPTURE]                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Auto-check captured image                              │
│  ✓ Resolution sufficient (12MP)                                 │
│  ✓ Text readable (OCR confidence > 80%)                         │
│  ✓ No glare detected                                            │
│  [RETAKE]              [CONFIRM & CONTINUE]                     │
└─────────────────────────────────────────────────────────────────┘
```

### Real-Time Quality Checks
- **Blur Detection:** Laplacian variance > 100
- **Lighting:** Histogram spread analysis, no clipping
- **Subject Detection:** Object detection model confirms perfume bottle present
- **Angle Validation:** Edge detection confirms correct orientation

---

## Pass/Fail Upload Checklist

### Automatic Rejection Criteria
An upload is immediately rejected if ANY of the following are detected:

| Issue | Detection Method |
|-------|------------------|
| Image too small | Resolution < 1920x1080 |
| Excessive blur | Laplacian variance < 50 |
| Wrong object detected | CNN classifier confidence < 70% |
| Extreme over/under exposure | Histogram clipping > 10% |
| Missing required angle | Photo count < 10 |
| Duplicate image | Perceptual hash similarity > 90% |
| Screenshot/upload from web | Metadata analysis, EXIF verification |

### Warning Flags (Allowed but flagged)
These don't block upload but reduce confidence score:

| Issue | Impact |
|-------|--------|
| Suboptimal lighting | -5 confidence points |
| Slight reflection/glare | -3 confidence points |
| Non-neutral background | -2 confidence points |
| Slightly off-center | -2 confidence points |
| JPEG artifacts detected | -5 confidence points |

---

## Example Template Gallery

### Photo 1: Bottle Front
```
┌─────────────────────────────┐
│                             │
│      [PERFUME BOTTLE]       │
│      ┌───────────┐          │
│      │   LOGO    │          │
│      │   TEXT    │          │
│      │   LABEL   │          │
│      └───────────┘          │
│                             │
│    Neutral background       │
└─────────────────────────────┘
Requirements: Label fully visible, text legible, no glare
```

### Photo 3: Bottle Bottom (Critical)
```
┌─────────────────────────────┐
│                             │
│         ┌──────┐            │
│         │BATCH │  ← Engraved│
│         │CODE  │    code    │
│         │A42B01│   must be  │
│         └──────┘   sharp    │
│                             │
└─────────────────────────────┘
Requirements: Batch code 100% readable, no flash reflection
```

### Photo 10: Fill Level
```
┌─────────────────────────────┐
│                             │
│        ═══════════          │ ← Fill line visible
│        ║ LIQUID ║           │
│        ║        ║           │
│        ╚════════╝           │
│                             │
│   Side view with light      │
│   behind bottle (optional)  │
└─────────────────────────────┘
Requirements: Meniscus visible, level plausible for claimed volume
```

---

## Brand-Specific Additions

Some brands require additional photos:

| Brand | Additional Photo | Reason |
|-------|------------------|--------|
| **Creed** | Magnetic cap test video | Genuine caps click magnetically |
| **Le Labo** | Label date/location stamp | Hand-stamped, not printed |
| **Byredo** | Box texture close-up | Distinctive grain pattern |
| **PDM** | Horse embossing detail | Quality of engraving |
| **MFK** | Box interior ribbon | Authenticity of packaging |

---

## Implementation Notes

### App Camera Module
- Use native camera APIs (CameraX for Android, AVFoundation for iOS)
- Implement tap-to-focus with focus peaking
- Provide grid overlay for alignment
- Auto-capture when all criteria met (optional)

### Backend Validation
```python
def validate_upload(image_set):
    checks = {
        'count': len(image_set) == 10,
        'resolution': all(img.width >= 1920 for img in image_set),
        'blur': all(laplacian_variance(img) > 50 for img in image_set),
        'duplicates': no_duplicates(image_set),
        'completeness': all_required_angles_present(image_set)
    }
    return all(checks.values()), checks
```

### Storage Structure
```
listings/
  {listing_id}/
    raw/
      01_bottle_front.jpg
      02_bottle_back.jpg
      ...
    processed/
      01_bottle_front_ocr.json
      01_bottle_front_features.json
      ...
```

---

## Rejection Messaging

When uploads fail, provide specific, actionable feedback:

| Failure | User Message |
|---------|--------------|
| Too blurry | "Photo is too blurry. Hold steady and tap to focus." |
| Wrong angle | "This doesn't look like the bottle front. Please retake." |
| Poor lighting | "Too dark. Move to a brighter area or turn on lights." |
| Glare detected | "Reflection detected. Adjust angle to avoid glare." |
| Batch code unreadable | "Batch code is unclear. Get closer and use macro mode." |

---

*Document Version: 1.0*
*Last Updated: 2026-02-22*
