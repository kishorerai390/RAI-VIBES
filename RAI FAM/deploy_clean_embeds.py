import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import asyncio
import discord
from discord.ui import View, Button, button
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

# Embed Colors (Sakura Pink & Radiant Gold)
COLOR_PINK = 0xFF69B4
COLOR_PURPLE = 0x9B59B6
COLOR_GOLD = 0xF1C40F
COLOR_DARK = 0x18191C

# Interactive Self-Role Views
class SelfRoleButton(Button):
    def __init__(self, role_name: str, label: str, emoji: str, style: discord.ButtonStyle, row: int = 0):
        super().__init__(label=label, emoji=emoji, style=style, row=row, custom_id=f"selfrole_{role_name}")
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.role_name)
        if not role:
            return await interaction.response.send_message(f"❌ Role `{self.role_name}` not found.", ephemeral=True)

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"➖ **Removed Role:** {role.mention}", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"➕ **Added Role:** {role.mention}", ephemeral=True)


class MovieRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("🍿 Movie Night Ping", "Movie Ping", "🍿", discord.ButtonStyle.primary))
        self.add_item(SelfRoleButton("🎌 Anime Watcher", "Anime", "🎌", discord.ButtonStyle.secondary))
        self.add_item(SelfRoleButton("👻 Horror & Thriller Fan", "Horror", "👻", discord.ButtonStyle.secondary))
        self.add_item(SelfRoleButton("🚀 Sci-Fi & Action Fan", "Sci-Fi/Action", "🚀", discord.ButtonStyle.secondary))
        self.add_item(SelfRoleButton("😂 Comedy & Chill", "Comedy", "😂", discord.ButtonStyle.secondary))


class NotificationRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("📢 Announcement Ping", "Announcements", "📢", discord.ButtonStyle.primary))
        self.add_item(SelfRoleButton("🎁 Giveaway Ping", "Giveaways", "🎁", discord.ButtonStyle.success))
        self.add_item(SelfRoleButton("⚡ Event Ping", "Events", "⚡", discord.ButtonStyle.secondary))


class MusicRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("🎧 Hip-Hop / Rap", "Hip-Hop", "🎧", discord.ButtonStyle.secondary))
        self.add_item(SelfRoleButton("🔊 EDM / Bass", "EDM / Bass", "🔊", discord.ButtonStyle.primary))
        self.add_item(SelfRoleButton("☕ Lo-Fi & Chill", "Lo-Fi", "☕", discord.ButtonStyle.success))


class VerifyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Verify & Enter Community", emoji="✅", style=discord.ButtonStyle.success, custom_id="verify_member_btn")
    async def verify_button(self, interaction: discord.Interaction, btn: Button):
        guild = interaction.guild
        verified_role = discord.utils.get(guild.roles, name="👥 Verified Member")
        if not verified_role:
            try:
                verified_role = await guild.create_role(name="👥 Verified Member", color=discord.Color.from_rgb(149, 165, 166))
            except Exception:
                return await interaction.response.send_message("❌ Verified role not found.", ephemeral=True)

        if verified_role in interaction.user.roles:
            return await interaction.response.send_message(f"✨ You are already verified in **{guild.name}**!", ephemeral=True)

        try:
            await interaction.user.add_roles(verified_role)
            await interaction.response.send_message(f"🎉 **Verification successful!** Welcome to **{guild.name}** — all channels unlocked! 💗🍿🎵", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)


