-- Fix RLS policy for personal_access_tokens table
-- Run this in Supabase SQL Editor

-- First, drop the existing policies to start fresh
DROP POLICY IF EXISTS "Users can manage their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can insert their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can update their own tokens" ON personal_access_tokens;
DROP POLICY IF EXISTS "Users can delete their own tokens" ON personal_access_tokens;

-- Create separate policies for each operation
-- Policy for INSERT (allow users to create their own tokens)
CREATE POLICY "Users can insert their own tokens" ON personal_access_tokens
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Policy for SELECT (allow users to view their own tokens)
CREATE POLICY "Users can select their own tokens" ON personal_access_tokens
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Policy for UPDATE (allow users to update their own tokens)
CREATE POLICY "Users can update their own tokens" ON personal_access_tokens
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Policy for DELETE (allow users to delete their own tokens)
CREATE POLICY "Users can delete their own tokens" ON personal_access_tokens
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Verify RLS is enabled
ALTER TABLE personal_access_tokens ENABLE ROW LEVEL SECURITY;

-- Test the policies by checking if we can see the table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'personal_access_tokens'
ORDER BY ordinal_position;
