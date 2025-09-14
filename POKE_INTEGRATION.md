# 📱 Poke Integration for Jolt

## Overview
Jolt now integrates with **Poke** to send personalized messages to users after they complete runs. This creates an interactive feedback loop where users can share their thoughts about their workouts.

## How It Works

### 🔄 **Real-time Flow:**
1. **User completes run** → Strava detects activity
2. **Strava webhook** → Jolt receives notification instantly
3. **Webhook calls `run_complete()`** → Activity processing
4. **Poke message sent** → "How did your 5km run feel today? 🏃‍♂️"
5. **User responds** → Direct feedback via Poke
6. **Data stored** → Responses tracked for insights

## 🏗️ **Architecture**

### **Database Tables:**
- **`poke_credentials`** - Stores user API keys (separate from auth.users)
- **`poke_messages`** - Tracks all messages sent and responses

### **Key Components:**
- **`PokeCredentialsManager`** - Manages API key storage/retrieval
- **`PokeService`** - Handles Poke API communication  
- **`StravaWebhookManager`** - Integrates Poke into webhook flow
- **UI Routes** - `/poke-settings` for key management

### **Security:**
- ✅ **Separate credentials table** (doesn't modify auth.users)
- ✅ **Row Level Security** (users only see their own data)
- ✅ **API key validation** before storage
- ✅ **Service role access** for webhook processing

## 📋 **Features**

### **For Users:**
- **Easy setup** - Add Poke API key via settings page
- **Test functionality** - Send test message to verify connection
- **Message history** - View recent Poke messages sent
- **Remove anytime** - Deactivate integration easily

### **For Developers:**
- **Webhook integration** - Automatic message sending
- **Response tracking** - Store user feedback
- **Analytics ready** - Message data for insights
- **Error handling** - Graceful failures

## 🎯 **User Experience**

### **Setup Process:**
1. Go to **Settings → Poke Settings**
2. Get API key from [poke.com/settings/advanced](https://poke.com/settings/advanced)
3. Enter API key and test connection
4. Receive instant test message confirmation

### **Daily Usage:**
1. Complete run (any Strava activity)
2. Receive Poke message within seconds
3. Reply with thoughts/feelings about the run
4. Data is tracked for future insights

## 📊 **Message Examples**

### **Distance-based:**
> "🏃‍♂️ Great job on your 5.2km run in 28:15! How did it feel? Any thoughts on your performance today?"

### **Activity-based:**
> "🏃‍♂️ Nice work on 'Morning Tempo Run'! How did your run go today? How are you feeling?"

## 🔌 **API Integration**

### **Poke API Usage:**
```python
# Send message
response = requests.post(
    'https://poke.com/api/v1/inbound-sms/webhook',
    headers={'Authorization': f'Bearer {api_key}'},
    json={'message': message_text}
)
```

### **Database Schema:**
```sql
-- Store API keys
CREATE TABLE poke_credentials (
    user_id UUID REFERENCES auth.users(id),
    api_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true
);

-- Track messages
CREATE TABLE poke_messages (
    user_id UUID REFERENCES auth.users(id),
    strava_activity_id BIGINT,
    message_text TEXT,
    poke_response JSONB,
    response_received BOOLEAN DEFAULT false
);
```

## 🚀 **Future Enhancements**

### **Phase 2:**
- **Response analysis** - NLP on user feedback
- **Personalized messages** - Adapt based on history
- **Mood tracking** - Correlate responses with performance

### **Phase 3:**
- **Training recommendations** - Based on feedback patterns
- **Social features** - Share insights with friends
- **AI coaching** - Personalized advice from responses

## 📚 **Usage Guide**

### **For New Users:**
1. Connect Strava account
2. Visit Poke Settings
3. Add API key and test
4. Complete a run to receive first message

### **For Existing Users:**
1. Automatic - messages sent after each activity
2. Check message history in Poke Settings
3. Update/remove API key anytime

---

🎉 **Poke integration provides instant, personalized feedback after every run, creating a more engaging and insightful training experience!**
