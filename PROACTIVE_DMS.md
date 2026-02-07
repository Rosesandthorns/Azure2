# Proactive DM Feature

## Overview

The bot can now proactively initiate DM conversations with users it has interacted with before. This feature allows the bot to:
- Follow up on unresolved questions
- Check in with users after periods of inactivity
- Share relevant information based on user interests
- Maintain ongoing relationships

## How It Works

### Background Process

Every 10 seconds, the background loop checks if any users are eligible for a proactive DM:

1. **User Selection**: Reviews all users who have interacted in the last 7 days
2. **Eligibility Check**: Applies multiple filters (see below)
3. **Message Generation**: Creates a contextual, personalized message
4. **Send DM**: Sends the message via Discord
5. **Recording**: Logs the DM in memory and scheduler

### Eligibility Criteria

A user must meet ALL of these criteria to receive a proactive DM:

1. **Feature Enabled**: `enable_proactive_dms: true` in config
2. **Inactivity Period**: Haven't interacted in at least `dm_inactivity_hours` (default: 24 hours)
3. **Cooldown Respected**: Haven't received a proactive DM in the last `dm_cooldown_hours` (default: 12 hours)
4. **Daily Limit**: Haven't exceeded `dm_max_per_user_per_day` (default: 1)
5. **Access Control**: User is allowed to receive DMs (respects whitelist/blacklist)
6. **DMs Enabled**: User hasn't disabled DMs from the bot

## Configuration

### Enable the Feature

In `config.yaml`:

```yaml
scheduler:
  # Existing settings...
  inactivity_minutes: 30
  curiosity_trigger_count: 3
  max_proactive_per_day: 5
  
  # Proactive DM settings
  enable_proactive_dms: true  # Enable the feature
  dm_inactivity_hours: 24     # Wait 24 hours after last interaction
  dm_max_per_user_per_day: 1  # Max 1 proactive DM per user per day
  dm_cooldown_hours: 12       # Wait 12 hours between DMs to same user
```

### Configuration Options Explained

**`enable_proactive_dms`** (boolean, default: `false`)
- Master switch for the entire feature
- Set to `true` to enable proactive DMs

**`dm_inactivity_hours`** (integer, default: `24`)
- How long to wait after a user's last interaction before considering them for a proactive DM
- Lower values = more frequent check-ins
- Higher values = respect user's space more

**`dm_max_per_user_per_day`** (integer, default: `1`)
- Maximum number of proactive DMs a single user can receive per day
- Prevents overwhelming users
- Resets at midnight UTC

**`dm_cooldown_hours`** (integer, default: `12`)
- Minimum time between proactive DMs to the same user
- Additional protection against spam
- Works in conjunction with daily limit

## Use Cases

### 1. Follow-up on Questions

**Scenario**: User asked a question but conversation ended before full resolution

```
User (2 days ago): "How do I learn Python?"
Bot (responding): "Here are some resources..."
[Conversation ends]

[After dm_inactivity_hours]
Bot (proactive DM): "Hey! I remember you were interested in learning 
                     Python. Did you get a chance to try those resources 
                     I mentioned?"
```

### 2. Check-in After Inactivity

**Scenario**: Regular user hasn't been active lately

```
User (last seen 3 days ago): Regular interactions about gaming
[User goes quiet]

[After dm_inactivity_hours]
Bot (proactive DM): "Haven't heard from you in a while! How's your 
                     gaming project going?"
```

### 3. Share Relevant Updates

**Scenario**: Bot learns something relevant to user's interests

```
User's profile: Interested in AI, machine learning
Recent memories: Asked about neural networks

[After dm_inactivity_hours]
Bot (proactive DM): "I came across an interesting development in neural 
                     networks that relates to what we discussed. Want to 
                     hear about it?"
```

## Safety Features

### 1. Respect User Privacy

- **Whitelist Mode**: Only DM approved users
  ```yaml
  discord:
    dm_whitelist: [123456789, 987654321]
  ```

- **Blacklist Mode**: Never DM specific users
  ```yaml
  discord:
    dm_blacklist: [111111111]
  ```

### 2. Rate Limiting

