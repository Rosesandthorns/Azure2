# Examples and Best Practices

## Example Interactions

### User Profile Building

**First interaction:**
```
User: Hi! I'm Alex and I love playing chess.
Bot: Nice to meet you, Alex! I've noted that you enjoy chess. 
     [Creates user profile with username "Alex"]
     [Stores memory: "User loves playing chess"]
```

**Later interaction:**
```
User: What do you know about me?
Bot: Let me check... You're Alex, and you mentioned you love playing chess.
     We first talked on [date].
     [Loads Alex's user profile and related memories]
```

**With mentioned users:**
```
User: Can you tell @Sarah about chess?
Bot: [Loads both Alex's and Sarah's profiles]
     Based on what I know about your interest in chess, Alex, 
     and Sarah's profile...
```

### DM Conversations

**Private context:**
```
DM from User: I'm having a tough day.
Bot: [Recognizes this is a DM - private context]
     I'm sorry to hear that. Would you like to talk about it?
     [More personal, empathetic tone in DMs]
```

**Server vs DM context:**
```
Server: @Bot what's the weather?
Bot: [Public response]

DM: what's the weather?
Bot: [Can be more conversational, knows it's private]
```

### Memory Types in Action

**Episodic Memory:**
```
User: I went to the park today.
Bot: [Stores as episodic memory, low-medium importance]
```

**Curiosity Memory:**
```
User: What's the best way to learn Python?
Bot: [Stores as curiosity, higher importance]
     [May follow up later if unanswered]
```

**Summary Memory:**
```
After several conversations about programming...
Bot: [Automatically creates summary memory]
     "Summary: recurring topics - Python, learning, projects, debugging"
```

### Belief Tracking

**Initial belief:**
```
User: I'm a software engineer.
Bot: [Creates memory with confidence 0.6]
```

**Confirmation:**
```
User: I've been coding for 10 years.
Bot: [Increases confidence to 0.8]
```

**Contradiction:**
```
User: Actually, I'm transitioning from marketing to tech.
Bot: [Detects contradiction, adjusts previous belief confidence down]
     [Creates new memory with transition context]
```

## Best Practices

### For Bot Administrators

#### 1. Configure DM Access Appropriately

**For personal assistant use:**
```yaml
respond_to_dms: true
dm_whitelist: [your_user_id]  # Only you can DM
dm_blacklist: []
```

**For team bot:**
```yaml
respond_to_dms: true
dm_whitelist: []  # Everyone on team can DM
dm_blacklist: [spam_user_id]  # Block known problems
```

**For public server:**
```yaml
respond_to_dms: false  # Disable DMs entirely
respond_to_mentions: true  # Only respond when mentioned
```

#### 2. Set Appropriate Importance Thresholds

**Low threshold (stores more):**
```yaml
memory:
  min_importance_to_store: 0.2
```
- More context
- Larger database
- Use when: small user base, lots of storage

**High threshold (stores less):**
```yaml
memory:
  min_importance_to_store: 0.5
```
- Only important stuff
- Smaller database
- Use when: large user base, limited storage

#### 3. Manage User Profiles

```bash
# Regular audits
!users 50  # Check who's most active
!user_memory <user_id>  # Review individual profiles

# Privacy compliance
# Encourage users to use !forget_me if they want data deleted
# Periodically inform users about data storage
```

#### 4. Monitor Memory Quality

```bash
# Check memory distribution
!memory 20  # Are memories relevant?

# Look for patterns
# - Too many low-confidence memories? Adjust thresholds
# - Too many curiosity memories? Bot might be asking too many questions
# - Lots of summaries? Good sign of learning
```

### For Users

#### Managing Your Data

**View your profile:**
```
!profile
```

**Delete your data:**
```
!forget_me
```

**Update your preferences:**
```
User: I prefer you to call me by my nickname "Alex"
Bot: [Updates notes in your profile]
```

### For Developers

#### Adding Custom Memory Types

```python
# In discord_gateway.py, _maybe_store_memory()

def _maybe_store_memory(self, user_id: int, content: str, retrieved: List[MemoryEntry]):
    # Detect game-related content
    if any(word in content.lower() for word in ["chess", "game", "play", "win", "lose"]):
        memory_type = "game_interaction"
        importance = 0.6
        metadata = {
            "category": "gaming",
            "competitive": "win" in content.lower() or "lose" in content.lower()
        }
    # Detect learning requests
    elif any(word in content.lower() for word in ["learn", "how to", "teach me"]):
        memory_type = "learning_request"
        importance = 0.7
        metadata = {
            "category": "education",
            "resolved": False  # Track if we answered it
        }
    # Default
    else:
        memory_type = "episodic"
        importance = 0.2 + len(content) / 200
        metadata = {}
    
    # Create memory with metadata
    entry = self.memory_service.create_memory(
        content=content,
        memory_type=memory_type,
        confidence=0.6,
        importance=importance,
        user_id=str(user_id),
        source_memory_ids=[m.id for m in retrieved],
        metadata=metadata,  # Include metadata
    )
    return entry
```

#### Using User Profile Preferences

```python
# In discord_gateway.py, _build_prompt()

def _build_prompt(self, content, retrieved, user_profile, mentioned_profiles, is_dm):
    # Check user preferences
    if user_profile and user_profile.preferences:
        prefs = user_profile.preferences
        
        # Adjust tone based on preferences
        if prefs.get("formal_tone"):
            tone_instruction = "Use formal, professional language."
        else:
            tone_instruction = "Use casual, friendly language."
        
        # Time-aware responses
        if prefs.get("timezone"):
            tz = prefs["timezone"]
            tone_instruction += f" User is in {tz} timezone."
        
        # Add to system prompts
        return [
            {"role": "system", "content": PERSONA_PROMPT},
            {"role": "system", "content": tone_instruction},
            # ... rest of prompt
        ]
```

