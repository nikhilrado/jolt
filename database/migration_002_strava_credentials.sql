-- Migration to add Strava credentials storage
-- This table will store Strava OAuth tokens for each user

CREATE TABLE IF NOT EXISTS strava_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    athlete_id BIGINT NOT NULL,
    athlete_data JSONB, -- Store athlete profile data
    scope TEXT, -- Store granted scopes (e.g., "read,activity:read_all")
    last_activity_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_id BIGINT, -- Track the latest activity we've seen
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_strava_user_id ON strava_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_strava_athlete_id ON strava_credentials(athlete_id);
CREATE INDEX IF NOT EXISTS idx_strava_active ON strava_credentials(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_strava_expires_at ON strava_credentials(expires_at);

-- RLS (Row Level Security) policies
ALTER TABLE strava_credentials ENABLE ROW LEVEL SECURITY;

-- Users can only see their own credentials
CREATE POLICY "Users can view own strava credentials" ON strava_credentials
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own credentials
CREATE POLICY "Users can insert own strava credentials" ON strava_credentials
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own credentials
CREATE POLICY "Users can update own strava credentials" ON strava_credentials
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own credentials
CREATE POLICY "Users can delete own strava credentials" ON strava_credentials
    FOR DELETE USING (auth.uid() = user_id);

-- Create a table to track activity notifications/messages
CREATE TABLE IF NOT EXISTS activity_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    strava_activity_id BIGINT NOT NULL,
    activity_type TEXT NOT NULL,
    activity_name TEXT,
    activity_data JSONB,
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for activity notifications
CREATE INDEX IF NOT EXISTS idx_activity_notifications_user_id ON activity_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_notifications_strava_id ON activity_notifications(strava_activity_id);
CREATE INDEX IF NOT EXISTS idx_activity_notifications_sent ON activity_notifications(notification_sent);

-- RLS for activity notifications
ALTER TABLE activity_notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own activity notifications" ON activity_notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own activity notifications" ON activity_notifications
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own activity notifications" ON activity_notifications
    FOR UPDATE USING (auth.uid() = user_id);
