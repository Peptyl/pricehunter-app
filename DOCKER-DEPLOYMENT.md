# Olfex Production Docker Deployment Setup

Complete production-ready Docker deployment configuration for Olfex (formerly PriceHunter).

## Files Created

### 1. **docker-compose.prod.yml** (Main Orchestration)
Production Docker Compose configuration with 6 services:
- **olfex-api**: FastAPI server on port 8000
- **olfex-scraper**: Playwright-based web scraper worker
- **olfex-scheduler**: APScheduler for automated scan cycles
- **postgres**: PostgreSQL 16-alpine for persistent storage
- **redis**: Redis 7-alpine for caching and job queue
- **caddy**: Caddy 2-alpine reverse proxy with automatic HTTPS

Features:
- Service health checks and auto-restart
- Environment variable injection from .env file
- Named volumes for data persistence
- Isolated bridge network for inter-service communication
- Proper depends_on conditions (service_healthy)

### 2. **Dockerfile** (API & Scheduler)
Multi-stage optimized Dockerfile for main application:
- Python 3.11 slim base image (94MB)
- Non-root user (olfex:1000) for security
- Health check endpoint integration
- Layer caching optimization

### 3. **Dockerfile.scraper** (Playwright Worker)
Specialized Dockerfile for scraper workers:
- Installs all Playwright system dependencies
- Pre-installs Chromium browser for headless automation
- Separate requirements for scraper tools
- Optimized for concurrent browser instances

### 4. **Caddyfile** (Reverse Proxy)
Caddy configuration for:
- API subdomain routing (api.olfex.app → :8000)
- Frontend SPA serving (olfex.app)
- Automatic HTTPS/TLS certificates
- Rate limiting (100 req/min for API)
- Cache headers for static assets
- Security headers (HSTS, X-Frame-Options, etc.)
- WWW redirect handling

### 5. **db/init.sql** (306 lines)
Comprehensive PostgreSQL production schema:

**Tables:**
- `products`: Fragrance metadata (brand, size, notes, ratings)
- `retailers`: E-commerce platforms (domain, tier, trust_score)
- `price_scans`: Partitioned price history by month (Mar 2026 - Feb 2027)
- `user_alerts`: Price drop notifications
- `scan_cycles`: Audit logs for scraper runs
- `retailer_health`: Monitoring metrics per retailer
- `alert_triggers`: Alert notification history

**Features:**
- Partition strategy: 12 monthly partitions for price_scans
- Materialized view: best_prices (latest lowest price per product)
- 15+ optimized indexes for query performance
- Foreign keys with CASCADE delete
- Triggers for automatic timestamp updates
- Sample retailer data (Sephora, Douglas, Nykaa, etc.)
- pg_stat_statements and pgcrypto extensions

### 6. **requirements.txt** (42 lines)
Production Python dependencies:
- FastAPI >= 0.104.0
- PostgreSQL: asyncpg, sqlalchemy, psycopg2
- Redis for caching and job queues
- APScheduler for job scheduling
- Beautifulsoup4 + rapidfuzz for web scraping
- Security: cryptography, python-dotenv
- Monitoring: python-json-logger

### 7. **requirements-scraper.txt** (8 lines)
Scraper-specific dependencies:
- playwright >= 1.40.0 (browser automation)
- lxml (XML parsing)
- anyio (async utilities)

### 8. **.env.example** (Complete Configuration Template)
Production-ready environment template with sections:
- Application: OLFEX_ENV, LOG_LEVEL, DEBUG
- Database: DB_PASSWORD, connection pool settings
- Redis: URL, password, database number
- API Server: host, port, workers, reload flag
- Domains: API_DOMAIN, FRONTEND_DOMAIN, CORS_ORIGINS
- Proxy: PROXY_PROVIDER, PROXY_API_KEY
- Scraper: MAX_CONCURRENT_BROWSERS, timeouts
- Scheduler: SCAN_TIMES, TIMEZONE
- Notifications: SLACK_WEBHOOK_URL, SMTP config
- Auth: Supabase credentials, JWT_SECRET
- Data Retention: PRICE_SCAN_RETENTION_DAYS (2 years)
- Feature Flags: alerts, favorites, price history
- Monitoring: Sentry, Prometheus

## Deployment Instructions

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum (8GB+ recommended)
- 20GB disk space for database growth

### Quick Start

1. **Clone and navigate:**
```bash
cd /sessions/intelligent-bold-ptolemy/pricehunter-app
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your values:
# - DB_PASSWORD: Strong random password (openssl rand -hex 32)
# - PROXY_API_KEY: Your residential proxy API key
# - JWT_SECRET: openssl rand -hex 32
# - SLACK_WEBHOOK_URL: Your Slack webhook for alerts
# - SUPABASE credentials for authentication
```

3. **Start services:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

4. **Verify deployment:**
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f olfex-api