#### Implementing User Notes Auto-Update

```python
# Add this to discord_gateway.py

def _extract_user_info_updates(self, content: str, user_id: str) -> None:
    """Extract and save information about the user from their message"""
    
    # Detect preferences
    if "prefer" in content.lower() or "like" in content.lower():
        profile = self.memory_service.get_user_profile(user_id)
        if profile:
            # Update notes
            new_note = f"[{datetime.now().date()}] {content}"
            updated_notes = f"{profile.notes}\n{new_note}".strip()
            self.memory_service.update_user_notes(user_id, updated_notes)
    
    # Detect timezone mentions
    tz_match = re.search(r'\b(EST|PST|GMT|UTC[+-]\d+)\b', content, re.I)
    if tz_match:
        profile = self.memory_service.get_user_profile(user_id)
        if profile:
            profile.preferences["timezone"] = tz_match.group(1)
            self.memory_service.create_or_update_user_profile(
                user_id,
                profile.username,
                preferences=profile.preferences
            )

# Call this in _process_message() before generating response
```

## Advanced Patterns

### Context-Aware Responses

```python
def _build_prompt(self, ...):
    # Different prompts for different contexts
    
    if is_dm:
        context_guidance = """
        This is a private DM. You can:
        - Be more personal and detailed
        - Ask follow-up questions freely
        - Discuss sensitive topics if appropriate
        """
    else:
        context_guidance = """
        This is a public server message. You should:
        - Keep responses concise
        - Be mindful others are reading
        - Avoid personal details unless user initiated
        """
    
    # Add to prompts
    messages = [
        {"role": "system", "content": PERSONA_PROMPT},
        {"role": "system", "content": context_guidance},
        # ...
    ]
```

### Progressive Disclosure

```python
# Only mention detailed user history after some interactions

if user_profile and user_profile.interaction_count > 5:
    # After 5 interactions, reference past conversations
    user_context = f"Long-time user: {user_profile.notes}"
else:
    # New user, keep it simple
    user_context = f"New user: {user_profile.username}"
```

### Privacy-Aware Mentions

```python
# Don't reveal private user info in public channels

if not is_dm and mentioned_profiles:
    # In public, only mention publicly-known info
    for profile in mentioned_profiles:
        # Filter notes to remove personal details
        safe_notes = filter_personal_info(profile.notes)
        user_context += f"- {profile.username}: {safe_notes}\n"
```

## Performance Optimization

### Database Indexing

Already included:
```sql
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_type ON memories(type);
CREATE INDEX idx_memories_timestamp ON memories(timestamp);
```

### Memory Cleanup

```python
# Add periodic cleanup task

async def cleanup_old_memories():
    while True:
        # Delete old, low-importance memories
        cutoff_date = datetime.now() - timedelta(days=90)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM memories WHERE importance < 0.3 AND timestamp < ?",
            (cutoff_date.isoformat(),)
        )
        conn.commit()
        
        await asyncio.sleep(86400)  # Daily
```

### Caching User Profiles

```python
# Add simple LRU cache
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_user_profile(user_id: str) -> Optional[UserProfile]:
    return self.memory_service.get_user_profile(user_id)

# Clear cache on updates
def create_or_update_user_profile(self, ...):
    # ... update logic ...
    get_cached_user_profile.cache_clear()
```

## Testing

### Unit Tests

```python
# test_memory_service.py
import unittest
from memory_service import MemoryService

class TestMemoryService(unittest.TestCase):
    def setUp(self):
        self.service = MemoryService(":memory:")  # In-memory DB
    
    def test_user_profile_creation(self):
        profile = self.service.create_or_update_user_profile(
            "123", "TestUser"
        )
        self.assertEqual(profile.username, "TestUser")
        self.assertEqual(profile.interaction_count, 1)
    
    def test_user_profile_update(self):
        self.service.create_or_update_user_profile("123", "TestUser")
        updated = self.service.create_or_update_user_profile("123", "TestUser")
        self.assertEqual(updated.interaction_count, 2)
```

### Integration Tests

```python
# Test full message flow
async def test_message_flow():
    # Setup
    gateway = create_test_gateway()
    
    # Simulate message
    mock_message = create_mock_message(
        author_id="123",
        content="Hello!"
    )
    
    # Process
    await gateway.on_message(mock_message)
    
    # Verify
    profile = gateway.memory_service.get_user_profile("123")
    assert profile is not None
    assert profile.interaction_count == 1
```

## Monitoring Dashboard

### SQL Queries for Analytics

```sql
-- Most active users
SELECT username, interaction_count, last_interaction
FROM user_profiles
ORDER BY interaction_count DESC
LIMIT 10;

-- Memory distribution by type
SELECT type, COUNT(*) as count, AVG(importance) as avg_importance
FROM memories
GROUP BY type;

-- User growth over time
SELECT DATE(first_seen) as date, COUNT(*) as new_users
FROM user_profiles
GROUP BY DATE(first_seen)
ORDER BY date DESC;

-- Confidence distribution
SELECT 
    CASE 
        WHEN confidence < 0.3 THEN 'low'
        WHEN confidence < 0.7 THEN 'medium'
        ELSE 'high'
    END as confidence_level,
    COUNT(*) as count
FROM memories
GROUP BY confidence_level;
```
