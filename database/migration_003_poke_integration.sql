-- Migration 003: Add Poke API integration
-- Creates poke_credentials table to store user's Poke API keys for sending post-run messages

-- Create table to store Poke API credentials (similar to strava_credentials)
CREATE TABLE IF NOT EXISTS public.poke_credentials (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    api_key TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    test_message_sent BOOLEAN DEFAULT false
);

-- Enable RLS on poke_credentials table
ALTER TABLE public.poke_credentials ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only manage their own Poke credentials
CREATE POLICY "Users can view own poke credentials"
ON public.poke_credentials
FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY "Users can insert own poke credentials"
ON public.poke_credentials
FOR INSERT
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own poke credentials"
ON public.poke_credentials
FOR UPDATE
USING (user_id = auth.uid());

CREATE POLICY "Users can delete own poke credentials"
ON public.poke_credentials
FOR DELETE
USING (user_id = auth.uid());

-- Policy: Service role can manage all poke credentials (for webhook processing)
CREATE POLICY "Service role can manage poke credentials"
ON public.poke_credentials
FOR ALL
USING (true);

-- Grant access to the service role
GRANT ALL ON public.poke_credentials TO service_role;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_poke_credentials_user_id 
ON public.poke_credentials(user_id);

CREATE INDEX IF NOT EXISTS idx_poke_credentials_active 
ON public.poke_credentials(user_id, is_active) 
WHERE is_active = true;

-- Add table to track poke messages sent
CREATE TABLE IF NOT EXISTS public.poke_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    strava_activity_id BIGINT NOT NULL,
    activity_type TEXT NOT NULL,
    activity_name TEXT NOT NULL,
    message_text TEXT NOT NULL,
    poke_response JSONB,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_received BOOLEAN DEFAULT FALSE,
    response_text TEXT,
    response_at TIMESTAMP WITH TIME ZONE
);

-- Enable RLS on poke_messages table
ALTER TABLE public.poke_messages ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own poke messages
CREATE POLICY "Users can view own poke messages"
ON public.poke_messages
FOR SELECT
USING (user_id = auth.uid());

-- Policy: Users can insert their own poke messages
CREATE POLICY "Users can insert own poke messages"
ON public.poke_messages
FOR INSERT
WITH CHECK (user_id = auth.uid());

-- Policy: System can insert poke messages for any user (for webhook processing)
CREATE POLICY "System can insert poke messages"
ON public.poke_messages
FOR INSERT
WITH CHECK (true);

-- Grant access to the service role
GRANT ALL ON public.poke_messages TO service_role;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_poke_messages_user_id 
ON public.poke_messages(user_id);

CREATE INDEX IF NOT EXISTS idx_poke_messages_activity_id 
ON public.poke_messages(strava_activity_id);

CREATE INDEX IF NOT EXISTS idx_poke_messages_sent_at 
ON public.poke_messages(sent_at DESC);

-- Add comment explaining the table
COMMENT ON TABLE public.poke_messages IS 'Tracks Poke messages sent to users about their Strava activities';
