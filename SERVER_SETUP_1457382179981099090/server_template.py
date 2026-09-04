import discord

# Blueprint for server roles
ROLES_BLUEPRINT = [
    # --- Staff & Leadership ---
    {
        "name": "👑 Founder & Owner",
        "color": discord.Color.from_rgb(245, 197, 24), # Gold
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(administrator=True)
    },
    {
        "name": "⚡ Co-Owner / Administrator",
        "color": discord.Color.from_rgb(231, 76, 60), # Crimson
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(administrator=True)
    },
    {
        "name": "🛡️ Moderator / Staff",
        "color": discord.Color.from_rgb(30, 144, 255), # Lightning Blue
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            manage_messages=True,
            kick_members=True,
            ban_members=True,
            mute_members=True,
            deafen_members=True,
            move_members=True
        )
    },
    {
        "name": "🎬 Cinema Host / Movie Master",
        "color": discord.Color.from_rgb(230, 126, 34), # Cinema Orange
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(priority_speaker=True, stream=True)
    },
    {
        "name": "🎵 Apex DJ / Sound Master",
        "color": discord.Color.from_rgb(155, 89, 182), # Purple
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(priority_speaker=True)
    },
    {
        "name": "💎 VIP & Server Booster",
        "color": discord.Color.from_rgb(244, 127, 255), # Pink
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(change_nickname=True, attach_files=True)
    },
    {
        "name": "🌟 Active Vibers",
        "color": discord.Color.from_rgb(46, 204, 113), # Emerald Green
        "hoist": True,
        "mentionable": False,
        "permissions": discord.Permissions(send_messages=True, connect=True, speak=True)
    },
    {
        "name": "👥 Verified Member",
        "color": discord.Color.from_rgb(149, 165, 166), # Silver
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions(send_messages=True, connect=True, speak=True)
    },
    {
        "name": "🤖 Official Bots",
        "color": discord.Color.from_rgb(52, 73, 94), # Dark Slate
        "hoist": True,
        "mentionable": False,
        "permissions": discord.Permissions(send_messages=True, embed_links=True, attach_files=True)
    },

    # --- Movie & Entertainment Self-Roles ---
    {"name": "🍿 Movie Night Ping", "color": discord.Color.orange(), "hoist": False, "mentionable": True},
    {"name": "🎌 Anime Watcher", "color": discord.Color.magenta(), "hoist": False, "mentionable": False},
    {"name": "👻 Horror & Thriller Fan", "color": discord.Color.dark_purple(), "hoist": False, "mentionable": False},
    {"name": "🚀 Sci-Fi & Action Fan", "color": discord.Color.blue(), "hoist": False, "mentionable": False},
    {"name": "😂 Comedy & Chill", "color": discord.Color.gold(), "hoist": False, "mentionable": False},

    # --- Notification Self-Roles ---
    {"name": "📢 Announcement Ping", "color": discord.Color.gold(), "hoist": False, "mentionable": True},
    {"name": "🎁 Giveaway Ping", "color": discord.Color.green(), "hoist": False, "mentionable": True},
    {"name": "⚡ Event Ping", "color": discord.Color.purple(), "hoist": False, "mentionable": True},

    # --- Gaming Platforms Self-Roles ---
    {"name": "🖥️ PC Gamer", "color": discord.Color.blue(), "hoist": False, "mentionable": False},
    {"name": "🎮 Console Gamer", "color": discord.Color.dark_blue(), "hoist": False, "mentionable": False},
    {"name": "📱 Mobile Gamer", "color": discord.Color.teal(), "hoist": False, "mentionable": False},

    # --- Music Genres Self-Roles ---
    {"name": "🎧 Hip-Hop / Rap", "color": discord.Color.orange(), "hoist": False, "mentionable": False},
    {"name": "🔊 EDM / Bass", "color": discord.Color.magenta(), "hoist": False, "mentionable": False},
    {"name": "☕ Lo-Fi & Chill", "color": discord.Color.blurple(), "hoist": False, "mentionable": False}
]

