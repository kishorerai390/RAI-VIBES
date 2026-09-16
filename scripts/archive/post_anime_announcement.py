import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ANNOUNCE_CHAN_ID = "1545502718792175646" # #📢・announcements

HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json", "User-Agent": "DiscordBot (Announce, 1.0)"}

content_text = "@everyone @here <@&1546088542885642324> <@&1546062599253135420>"

embed_data = {
    "title": "🌸 ◈ 𝐑𝐀𝐈 𝐅𝐀𝐌 𝐗 𝐇𝐈𝐀𝐍𝐈𝐌𝐄 • 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝐋𝐀𝐔𝐍𝐂𝐇 ◈ 🌸",
    "description": (
        "✨ **ATTENTION ANIME LOVERS & RAI FAMILY!** ✨\n\n"
        "We are thrilled to officially unveil our brand new platform for streaming the latest and highest quality anime — "
        "featuring **Zero Buffering, Ultra-HD 4K streaming, Sub & Dub, and Ad-Free experience**! 🍿🎬\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌐 **OFFICIAL STREAMING PORTAL IS LIVE:**\n"
        "🔗 **[https://hianime.at](https://hianime.at)**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### 🌟 **Key Features of HiAnime:**\n"
        "• ⚡ **Ultra HD 1080p & 4K Quality** — Crystal clear playback for every show\n"
        "• 🎌 **Sub & Dub Dual Audio** — Switch effortlessly between Japanese & English\n"
        "• 🚀 **High-Speed Global CDN** — Lightning-fast loading with zero lag\n"
        "• 📱 **Mobile & Desktop Optimized** — Smooth cinema experience anywhere\n"
        "• 💬 **Simulcast Episode Drops** — Airs immediately as released in Japan!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "### 🍿 **Upcoming Anime Watch Parties:**\n"
        "Join us in our Cinema Theaters <#1545502762467328185> (**🎦・MOVIE¹**) & <#1545803585550426234> (**🎦・MOVIE²**) "
        "for live community watch parties streamed straight from **HiAnime**!\n\n"
        "👉 **Start watching now:** [https://hianime.at](https://hianime.at)\n"
        "*Drop your favorite anime in chat below!* 🔥✨"
    ),
    "color": 16738740, # 0xFF69B4 (Vibrant Pink)
    "thumbnail": {
        "url": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    },
    "image": {
        "url": "https://media.giphy.com/media/xT9IgzoKnwFNmISR8I/giphy.gif"
    },
    "footer": {
        "text": "RAI FAM 💗 • Official Anime Streaming Platform",
        "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/c39edf51a428bd0368a72b5c463a5c6f.png"
    }
}

payload = {
    "content": content_text,
    "embeds": [embed_data]
}

req = urllib.request.Request(
    f"https://discord.com/api/v10/channels/{ANNOUNCE_CHAN_ID}/messages",
    data=json.dumps(payload).encode('utf-8'),
    headers=HEADERS,
    method='POST'
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        msg_id = res.get('id')
        print(f"🎉 SUCCESS! Announcement posted to #📢・announcements (Message ID: {msg_id})")
        
        # Add reactions to the announcement
        for emoji in ["🔥", "🍿", "🌸", "❤️"]:
            try:
                emoji_encoded = urllib.parse.quote(emoji)
                r_req = urllib.request.Request(
                    f"https://discord.com/api/v10/channels/{ANNOUNCE_CHAN_ID}/messages/{msg_id}/reactions/{emoji_encoded}/@me",
                    headers=HEADERS,
                    method='PUT'
                )
                with urllib.request.urlopen(r_req) as r_resp:
                    pass
            except Exception:
                pass
        print("✅ Added hype reactions to announcement!")
except Exception as e:
    print(f"❌ Error posting announcement: {e}")
