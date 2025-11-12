-- Add sentiment columns to Chat (Postgres-friendly)
ALTER TABLE IF EXISTS Chat
  ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(50),
  ADD COLUMN IF NOT EXISTS sentiment_score DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;

CREATE TABLE IF NOT EXISTS Reports (
  report_id SERIAL PRIMARY KEY,
  session_id INT NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',
  requested_by VARCHAR(100),
  report_md TEXT,
  report_json JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_session ON Reports(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_processed_at ON Chat(processed_at);
