import asyncio
import os
import sys
from pathlib import Path
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from utils.persistent_views import ColorRolesView

GUILD_ID = 1457382179981099090
RULES_CHANNEL_ID = 1545502710101704714
ROLES_CHANNEL_ID = 1545502722739150898

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found!")
        await client.close()
        return

    print(f"Deploying Everglow Cards to {guild.name}...")

    # 1. Deploy Color Role Picker in #roles
    roles_ch = guild.get_channel(ROLES_CHANNEL_ID)
    if roles_ch:
        embed_color = discord.Embed(
            title="🎨 ┊ ᯓ ⋆ AESTHETIC NAME COLOR PALETTE ⋆ ᯓ",
            description=(
                "✦ ───────────────────────────────────── ✦\n\n"
                "### ✨ **Customize Your Chat Color**\n"
                "Select your favorite Everglow aesthetic hue below to color your username across the entire server!\n\n"
                "🌸 **Sakura Pink** — Soft radiant blossom glow\n"
                "💜 **Neon Purple** — Cosmic lavender starlight\n"
                "🩵 **Cyber Cyan** — Electric aurora teal\n"
                "💛 **Royal Gold** — Warm sovereign amber\n\n"
                "✦ ───────────────────────────────────── ✦\n"
                "*Click any button below to equip. Clicking again will remove your color.*"
            ),
            color=0xFF758C
        )
        embed_color.set_footer(text="RAI VIBES 💗 • Everglow Identity Engine", icon_url=config.RAI_ICON_URL)
        await roles_ch.send(embed=embed_color, view=ColorRolesView())
        print("1. Deployed Everglow Color Palette Selector to #roles")

    # 2. Deploy Everglow Rules & Guidelines in #rules-and-info
    rules_ch = guild.get_channel(RULES_CHANNEL_ID)
    if rules_ch:
        embed_rules = discord.Embed(
            title="📜 ┊ ᯓ ⋆ RAI FAM COMMUNITY CODEX & RULES ⋆ ᯓ",
            description=(
                "✦ ───────────────────────────────────── ✦\n\n"
                "### 🌟 **Welcome to RAI FAM & RAI VIBES**\n"
                "To ensure a chill, high-energy gaming and hangout environment, all members agree to the following standards:\n\n"
                "**1. Respect & Etiquette 🤝**\n"
                "• Treat every member, streamer, and guest with mutual respect.\n"
                "• No harassment, toxic hate speech, racism, or discriminatory behavior.\n\n"
                "**2. Content Standards 🛡️**\n"
                "• Strictly family-safe and clean community vibes (No NSFW / Explicit content).\n"
                "• Keep topics focused on gaming, music, tech, art, and good vibes.\n\n"
                "**3. Anti-Spam & Clean Comms 🔇**\n"
                "• No mic-spamming, ear-rape audio, or screaming in public voice lounges.\n"
                "• Keep bot commands in <#1549416359723532480> and gaming clips in <#1551184138932068373>.\n\n"
                "**4. No Unauthorized Promotion 🚫**\n"
                "• No unsolicited server invites or DM advertising.\n"
                "• Partner with us legitimately in <#1550159859607928882>!\n\n"
                "**5. Activity Tiers & Rewards 👑**\n"
                "• Level up passively by chatting and chilling in VCs to unlock exclusive perks:\n"
                "  `Level 5:` ✨・Starlight Initiate • `Level 15:` 🌸・Aurora Voyager\n"
                "  `Level 30:` 💫・Nebula Elite • `Level 50:` 👑・Celestial Sovereign\n\n"
                "✦ ───────────────────────────────────── ✦\n"
                "*Need help? Open a private ticket in <#1545514505520545886> anytime.*"
            ),
            color=0x70A1FF
        )
        embed_rules.set_footer(text="RAI FAM 💗 • Everglow Official Guidelines", icon_url=config.RAI_ICON_URL)
        await rules_ch.send(embed=embed_rules)
        print("2. Deployed Everglow Community Codex & Rules to #rules-and-info")

    print("Deployment finished successfully!")
    await client.close()

client.run(os.getenv("DISCORD_BOT_TOKEN"))
