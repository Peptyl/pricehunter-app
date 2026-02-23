# AI-VERIFICATION-SYSTEM.md
## Multi-Stage Computer Vision Pipeline for Perfume Authentication

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI VERIFICATION PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────┘

   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │  STAGE 1 │ → │  STAGE 2 │ → │  STAGE 3 │ → │  STAGE 4 │ → │  STAGE 5 │
   │  Image   │   │  OCR &   │   │ Packaging│   │  Bottle  │   │  Final   │
   │  Quality │   │  Code    │   │  Anomaly │   │ Geometry │   │  Score   │
   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
        ↓              ↓              ↓              ↓              ↓
    [0-100]        [0-100]        [0-100]        [0-100]        [0-100]
        │              │              │              │              │
        └──────────────┴──────────────┴──────────────┴──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │   WEIGHTED FINAL SCORE      │
                    │   (Confidence 0-100)        │
                    └─────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │   DECISION THRESHOLD        │
                    │   ≥85: Legit ✅             │
                    │   60-84: Review ⚠️          │
                    │   <60: Suspicious ❌        │
                    └─────────────────────────────┘
```

---

## Stage 1: Image Quality Assessment

### Purpose
Ensure images meet minimum standards for downstream analysis.

### Algorithms
```python
# Blur detection using Laplacian variance
def detect_blur(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return min(variance / 500, 100)  # Normalize to 0-100

# Exposure check
def check_exposure(image):
    hist = cv2.calcHist([image], [0], None, [256], [0,256])
    clipped = np.sum(hist[:10]) + np.sum(hist[-10:])
    total = np.sum(hist)
    return 100 - (clipped / total * 1000)  # Penalize clipping

# Resolution check
def check_resolution(image):
    h, w = image.shape[:2]
    return min((h * w) / (1920 * 1080) * 100, 100)
```

### Scoring
| Metric | Weight | Threshold |
|--------|--------|-----------|
| Sharpness | 40% | Variance > 100 |
| Exposure | 30% | No clipping |
| Resolution | 30% | 1080p minimum |

---

## Stage 2: OCR & Code Parsing

### 2.1 Batch Code Extraction

**Target Locations:**
- Bottle bottom (engraved or printed)
- Box bottom/side
- Back label

**OCR Pipeline:**
```python
import pytesseract
from PIL import Image

def extract_batch_code(image):
    # Preprocessing for engraved text
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Enhance engraved text
    kernel = np.ones((2,2), np.uint8)
    morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    
    # Adaptive threshold for uneven lighting
    thresh = cv2.adaptiveThreshold(
        morph, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # OCR with alphanumeric pattern
    text = pytesseract.image_to_string(
        thresh, 
        config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    )
    
    # Pattern matching for batch codes
    patterns = {
        'creed_pre2022': r'A\d{3}[A-Z]\d{2}',      # A4219P01
        'creed_post2022': r'F\d{6}',               # F001025
        'tomford': r'[A-Z]\d{2}',                  # A32
        'lelabo': r'\d{2}/\d{4}',                  # 09/2024
        'mfk': r'\d{4}[A-Z]\d{2}',                 # 2024AB01
        'byredo': r'[A-Z]{2}\d{4}',                # AB2401
    }
    
    return match_batch_pattern(text, patterns)
```

### 2.2 Barcode Parsing

```python
from pyzbar.pyzbar import decode

def extract_barcode(image):
    barcodes = decode(image)
    for barcode in barcodes:
        if barcode.type == 'EAN13':
            return {
                'code': barcode.data.decode('utf-8'),
                'type': 'EAN13',
                'valid': validate_ean13_checksum(barcode.data)
            }
    return None

def validate_ean13_checksum(code):
    # EAN-13 validation
    digits = [int(d) for d in code[:12]]
    checksum = sum(d * (3 if i % 2 else 1) for i, d in enumerate(digits))
    check_digit = (10 - (checksum % 10)) % 10
    return check_digit == int(code[12])
```

### 2.3 Code Verification Logic

| Check | Method | Weight |
|-------|--------|--------|
| Batch code format valid | Regex pattern match | 20% |
| Code matches brand format | Brand-specific validator | 25% |
| Bottle/box codes match | String comparison | 30% |
| Barcode valid checksum | EAN-13 validation | 15% |
| Barcode matches product | Database lookup | 10% |

---

## Stage 3: Packaging Anomaly Detection

### 3.1 Typography Analysis

**Font Consistency Check:**
```python
def analyze_typography(image, brand_reference):
    # Extract text regions
    text_regions = detect_text_regions(image)
    
    # Compare against brand reference fonts
    scores = []
    for region in text_regions:
        font_features = extract_font_features(region)
        similarity = compare_fonts(font_features, brand_reference['fonts'])
        scores.append(similarity)
    
    return np.mean(scores) * 100
```

**Spelling/Character Anomaly:**
- OCR text checked against known ingredient lists
- Flag unknown spellings or character substitutions
- Common fake indicator: "Eau de Toilette" → "Eau de Toilettte"

### 3.2 Logo & Brand Mark Verification

```python
# Using Siamese Network or Feature Matching
def verify_logo(image, brand):
    # Load reference logo features
    reference = load_reference_logo(brand)
    
    # Extract logo region (YOLO detection)
    logo_region = detect_logo_region(image)
    
    # Feature extraction (SIFT or deep features)
    features = extract_logo_features(logo_region)
    
    # Similarity score
    similarity = cosine_similarity(features, reference)
    return similarity * 100
```

### 3.3 Color Accuracy Check

```python
def check_colors(image, brand_palette):
    # Extract dominant colors
    pixels = image.reshape(-1, 3)
    kmeans = KMeans(n_clusters=5).fit(pixels)
    dominant_colors = kmeans.cluster_centers_
    
    # Compare to brand reference palette
    color_score = color_distance(dominant_colors, brand_palette)
    return max(0, 100 - color_score)
```

### 3.4 Print Quality Analysis

| Anomaly | Detection Method | Indicator |
|---------|------------------|-----------|
| Blurry text | Edge sharpness metric | Counterfeit printing |
| Pixelation | FFT high-frequency analysis | Low-res source |
| Color bleeding | Gradient analysis | Poor printing |
| Misalignment | Hough line detection | Quality issues |

---

## Stage 4: Bottle Geometry & Physical Verification

### 4.1 Shape Consistency

```python
def analyze_geometry(image, brand_model):
    # Edge detection
    edges = cv2.Canny(image, 50, 150)
    
    # Contour extraction
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Compare to reference shape
    main_contour = max(contours, key=cv2.contourArea)
    similarity = cv2.matchShapes(main_contour, brand_model['contour'], cv2.CONTOURS_MATCH_I1, 0)
    
    return max(0, 100 - similarity * 100)
```

### 4.2 Label Alignment Check

```python
def check_label_alignment(image):
    # Detect label edges
    edges = cv2.Canny(image, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    
    # Calculate angles
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
        angles.append(angle)
    
    # Check for parallelism (labels should be aligned)
    angle_variance = np.var(angles)
    return max(0, 100 - angle_variance)
```

### 4.3 Cap & Nozzle Inspection

| Feature | Check | Method |
|---------|-------|--------|
| Cap fit | Tightness indicator | Visual gap analysis |
| Nozzle symmetry | Centered spray hole | Circle detection |
| Stem straightness | Alignment | Line detection |
| Material quality | Surface texture | GLCM features |

---

## Stage 5: Fill Line & Content Verification

### 5.1 Liquid Level Detection

```python
def analyze_fill_level(image, claimed_volume):
    # Detect liquid boundary
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Enhance liquid-air boundary
    blurred = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find meniscus (liquid curve)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
    
    if lines is not None:
        # Calculate fill percentage from line position
        fill_percentage = estimate_fill_from_line(lines, image.shape[0])
        
        # Compare to expected for claimed volume
        expected_range = get_expected_fill_range(claimed_volume)
        
        if expected_range[0] <= fill_percentage <= expected_range[1]:
            return 100  # Plausible
        else:
            return max(0, 100 - abs(fill_percentage - expected_range[1]) * 5)
    
    return 50  # Uncertain
```

### 5.2 Refill Detection

| Indicator | Detection Method |
|-----------|------------------|
| Residue marks | Edge detection around neck |
| Scratches on threads | Texture analysis |
| Unusual meniscus shape | Curve fitting |
| Color inconsistency | RGB histogram analysis |

---

## Cross-Reference System

### Authentic Reference Database

```python
# Reference data structure
reference_db = {
    'creed_aventus_100ml': {
        'batch_patterns': [r'A\d{3}[A-Z]\d{2}', r'F\d{6}'],
        'logo_features': np.array([...]),  # Pre-computed
        'label_geometry': {'width': 120, 'height': 80, ...},
        'color_palette': [(R,G,B), ...],
        'font_fingerprints': [...],
        'typical_fill_range': (85, 95),  # % of bottle height
    },
    # ... more products
}
```

### Matching Algorithm

```python
def cross_reference(extracted_features, product_id):
    reference = reference_db[product_id]
    
    scores = {
        'batch_valid': validate_batch_format(extracted_features['batch'], reference['batch_patterns']),
        'logo_match': cosine_similarity(extracted_features['logo'], reference['logo_features']),
        'color_match': color_distance(extracted_features['colors'], reference['color_palette']),
        'geometry_match': shape_similarity(extracted_features['shape'], reference['label_geometry']),
    }
    
    # Weighted combination
    weights = {'batch_valid': 0.3, 'logo_match': 0.25, 'color_match': 0.25, 'geometry_match': 0.2}
    final_score = sum(scores[k] * weights[k] for k in scores) * 100
    
    return final_score, scores
```

---

## Final Scoring Model

### Weighted Combination

| Stage | Weight | Description |
|-------|--------|-------------|
| Image Quality | 10% | Can we even analyze this? |
| OCR & Codes | 25% | Are identifiers valid and matching? |
| Packaging | 30% | Does printing quality match authentic? |
| Bottle Geometry | 20% | Are physical characteristics correct? |
| Fill/Content | 15% | Is the product genuine and unopened? |

### Decision Thresholds

```python
def get_verdict(score):
    if score >= 85:
        return {
            'status': 'LEGIT',
            'badge': '✅ Verified Authentic',
            'buyer_message': 'High confidence authenticity. Listed with guarantee.',
            'action': 'LIST_IMMEDIATELY'
        }
    elif score >= 60:
        return {
            'status': 'REVIEW',
            'badge': '⚠️ Under Review',
            'buyer_message': 'Additional verification in progress.',
            'action': 'QUEUE_HUMAN_REVIEW'
        }
    else:
        return {
            'status': 'SUSPICIOUS',
            'badge': '❌ Not Verified',
            'buyer_message': 'Could not verify authenticity.',
            'action': 'REJECT_WITH_REASONS'
        }
```

---

## Model Training & Updates

### Training Data Requirements
See DATA-NEEDS.md for collection strategy.

### Continuous Learning Pipeline
```
New verified authentic images → Feature extraction → Retrain monthly
Confirmed fake reports → Add to negative set → Update classifier
Human reviewer corrections → Fine-tune thresholds → Deploy weekly
```

### A/B Testing
- Shadow mode: Run new model alongside current, compare decisions
- Gradual rollout: 5% → 25% → 100% of traffic
- Monitor: False positive rate, human review queue depth

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Processing time | < 30 seconds per listing |
| Accuracy (authentic) | > 95% recall |
| Accuracy (fake) | > 85% precision |
| Human review rate | < 20% of listings |
| False positive rate | < 5% |

---

## Implementation Stack

| Component | Technology |
|-----------|------------|
| Image preprocessing | OpenCV, Pillow |
| OCR | Tesseract, AWS Textract |
| Deep learning | PyTorch / TensorFlow |
| Feature extraction | ResNet50, SIFT (OpenCV) |
| Object detection | YOLOv8 |
| Vector similarity | FAISS, Annoy |
| Inference serving | FastAPI + Ray Serve |

---

*Document Version: 1.0*
*Last Updated: 2026-02-22*
