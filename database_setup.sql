-- Personal Access Tokens table (simplified for one token per user)
CREATE TABLE IF NOT EXISTS personal_access_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE, -- SHA-256 hash of the actual token
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_pat_user_id ON personal_access_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_pat_token_hash ON personal_access_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_pat_active ON personal_access_tokens(is_active) WHERE is_active = TRUE;

-- RLS (Row Level Security) policies
ALTER TABLE personal_access_tokens ENABLE ROW LEVEL SECURITY;

-- Users can only see their own tokens
CREATE POLICY "Users can view own tokens" ON personal_access_tokens
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own tokens
CREATE POLICY "Users can insert own tokens" ON personal_access_tokens
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own tokens
CREATE POLICY "Users can update own tokens" ON personal_access_tokens
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own tokens
CREATE POLICY "Users can delete own tokens" ON personal_access_tokens
    FOR DELETE USING (auth.uid() = user_id);
