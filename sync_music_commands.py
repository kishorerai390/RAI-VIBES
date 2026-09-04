import sys
import os
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
headers = {
    "Authorization": f"Bot {token}",
    "Content-Type": "application/json"
}

app_res = requests.get("https://discord.com/api/v10/oauth2/applications/@me", headers=headers)
app_id = app_res.json()["id"]

# Pure Music & Audio Commands Payload for Discord Global Commands
music_commands_payload = [
    # 1. Core Playback
    {
        "name": "play",
        "description": "Play music from YouTube or Spotify (link or search name).",
        "options": [
            {
                "name": "query",
                "description": "Song name, artist, or YouTube/Spotify URL",
                "type": 3,
                "required": True
            }
        ]
    },
    {
        "name": "pause",
        "description": "Pause current music playback."
    },
    {
        "name": "resume",
        "description": "Resume paused music playback."
    },
    {
        "name": "skip",
        "description": "Skip the currently playing song."
    },
    {
        "name": "stop",
        "description": "Stop music, clear queue, and leave voice channel."
    },
    {
        "name": "nowplaying",
        "description": "Display currently playing song with interactive controls."
    },
    {
        "name": "queue",
        "description": "Display upcoming songs in the queue."
    },
    {
        "name": "volume",
        "description": "Adjust player volume (0% - 200%).",
        "options": [
            {
                "name": "level",
                "description": "Volume percentage (0-200)",
                "type": 4,
                "required": True
            }
        ]
    },
    {
        "name": "loop",
        "description": "Set repeat mode: off, track, or queue.",
        "options": [
            {
                "name": "mode",
                "description": "Loop mode",
                "type": 3,
                "required": False,
                "choices": [
                    {"name": "Off", "value": "off"},
                    {"name": "Track (Repeat Current Song)", "value": "track"},
                    {"name": "Queue (Repeat Entire Queue)", "value": "queue"}
                ]
            }
        ]
    },
    {
        "name": "shuffle",
        "description": "Shuffle songs in the current queue."
    },
    {
        "name": "remove",
        "description": "Remove a specific song from queue by its index.",
        "options": [
            {
                "name": "index",
                "description": "Position index in queue to remove",
                "type": 4,
                "required": True
            }
        ]
    },
    {
        "name": "search",
        "description": "Search YouTube and choose from top 5 results interactively.",
        "options": [
            {
                "name": "query",
                "description": "Search terms",
                "type": 3,
                "required": True
            }
        ]
    },

    # 2. 24/7 Radio & Tamil Streams
    {
        "name": "tamilnadufm",
        "description": "Stream 24/7 Live Tamil Nadu FM Radio non-stop!"
    },
    {
        "name": "tnfm",
        "description": "Quick shortcut: Stream 24/7 Tamil Nadu FM Live!"
    },
    {
        "name": "tamil",
        "description": "Quick shortcut: Stream 24/7 Non-Stop Tamil Hit Songs!"
    },
    {
        "name": "radio",
        "description": "Stream continuous 24/7 live themed radio stations.",
        "options": [
            {
                "name": "station",
                "description": "Choose a 24/7 Radio Station",
                "type": 3,
                "required": False,
                "choices": [
                    {"name": "📻 Tamil Nadu FM Live 24/7", "value": "tamilnadu_fm"},
                    {"name": "☀️ Sooriyan Tamil FM 24/7", "value": "sooriyan_fm"},
                    {"name": "☕ Tamil Slowed & Lofi Beats 24/7", "value": "tamil_lofi"},
                    {"name": "🎼 A.R. Rahman 24/7 Radio", "value": "tamil_ar"},
                    {"name": "🌈 Vanavil Tamil Hits 24/7", "value": "vanavil_fm"},
                    {"name": "☕ Lofi Beats 24/7", "value": "lofi"},
                    {"name": "🌆 Synthwave / Retro 24/7", "value": "synthwave"},
                    {"name": "🎮 Gaming Beats 24/7", "value": "gaming"},
                    {"name": "🍃 Chillout Lounge 24/7", "value": "chill"}
                ]
            }
        ]
    },
    {
        "name": "stay247",
        "description": "Toggle or set 24/7 mode (prevents bot from leaving voice channel).",
        "options": [
            {
                "name": "mode",
                "description": "Choose to explicitly Enable or Disable 24/7 mode",
                "type": 3,
                "required": False,
                "choices": [
                    {"name": "✅ Enable 24/7 Mode (Never leave VC)", "value": "enable"},
                    {"name": "❌ Disable 24/7 Mode (Leave when inactive)", "value": "disable"}
                ]
            }
        ]
    },

    # 3. Audio FX & Lyrics
    {
        "name": "lyrics",
        "description": "Get lyrics for currently playing song or search by name.",
        "options": [
            {
                "name": "song",
                "description": "Optional song title to search",
                "type": 3,
                "required": False
            }
        ]
    },
    {
        "name": "bassboost",
        "description": "Boost the sub-bass frequencies.",
        "options": [
            {
                "name": "level",
                "description": "Bass boost intensity level",
                "type": 3,
                "required": False,
                "choices": [
                    {"name": "Off (Disable)", "value": "off"},
                    {"name": "Low (Subtle Punch)", "value": "low"},
                    {"name": "Medium (Rich Thunder)", "value": "medium"},
                    {"name": "High (Heavy Rumble)", "value": "high"},
                    {"name": "Extreme (Asgard Quake)", "value": "extreme"}
                ]
            }
        ]
    },
    {
        "name": "nightcore",
        "description": "Toggle high-energy Nightcore pitch & speed filter."
    },
    {
        "name": "slowed",
        "description": "Toggle aesthetic Slowed + Reverb audio filter."
    },
    {
        "name": "spatial8d",
        "description": "Toggle 8D 360-degree spatial headphone rotation."
    },
    {
        "name": "vaporwave",
        "description": "Toggle nostalgic retro Vaporwave filter."
    },
    {
        "name": "speed",
        "description": "Adjust playback speed (0.5x to 2.0x).",
        "options": [
            {
                "name": "value",
                "description": "Speed factor (e.g. 1.25 for 1.25x)",
                "type": 10,
                "required": True
            }
        ]
    },
    {
        "name": "filter_reset",
        "description": "Reset and remove all active audio filters."
    },

    # 4. Utilities & Info
    {
        "name": "ping",
        "description": "Check RAI VIBES response latency."
    },
    {
        "name": "help",
        "description": "Show full list of RAI VIBES music & audio commands."
    },
    {
        "name": "info",
        "description": "Display bot system status, guilds, and uptime."
    }
]

print(f"Syncing {len(music_commands_payload)} clean Music & Audio commands globally with Discord...")
put_res = requests.put(
    f"https://discord.com/api/v10/applications/{app_id}/commands",
    headers=headers,
    json=music_commands_payload
)

print(f"Sync Status Code: {put_res.status_code}")
if put_res.status_code in (200, 201):
    result = put_res.json()
    print(f"✨ Successfully synchronized {len(result)} pure Music & Audio slash commands globally!")
else:
    print(f"❌ Error syncing commands: {put_res.text}")
