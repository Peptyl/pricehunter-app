#!/usr/bin/env python3
"""
Olfex Backend API - PostgreSQL Version
FastAPI server for price tracking and alerts
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import psycopg2
import psycopg2.extras
import json
import redis
import os

app = FastAPI(title="Olfex API", version="1.0.0")

# CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'olfex')
DB_USER = os.getenv('DB_USER', 'olfex')
DB_PASS = os.getenv('DB_PASS', 'olfex123')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

def get_db_conn():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def get_redis():
    """Get Redis connection"""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        return r
    except:
        return None

def init_db():
    """Initialize database tables"""
    conn = get_db_conn()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_alerts (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255),
            perfume_id VARCHAR(255),
            target_price DECIMAL(10,2),
            size_ml INTEGER,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id SERIAL PRIMARY KEY,
            perfume_id VARCHAR(255),
            retailer VARCHAR(255),
            price DECIMAL(10,2),
            currency VARCHAR(10),
            size_ml INTEGER,
            in_stock BOOLEAN,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(255) PRIMARY KEY,
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(50),
            country VARCHAR(50),
            tier VARCHAR(50) DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

# Models
class AlertRequest(BaseModel):
    user_id: str
    perfume_id: str
    target_price: float
    size_ml: int

class UserCreate(BaseModel):
    email: str
    country: str = 'UK'
    tier: str = 'free'

class TierUpgrade(BaseModel):
    user_id: str
    tier: str

# Authentication middleware
async def check_tier_access(user_id: str, required_tier: str) -> bool:
    """Check if user has required tier access"""
    conn = get_db_conn()
    c = conn.cursor()
    
    c.execute('SELECT tier FROM users WHERE id = %s', (user_id,))
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
    # Try Redis cache first
    r = get_redis()
    if r:
        cached = r.get('perfumes:list')
        if cached:
            return json.loads(cached)
    
    # Load from file
    with open('/home/peptyl/.openclaw/workspace/olfex/data/perfumes.json') as f:
        data = json.load(f)
    
    # Cache for 5 minutes
    if r:
        r.setex('perfumes:list', 300, json.dumps(data['top_10_niche_perfumes']))
    
    return data['top_10_niche_perfumes']

@app.get("/api/perfumes/{perfume_id}/prices")
def get_prices(perfume_id: str):
    """Get current prices from all retailers"""
    # Try Redis cache
    r = get_redis()
    cache_key = f'prices:{perfume_id}'
    if r:
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
    
    conn = get_db_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    c.execute('''
        SELECT * FROM price_history 
        WHERE perfume_id = %s 
        ORDER BY scraped_at DESC
        LIMIT 20
    ''', (perfume_id,))
    
    rows = c.fetchall()
    conn.close()
    
    result = [dict(row) for row in rows]
    
    # Cache for 2 minutes
    if r:
        r.setex(cache_key, 120, json.dumps(result))
    
    return result

@app.post("/api/alerts")
def create_alert(alert: AlertRequest):
    """Create price alert"""
    conn = get_db_conn()
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO price_alerts (user_id, perfume_id, target_price, size_ml)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (alert.user_id, alert.perfume_id, alert.target_price, alert.size_ml))
    
    alert_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    
    # Invalidate cache
    r = get_redis()
    if r:
        r.delete(f'alerts:{alert.user_id}')
    
    return {
        'success': True,
        'alert_id': alert_id,
        'message': f"Alert set for £{alert.target_price}"
    }

@app.get("/api/alerts/{user_id}")
def get_user_alerts(user_id: str):
    """Get user's active alerts"""
    # Try Redis cache
    r = get_redis()
    cache_key = f'alerts:{user_id}'
    if r:
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
    
    conn = get_db_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    c.execute('''
        SELECT * FROM price_alerts 
        WHERE user_id = %s AND status = 'active'
        ORDER BY created_at DESC
    ''', (user_id,))
    
    rows = c.fetchall()
    conn.close()
    
    result = [dict(row) for row in rows]
    
    # Cache for 1 minute
    if r:
        r.setex(cache_key, 60, json.dumps(result))
    
    return result

