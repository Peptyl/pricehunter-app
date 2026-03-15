# Deployment Guide

**Deploy Olfex backend and mobile apps**

## Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Expo CLI (`npm install -g expo-cli`)
- Accounts: Clerk, RevenueCat, Firebase

## Backend Deployment

### 1. Configure Environment

```bash
cd backend
cp .env.example .env

# Edit .env with your keys:
# CLERK_PUBLISHABLE_KEY=pk_test_...
# REVENUECAT_API_KEY=...
# FIREBASE_CONFIG=...
```

### 2. Start Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Run migrations
python3 -m alembic upgrade head

# Start API
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Verify

```bash
curl http://localhost:8000/health
# Should return: {"status": "ok"}
```

## Mobile App Deployment

### iOS (App Store)

```bash
cd mobile

# Install dependencies
npm install

# Configure app.json with your bundle ID
# "bundleIdentifier": "com.peptyl.olfex"

# Build for production
expo build:ios

# Or EAS Build (recommended)
eas build --platform ios

# Submit to App Store
eas submit --platform ios
```

### Android (Play Store)

```bash
cd mobile

# Install dependencies
npm install

# Configure app.json with your package name
# "package": "com.peptyl.olfex"

# Build for production
expo build:android

# Or EAS Build (recommended)
eas build --platform android

# Submit to Play Store
eas submit --platform android
```

## Environment Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `CLERK_PUBLISHABLE_KEY` | clerk.dev | Auth |
| `REVENUECAT_API_KEY` | revenuecat.com | Payments |
| `FIREBASE_API_KEY` | firebase.google.com | Analytics |
| `DATABASE_URL` | Render/Railway | PostgreSQL |
| `REDIS_URL` | Render/Railway | Caching |

## Production Checklist

- [ ] Environment variables set
- [ ] Database migrated
- [ ] SSL certificate configured
- [ ] CDN for assets (optional)
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] Backup strategy

## Support

- Backend issues: Check logs with `docker-compose logs api`
- Mobile issues: Check Expo dashboard
- Payment issues: Check RevenueCat dashboard
- Auth issues: Check Clerk dashboard
