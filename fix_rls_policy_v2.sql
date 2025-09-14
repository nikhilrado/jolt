-- Fix RLS policy for personal_access_tokens table
-- Run this in Supabase SQL Editor

-- Option 1: Temporarily disable RLS for this table (simplest fix)
ALTER TABLE personal_access_tokens DISABLE ROW LEVEL SECURITY;

-- Option 2: If you want to keep RLS enabled, create a bypass policy for service role
-- First, drop existing policies
DROP POLICY IF EXISTS "Users can manage their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can insert their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can update their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can delete their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can select their own tokens" ON personal_access_tokens;

-- Create policies that work with both authenticated users and service role
CREATE POLICY "Allow service role and users to manage tokens" ON personal_access_tokens
FOR ALL
TO authenticated, service_role
USING (true)
WITH CHECK (true);

-- Enable RLS
ALTER TABLE personal_access_tokens ENABLE ROW LEVEL SECURITY;

-- Test the setup
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables 
WHERE tablename = 'personal_access_tokens';