@app.get("/api/deals")
def get_current_deals(tier: str = 'free'):
    """Get current best deals - tiered access"""
    
    # Try Redis cache
    r = get_redis()
    cache_key = f'deals:{tier}'
    if r:
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
    
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
        visible_deals = all_deals[:3]
        total_savings = sum(d['savings'] for d in all_deals)
        
        result = {
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
        result = {
            'scan_time': datetime.now().isoformat(),
            'tier': tier,
            'deals_shown': len(all_deals),
            'deals_total': len(all_deals),
            'deals': all_deals,
            'bonus': 'AI predictions active' if tier == 'pro' else None
        }
    
    else:
        return {'error': 'Invalid tier'}
    
    # Cache for 30 seconds
    if r:
        r.setex(cache_key, 30, json.dumps(result))
    
    return result

@app.get("/api/ai/predict/{perfume_id}")
def predict_price(perfume_id: str, user_id: str):
    """AI price prediction - Premium+ only"""
    if not check_tier_access(user_id, 'premium'):
        return {
            'error': 'Premium feature',
            'upgrade_url': '/upgrade',
            'message': 'AI predictions require Premium subscription'
        }
    
    return {
        'perfume_id': perfume_id,
        'current_price': 175.00,
        'predicted_drop': 155.00,
        'confidence': 0.78,
        'predicted_date': '2025-03-15',
        'recommendation': 'WAIT - Price likely to drop in 2 weeks'
    }

@app.get("/api/ai/recommendations/{user_id}")
def get_recommendations(user_id: str):
    """Personalized recommendations - Premium+ only"""
    if not check_tier_access(user_id, 'premium'):
        return {
            'error': 'Premium feature',
            'upgrade_url': '/upgrade',
            'message': 'Personalized recommendations require Premium subscription'
        }
    
    return {
        'recommendations': [
            {
                'perfume': 'Creed Aventus',
                'reason': 'Based on your interest in PDM Layton',
                'deal_price': 175.00,
                'match_score': 0.92
            }
        ],
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
    
    return {
        'opportunities': [
            {
                'perfume': 'Creed Aventus 100ml',
                'buy_market': 'Poland',
                'buy_price': 150.00,
                'sell_market': 'UK',
                'sell_price': 220.00,
                'profit': 70.00,
                'roi': '47%'
            }
        ],
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
    
    return {
        'perfume': perfume_name,
        'mentions_30d': 15420,
        'sentiment': 'bullish',
        'trending': True,
        'prediction': 'Price may rise due to demand'
    }

@app.post("/api/users")
def create_user(user: UserCreate):
    """Create new user"""
    import uuid
    user_id = str(uuid.uuid4())
    
    conn = get_db_conn()
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO users (id, email, country, tier)
            VALUES (%s, %s, %s, %s)
        ''', (user_id, user.email, user.country, user.tier))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'user_id': user_id,
            'email': user.email,
            'tier': user.tier
        }
    except psycopg2.IntegrityError:
        conn.close()
        raise HTTPException(400, "Email already exists")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    status = {'status': 'ok', 'time': datetime.now().isoformat()}
    
    # Check PostgreSQL
    try:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('SELECT 1')
        conn.close()
        status['postgres'] = 'connected'
    except Exception as e:
        status['postgres'] = f'error: {str(e)}'
    
    # Check Redis
    try:
        r = get_redis()
        if r:
            r.ping()
            status['redis'] = 'connected'
        else:
            status['redis'] = 'not available'
    except Exception as e:
        status['redis'] = f'error: {str(e)}'
    
    return status

@app.get("/api/stats")
def get_stats():
    """Get API statistics"""
    conn = get_db_conn()
    c = conn.cursor()
    
    stats = {}
    
    # User count
    c.execute('SELECT COUNT(*) FROM users')
    stats['total_users'] = c.fetchone()[0]
    
    # Alerts count
    c.execute('SELECT COUNT(*) FROM price_alerts')
    stats['total_alerts'] = c.fetchone()[0]
    
    # Active alerts
    c.execute("SELECT COUNT(*) FROM price_alerts WHERE status = 'active'")
    stats['active_alerts'] = c.fetchone()[0]
    
    # Price history count
    c.execute('SELECT COUNT(*) FROM price_history')
    stats['price_records'] = c.fetchone()[0]
    
    conn.close()
    
    return stats

if __name__ == '__main__':
    import uvicorn
    print("🚀 Starting Olfex API...")
    print("📊 PostgreSQL + Redis Enabled")
    print("🔧 Endpoints:")
    print("  GET  /api/perfumes")
    print("  GET  /api/perfumes/{id}/prices")
    print("  POST /api/alerts")
    print("  GET  /api/deals")
    print("  GET  /health")
    
    # Initialize database
    init_db()
    
    uvicorn.run(app, host='0.0.0.0', port=8000)
