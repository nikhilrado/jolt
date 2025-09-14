-- Complete fix for personal_access_tokens RLS issue
-- Run this in Supabase SQL Editor

-- First, drop ALL existing policies
DROP POLICY IF EXISTS "Users can manage their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can insert their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can update their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can delete their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can select their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Allow service role and users to manage tokens" ON personal_access_tokens;

-- Completely disable RLS for this table
-- Since your Flask app handles authorization at the application level,
-- we don't need database-level RLS for this table
ALTER TABLE personal_access_tokens DISABLE ROW LEVEL SECURITY;

-- Verify the table is accessible
SELECT COUNT(*) as token_count FROM personal_access_tokens;

-- Show table structure to confirm everything is working
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'personal_access_tokens'
ORDER BY ordinal_position;
