-- Reggie - AI Regulations Co-Pilot Database Initialization
-- This script sets up the initial database schema and security settings

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS esg_copilot;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set default schema
SET search_path TO esg_copilot, public;

-- Create custom types
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('admin', 'user', 'readonly');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_status') THEN
        CREATE TYPE document_status AS ENUM ('processing', 'completed', 'failed', 'deleted');
    END IF;
END
$$;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create sessions table for session management
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    status document_status DEFAULT 'processing',
    upload_path TEXT NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create document_chunks table for ChromaDB integration
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding_id VARCHAR(255), -- ChromaDB ID reference
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_conversations table
CREATE TABLE IF NOT EXISTS chat_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create analytics tables
CREATE TABLE IF NOT EXISTS analytics.usage_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    dimensions JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics.api_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    request_size BIGINT DEFAULT 0,
    response_size BIGINT DEFAULT 0,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_id ON document_chunks(embedding_id);

CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_id ON chat_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_created_at ON chat_conversations(created_at);

CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_generated_at ON reports(generated_at);

CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON audit.activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON audit.activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON audit.activity_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_usage_metrics_name ON analytics.usage_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_usage_metrics_recorded_at ON analytics.usage_metrics(recorded_at);

CREATE INDEX IF NOT EXISTS idx_api_requests_endpoint ON analytics.api_requests(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_requests_user_id ON analytics.api_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_api_requests_created_at ON analytics.api_requests(created_at);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_chat_conversations_updated_at ON chat_conversations;
CREATE TRIGGER update_chat_conversations_updated_at
    BEFORE UPDATE ON chat_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function for session cleanup
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create function for metrics aggregation
CREATE OR REPLACE FUNCTION aggregate_daily_metrics()
RETURNS void AS $$
BEGIN
    -- Aggregate API request metrics
    INSERT INTO analytics.usage_metrics (metric_name, metric_value, dimensions, recorded_at)
    SELECT 
        'daily_api_requests',
        COUNT(*),
        jsonb_build_object(
            'date', DATE(created_at),
            'endpoint', endpoint,
            'method', method
        ),
        DATE(created_at) + INTERVAL '1 day' - INTERVAL '1 second'
    FROM analytics.api_requests
    WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY DATE(created_at), endpoint, method
    ON CONFLICT DO NOTHING;
    
    -- Aggregate user activity metrics
    INSERT INTO analytics.usage_metrics (metric_name, metric_value, dimensions, recorded_at)
    SELECT 
        'daily_active_users',
        COUNT(DISTINCT user_id),
        jsonb_build_object('date', DATE(created_at)),
        DATE(created_at) + INTERVAL '1 day' - INTERVAL '1 second'
    FROM analytics.api_requests
    WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
      AND user_id IS NOT NULL
    GROUP BY DATE(created_at)
    ON CONFLICT DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA esg_copilot TO esg_user;
GRANT USAGE ON SCHEMA analytics TO esg_user;
GRANT USAGE ON SCHEMA audit TO esg_user;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA esg_copilot TO esg_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO esg_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO esg_user;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA esg_copilot TO esg_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analytics TO esg_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO esg_user;

-- Set up row-level security (optional, for multi-tenant scenarios)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_conversations ENABLE ROW LEVEL SECURITY;

-- Create sample admin user (password should be changed in production)
-- Password is 'admin123' hashed with bcrypt
INSERT INTO users (email, hashed_password, full_name, role, is_active)
VALUES (
    'admin@reggie-ai-copilot.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kOQyXVyDO',
    'ESG Copilot Admin',
    'admin',
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Create health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS jsonb AS $$
BEGIN
    RETURN jsonb_build_object(
        'database', 'healthy',
        'timestamp', CURRENT_TIMESTAMP,
        'connections', (SELECT count(*) FROM pg_stat_activity),
        'version', version()
    );
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Reggie - AI Regulations Co-Pilot database initialization completed successfully';
END $$;