- **Per-user daily limit**: Prevents spam to individuals
- **Global cooldown**: Prevents rapid-fire DMs
- **Inactivity threshold**: Only DM after meaningful gap

### 3. Discord API Respect

- Handles `discord.Forbidden` gracefully if user has DMs disabled
- Logs all DM attempts for monitoring
- Only sends one DM per check cycle (not all eligible users at once)

### 4. Transparency

All proactive DMs are logged:
- In the `memories` table with type `proactive_outreach`
- In transparency logs
- Includes metadata: `{"type": "outbound_dm", "initiated_by": "bot"}`

## Message Generation

### Context Used

When generating a proactive DM, the bot considers:

1. **User Profile**:
   - Username
   - Total interaction count
   - Notes about the user

2. **Recent Conversation Topics**:
   - Last 3 memories from conversations

3. **Unresolved Curiosities**:
   - Questions the user asked
   - Topics they seemed interested in

4. **Persona Guidelines**:
   - Friendly, non-intrusive tone
   - Brief and respectful
   - Natural conversation starter

### Message Examples

**Good proactive DMs**:
```
"Hey Alex! I remember you were working on that chess strategy. 
 How's it going?"

"Hi! Haven't heard from you in a few days. Everything okay?"

"Quick question - did you ever figure out that Python issue 
 you mentioned?"
```

**What the bot avoids**:
```
❌ "HEY HEY HEY TALK TO ME!!!"
❌ "I noticed you haven't responded in exactly 47.3 hours..."
❌ "Here's a 500-word essay about everything we discussed..."
```

## Monitoring

### Check DM Activity

```bash
# View proactive DMs sent
sqlite3 data/memory.db

SELECT user_id, content, timestamp 
FROM memories 
WHERE type = 'proactive_outreach' 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Admin Commands

```
# View user's memory (includes proactive DMs)
!user_memory <user_id>
```

### Logs

The bot logs:
```
INFO: Proactive DM approved for user 123456789
INFO: Sent proactive DM to username (123456789)
WARNING: Cannot send DM to user 987654321 - DMs disabled
```

## Best Practices

### Recommended Settings

**For Personal Assistant (1-5 users)**:
```yaml
enable_proactive_dms: true
dm_inactivity_hours: 12      # Check in after 12 hours
dm_max_per_user_per_day: 2   # Can send 2 per day
dm_cooldown_hours: 6         # 6 hour cooldown
```

**For Small Community Bot (5-20 users)**:
```yaml
enable_proactive_dms: true
dm_inactivity_hours: 24      # Wait a full day
dm_max_per_user_per_day: 1   # One per user per day
dm_cooldown_hours: 12        # 12 hour cooldown
```

**For Public Bot (20+ users)**:
```yaml
enable_proactive_dms: false  # Disabled by default
# OR use whitelist
dm_whitelist: [admin_ids]    # Only DM admins/testers
```

### Testing the Feature

1. **Start Conservative**:
   ```yaml
   enable_proactive_dms: true
   dm_inactivity_hours: 48    # Wait 2 days
   dm_max_per_user_per_day: 1
   ```

2. **Test with Whitelist**:
   ```yaml
   dm_whitelist: [your_user_id]  # Only you get DMs
   ```

3. **Monitor Logs**: Check for:
   - How often DMs are sent
   - User responses (positive/negative)
   - Any `discord.Forbidden` errors

4. **Adjust Based on Feedback**: Lower inactivity hours if users like it, raise if they find it intrusive

### User Feedback

If users complain about proactive DMs:

1. **Immediate**: Add them to blacklist
   ```yaml
   dm_blacklist: [user_id]
   ```

2. **Long-term**: Adjust global settings
   ```yaml
   dm_inactivity_hours: 72  # Wait 3 days instead
   ```

3. **Feature**: Add `!disable_proactive_dms` command

## Advanced Customization

### Custom Message Logic

Edit `discord_gateway.py`, `_send_proactive_dm_to_user()`:

```python
# Add custom logic based on user characteristics
if profile.interaction_count > 50:
    # Regular users get more casual messages
    tone = "casual, friendly"
