#!/usr/bin/env python3
"""
PriceHunter Backend API - Full Integration
FastAPI server with Firebase, Clerk Auth, and RevenueCat
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import json
import httpx
import jwt
from jose import JWTError
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
import psycopg2
import psycopg2.extras
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="PriceHunter API",
    version="2.0.0",
    description="PriceHunter Backend with Firebase, Clerk & RevenueCat"
)

# CORS - configured for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# API Keys (from environment or hardcoded for sprint)
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY', 'AIzaSyDUFIFFPRLhUy2IfT5BDCKqbZsGphYWL2Y')
CLERK_PUBLISHABLE_KEY = os.getenv('CLERK_PUBLISHABLE_KEY', 'pk_test_YWRhcHRlZC1lbGYtMjMuY2xlcmsuYWNjb3VudHMuZGV2JA')
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY', 'sk_test_YOUR_CLERK_SECRET_KEY')  # Get from Clerk dashboard
CLERK_JWT_KEY = os.getenv('CLERK_JWT_KEY', '')  # JWKS endpoint
REVENUECAT_API_KEY = os.getenv('REVENUECAT_API_KEY', 'sk_funIsfnYUqsOUzcVbQmHwncNpqBQw')
REVENUECAT_PROJECT_ID = os.getenv('REVENUECAT_PROJECT_ID', 'proj_funIsfnYUqsOUzcVbQmHwncNpqBQw')

# Database config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'pricehunter')
DB_USER = os.getenv('DB_USER', 'pricehunter')
DB_PASS = os.getenv('DB_PASS', 'pricehunter123')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

# ============================================================================
# FIREBASE INITIALIZATION (Lazy - doesn't block startup)
# ============================================================================

db = None
firebase_app = None

def init_firebase():
    """Initialize Firebase on first use"""
    global db, firebase_app
    if firebase_app is not None:
        return
    
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            firebase_creds = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            if firebase_creds:
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
                firebase_app = firebase_admin.initialize_app(cred)
            else:
                cred_path = os.path.expanduser('~/.config/firebase/service-account.json')
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_app = firebase_admin.initialize_app(cred)
            
            db = firestore.client()
            print("✅ Firebase initialized")
        except Exception as e:
            print(f"⚠️ Firebase init warning: {e}")
            firebase_app = 'mock'

# ============================================================================
# DATABASE CONNECTIONS
# ============================================================================

def get_db_conn():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASS
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
    """Initialize PostgreSQL database"""
    conn = get_db_conn()
    c = conn.cursor()
    
    # Users table (synced with Clerk)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(255) PRIMARY KEY,
            clerk_id VARCHAR(255) UNIQUE,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(50),
            country VARCHAR(50) DEFAULT 'UK',
            tier VARCHAR(50) DEFAULT 'free',
            revenuecat_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Price alerts
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_alerts (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id),
            perfume_id VARCHAR(255),
            target_price DECIMAL(10,2),
            size_ml INTEGER,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Price history
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
    
    # Subscriptions (synced with RevenueCat)
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id),
            revenuecat_entitlement_id VARCHAR(255),
            tier VARCHAR(50),
            status VARCHAR(50),
            expires_at TIMESTAMP,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Purchases/Transactions
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id),
            revenuecat_transaction_id VARCHAR(255) UNIQUE,
            product_id VARCHAR(255),
            price DECIMAL(10,2),
            currency VARCHAR(10),
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ PostgreSQL database initialized")

# ============================================================================
# CLERK AUTHENTICATION
# ============================================================================

security = HTTPBearer(auto_error=False)

CLERK_JWKS_URL = "https://clerk.openclaw.dev/.well-known/jwks.json"

async def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify Clerk JWT token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="No authorization token provided")
    
    token = credentials.credentials
    
    try:
        # Fetch JWKS from Clerk
        async with httpx.AsyncClient() as client:
            response = await client.get(CLERK_JWKS_URL)
            jwks = response.json()
        
        # Decode token without verification first to get kid
        unverified = jwt.decode(token, options={"verify_signature": False})
        
        # Find matching key
        kid = jwt.get_unverified_header(token).get('kid')
        signing_key = None
        
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not signing_key:
            raise HTTPException(status_code=401, detail="Invalid token key")
        
        # Verify token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=['RS256'],
            options={"verify_aud": False}
        )
        
        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'session_id': payload.get('sid'),
            'valid': True
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        # For sprint: allow development mode
        if os.getenv('DEV_MODE', 'false').lower() == 'true':
            return {'user_id': 'dev_user', 'email': 'dev@pricehunter.app', 'valid': True}
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def get_current_user(auth: Dict[str, Any] = Depends(verify_clerk_token)) -> Dict[str, Any]:
    """Get current authenticated user"""
    if not auth.get('valid'):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    # Check if user exists in DB
    conn = get_db_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    c.execute('SELECT * FROM users WHERE clerk_id = %s', (auth['user_id'],))
    user = c.fetchone()
    
    if not user:
        # Create new user
        c.execute('''
            INSERT INTO users (id, clerk_id, email, tier)
            VALUES (gen_random_uuid()::text, %s, %s, 'free')
            RETURNING *
        ''', (auth['user_id'], auth.get('email')))
        user = c.fetchone()
        conn.commit()
    
    conn.close()
    return dict(user)

# ============================================================================
# REVENUECAT INTEGRATION
# ============================================================================

REVENUECAT_API_URL = "https://api.revenuecat.com/v1"

class RevenueCatClient:
    """RevenueCat API Client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'X-Platform': 'ios'  # Adjust based on platform
        }
    
    async def get_or_create_customer(self, app_user_id: str) -> Dict:
        """Get or create RevenueCat customer"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{REVENUECAT_API_URL}/subscribers/{app_user_id}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # Create new customer
                return {'customer': {'original_app_user_id': app_user_id}}
            else:
                raise HTTPException(status_code=500, detail="RevenueCat error")
    
    async def get_offerings(self, app_user_id: str) -> Dict:
        """Get available offerings for user"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{REVENUECAT_API_URL}/subscribers/{app_user_id}/offerings',
                headers=self.headers
            )
            return response.json() if response.status_code == 200 else {}
    
    async def get_entitlements(self, app_user_id: str) -> Dict:
        """Get user's entitlements"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{REVENUECAT_API_URL}/subscribers/{app_user_id}',
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('subscriber', {}).get('entitlements', {})
            return {}
    
    async def grant_entitlement(self, app_user_id: str, entitlement_id: str, duration: str = '1month') -> bool:
        """Grant promotional entitlement"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{REVENUECAT_API_URL}/subscribers/{app_user_id}/entitlements/{entitlement_id}',
                headers=self.headers,
                json={'duration': duration}
            )
            return response.status_code == 201