# Test API
curl http://localhost:8000/health
```

5. **Access services:**
- API: http://localhost:8000 or https://api.olfex.app
- Frontend: https://olfex.app
- Database: postgresql://olfex:PASSWORD@localhost:5432/olfex
- Redis: redis://localhost:6379

## Database Initialization

The database automatically initializes on first run via docker-entrypoint-initdb.d/init.sql:
- All tables are created automatically
- Monthly partitions for price_scans table
- Materialized view for best prices
- Sample retailer data inserted
- Indexes created for query optimization

## Production Considerations

### Scaling
- **API**: Run multiple olfex-api containers behind Caddy
- **Scraper**: Run 2-3 olfex-scraper instances (MAX_CONCURRENT_BROWSERS=1-2 each)
- **Database**: Use managed PostgreSQL (AWS RDS, DigitalOcean)
- **Redis**: Use managed Redis (AWS ElastiCache, DigitalOcean)

### Monitoring
- **Health Checks**: All services have healthcheck definitions
- **Logs**: Aggregate with ELK, Datadog, or Splunk
- **Metrics**: Enable METRICS_ENABLED=true for Prometheus
- **Errors**: Configure SENTRY_DSN for error tracking

### Security
- Change all default passwords in .env
- Use strong DB_PASSWORD (openssl rand -hex 32)
- Enable SSL/TLS (Caddy does this automatically)
- Restrict Redis access (REDIS_PASSWORD)
- Use environment secrets in production (AWS Secrets Manager, etc.)
- Run containers as non-root user (olfex:1000)

### Backups
- PostgreSQL data: Backup pgdata volume
- Redis data: Backup redisdata volume
- Caddy certificates: Backup caddy_data volume
- Schedule: Daily backups, 30-day retention

### Performance
- **Price Scans Partitioning**: 12-month rolling window
- **Index Strategy**: 15+ optimized indexes
- **Materialized View**: Refresh after each scan cycle
- **Connection Pool**: DB_POOL_SIZE=20, MAX_OVERFLOW=40
- **Cache**: Redis for API responses (1 hour TTL)

## Network Architecture

```
┌─────────────────────────────────────────────┐
│         Internet / Load Balancer            │
└─────────────────────┬───────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
   ┌────▼─────┐            ┌───────▼────┐
   │  Caddy   │            │ Caddy (HA) │
   │  :80/:443│            │ :80/:443   │
   └────┬─────┘            └───────┬────┘
        │                          │
        │    olfex-network         │
        └──────────────┬───────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼────┐       ┌─────▼──────┐    ┌─────▼────┐
│ API    │       │  Scheduler │    │ Scraper  │
│ :8000  │       │ (APSchedul) │    │ (Playwright)
└────────┘       └─────┬──────┘    └────┬─────┘
                       │                 │
                  ┌────┴─────────────────┘
                  │
            ┌─────▼──────┐    ┌──────────┐
            │ PostgreSQL │    │  Redis   │
            │ :5432      │    │ :6379    │
            └────────────┘    └──────────┘
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs olfex-api

# Verify .env file
cat .env | grep -v '^#' | grep -v '^$'

# Check port availability
netstat -tlnp | grep 8000
```

### Database Connection Error
```bash
# Verify PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U olfex -d olfex -c "SELECT version();"

# Check init.sql errors
docker-compose -f docker-compose.prod.yml logs postgres
```

### Scraper Issues
```bash
# Check scraper logs
docker-compose -f docker-compose.prod.yml logs olfex-scraper

# Test browser installation
docker-compose -f docker-compose.prod.yml exec olfex-scraper \
  playwright install-deps chromium
```

### API Health Check Failing
```bash
# Test endpoint directly
curl -v http://localhost:8000/health

# Check if app is starting correctly
docker-compose -f docker-compose.prod.yml logs olfex-api | tail -20
```

## Cleanup

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Remove volumes (WARNING: deletes data!)
docker-compose -f docker-compose.prod.yml down -v

# Prune unused images
docker image prune -a
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy with Docker Compose
        run: |
          docker-compose -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.prod.yml up -d
```

## File Locations Summary

```
/sessions/intelligent-bold-ptolemy/pricehunter-app/
├── docker-compose.prod.yml      # Main orchestration
├── Dockerfile                   # API & scheduler image
├── Dockerfile.scraper           # Scraper worker image
├── Caddyfile                    # Reverse proxy config
├── requirements.txt             # Python dependencies
├── requirements-scraper.txt     # Scraper dependencies
├── .env.example                 # Configuration template
├── .env                         # (Create from .env.example)
└── db/
    └── init.sql                 # Database schema (306 lines)
```

## Version Information

- Python: 3.11
- PostgreSQL: 16-alpine
- Redis: 7-alpine
- Caddy: 2-alpine
- Docker: 20.10+
- Docker Compose: 2.0+

---

For detailed documentation on individual services, see respective configuration files.