class TicketCreateView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Open Support Ticket", emoji="📩", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket_button(self, interaction: discord.Interaction, btn: Button):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name="🛡️ Moderator / Staff")
        cat = discord.utils.get(guild.categories, name="🛡️ ━━ ⋆⋅ STAFF HEADQUARTERS ⋅⋆ ━━")

        ticket_channel_name = f"ticket-{interaction.user.name.lower()}"
        existing = discord.utils.get(guild.text_channels, name=ticket_channel_name)
        if existing:
            return await interaction.response.send_message(f"⚠️ You already have an open ticket: {existing.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)

        try:
            ticket_chan = await guild.create_text_channel(
                name=ticket_channel_name,
                category=cat,
                overwrites=overwrites,
                reason=f"Support ticket for {interaction.user.name}"
            )
            embed = discord.Embed(
                title="📩 Private Support Ticket",
                description=f"Hello {interaction.user.mention}! Our staff team has been notified.\nPlease describe how we can assist you.",
                color=COLOR_PINK
            )
            await ticket_chan.send(content=f"{interaction.user.mention} {staff_role.mention if staff_role else ''}", embed=embed)
            await interaction.response.send_message(f"✅ Ticket created! Please go to {ticket_chan.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Could not create ticket: {e}", ephemeral=True)


client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    print(f"🚀 Deploying fresh, branded embeds for {guild.name}...")

    # 1. VERIFICATION GATE
    v_chan = discord.utils.get(guild.text_channels, name="╭・「✅」verify-here")
    if v_chan:
        await v_chan.purge(limit=10)
        v_embed = discord.Embed(
            title=f"🌸 {guild.name.upper()} • MEMBER VERIFICATION 🌸",
            description=(
                f"Welcome to **{guild.name}**! 💗🍿🎵\n\n"
                "We are a cozy, aesthetic community for **streaming movies, listening to high-fidelity music, and chilling with friends**.\n\n"
                "🛡️ **To prevent bots and unlock all channels:**\n"
                "Click the green **`[✅ Verify & Enter Community]`** button below!\n\n"
                "*(By verifying, you agree to treat everyone with respect and follow server rules.)*"
            ),
            color=COLOR_PINK
        )
        v_embed.set_thumbnail(url=guild.icon.url if guild.icon else "https://cdn-icons-png.flaticon.com/512/9422/9422896.png")
        v_embed.set_footer(text=f"{guild.name} • Instant 1-Click Verification", icon_url=guild.icon.url if guild.icon else None)
        await v_chan.send(embed=v_embed, view=VerifyButtonView())
        print("✅ Sent Verification Gate Embed!")

    # 2. RULES EMBED
    r_chan = discord.utils.get(guild.text_channels, name="├・「📜」rules-guidelines")
    if r_chan:
        await r_chan.purge(limit=10)
        r_embed = discord.Embed(
            title=f"📜 {guild.name.upper()} • OFFICIAL GUIDELINES 📜",
            description=(
                "**1️⃣ Respect & Good Vibes:**\n"
                "Treat all members with kindness. Harassment, hate speech, or toxicity will result in an immediate timeout or ban.\n\n"
                "**2️⃣ No Spam & Clean Chat:**\n"
                "Avoid spamming messages, emojis, or mass-tagging members. Keep media in `#├・「📸」media-gallery`.\n\n"
                "**3️⃣ Voice & Cinema Etiquette:**\n"
                "Do not mic-spam or scream in voice lounges. During movie streams in `🎥・Cinema Theater`, mute your mic unless discussing the film.\n\n"
                "**4️⃣ Music & Commands:**\n"
                "Use `/play <song>` in `#╭・「🎵」music-commands` or any voice chat. Respect queue orders.\n\n"
                "**5️⃣ Follow Discord ToS:**\n"
                "All members must adhere to Discord Community Guidelines."
            ),
            color=COLOR_GOLD
        )
        r_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2237/2237931.png")
        r_embed.set_footer(text=f"{guild.name} • Chill & Safe Community", icon_url=guild.icon.url if guild.icon else None)
        await r_chan.send(embed=r_embed)
        print("✅ Sent Rules Embed!")

    # 3. SELF-ROLES EMBEDS
    s_chan = discord.utils.get(guild.text_channels, name="├・「⭐」self-roles")
    if s_chan:
        await s_chan.purge(limit=10)

        # Cinema & Movie Roles
        embed_movie = discord.Embed(
            title="🍿 Cinema & Watch Party Roles",
            description="Click the buttons below to receive notifications when we stream movies, anime, or shows!",
            color=COLOR_PINK
        )
        await s_chan.send(embed=embed_movie, view=MovieRolesView())

        # Notification & Event Roles
        embed_pings = discord.Embed(
            title="📢 Server Announcements & Giveaways",
            description="Toggle notifications for server updates, community giveaways, and special events.",
            color=COLOR_GOLD
        )
        await s_chan.send(embed=embed_pings, view=NotificationRolesView())

        # Music Roles
        embed_music = discord.Embed(
            title="🎵 Music Genre & Audio Roles",
            description="Pick your favorite genres to vibe with other music lovers!",
            color=COLOR_PURPLE
        )
        await s_chan.send(embed=embed_music, view=MusicRolesView())
        print("✅ Sent Self-Roles Embeds!")

    # 4. TICKET SUPPORT EMBED
    t_chan = discord.utils.get(guild.text_channels, name="╰・「🎫」create-ticket")
    if t_chan:
        await t_chan.purge(limit=10)
        t_embed = discord.Embed(
            title=f"🎫 {guild.name.upper()} • SUPPORT & HELP",
            description=(
                "Need assistance, want to report an issue, or ask questions to the staff team?\n\n"
                "Click **`[📩 Open Support Ticket]`** below to create a private channel with server moderators."
            ),
            color=COLOR_PINK
        )
        t_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2065/2065207.png")
        t_embed.set_footer(text=f"{guild.name} • 24/7 Support Desk", icon_url=guild.icon.url if guild.icon else None)
        await t_chan.send(embed=t_embed, view=TicketCreateView())
        print("✅ Sent Ticket Embed!")

    print("\n🎉 ALL EMBEDS DEPLOYED SUCCESSFULLY WITH 'RAI FAM💗' BRANDING!")
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
