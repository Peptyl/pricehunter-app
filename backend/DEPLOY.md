# PriceHunter Backend - Deployment Guide

## Overview
FastAPI backend with Firebase, Clerk authentication, and RevenueCat subscriptions.

## Quick Deploy to Render

1. **Fork/Clone the repo**: https://github.com/Peptyl/pricehunter-app

2. **Click Deploy to Render**:
   [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

3. **Set Environment Variables** in Render Dashboard:
   ```
   FIREBASE_API_KEY=AIzaSyDUFIFFPRLhUy2IfT5BDCKqbZsGphYWL2Y
   CLERK_PUBLISHABLE_KEY=pk_test_YWRhcHRlZC1lbGYtMjMuY2xlcmsuYWNjb3VudHMuZGV2JA
   CLERK_SECRET_KEY=sk_test_YOUR_SECRET_KEY_FROM_CLERK_DASHBOARD
   REVENUECAT_API_KEY=sk_funIsfnYUqsOUzcVbQmHwncNpqBQw
   ```

4. **Deploy** - Render will automatically provision PostgreSQL and Redis.

## API Endpoints

### Public
- `GET /` - API info
- `GET /health` - Health check
- `GET /api/perfumes` - List perfumes

### Protected (requires Clerk JWT)
- `GET /api/auth/me` - Current user
- `GET /api/deals` - Get deals (tiered by subscription)
- `GET /api/subscriptions/status` - Subscription status
- `GET /api/subscriptions/offerings` - Available plans
- `POST /api/alerts` - Create price alert
- `GET /api/alerts` - List user alerts

### Webhooks
- `POST /api/auth/webhook` - Clerk user sync
- `POST /api/subscriptions/webhook` - RevenueCat events

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | No | Server port (default: 8000) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | No | Redis connection string |
| `FIREBASE_API_KEY` | Yes | Firebase API key |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | No | Firebase service account JSON |
| `CLERK_PUBLISHABLE_KEY` | Yes | Clerk public key |
| `CLERK_SECRET_KEY` | Yes | Clerk secret key |
| `REVENUECAT_API_KEY` | Yes | RevenueCat secret key |
| `REVENUECAT_PROJECT_ID` | No | RevenueCat project ID |

## Mobile App Integration

### iOS (Swift)
```swift
// 1. Configure Clerk
Clerk.configure(publishableKey: "pk_test_...")

// 2. Get JWT token
let token = try await Clerk.shared.session?.getToken()

// 3. Call API
var request = URLRequest(url: URL(string: "https://your-api.com/api/deals")!)
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
let (data, _) = try await URLSession.shared.data(for: request)
```

### RevenueCat Setup
```swift
// Configure RevenueCat
Purchases.configure(withAPIKey: "appl_...", appUserID: clerkUserId)

// Get offerings
let offerings = try await Purchases.shared.offerings()
```

## Testing

```bash
# Health check
curl https://your-api.com/health

# Get deals (requires auth token)
curl -H "Authorization: Bearer YOUR_CLERK_JWT" \
  https://your-api.com/api/deals
```

## Local Development

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Server runs at http://localhost:8000