elif profile.interaction_count < 5:
    # New users get more formal messages
    tone = "polite, respectful"
else:
    tone = "friendly"

prompt = [
    {"role": "system", "content": f"{PERSONA_PROMPT}\n\nUse a {tone} tone."},
    # ... rest of prompt
]
```

### Conditional DMs

```python
# Only DM users with unresolved curiosities
if not curiosities:
    self.logger.debug(f"No curiosities for user {profile.user_id}, skipping DM")
    return

# Only DM users who've interacted recently
if profile.interaction_count < 3:
    self.logger.debug(f"User {profile.user_id} too new, skipping DM")
    return
```

### Time-Based Logic

```python
from datetime import datetime

# Don't send DMs at night (user's timezone if known)
current_hour = datetime.utcnow().hour
if current_hour < 8 or current_hour > 22:  # Between 8 AM - 10 PM UTC
    self.logger.debug("Outside appropriate hours for DM")
    return
```

## Privacy & Ethics

### Transparency

Users should know the bot might proactively DM them. Add this to your bot's description:

> "This bot may occasionally send proactive DMs to follow up on conversations 
> or check in. You can disable this with the !disable_proactive_dms command."

### Opt-Out

Implement user opt-out:

```python
# In user_profiles table, add opt_out field
# Then check it before sending DMs

if profile.metadata.get("opt_out_proactive_dms"):
    return  # Don't send DM
```

### GDPR Compliance

The `!forget_me` command already deletes all user data, including:
- User profile (which stops future proactive DMs)
- All memories
- DM sending history

## Troubleshooting

### DMs Not Being Sent

**Check 1**: Feature enabled?
```yaml
enable_proactive_dms: true
```

**Check 2**: Any eligible users?
- Need users with `dm_inactivity_hours` of inactivity
- Not on blacklist
- Haven't exceeded daily limit

**Check 3**: Logs show what?
```
# Should see:
INFO: Proactive DM approved for user X

# Or:
DEBUG: Not enough inactivity for user X
DEBUG: Max DMs reached for user X today
```

**Check 4**: Discord permissions?
- Bot needs ability to send DMs
- User must allow DMs from server members

### Too Many DMs

**Immediate fix**:
```yaml
enable_proactive_dms: false
```

**Adjust settings**:
```yaml
dm_inactivity_hours: 72     # More time between
dm_max_per_user_per_day: 1  # Reduce daily limit
dm_cooldown_hours: 24       # Longer cooldown
```

### Wrong Users Getting DMs

**Check whitelist**:
```yaml
dm_whitelist: [allowed_user_ids]  # Only these users
```

**Check blacklist**:
```yaml
dm_blacklist: [blocked_user_ids]  # Never these users
```

## Future Enhancements

Possible additions:

1. **User preferences**: Let users set their preferred contact frequency
2. **Smart timing**: Learn when users are most active
3. **Topic matching**: Only DM about specific topics user cares about
4. **Response tracking**: Learn which types of DMs users engage with
5. **Conversation threads**: Continue previous conversations naturally

## Example Log Output

```
2026-02-07 10:30:15 INFO Scheduler: Proactive DM approved for user 123456789
2026-02-07 10:30:16 INFO DiscordGateway: Sent proactive DM to Alex (123456789)
2026-02-07 10:30:16 INFO Scheduler: Recorded DM to user 123456789 (count today: 1)

# 12 hours later...
2026-02-07 22:30:15 DEBUG Scheduler: DM cooldown active for user 123456789

# Next day...
2026-02-08 10:30:15 INFO Scheduler: Proactive DM approved for user 123456789
2026-02-08 10:30:16 WARNING DiscordGateway: Cannot send DM to user 123456789 - DMs disabled
```

## Summary

Proactive DMs enable your bot to:
✅ Build stronger relationships with users
✅ Follow up on unresolved topics
✅ Stay engaged during quiet periods
✅ Provide value without being prompted

But must be used carefully to:
❌ Not spam users
❌ Respect privacy preferences  
❌ Maintain appropriate boundaries
❌ Stay compliant with Discord ToS

Start with conservative settings, monitor user responses, and adjust based on feedback!