# Blueprint for Categories & Channels (Chill, Movies, Music, Conversations)
CATEGORIES_BLUEPRINT = [
    {
        "name": "📊 ━━ ⋆⋅ STATS ⋅⋆ ━━",
        "channels": [
            {"name": "👥・Members: 0", "type": "voice", "user_limit": 0, "locked": True},
            {"name": "🔊・In Lounges: 0", "type": "voice", "user_limit": 0, "locked": True},
            {"name": "🍿・Cinema: Ready", "type": "voice", "user_limit": 0, "locked": True}
        ]
    },
    {
        "name": "📌 ━━ ⋆⋅ WELCOME & INFO ⋅⋆ ━━",
        "channels": [
            {"name": "╭・「✅」verify-here", "type": "text", "topic": "Click button to verify and unlock server channels!", "read_only": True},
            {"name": "├・「👋」welcome", "type": "text", "topic": "Welcome new members to the community!", "read_only": True},
            {"name": "├・「📜」rules-guidelines", "type": "text", "topic": "Official community rules & server code of conduct.", "read_only": True},
            {"name": "├・「📢」announcements", "type": "text", "topic": "Important server news and movie night schedules.", "read_only": True},
            {"name": "├・「⭐」self-roles", "type": "text", "topic": "Pick your movie, music, gaming, and notification roles.", "read_only": True},
            {"name": "├・「🎉」celebrations", "type": "text", "topic": "Birthday and milestone celebrations for members.", "read_only": True},
            {"name": "╰・「🎫」create-ticket", "type": "text", "topic": "Click button to open private staff/support tickets.", "read_only": True}
        ]
    },
    {
        "name": "🍿 ━━ ⋆⋅ CINEMA & MOVIE NIGHTS ⋅⋆ ━━",
        "channels": [
            {"name": "╭・「🎬」movie-schedule", "type": "text", "topic": "Upcoming movie nights, anime marathons, and watch parties.", "read_only": True},
            {"name": "├・「🍿」movie-discussion", "type": "text", "topic": "Chat, react, and talk about movies and shows in real-time!", "read_only": False},
            {"name": "╰・「📺」movie-suggestions", "type": "text", "topic": "Suggest and vote on movies to stream next.", "read_only": False},
            {"name": "🎥・Cinema Theater 1 [Screen Share]", "type": "voice", "user_limit": 0, "bitrate": 96000},
            {"name": "🎥・Cinema Theater 2 [Anime & Shows]", "type": "voice", "user_limit": 0, "bitrate": 96000}
        ]
    },
    {
        "name": "💬 ━━ ⋆⋅ CHILL & CONVERSATIONS ⋅⋆ ━━",
        "channels": [
            {"name": "╭・「💬」lounge-chat", "type": "text", "topic": "Main cozy conversation and hangout channel.", "read_only": False},
            {"name": "├・「📸」media-gallery", "type": "text", "topic": "Share photos, selfies, aesthetic pictures, and memes.", "read_only": False},
            {"name": "├・「⭐」hall-of-fame", "type": "text", "topic": "Starboard showcasing the best community moments!", "read_only": True},
            {"name": "├・「🔢」counting-game", "type": "text", "topic": "Count together without breaking the streak!", "read_only": False},
            {"name": "├・「📊」polls-and-voting", "type": "text", "topic": "Vote in daily community polls.", "read_only": False},
            {"name": "├・「🤖」bot-commands", "type": "text", "topic": "Play games (/coinflip, /dice, /daily) and check stats.", "read_only": False},
            {"name": "╰・「💡」suggestions", "type": "text", "topic": "Ideas and feedback for the server.", "read_only": False}
        ]
    },
    {
        "name": "🎵 ━━ ⋆⋅ APEX MUSIC & LO-FI ⋅⋆ ━━",
        "channels": [
            {"name": "╭・「🎵」music-commands", "type": "text", "topic": "Control APEX VIBES music bot (/play, /queue, /bassboost, /radio).", "read_only": False},
            {"name": "╰・「☕」lofi-cafe-chat", "type": "text", "topic": "Chat while enjoying 24/7 Lo-Fi, Synthwave, and chill radio streams.", "read_only": False},
            {"name": "☕・Lo-Fi Study Cafe [24/7]", "type": "voice", "user_limit": 0, "bitrate": 96000},
            {"name": "🌙・Late Night Chill Lounge", "type": "voice", "user_limit": 0, "bitrate": 96000},
            {"name": "🔊・HD Music Lounge [320kbps]", "type": "voice", "user_limit": 0, "bitrate": 96000}
        ]
    },
    {
        "name": "🔊 ━━ ⋆⋅ CHILLOUT VOICE LOUNGES ⋅⋆ ━━",
        "channels": [
            {"name": "➕・Join to Create Voice", "type": "voice", "user_limit": 0},
            {"name": "🔊・Cozy Talk 1", "type": "voice", "user_limit": 0},
            {"name": "🔊・Cozy Talk 2", "type": "voice", "user_limit": 0},
            {"name": "🔊・Duo Hangout (2 Max)", "type": "voice", "user_limit": 2},
            {"name": "🔊・Squad Hangout (4 Max)", "type": "voice", "user_limit": 4},
            {"name": "💤・Sleep & Rain Sounds", "type": "voice", "user_limit": 0}
        ]
    },
    {
        "name": "🛡️ ━━ ⋆⋅ STAFF HEADQUARTERS ⋅⋆ ━━",
        "channels": [
            {"name": "🛡️・staff-lounge", "type": "text", "topic": "Private discussions for server moderators & admins.", "staff_only": True},
            {"name": "📋・audit-moderation-logs", "type": "text", "topic": "Automated server mod logs and member alerts.", "staff_only": True}
        ]
    }
]