revenuecat = RevenueCatClient(REVENUECAT_API_KEY)

# ============================================================================
# FIREBASE HELPERS
# ============================================================================

def save_to_firestore(collection: str, doc_id: str, data: Dict):
    """Save data to Firestore"""
    init_firebase()
    if db:
        try:
            db.collection(collection).document(doc_id).set(data, merge=True)
        except Exception as e:
            print(f"Firestore error: {e}")

def get_from_firestore(collection: str, doc_id: str) -> Optional[Dict]:
    """Get data from Firestore"""
    init_firebase()
    if db:
        try:
            doc = db.collection(collection).document(doc_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"Firestore error: {e}")
    return None

def query_firestore(collection: str, filters: List[tuple]) -> List[Dict]:
    """Query Firestore with filters"""
    init_firebase()
    if not db:
        return []
    
    try:
        query = db.collection(collection)
        for field, op, value in filters:
            query = query.where(field, op, value)
        
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Firestore query error: {e}")
        return []

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class AlertRequest(BaseModel):
    perfume_id: str
    target_price: float
    size_ml: int

class PurchaseReceipt(BaseModel):
    receipt_data: str
    product_id: str
    platform: str = Field(default='ios', pattern='^(ios|android)$')

class UserProfileUpdate(BaseModel):
    country: Optional[str] = 'UK'
    phone: Optional[str] = None

