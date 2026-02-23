#!/usr/bin/env python3
"""
PriceHunter Backend API
FastAPI server for price tracking and alerts
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
import json

app = FastAPI(title="PriceHunter API", version="1.0")

# CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect('pricehunter.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            perfume_id TEXT,
            target_price REAL,
            size_ml INTEGER,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perfume_id TEXT,
            retailer TEXT,
            price REAL,
            currency TEXT,
            size_ml INTEGER,
            in_stock BOOLEAN,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            phone TEXT,
            country TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Models
class AlertRequest(BaseModel):
    user_id: str
    perfume_id: str
    target_price: float
    size_ml: int

class UserCreate(BaseModel):
    email: str
    country: str = 'UK'
    tier: str = 'free'  # free, premium, pro

class TierUpgrade(BaseModel):
    user_id: str
    tier: str  # premium, pro

# Authentication middleware
async def check_tier_access(user_id: str, required_tier: str) -> bool:
    """Check if user has required tier access"""
    conn = sqlite3.connect('pricehunter.db')
    c = conn.cursor()
    
    c.execute('SELECT tier FROM users WHERE id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return False
    
    user_tier = result[0]
    
    tier_hierarchy = {'free': 0, 'premium': 1, 'pro': 2}
    return tier_hierarchy.get(user_tier, 0) >= tier_hierarchy.get(required_tier, 0)

@app.get("/api/perfumes")
def get_perfumes():
    """Get list of tracked perfumes"""
    with open('/home/peptyl/.openclaw/workspace/pricehunter/data/perfumes.json') as f:
        data = json.load(f)
    return data['top_10_niche_perfumes']

@app.get("/api/perfumes/{perfume_id}/prices")
def get_prices(perfume_id: str):
    """Get current prices from all retailers"""
    conn = sqlite3.connect('pricehunter.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
        SELECT * FROM price_history 
        WHERE perfume_id = ? 
        ORDER BY scraped_at DESC
        LIMIT 20
    ''', (perfume_id,))
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.post("/api/alerts")
def create_alert(alert: AlertRequest):
    """Create price alert"""
    conn = sqlite3.connect('pricehunter.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO price_alerts (user_id, perfume_id, target_price, size_ml)
        VALUES (?, ?, ?, ?)
    ''', (alert.user_id, alert.perfume_id, alert.target_price, alert.size_ml))
    
    alert_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'alert_id': alert_id,
        'message': f"Alert set for £{alert.target_price}"
    }

@app.get("/api/alerts/{user_id}")
def get_user_alerts(user_id: str):
    """Get user's active alerts"""
    conn = sqlite3.connect('pricehunter.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
        SELECT * FROM price_alerts 
        WHERE user_id = ? AND status = 'active'
        ORDER BY created_at DESC
    ''', (user_id,))
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.get("/api/deals")
def get_current_deals(tier: str = 'free'):
    """Get current best deals - tiered access"""
    
    # Mock data - full deals
    all_deals = [
        {
            'perfume': 'Creed Aventus 100ml',
            'best_price': 175.00,
            'retailer': 'FragranceBuy.ca',
            'retail_price': 265.00,
            'savings': 90.00,
            'savings_percent': 34,
            'locked': tier == 'free',
            'time_remaining': '3 hours',
            'stock': 'Low (2 left)'
        },
        {
            'perfume': 'Parfums de Marley Layton 125ml',
            'best_price': 135.00,
            'retailer': 'Notino',
            'retail_price': 180.00,
            'savings': 45.00,
            'savings_percent': 25,
            'locked': tier == 'free',
            'time_remaining': '6 hours',
            'stock': 'In stock'
        },
        {
            'perfume': 'MFK Baccarat Rouge 540 70ml',
            'best_price': 195.00,
            'retailer': 'MaxAroma',
            'retail_price': 245.00,
            'savings': 50.00,
            'savings_percent': 20,
            'locked': False,
            'time_remaining': '12 hours',
            'stock': 'High'
        }
    ]
    
    # Tier filtering
    if tier == 'free':
        # Free users see top 3 deals, some locked
        visible_deals = all_deals[:3]
        total_savings = sum(d['savings'] for d in all_deals)
        
        return {
            'scan_time': datetime.now().isoformat(),
            'tier': 'free',
            'deals_shown': 3,
            'deals_total': len(all_deals),
            'deals': visible_deals,
            'upsell': {
                'message': f'🔒 {len(all_deals) - 3} more deals hidden',
                'savings_missed': f'£{total_savings - sum(d["savings"] for d in visible_deals):.0f}',
                'cta': 'Upgrade to Premium for instant access'
            }
        }
    
    elif tier in ['premium', 'pro']:
        # Premium/Pro see all deals, unlocked
        return {
            'scan_time': datetime.now().isoformat(),
            'tier': tier,
            'deals_shown': len(all_deals),
            'deals_total': len(all_deals),
            'deals': all_deals,
            'bonus': 'AI predictions active' if tier == 'pro' else None
        }
    
    return {'error': 'Invalid tier'}


@app.get("/api/ai/predict/{perfume_id}")
def predict_price(perfume_id: str, user_id: str):
    """AI price prediction - Premium+ only"""
    if not check_tier_access(user_id, 'premium'):
        return {
            'error': 'Premium feature',
            'upgrade_url': '/upgrade',
            'message': 'AI predictions require Premium subscription'
        }
    
    from intelligence.ai_engine import AIDealPredictor
    predictor = AIDealPredictor()
    
    return predictor.predict_price_drop(perfume_id, 'notino')


@app.get("/api/ai/recommendations/{user_id}")
def get_recommendations(user_id: str):
    """Personalized recommendations - Premium+ only"""
    if not check_tier_access(user_id, 'premium'):
        return {
            'error': 'Premium feature',
            'upgrade_url': '/upgrade',
            'message': 'Personalized recommendations require Premium subscription'
        }
    
    from intelligence.ai_engine import PersonalizedRecommender
    recommender = PersonalizedRecommender()
    
    return {
        'recommendations': recommender.get_recommendations(user_id),
        'generated_at': datetime.now().isoformat()
    }


@app.get("/api/ai/arbitrage")
def get_arbitrage(user_id: str, min_profit: float = 30.0):
    """Arbitrage opportunities - Pro only"""
    if not check_tier_access(user_id, 'pro'):
        return {
            'error': 'Pro feature',
            'upgrade_url': '/upgrade',
            'message': 'Arbitrage finder requires Pro subscription'
        }
    
    from intelligence.ai_engine import ArbitrageDetector
    detector = ArbitrageDetector()
    
    return {
        'opportunities': detector.find_arbitrage(min_profit),
        'disclaimer': 'For educational purposes. Check local laws and regulations.'
    }


@app.get("/api/ai/sentiment/{perfume_name}")
def get_sentiment(perfume_name: str, user_id: str):
    """Market sentiment analysis - Premium+ only"""
    if not check_tier_access(user_id, 'premium'):
        return {
            'error': 'Premium feature',
            'upgrade_url': '/upgrade'
        }
    
    from intelligence.ai_engine import MarketSentimentAnalyzer
    analyzer = MarketSentimentAnalyzer()
    
    return analyzer.get_sentiment(perfume_name)

@app.post("/api/users")
def create_user(user: UserCreate):
    """Create new user"""
    import uuid
    user_id = str(uuid.uuid4())
    
    conn = sqlite3.connect('pricehunter.db')
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO users (id, email, country)
            VALUES (?, ?, ?)
        ''', (user_id, user.email, user.country))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'user_id': user_id,
            'email': user.email
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Email already exists")

@app.get("/health")
def health_check():
    return {'status': 'ok', 'time': datetime.now().isoformat()}

if __name__ == '__main__':
    import uvicorn
    print("Starting PriceHunter API...")
    print("Endpoints:")
    print("  GET  /api/perfumes")
    print("  GET  /api/perfumes/{id}/prices")
    print("  POST /api/alerts")
    print("  GET  /api/deals")
    uvicorn.run(app, host='0.0.0.0', port=8001)
