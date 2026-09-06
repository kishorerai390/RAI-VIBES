import os
import sys
import base64
import shutil
import asyncio
import requests
from pathlib import Path
from dotenv import load_dotenv
import discord

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN_VIBES = os.getenv("DISCORD_BOT_TOKEN")
TOKEN_SENTINEL = os.getenv("SECURITY_BOT_TOKEN")
GUILD_ID = 1457382179981099090

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Image Files
GEN_ICON = r"C:\Users\kishore\.gemini\antigravity-ide\brain\f702fb63-3851-4c49-a66f-04de06a1d35b\server_icon_new_1788714131617.jpg"
GEN_BANNER = r"C:\Users\kishore\.gemini\antigravity-ide\brain\f702fb63-3851-4c49-a66f-04de06a1d35b\server_banner_new_1788714156224.jpg"
DEST_ICON = ASSETS_DIR / "server_icon.jpg"
DEST_BANNER = ASSETS_DIR / "server_banner.jpg"

def copy_images():
    print("📁 Copying new Server Icon & Banner...")
    if os.path.exists(GEN_ICON):
        shutil.copyfile(GEN_ICON, DEST_ICON)
        print("  ✅ Saved: assets/server_icon.jpg")
    if os.path.exists(GEN_BANNER):
        shutil.copyfile(GEN_BANNER, DEST_BANNER)
        print("  ✅ Saved: assets/server_banner.jpg")

def get_data_uri(path):
    with open(path, "rb") as f:
        return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"

# 2. Update Server Icon & Banner via REST
def update_guild_branding():
    print("\n👑 Updating Server Icon & Banner on Discord...")
    headers = {"Authorization": f"Bot {TOKEN_VIBES}", "Content-Type": "application/json"}
    payload = {}
    if DEST_ICON.exists():
        payload["icon"] = get_data_uri(DEST_ICON)
    if DEST_BANNER.exists():
        payload["banner"] = get_data_uri(DEST_BANNER)

    r = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=headers, json=payload)
    if r.status_code == 200:
        print("  🎉 Server Icon & Banner successfully updated!")
    elif r.status_code == 400 and "banner" in r.text.lower():
        # Fallback if server boost tier doesn't support banner
        r = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=headers, json={"icon": payload.get("icon")})
        if r.status_code == 200:
            print("  🎉 Server Icon successfully updated! (Banner requires Boost Level 2)")
        else:
            print(f"  ⚠️ Icon update status: {r.status_code} {r.text}")
    else:
        print(f"  ⚠️ Branding response: {r.status_code} {r.text}")

# 3. Update Channel Topics
CHANNEL_TOPICS = {
    1545502730699808768: "💬 ┊ The main heartbeat of RAI FAM • Spread good vibes, chat & make friends ✨",
    1545534637122527332: "🎧 ┊ Type /play <song> to queue your favorite music with RAI VIBES 💗",
    1546097792915873842: "🍿 ┊ Daily anime discussions, seasonal rankings & recommendations 🌸",
    1545803554550190212: "⚡ ┊ Squad up for BGMI, Free Fire, Roblox & casual gaming 🎮",
    1545834933417672744: "💎 ┊ Exclusive executive VIP lounge for Server Boosters & Donators 🥂",
    1546125872661012611: "🧭 ┊ Official navigation directory & server guide for RAI FAM 🌸",
    1545502710101704714: "📜 ┊ Community rules, safety guidelines & server etiquette ⚖️",
    1545502700840427702: "✨ ┊ Complete 1-click Sentinel verification to access all channels 🛡️",
    1545502722739150898: "🎀 ┊ Customize your notifications, pings & gaming roles here 🎭"
}

