-- Aperture Database Migration Script
-- Version: 1.1
-- Date: 2025-02-14
-- Description: Add new tables for quota usage tracking, free provider quota, and daily cost analysis

-- =============================================================================
-- 1. Quota Usage Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS quota_usage (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    tokens_used BIGINT DEFAULT 0,
    calls_made INT DEFAULT 0,
    cost_incurred DECIMAL(10,4) DEFAULT 0,
    quota_limit BIGINT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for quota_usage table
CREATE INDEX IF NOT EXISTS ix_quota_usage_id ON quota_usage(id);
CREATE INDEX IF NOT EXISTS ix_quota_usage_model_id ON quota_usage(model_id);
CREATE INDEX IF NOT EXISTS ix_quota_usage_period_start ON quota_usage(period_start);
CREATE INDEX IF NOT EXISTS ix_quota_usage_model_period ON quota_usage(model_id, period_type, period_start);

-- =============================================================================
-- 2. Free Provider Quota Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS free_provider_quota (
    id SERIAL PRIMARY KEY,
    provider_id VARCHAR(100) NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    requests_used INT DEFAULT 0,
    tokens_used BIGINT DEFAULT 0,
    daily_limit INT,
    monthly_limit INT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for free_provider_quota table
CREATE INDEX IF NOT EXISTS ix_free_provider_quota_id ON free_provider_quota(id);
CREATE INDEX IF NOT EXISTS ix_free_provider_quota_provider_id ON free_provider_quota(provider_id);
CREATE INDEX IF NOT EXISTS ix_free_provider_quota_date ON free_provider_quota(date);
CREATE UNIQUE INDEX IF NOT EXISTS ix_free_provider_quota_provider_date ON free_provider_quota(provider_id, date);

-- =============================================================================
-- 3. Cost Analysis Daily Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS cost_analysis_daily (
    id SERIAL PRIMARY KEY,
    analysis_date TIMESTAMP WITH TIME ZONE NOT NULL,
    total_cost DECIMAL(10,4) NOT NULL,
    total_tokens BIGINT NOT NULL,
    total_requests INT NOT NULL,
    avg_cost_per_request DECIMAL(10,6),
    cache_hit_rate DECIMAL(5,2),
    cost_savings DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for cost_analysis_daily table
CREATE INDEX IF NOT EXISTS ix_cost_analysis_daily_id ON cost_analysis_daily(id);
CREATE INDEX IF NOT EXISTS ix_cost_analysis_daily_analysis_date ON cost_analysis_daily(analysis_date);

-- Unique constraint on analysis_date
ALTER TABLE cost_analysis_daily ADD CONSTRAINT uq_cost_analysis_daily_date UNIQUE (analysis_date);

-- =============================================================================
-- 4. Additional Indexes for Existing Tables (Performance Optimization)
-- =============================================================================

-- Add composite indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS ix_cost_records_model_timestamp ON cost_records(model_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_cost_records_user_timestamp ON cost_records(user_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_chat_logs_user_created ON chat_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_chat_logs_model_created ON chat_logs(selected_model_id, created_at);

-- =============================================================================
-- 5. Comments for Documentation
-- =============================================================================

COMMENT ON TABLE quota_usage IS 'Tracks quota usage per model over different time periods';
COMMENT ON TABLE free_provider_quota IS 'Tracks daily and monthly usage for free tier providers';
COMMENT ON TABLE cost_analysis_daily IS 'Daily aggregated cost analysis metrics';

COMMENT ON COLUMN quota_usage.period_type IS 'Time period type: daily, weekly, monthly';
COMMENT ON COLUMN quota_usage.quota_limit IS 'Maximum allowed quota for the period';

COMMENT ON COLUMN free_provider_quota.daily_limit IS 'Maximum requests allowed per day';
COMMENT ON COLUMN free_provider_quota.monthly_limit IS 'Maximum requests allowed per month';

COMMENT ON COLUMN cost_analysis_daily.cache_hit_rate IS 'Percentage of requests served from cache';
COMMENT ON COLUMN cost_analysis_daily.cost_savings IS 'Estimated cost savings from caching and optimization';

-- =============================================================================
-- 6. Rollback Script (for reference)
-- =============================================================================

/*
-- To rollback this migration, run:
DROP TABLE IF EXISTS cost_analysis_daily;
DROP TABLE IF EXISTS free_provider_quota;
DROP TABLE IF EXISTS quota_usage;

-- Drop additional indexes
DROP INDEX IF EXISTS ix_cost_records_model_timestamp;
DROP INDEX IF EXISTS ix_cost_records_user_timestamp;
DROP INDEX IF EXISTS ix_chat_logs_user_created;
DROP INDEX IF EXISTS ix_chat_logs_model_created;
*/
