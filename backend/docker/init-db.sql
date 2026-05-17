-- ============================================================
-- SAR Irrigation Scheduling System — Database Initialization
-- Run automatically by PostgreSQL container on first start
-- ============================================================

-- Enable PostGIS extension for spatial data support
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'SAR Irrigation database initialized with PostGIS support';
END $$;