def update_channel_topics():
    print("\n📝 Updating Channel Topics...")
    headers = {"Authorization": f"Bot {TOKEN_VIBES}", "Content-Type": "application/json"}
    for ch_id, topic in CHANNEL_TOPICS.items():
        url = f"https://discord.com/api/v10/channels/{ch_id}"
        r = requests.patch(url, headers=headers, json={"topic": topic})
        if r.status_code == 200:
            print(f"  ✅ Updated topic for channel {ch_id}")
        else:
            print(f"  ⚠️ Topic note for {ch_id}: {r.status_code}")

# 4. Deploy Aesthetic Embeds
async def deploy_embeds():
    print("\n🎀 Deploying Aesthetic Embed Panels (Guide, Rules, Verify, Roles)...")
    intents = discord.Intents.default()
    intents.guilds = True
    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        print(f"  🤖 Logged in as {bot.user} to deploy panels...")
        guild = bot.get_guild(GUILD_ID) or await bot.fetch_guild(GUILD_ID)

        # A. # 🧭 ┊ server-guide
        guide_chan = bot.get_channel(1546125872661012611)
        if guide_chan:
            try:
                # Clear previous bot messages
                async for m in guide_chan.history(limit=10):
                    if m.author == bot.user:
                        await m.delete()
            except Exception:
                pass

            embed = discord.Embed(
                title="🌸 ＷＥＬＣＯＭＥ  ＴＯ  ＲＡＩ  ＦＡＭ 🌸",
                description=(
                    "**Command the Vibe • Hear the Rhythm • Rule the Community**\n\n"
                    "Welcome to the official **RAI FAM 💗** server! Here is your quick navigation guide to make the most out of our aesthetic sanctuary."
                ),
                color=0xFF69B4
            )
            embed.add_field(
                name="📌 ＩＮＦＯＲＭＡＴＩＯＮ",
                value=(
                    "• <#1545502700840427702> — Click the button to unlock all channels.\n"
                    "• <#1545502710101704714> — Read our server rules & etiquette.\n"
                    "• <#1545502722739150898> — Grab your notification & gaming roles."
                ),
                inline=False
            )
            embed.add_field(
                name="💬 ＣＯＭＭＵＮＩＴＹ  ＬＯＵＮＧＥＳ",
                value=(
                    "• <#1545502730699808768> — Chat, chill, and meet new members.\n"
                    "• <#1546097792915873842> — Anime discussions and recommendations.\n"
                    "• <#1545803554550190212> — Find squad mates for BGMI, FF & Roblox."
                ),
                inline=False
            )
            embed.add_field(
                name="🎵 ＲＡＩ  ＶＩＢＥＳ  ＭＵＳＩＣ",
                value=(
                    "• <#1545534637122527332> — Request songs with `/play <song>`\n"
                    "• Use `/bassboost`, `/spatial8d`, `/nightcore` for elite audio filters.\n"
                    "• Join `➕ ┊ Create Your VC` to spin up a private temporary hangout room!"
                ),
                inline=False
            )
            embed.set_footer(text="RAI FAM 💗 • Est. 2026 • Good Vibes Only", icon_url=bot.user.display_avatar.url)
            await guide_chan.send(embed=embed)
            print("  ✅ Posted Server Guide Embed!")

        # B. # 📜 ┊ rules-and-info
        rules_chan = bot.get_channel(1545502710101704714)
        if rules_chan:
            try:
                async for m in rules_chan.history(limit=10):
                    if m.author == bot.user:
                        await m.delete()
            except Exception:
                pass

            embed = discord.Embed(
                title="📜 ＲＡＩ  ＦＡＭ  ＣＯＭＭＵＮＩＴＹ  ＲＵＬＥＳ 📜",
                description="To ensure an enjoyable, safe, and aesthetic environment for all members, please abide by our core decrees:",
                color=0xFF1493
            )
            embed.add_field(
                name="1️⃣ ┊ Mutual Respect & Dignity",
                value="Treat everyone with respect. Harassment, hate speech, toxicity, and excessive drama are strictly prohibited.",
                inline=False
            )
            embed.add_field(
                name="2️⃣ ┊ No Spam or Unsolicited Self-Promotion",
                value="Avoid spamming text, emojis, or mass mentions. DM advertising or sending server invites without permission will result in an immediate ban.",
                inline=False
            )
            embed.add_field(
                name="3️⃣ ┊ Keep Content Safe for Work (SFW)",
                value="No NSFW, explicit, gore, or sexually suggestive media. Keep avatars, banners, and nicknames server-appropriate.",
                inline=False
            )
            embed.add_field(
                name="4️⃣ ┊ Channel Etiquette & Purpose",
                value="Use channels for their designated topic (e.g. music commands in <#1545534637122527332>, anime talk in <#1546097792915873842>).",
                inline=False
            )
            embed.add_field(
                name="5️⃣ ┊ Voice Channel Courtesy",
                value="Do not ear-rape, scream into microphones, or use aggressive soundboards. Respect music channel listening queues.",
                inline=False
            )
            embed.add_field(
                name="6️⃣ ┊ Staff & Moderator Discretion",
                value="Our Sentinel Staff have the final say. If you experience issues, open a ticket in <#1545514505520545886>.",
                inline=False
            )
            embed.set_footer(text="By participating in RAI FAM, you agree to Discord Terms of Service.", icon_url=bot.user.display_avatar.url)
            await rules_chan.send(embed=embed)
            print("  ✅ Posted Rules Embed!")

        # C. # ✨ ┊ verify-here (with interactive button)
        verify_chan = bot.get_channel(1545502700840427702)
        if verify_chan:
            try:
                async for m in verify_chan.history(limit=10):
                    if m.author == bot.user:
                        await m.delete()
            except Exception:
                pass

            from utils.persistent_views import VerifyButtonView
            bot.add_view(VerifyButtonView())

            embed = discord.Embed(
                title="🛡️ ＳＥＮＴＩＮＥＬ  ＶＥＲＩＦＩＣＡＴＩＯＮ 🛡️",
                description=(
                    "Welcome to **RAI FAM 💗**!\n\n"
                    "To safeguard our community against automated raid bots and spam, all new members must complete verification.\n\n"
                    "👉 **Click the green button below** to unlock full access to the server instantly!"
                ),
                color=0x00BFFF
            )
            embed.set_footer(text="Protected by RAI SENTINEL 🛡️ • 24/7 Active Defense")
            await verify_chan.send(embed=embed, view=VerifyButtonView())
            print("  ✅ Posted Verification Card with Interactive Button!")

        # D. # 🎀 ┊ self-roles
        roles_chan = bot.get_channel(1545502722739150898)
        if roles_chan:
            try:
                async for m in roles_chan.history(limit=10):
                    if m.author == bot.user:
                        await m.delete()
            except Exception:
                pass

            from utils.persistent_views import NotificationRolesView, GamingRolesView
            bot.add_view(NotificationRolesView())
            bot.add_view(GamingRolesView())

            embed1 = discord.Embed(
                title="📢 ＮＯＴＩＦＩＣＡＴＩＯＮ  ＲＯＬＥＳ",
                description="Select which server updates and announcements you wish to be pinged for:",
                color=0xDA70D6
            )
            await roles_chan.send(embed=embed1, view=NotificationRolesView())

            embed2 = discord.Embed(
                title="🎮 ＧＡＭＩＮＧ  ＲＯＬＥＳ",
                description="Pick your favorite games to find squad teammates and access gaming chats:",
                color=0x9B59B6
            )
            await roles_chan.send(embed=embed2, view=GamingRolesView())
            print("  ✅ Posted Self-Roles Panels!")

        await bot.close()

    await bot.start(TOKEN_VIBES)

if __name__ == "__main__":
    copy_images()
    update_guild_branding()
    update_channel_topics()
    asyncio.run(deploy_embeds())
    print("\n🎉 Full Server Aesthetic Transformation Complete!")
