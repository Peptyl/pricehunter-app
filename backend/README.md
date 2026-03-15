# Olfex Backend API v2.0

Full-featured FastAPI backend with Firebase, Clerk authentication, and RevenueCat subscriptions.

## Features

- ✅ **FastAPI** - Modern, fast Python web framework
- ✅ **Firebase Admin** - Firestore integration (lazy-loaded)
- ✅ **Clerk Auth** - JWT authentication and user management
- ✅ **RevenueCat** - Subscription management and entitlements
- ✅ **PostgreSQL** - Primary database for users, alerts, purchases
- ✅ **Redis** - Caching layer
- ✅ **Tiered Access** - Free/Premium/Pro subscription tiers

## Quick Start

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Server runs at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Key Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /health` | No | Health check |
| `GET /api/perfumes` | No | List all perfumes |
| `GET /api/deals` | Yes | Get deals (tier-based) |
| `POST /api/alerts` | Yes | Create price alert |
| `GET /api/subscriptions/status` | Yes | Subscription status |
| `POST /api/subscriptions/webhook` | No | RevenueCat webhooks |

## Deployment

See [DEPLOY.md](DEPLOY.md) for detailed deployment instructions.

### Quick Deploy to Render

1. Fork this repo
2. Create new Web Service on Render
3. Select "Python" environment
4. Set environment variables from `.env.example`
5. Deploy!

## Testing

```bash
# Run E2E tests
python test_e2e.py http://localhost:8000
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
# Required
DATABASE_URL=postgresql://...
FIREBASE_API_KEY=...
CLERK_PUBLISHABLE_KEY=...
CLERK_SECRET_KEY=...
REVENUECAT_API_KEY=...
```

## Architecture

```
┌─────────────┐      JWT Token       ┌─────────────┐
│  Mobile App │ ────────────────────>│   Backend   │
│  (Clerk)    │                      │  (FastAPI)  │
└─────────────┘                      └──────┬──────┘
                                            │
       ┌────────────────────────────────────┼────────────────────┐
       │                                    │                    │
       ▼                                    ▼                    ▼
  ┌─────────┐                        ┌──────────┐         ┌──────────┐
  │RevenueCat│                       │PostgreSQL│         │ Firebase │
  │(Billing) │                       │ (Data)   │         │(Firestore│
  └─────────┘                        └──────────┘         └──────────┘
```

## License

Private - Olfex App
