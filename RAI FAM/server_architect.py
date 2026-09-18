import asyncio
import logging
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, button
import colorama
from colorama import Fore, Style

import config
from server_template import ROLES_BLUEPRINT, CATEGORIES_BLUEPRINT

# Initialize Colorama & Logging
colorama.init(autoreset=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ServerArchitect")

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!setup_", intents=intents)


# =============================================================================
# INTERACTIVE SELF-ROLE VIEWS
# =============================================================================
class SelfRoleButton(Button):
    def __init__(self, role_name: str, label: str, emoji: str, style: discord.ButtonStyle, row: int):
        super().__init__(label=label, emoji=emoji, style=style, row=row, custom_id=f"selfrole_{role_name}")
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.role_name)
        if not role:
            return await interaction.response.send_message(f"❌ Role `{self.role_name}` not found on server.", ephemeral=True)

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
        self.add_item(SelfRoleButton("🍿 Movie Night Ping", "Movie Ping", "🍿", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("🎌 Anime Watcher", "Anime", "🎌", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("👻 Horror & Thriller Fan", "Horror", "👻", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("🚀 Sci-Fi & Action Fan", "Sci-Fi/Action", "🚀", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("😂 Comedy & Chill", "Comedy", "😂", discord.ButtonStyle.secondary, row=0))


class NotificationRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("📢 Announcement Ping", "Announcements", "📢", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("🎁 Giveaway Ping", "Giveaways", "🎁", discord.ButtonStyle.success, row=0))
        self.add_item(SelfRoleButton("⚡ Event Ping", "Events", "⚡", discord.ButtonStyle.secondary, row=0))


class GamingRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("🖥️ PC Gamer", "PC", "🖥️", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("🎮 Console Gamer", "Console", "🎮", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("📱 Mobile Gamer", "Mobile", "📱", discord.ButtonStyle.secondary, row=0))


class MusicRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("🎧 Hip-Hop / Rap", "Hip-Hop", "🎧", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("🔊 EDM / Bass", "EDM / Bass", "🔊", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("☕ Lo-Fi & Chill", "Lo-Fi", "☕", discord.ButtonStyle.success, row=0))


# =============================================================================
# VERIFICATION VIEW
# =============================================================================
class VerifyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Verify & Enter Community", emoji="✅", style=discord.ButtonStyle.success, custom_id="verify_member_btn")
    async def verify_button(self, interaction: discord.Interaction, btn: Button):
        guild = interaction.guild
        verified_role = discord.utils.get(guild.roles, name="👥 Verified Member")

        if not verified_role:
            return await interaction.response.send_message("❌ Verified role not found on server.", ephemeral=True)

        if verified_role in interaction.user.roles:
            return await interaction.response.send_message("✨ You are already verified! Enjoy the server.", ephemeral=True)

        try:
            await interaction.user.add_roles(verified_role, reason="Passed Verification Gate")
            await interaction.response.send_message("🎉 **Verification successful!** Welcome — all channels are now unlocked! 🍿🎵", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)


# =============================================================================
# TICKET SUPPORT VIEW
# =============================================================================
class TicketCreateView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Open Support Ticket", emoji="📩", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket_button(self, interaction: discord.Interaction, btn: Button):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name="🛡️ Moderator / Staff")
        cat = discord.utils.get(guild.categories, name="🛡️ ━━ ⋆⋅ STAFF HEADQUARTERS ⋅⋆ ━━")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_chan_name = f"ticket-{interaction.user.name[:12]}"
        existing = discord.utils.get(guild.channels, name=ticket_chan_name.lower())
        if existing:
            return await interaction.response.send_message(f"⚠️ You already have an open ticket: {existing.mention}", ephemeral=True)

        ticket_chan = await guild.create_text_channel(
            name=ticket_chan_name,
            category=cat,
            overwrites=overwrites,
            topic=f"Support ticket for {interaction.user.mention}"
        )

        embed = discord.Embed(
            title="📩 APEX SUPPORT TICKET",
            description=f"Welcome {interaction.user.mention}! Our staff team has been notified and will assist you shortly.",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="Apex Support Team", icon_url=config.RAI_ICON_URL)

        await ticket_chan.send(content=f"{interaction.user.mention} {staff_role.mention if staff_role else ''}", embed=embed)
        await interaction.response.send_message(f"✅ Ticket created! Head over to {ticket_chan.mention}", ephemeral=True)


# =============================================================================
# POST OFFICIAL EMBEDS
# =============================================================================
async def post_server_embeds(guild: discord.Guild, created_channels: dict):
    logger.info("Posting official embeds into Information channels...")

    # 1. Verification Gate Embed
    verify_chan = created_channels.get("╭・「✅」verify-here")
    if verify_chan:
        embed_v = discord.Embed(
            title="🛡️ APEX COMMUNITY • MEMBER VERIFICATION",
            description=(
                "Welcome to **APEX COMMUNITY & CHILLOUT LOUNGE**! 🍿🎵\n\n"
                "To prevent spam bots and keep our community friendly, safe, and neat, "
                "please click the **`[✅ Verify & Enter Community]`** button below to unlock all channels.\n\n"
                "By clicking verify, you agree to follow our server guidelines."
            ),
            color=config.COLOR_PRIMARY
        )
        embed_v.set_thumbnail(url=config.RAI_ICON_URL)
        embed_v.set_footer(text="Instant 1-Click Verification", icon_url=config.RAI_ICON_URL)
        await verify_chan.send(embed=embed_v, view=VerifyButtonView())

    # 2. Rules Embed
    rules_chan = created_channels.get("├・「📜」rules-guidelines")
    if rules_chan:
        embed1 = discord.Embed(
            title="📜 APEX COMMUNITY • OFFICIAL SERVER RULES",
            description=(
                "Welcome to **APEX CHILL & CINEMA**! 🍿\n\n"
                "**1. Treat Everyone with Respect**\n"
                "• No harassment, hate speech, bullying, toxicity, or discrimination.\n\n"
                "**2. Keep Channels Clean & Relevant**\n"
                "• Movie talks go in `├・「🍿」movie-discussion`.\n"
                "• Bot games go in `├・「🤖」bot-commands`.\n\n"
                "**3. Cinema & Voice Etiquette**\n"
                "• During movie nights, please mute your microphone or keep background noise minimal.\n\n"
                "**4. No Spamming or Self-Promotion**\n"
                "• Keep links and advertisements out of public channels."
            ),
            color=config.COLOR_PRIMARY
        )
        embed1.set_thumbnail(url=config.RAI_ICON_URL)
        embed1.set_footer(text="Apex Moderation Team • Respect & Chill", icon_url=config.RAI_ICON_URL)
        await rules_chan.send(embed=embed1)

    # 3. Interactive Self-Roles Embeds
    selfrole_chan = created_channels.get("├・「⭐」self-roles")
    if selfrole_chan:
        # Movies
        embed_movie = discord.Embed(
            title="🍿 MOVIE & ANIME ROLES",
            description="Select your favorite genres and get pinged when we host Movie Nights:",
            color=config.COLOR_GOLD
        )
        await selfrole_chan.send(embed=embed_movie, view=MovieRolesView())

        # Notifications
        embed_notif = discord.Embed(
            title="🔔 NOTIFICATION ROLES",
            description="Click buttons below for announcements, giveaways, and events:",
            color=config.COLOR_PRIMARY
        )
        await selfrole_chan.send(embed=embed_notif, view=NotificationRolesView())

        # Gaming & Music
        embed_gm = discord.Embed(
            title="🎮 GAMING & 🎧 MUSIC TASTE ROLES",
            description="Pick your gaming platforms and favorite music vibes:",
            color=config.COLOR_PURPLE
        )
        await selfrole_chan.send(embed=embed_gm, view=GamingRolesView())
        await selfrole_chan.send(view=MusicRolesView())

    # 4. Movie Schedule Announcement Embed
    movie_sched_chan = created_channels.get("╭・「🎬」movie-schedule")
    if movie_sched_chan:
        embed_m = discord.Embed(
            title="🎬 APEX CINEMA • UPCOMING WATCH PARTIES",
            description=(
                "Welcome to **Apex Cinema**! 🍿\n\n"
                "We host community movie nights, anime marathons, and watch parties right here in Discord screen share!\n\n"
                "**How It Works:**\n"
                "• Get the 🍿 **Movie Night Ping** in `├・「⭐」self-roles` to be alerted when a stream starts.\n"
                "• Suggest movies in `╰・「📺」movie-suggestions`.\n"
                "• Join `🎥・Cinema Theater 1` to watch together!"
            ),
            color=config.COLOR_GOLD
        )
        embed_m.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2809/2809590.png")
        embed_m.set_footer(text="Apex Cinema & Chill", icon_url=config.RAI_ICON_URL)
        await movie_sched_chan.send(embed=embed_m)

    # 5. Ticket Embed
    ticket_chan = created_channels.get("╰・「🎫」create-ticket")
    if ticket_chan:
        embed_ticket = discord.Embed(
            title="🎫 NEED HELP? OPEN A SUPPORT TICKET",
            description="Click the button below to open a private ticket with our Staff Team for questions, reports, or partnerships.",
            color=config.COLOR_PRIMARY
        )
        embed_ticket.set_footer(text="Apex Community Support", icon_url=config.RAI_ICON_URL)
        await ticket_chan.send(embed=embed_ticket, view=TicketCreateView())

    # 6. Music Guide Embed
    music_chan = created_channels.get("╭・「🎵」music-commands")
    if music_chan:
        embed3 = discord.Embed(
            title="🎵 APEX VIBES • MUSIC BOT GUIDE",
            description=(
                "**Play High Quality Music & Lo-Fi 24/7!**\n\n"
                "• `/play <song>` or `@APEX VIBES play <song>` - Play from YouTube or Spotify\n"
                "• `/search <song>` - Top 5 Interactive Dropdown Selection\n"
                "• `/bassboost <level>` - Boost sub-bass from Low to Extreme\n"
                "• `/volume <0-200>` - Up to 200% Super Boost\n"
                "• `/radio <lofi|synthwave|rock|jazz>` - 24/7 Live Radio\n"
                "• `/movie_schedule` - Schedule a movie night"
            ),
            color=config.COLOR_PRIMARY
        )
        embed3.set_thumbnail(url=config.RAI_ICON_URL)
        embed3.set_footer(text="RAI VIBES 💗 • HD Audio System", icon_url=config.RAI_ICON_URL)
        await music_chan.send(embed=embed3)


# =============================================================================
# SERVER STRUCTURING EXECUTION
# =============================================================================
async def build_server(guild: discord.Guild):
    print(f"\n{Fore.CYAN}=" * 70)
    print(f"{Fore.YELLOW}⚡ RE-STRUCTURING SERVER INTO CHILL, CINEMA & MUSIC FOR: {guild.name} (ID: {guild.id})")
    print(f"{Fore.CYAN}=" * 70)

    # 1. Setup Roles
    logger.info("Building Role Hierarchy & Self-Roles...")
    existing_roles = {r.name: r for r in guild.roles}
    created_roles = {}

    for r_data in reversed(ROLES_BLUEPRINT):
        role_name = r_data["name"]
        if role_name in existing_roles:
            created_roles[role_name] = existing_roles[role_name]
        else:
            try:
                new_role = await guild.create_role(
                    name=role_name,
                    color=r_data["color"],
                    hoist=r_data.get("hoist", False),
                    mentionable=r_data.get("mentionable", False),
                    permissions=r_data.get("permissions", discord.Permissions.none()),
                    reason="Apex Server Chill & Cinema Setup"
                )
                logger.info(f"{Fore.GREEN}Created Role: '{role_name}'")
                created_roles[role_name] = new_role
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Failed to create role '{role_name}': {e}")

    # 2. Setup Categories & Channels
    logger.info("Building Aesthetic Categories, Cinema, and Channels...")
    created_channels_map = {}
    staff_role = created_roles.get("🛡️ Moderator / Staff")

    for cat_data in CATEGORIES_BLUEPRINT:
        cat_name = cat_data["name"]
        existing_cat = discord.utils.get(guild.categories, name=cat_name)

        if not existing_cat:
            try:
                category = await guild.create_category(cat_name, reason="Apex Server Setup")
                logger.info(f"{Fore.CYAN}Created Category: '{cat_name}'")
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Failed to create category '{cat_name}': {e}")
                continue
        else:
            category = existing_cat

        for ch_data in cat_data["channels"]:
            ch_name = ch_data["name"]
            existing_ch = discord.utils.get(category.channels, name=ch_name)

            if existing_ch:
                created_channels_map[ch_name] = existing_ch
                continue

            # Permission Overwrites
            overwrites = {}
            if ch_data.get("locked"):
                overwrites[guild.default_role] = discord.PermissionOverwrite(connect=False, read_messages=True)
            elif ch_data.get("read_only"):
                overwrites[guild.default_role] = discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=True)
            elif ch_data.get("staff_only"):
                overwrites[guild.default_role] = discord.PermissionOverwrite(read_messages=False)
                if staff_role:
                    overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            try:
                if ch_data["type"] == "text":
                    new_ch = await guild.create_text_channel(
                        name=ch_name,
                        category=category,
                        topic=ch_data.get("topic"),
                        overwrites=overwrites,
                        reason="Apex Server Setup"
                    )
                elif ch_data["type"] == "voice":
                    new_ch = await guild.create_voice_channel(
                        name=ch_name,
                        category=category,
                        user_limit=ch_data.get("user_limit", 0),
                        bitrate=ch_data.get("bitrate", 64000),
                        overwrites=overwrites,
                        reason="Apex Server Setup"
                    )
                logger.info(f"{Fore.GREEN}Created Channel: '{ch_name}'")
                created_channels_map[ch_name] = new_ch
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Failed to create channel '{ch_name}': {e}")

    # 3. Post Formatted Embeds
    await post_server_embeds(guild, created_channels_map)

    print(f"\n{Fore.GREEN}=" * 70)
    print(f"{Fore.GREEN}✅ CHILL, CINEMA & MUSIC SETUP COMPLETED SUCCESSFULLY FOR '{guild.name}'!")
    print(f"{Fore.YELLOW}Your aesthetic chillout server with movie night channels & verification is live!")
    print(f"{Fore.GREEN}=" * 70)


@bot.event
async def on_ready():
    logger.info(f"Logged in as: {bot.user.name}#{bot.user.discriminator}")
    
    target_guild = bot.get_guild(config.TARGET_GUILD_ID)
    if not target_guild and bot.guilds:
        target_guild = bot.guilds[0]

    if target_guild:
        await build_server(target_guild)
    else:
        logger.error(f"Bot is not in server ID: {config.TARGET_GUILD_ID}")

    await bot.close()


def main():
    bot.run(config.DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()
