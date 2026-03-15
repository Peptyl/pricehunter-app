-- Olfex Production Database Schema
-- PostgreSQL 16+ with partitioning and materialized views

-- Create schema
CREATE SCHEMA IF NOT EXISTS olfex;
SET search_path TO olfex;

-- ============================================================================
-- Products Table
-- ============================================================================
CREATE TABLE products (
    id VARCHAR(100) PRIMARY KEY,
    brand VARCHAR(200) NOT NULL,
    name VARCHAR(200) NOT NULL,
    size_ml INTEGER NOT NULL,
    concentration VARCHAR(50),
    typical_retail_gbp DECIMAL(10,2),
    fragrantica_slug VARCHAR(300),
    image_url TEXT,
    notes JSONB,
    accords JSONB,
    ratings JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_updated ON products(updated_at DESC);

-- ============================================================================
-- Retailers Table
-- ============================================================================
CREATE TABLE retailers (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    domain VARCHAR(200) NOT NULL UNIQUE,
    country VARCHAR(10),
    currency VARCHAR(10) DEFAULT 'GBP',
    tier INTEGER DEFAULT 1,
    trust_score INTEGER DEFAULT 100,
    platform VARCHAR(50),
    scraper_config JSONB,
    shipping JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_retailers_active ON retailers(is_active);
CREATE INDEX idx_retailers_domain ON retailers(domain);

-- ============================================================================
-- Price Scans Table (Partitioned by Month)
-- ============================================================================
CREATE TABLE price_scans (
    id BIGSERIAL,
    product_id VARCHAR(100) NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    retailer_id VARCHAR(100) NOT NULL REFERENCES retailers(id) ON DELETE CASCADE,
    price_local DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    price_gbp DECIMAL(10,2) NOT NULL,
    shipping_gbp DECIMAL(10,2) DEFAULT 0,
    vat_gbp DECIMAL(10,2) DEFAULT 0,
    total_landed_gbp DECIMAL(10,2) NOT NULL,
    exchange_rate DECIMAL(10,6),
    in_stock BOOLEAN DEFAULT true,
    confidence DECIMAL(5,2) DEFAULT 100,
    url TEXT,
    scanned_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, scanned_at)
) PARTITION BY RANGE (scanned_at);

-- Create partitions for 12 months ahead (Mar 2026 - Feb 2027)
CREATE TABLE price_scans_2026_03 PARTITION OF price_scans
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

CREATE TABLE price_scans_2026_04 PARTITION OF price_scans
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE TABLE price_scans_2026_05 PARTITION OF price_scans
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE TABLE price_scans_2026_06 PARTITION OF price_scans
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE price_scans_2026_07 PARTITION OF price_scans
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

CREATE TABLE price_scans_2026_08 PARTITION OF price_scans
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');

CREATE TABLE price_scans_2026_09 PARTITION OF price_scans
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

CREATE TABLE price_scans_2026_10 PARTITION OF price_scans
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

CREATE TABLE price_scans_2026_11 PARTITION OF price_scans
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');

CREATE TABLE price_scans_2026_12 PARTITION OF price_scans
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

CREATE TABLE price_scans_2027_01 PARTITION OF price_scans
    FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');

CREATE TABLE price_scans_2027_02 PARTITION OF price_scans
    FOR VALUES FROM ('2027-02-01') TO ('2027-03-01');

-- Indexes on partitions
CREATE INDEX idx_price_scans_product ON price_scans(product_id, scanned_at DESC);
CREATE INDEX idx_price_scans_retailer ON price_scans(retailer_id, scanned_at DESC);
CREATE INDEX idx_price_scans_landed ON price_scans(total_landed_gbp);
CREATE INDEX idx_price_scans_stock ON price_scans(in_stock, scanned_at DESC);

-- ============================================================================
-- Best Prices Materialized View
-- ============================================================================
CREATE MATERIALIZED VIEW best_prices AS
SELECT DISTINCT ON (product_id)
    product_id,
    retailer_id,
    total_landed_gbp,
    price_local,
    currency,
    in_stock,
    url,
    scanned_at
FROM price_scans
WHERE in_stock = true
ORDER BY product_id, total_landed_gbp ASC, scanned_at DESC;

CREATE UNIQUE INDEX idx_best_prices_product ON best_prices(product_id);
CREATE INDEX idx_best_prices_retailer ON best_prices(retailer_id);

-- ============================================================================
-- User Alerts Table
-- ============================================================================
CREATE TABLE user_alerts (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(200) NOT NULL,
    product_id VARCHAR(100) NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    target_price_gbp DECIMAL(10,2) NOT NULL,
    alert_type VARCHAR(50) DEFAULT 'price_drop',
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_alerts_user ON user_alerts(user_id, is_active);
CREATE INDEX idx_user_alerts_product ON user_alerts(product_id);
CREATE INDEX idx_user_alerts_active ON user_alerts(is_active);

-- ============================================================================
-- Scan Cycle Logs
-- ============================================================================
CREATE TABLE scan_cycles (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    products_scanned INTEGER DEFAULT 0,
    retailers_scanned INTEGER DEFAULT 0,
    total_prices_found INTEGER DEFAULT 0,
    anomalies_detected INTEGER DEFAULT 0,
    errors JSONB,
    status VARCHAR(50) DEFAULT 'running'
);

CREATE INDEX idx_scan_cycles_status ON scan_cycles(status);
CREATE INDEX idx_scan_cycles_started ON scan_cycles(started_at DESC);

-- ============================================================================
-- Retailer Health Metrics
-- ============================================================================
CREATE TABLE retailer_health (
    id BIGSERIAL PRIMARY KEY,
    retailer_id VARCHAR(100) NOT NULL REFERENCES retailers(id) ON DELETE CASCADE,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    success_rate DECIMAL(5,2),
    avg_response_ms INTEGER,
    consecutive_failures INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'healthy',
    extraction_method VARCHAR(50)
);

CREATE INDEX idx_retailer_health_retailer ON retailer_health(retailer_id, recorded_at DESC);
CREATE INDEX idx_retailer_health_status ON retailer_health(status);

-- ============================================================================
-- Price Alerts History (for auditing)
-- ============================================================================
CREATE TABLE alert_triggers (
    id BIGSERIAL PRIMARY KEY,
    alert_id BIGINT REFERENCES user_alerts(id) ON DELETE CASCADE,
    user_id VARCHAR(200) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    target_price_gbp DECIMAL(10,2),
    actual_price_gbp DECIMAL(10,2),
    retailer_id VARCHAR(100) NOT NULL,
    triggered_at TIMESTAMPTZ DEFAULT NOW(),
    notification_sent BOOLEAN DEFAULT false
);

CREATE INDEX idx_alert_triggers_user ON alert_triggers(user_id);
CREATE INDEX idx_alert_triggers_triggered ON alert_triggers(triggered_at DESC);

-- ============================================================================
-- Functions
-- ============================================================================

-- Refresh best_prices materialized view concurrently
CREATE OR REPLACE FUNCTION refresh_best_prices()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY best_prices;
END;
$$ LANGUAGE plpgsql;

-- Update product modified timestamp
CREATE OR REPLACE FUNCTION update_product_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update retailer modified timestamp
CREATE OR REPLACE FUNCTION update_retailer_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update user alert timestamp
CREATE OR REPLACE FUNCTION update_alert_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers
-- ============================================================================

CREATE TRIGGER trg_update_product_ts
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION update_product_timestamp();

CREATE TRIGGER trg_update_retailer_ts
BEFORE UPDATE ON retailers
FOR EACH ROW
EXECUTE FUNCTION update_retailer_timestamp();

CREATE TRIGGER trg_update_alert_ts
BEFORE UPDATE ON user_alerts
FOR EACH ROW
EXECUTE FUNCTION update_alert_timestamp();

-- ============================================================================
-- Sample Data (Optional - for testing)
-- ============================================================================

-- Insert sample retailers
INSERT INTO retailers (id, name, domain, country, currency, tier, trust_score, platform) VALUES
    ('sephora-uk', 'Sephora UK', 'sephora.co.uk', 'GB', 'GBP', 1, 95, 'custom'),
    ('douglas-de', 'Douglas Germany', 'douglas.de', 'DE', 'EUR', 1, 92, 'shopify'),
    ('nykaa-in', 'Nykaa India', 'nykaa.com', 'IN', 'INR', 2, 88, 'custom'),
    ('fleur-du-mal', 'Fleur du Mal', 'fleurdumal.com', 'GB', 'GBP', 2, 90, 'custom')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- Performance Tuning
-- ============================================================================

-- Analyze tables
ANALYZE products;
ANALYZE retailers;
ANALYZE price_scans;

-- Enable some useful extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- Row-Level Security (Optional for multi-tenant setup)
-- ============================================================================

-- Uncomment to enable RLS for user_alerts
-- ALTER TABLE user_alerts ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY user_alert_policy ON user_alerts
--     USING (user_id = current_user_id());

-- ============================================================================
-- Retention Policy
-- ============================================================================
-- Note: Run this periodically to archive old data
-- DELETE FROM price_scans WHERE scanned_at < NOW() - INTERVAL '2 years';
-- REINDEX TABLE price_scans;
