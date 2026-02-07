# Azure Discord AI Bot - Final Edition

Azure-codex with Azure-improved features integrated.

## What This Is

This is **Azure-codex** (your current working version) with ONLY these features added from Azure-improved:

1. ✅ **User Profiles** - Dedicated table tracking users (username, interaction count, timestamps, notes)
2. ✅ **DM Whitelist/Blacklist** - Control who can DM the bot
3. ✅ **User Commands** - !profile, !forget_me, !help
4. ✅ **Admin User Management** - !users, !user_memory
5. ✅ **Proactive DM System** - Bot can initiate conversations with inactive users

## What's NOT Changed

- ✅ All Azure-codex features remain intact
- ✅ ProfileService still works exactly as before  
- ✅ Consciousness loops, thought streams, reflection worker - all unchanged
- ✅ Image analysis, personality state, belief tracking - all unchanged
- ✅ Retrieval engine from codex (NOT ChromaDB from improved)

## Quick Start

1. **Edit config.yaml**:
   - Add your Discord bot token
   - Add your user ID to admin_user_ids
   - Configure DM settings (optional)
   - Enable proactive DMs (optional)

2. **Run it**:
   ```bash
   python smart_launch.py
   ```
   The smart launcher will ensure a supported Python version is used, install
   dependencies, and then start the bot.

## New Configuration Options

```yaml
discord:
  # DM Settings (NEW from Azure-improved)
  respond_to_dms: true
  dm_whitelist: []  # Empty = allow all
  dm_blacklist: []  # Block specific users
  respond_to_mentions: true
  respond_to_generic: false

scheduler:
  # Proactive DM Settings (NEW from Azure-improved)
  enable_proactive_dms: false  # Set true to enable
  dm_inactivity_hours: 24
  dm_max_per_user_per_day: 1
  dm_cooldown_hours: 12
```

## New Commands

### User Commands (anyone can use):
- `!profile` - View your user profile
- `!forget_me` - Delete all your data
- `!help` - Show available commands

### Admin Commands (admin_user_ids only):
- `!users [n]` - List n recent users
- `!user_memory <user_id>` - View specific user's profile and memories
- Plus all existing admin commands

## How User Profiles Work

Every time a user interacts with Azure, their profile is automatically created/updated with:
- User ID and username
- First seen timestamp
- Last interaction timestamp
- Interaction count
- Custom notes and preferences (can be set programmatically)

This data is stored in a dedicated `user_profiles` table, separate from memories.

## How Proactive DMs Work

When enabled (`enable_proactive_dms: true`), Azure will:
1. Check for users who haven't interacted in X hours
2. Respect daily limits and cooldowns
3. Check whitelist/blacklist settings
4. Generate a personalized message based on conversation history
5. Send a DM to check in

See [PROACTIVE_DMS.md](PROACTIVE_DMS.md) for full documentation.

## What's Different from Pure Azure-Codex

1. **Database**: Added `user_profiles` table
2. **Config**: Added DM and proactive DM settings
3. **Commands**: Added user commands (!profile, !forget_me, etc.)
4. **DM Handling**: Enhanced with access control
5. **Auto-Tracking**: Users are automatically profiled on interaction

Everything else works exactly like Azure-codex.

## Migration from Azure-Codex

If you're upgrading from plain Azure-codex:
- ✅ Fully backward compatible
- ✅ Existing data works fine
- ✅ User profiles created automatically
- ✅ No manual migration needed

Just update your config.yaml with the new optional settings.

## Files Changed from Azure-Codex

- `memory_service.py` - Added UserProfile class and methods
- `scheduler.py` - Added proactive DM scheduling
- `discord_gateway.py` - Added DM handling and user commands
- `main.py` - Added new config options
- `config.yaml` - Added new settings

## Documentation

- [PROACTIVE_DMS.md](PROACTIVE_DMS.md) - Proactive DM feature guide
- [EXAMPLES.md](EXAMPLES.md) - Usage examples

## Architecture

This is still Azure-codex at its core, with:
- Consciousness loops
- Thought stream generation
- Reflection worker
- Personality state
- Belief tracking
- Reasoning engine  
- Image analysis
- ProfileService (unchanged)
- **PLUS** user profile tracking and proactive DMs from Azure-improved

---

**TL;DR**: Azure-codex works exactly as before, but now tracks users better and can optionally send proactive DMs.
