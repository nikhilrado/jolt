-- Personal Access Tokens Migration
-- Run this in your Supabase SQL Editor

-- Create the personal_access_tokens table
CREATE TABLE IF NOT EXISTS personal_access_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    scopes TEXT[] DEFAULT ARRAY['read:activities'],
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_pat_user_id ON personal_access_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_pat_token_hash ON personal_access_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_pat_active ON personal_access_tokens(is_active) WHERE is_active = TRUE;

-- Enable Row Level Security
ALTER TABLE personal_access_tokens ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can only see their own tokens
CREATE POLICY "Users can view own tokens" ON personal_access_tokens
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only create tokens for themselves
CREATE POLICY "Users can create own tokens" ON personal_access_tokens
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own tokens
CREATE POLICY "Users can update own tokens" ON personal_access_tokens
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own tokens
CREATE POLICY "Users can delete own tokens" ON personal_access_tokens
    FOR DELETE USING (auth.uid() = user_id);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_personal_access_tokens_updated_at 
    BEFORE UPDATE ON personal_access_tokens 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