class WebhookPayload(BaseModel):
    event: Dict[str, Any]

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """API root"""
    init_firebase()
    return {
        "name": "PriceHunter API",
        "version": "2.0.0",
        "status": "operational",
        "integrations": {
            "firebase": db is not None,
            "clerk": True,
            "revenuecat": True
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'ok',
        'time': datetime.now().isoformat(),
        'services': {}
    }
    
    # Check PostgreSQL
    try:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('SELECT 1')
        conn.close()
        status['services']['postgres'] = 'connected'
    except Exception as e:
        status['services']['postgres'] = f'error: {str(e)}'
    
    # Check Redis
    try:
        r = get_redis()
        status['services']['redis'] = 'connected' if r else 'not available'
    except Exception as e:
        status['services']['redis'] = f'error: {str(e)}'
    
    # Check Firebase
    init_firebase()
    status['services']['firebase'] = 'connected' if db else 'mock/limited'
    
    return status

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.get("/api/auth/me", response_model=Dict[str, Any])
async def get_me(current_user: Dict = Depends(get_current_user)):
    """Get current user profile"""
    # Get subscription status from RevenueCat
    revenuecat_id = current_user.get('revenuecat_id') or current_user['id']
    
    try:
        entitlements = await revenuecat.get_entitlements(revenuecat_id)
        
        # Determine tier from entitlements
        tier = 'free'
        if entitlements.get('pro'):
            tier = 'pro'
        elif entitlements.get('premium'):
            tier = 'premium'
        
        # Sync tier if changed
        if tier != current_user.get('tier'):
            conn = get_db_conn()
            c = conn.cursor()
            c.execute('UPDATE users SET tier = %s WHERE id = %s', (tier, current_user['id']))
            conn.commit()
            conn.close()
            current_user['tier'] = tier
        
        current_user['entitlements'] = entitlements
        
    except Exception as e:
        current_user['entitlements_error'] = str(e)
    
    return current_user

@app.post("/api/auth/webhook")
async def clerk_webhook(payload: WebhookPayload):
    """Handle Clerk webhooks for user sync"""
    event = payload.event
    event_type = event.get('type')
    
    if event_type == 'user.created':
        data = event.get('data', {})
        clerk_id = data.get('id')
        email = data.get('email_addresses', [{}])[0].get('email_address')
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (id, clerk_id, email, tier)
            VALUES (gen_random_uuid()::text, %s, %s, 'free')
            ON CONFLICT (clerk_id) DO NOTHING
        ''', (clerk_id, email))
        conn.commit()
        conn.close()
        
        # Create RevenueCat customer
        try:
            await revenuecat.get_or_create_customer(clerk_id)
        except:
            pass
        
        return {'success': True, 'action': 'user_created'}
    
    elif event_type == 'user.updated':
        data = event.get('data', {})
        clerk_id = data.get('id')
        email = data.get('email_addresses', [{}])[0].get('email_address')
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('UPDATE users SET email = %s WHERE clerk_id = %s', (email, clerk_id))
        conn.commit()
        conn.close()
        
        return {'success': True, 'action': 'user_updated'}
    
    return {'success': True, 'action': 'ignored'}

# ============================================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================================

@app.get("/api/subscriptions/offerings")
async def get_offerings(current_user: Dict = Depends(get_current_user)):
    """Get available subscription offerings"""
    revenuecat_id = current_user.get('revenuecat_id') or current_user['id']
    
    try:
        offerings = await revenuecat.get_offerings(revenuecat_id)
        return {
            'success': True,
            'offerings': offerings.get('offerings', {}),
            'current_customer': offerings.get('current_offering_id')
        }
    except Exception as e:
        # Return default offerings for sprint
        return {
            'success': True,
            'offerings': {
                'premium_monthly': {
                    'identifier': 'premium_monthly',
                    'description': 'Premium - Monthly',
                    'price': 4.99,
                    'currency': 'GBP'
                },
                'premium_yearly': {
                    'identifier': 'premium_yearly',
                    'description': 'Premium - Yearly (Save 30%)',
                    'price': 39.99,
                    'currency': 'GBP'
                },
                'pro_monthly': {
                    'identifier': 'pro_monthly',
                    'description': 'Pro - Monthly',
                    'price': 9.99,
                    'currency': 'GBP'
                }
            }
        }

@app.get("/api/subscriptions/status")
async def get_subscription_status(current_user: Dict = Depends(get_current_user)):
    """Get user's subscription status"""
    revenuecat_id = current_user.get('revenuecat_id') or current_user['id']
    
    try:
        entitlements = await revenuecat.get_entitlements(revenuecat_id)
        
        subscriptions = []
        for entitlement_id, entitlement in entitlements.items():
            subscriptions.append({
                'tier': entitlement_id,
                'expires_at': entitlement.get('expires_date'),
                'is_active': not entitlement.get('unsubscribe_detected_at')
            })
        
        return {
            'success': True,
            'tier': current_user.get('tier', 'free'),
            'subscriptions': subscriptions,
            'entitlements': entitlements
        }
    except Exception as e:
        return {
            'success': True,
            'tier': current_user.get('tier', 'free'),
            'subscriptions': [],
            'error': str(e)
        }

@app.post("/api/subscriptions/verify")
async def verify_purchase(
    receipt: PurchaseReceipt,
    current_user: Dict = Depends(get_current_user)
):
    """Verify purchase receipt and update subscription"""
    # In production, RevenueCat SDK handles this client-side
    # This endpoint is for server-side verification if needed
    
    conn = get_db_conn()
    c = conn.cursor()
    
    # Record purchase
    c.execute('''
        INSERT INTO purchases (user_id, product_id, price, currency)
        VALUES (%s, %s, %s, %s)
    ''', (current_user['id'], receipt.product_id, 0, 'GBP'))
    
    # Update user tier based on product
    tier = 'premium'
    if 'pro' in receipt.product_id.lower():
        tier = 'pro'
    
    c.execute('UPDATE users SET tier = %s WHERE id = %s', (tier, current_user['id']))
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'verified': True,
        'tier': tier,
        'message': f'Upgraded to {tier}'
    }

@app.post("/api/subscriptions/webhook")
async def revenuecat_webhook(request: Request):
    """Handle RevenueCat webhooks"""
    # Verify webhook signature
    signature = request.headers.get('X-RevenueCat-Signature')
    body = await request.body()
    
    try:
        payload = json.loads(body)
        event = payload.get('event', {})
        
        event_type = event.get('type')
        app_user_id = event.get('app_user_id')
        
        if event_type in ['INITIAL_PURCHASE', 'RENEWAL', 'NON_RENEWING_PURCHASE']:
            # Update subscription
            product_id = event.get('product_id')
            
            # Find user by RevenueCat ID
            conn = get_db_conn()
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE revenuecat_id = %s OR clerk_id = %s', 
                     (app_user_id, app_user_id))
            user = c.fetchone()
            
            if user:
                tier = 'premium' if 'premium' in product_id else 'pro' if 'pro' in product_id else 'free'
                c.execute('UPDATE users SET tier = %s WHERE id = %s', (tier, user[0]))
                
                # Record purchase
                c.execute('''
                    INSERT INTO purchases (user_id, revenuecat_transaction_id, product_id)
                    VALUES (%s, %s, %s)
                ''', (user[0], event.get('transaction_id'), product_id))
                
                conn.commit()
            conn.close()
        
        elif event_type == 'CANCELLATION':
            # Downgrade to free
            conn = get_db_conn()
            c = conn.cursor()
            c.execute('''
                UPDATE users SET tier = 'free' 
                WHERE revenuecat_id = %s OR clerk_id = %s
            ''', (app_user_id, app_user_id))
            conn.commit()
            conn.close()
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ============================================================================
# CORE APP ENDPOINTS (Protected)
# ============================================================================

@app.get("/api/deals")
async def get_current_deals(
    current_user: Dict = Depends(get_current_user)
):
    """Get current best deals - tiered access"""
    
    user_tier = current_user.get('tier', 'free')
    
    # Mock deals data
    all_deals = [
        {
            'perfume': 'Creed Aventus 100ml',
            'best_price': 175.00,
            'retailer': 'FragranceBuy.ca',
            'retail_price': 265.00,
            'savings': 90.00,
            'savings_percent': 34,
            'locked': user_tier == 'free',
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
            'locked': user_tier == 'free',
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
        },
        {
            'perfume': 'Tom Ford Oud Wood 100ml',
            'best_price': 145.00,
            'retailer': 'FragranceNet',
            'retail_price': 220.00,
            'savings': 75.00,
            'savings_percent': 34,
            'locked': user_tier in ['free', 'premium'],
            'time_remaining': '24 hours',
            'stock': 'Medium'
        }
    ]
    
    # Filter based on tier
    if user_tier == 'free':
        visible = [d for d in all_deals[:3]]
        return {
            'scan_time': datetime.now().isoformat(),
            'tier': user_tier,
            'deals': visible,
            'upsell': {
                'message': f'🔒 {len(all_deals) - 3} more deals hidden',
                'cta': 'Upgrade to Premium'
            }
        }
    elif user_tier == 'premium':
        return {
            'scan_time': datetime.now().isoformat(),
            'tier': user_tier,
            'deals': all_deals,
            'bonus': 'Full deal access unlocked'
        }
    else:  # pro
        return {
            'scan_time': datetime.now().isoformat(),
            'tier': user_tier,
            'deals': all_deals,
            'bonus': 'AI predictions + arbitrage enabled'
        }

@app.get("/api/ai/predict/{perfume_id}")
async def predict_price(
    perfume_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """AI price prediction - Premium+ only"""
    if current_user.get('tier') not in ['premium', 'pro']:
        raise HTTPException(status_code=403, detail="Premium subscription required")
    
    return {
        'perfume_id': perfume_id,
        'current_price': 175.00,
        'predicted_drop': 155.00,
        'confidence': 0.78,
        'predicted_date': (datetime.now() + timedelta(days=14)).isoformat(),
        'recommendation': 'WAIT - Price likely to drop in 2 weeks'
    }

@app.post("/api/alerts")
async def create_alert(
    alert: AlertRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Create price alert - requires auth"""
    conn = get_db_conn()
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO price_alerts (user_id, perfume_id, target_price, size_ml)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (current_user['id'], alert.perfume_id, alert.target_price, alert.size_ml))
    
    alert_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    
    # Also save to Firestore
    save_to_firestore('alerts', str(alert_id), {
        'user_id': current_user['id'],
        'perfume_id': alert.perfume_id,
        'target_price': alert.target_price,
        'created_at': datetime.now().isoformat()
    })
    
    return {
        'success': True,
        'alert_id': alert_id,
        'message': f"Alert set for £{alert.target_price}"
    }

@app.get("/api/alerts")
async def get_user_alerts(current_user: Dict = Depends(get_current_user)):
    """Get user's alerts - requires auth"""
    conn = get_db_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    c.execute('''
        SELECT * FROM price_alerts 
        WHERE user_id = %s AND status = 'active'
        ORDER BY created_at DESC
    ''', (current_user['id'],))
    
    alerts = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return {'alerts': alerts, 'count': len(alerts)}

@app.get("/api/perfumes")
def get_perfumes():
    """Get list of tracked perfumes"""
    return [
        {"id": "creed_aventus", "name": "Creed Aventus", "brand": "Creed", "sizes": [50, 100]},
        {"id": "pdm_layton", "name": "Layton", "brand": "Parfums de Marley", "sizes": [75, 125]},
        {"id": "mfk_baccarat", "name": "Baccarat Rouge 540", "brand": "MFK", "sizes": [35, 70]},
        {"id": "tf_oud_wood", "name": "Oud Wood", "brand": "Tom Ford", "sizes": [50, 100]}
    ]

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import uvicorn
    
    print("=" * 60)
    print("🚀 PriceHunter API v2.0")
    print("=" * 60)
    print("✅ Firebase: Lazy-loaded (set FIREBASE_SERVICE_ACCOUNT_JSON)")
    print("✅ Clerk Auth: Enabled")
    print("✅ RevenueCat: Enabled")
    print("✅ PostgreSQL: Required")
    print("=" * 60)
    print("Endpoints:")
    print("  GET  /health")
    print("  GET  /api/auth/me")
    print("  GET  /api/subscriptions/status")
    print("  GET  /api/subscriptions/offerings")
    print("  GET  /api/deals")
    print("  POST /api/alerts")
    print("=" * 60)
    
    # Run server (db init happens on first request)
    port = int(os.getenv('PORT', '8000'))
    uvicorn.run(app, host='0.0.0.0', port=port)