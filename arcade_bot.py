import os
import sys
import socket
import asyncio
import logging
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Prevent discord.errors.InteractionResponded by making deferrals idempotent
_orig_context_defer = commands.Context.defer
async def _safe_context_defer(self, *args, **kwargs):
    if self.interaction and self.interaction.response.is_done():
        return
    return await _orig_context_defer(self, *args, **kwargs)
commands.Context.defer = _safe_context_defer

_orig_interaction_defer = discord.InteractionResponse.defer
async def _safe_interaction_defer(self, *args, **kwargs):
    if self.is_done():
        return
    return await _orig_interaction_defer(self, *args, **kwargs)
discord.InteractionResponse.defer = _safe_interaction_defer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

# Ensure single instance of RAI ARCADE using OS-level local socket mutex
_instance_lock_socket = None

def acquire_instance_lock(port: int = 59126) -> bool:
    global _instance_lock_socket
    if _instance_lock_socket is not None:
        return True
    _instance_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_lock_socket.bind(("127.0.0.1", port))
        return True
    except OSError:
        print(f"[CRITICAL] Another instance of RAI ARCADE is already running (Port {port} in use)!")
        print("[CRITICAL] Exiting immediately to prevent duplicate responses.")
        sys.exit(0)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("RaiArcade")

BOT_NAME = "RAI PLAY 🎮"

BANNER = """
  ██████╗  █████╗ ██╗    ██████╗ ██╗      █████╗ ██╗   ██╗
  ██╔══██╗██╔══██╗██║    ██╔══██╗██║     ██╔══██╗╚██╗ ██╔╝
  ██████╔╝███████║██║    ██████╔╝██║     ███████║ ╚████╔╝ 
  ██╔══██╗██╔══██║██║    ██╔═══╝ ██║     ██╔══██║  ╚██╔╝  
  ██║  ██║██║  ██║██║    ██║     ███████╗██║  ██║   ██║   
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝    ╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   
       🎮 RAI PLAY • ECONOMY • CASINO • MINIGAMES • SQUADS 🎮
"""

ARCADE_EXTENSIONS = [
    "cogs.economy",
    "cogs.casino",
    "cogs.leveling",
    "cogs.pets",
    "cogs.squads",
    "cogs.party_games",
    "cogs.arcade_panel",
    "cogs.anime",
    "cogs.lottery",
    "cogs.productivity",
    "cogs.suggestions",
    "cogs.giveaway",
    "cogs.exchange",
    "cogs.duels",
    "cogs.wyr",
    "cogs.quotes",
    # "cogs.qotd",  # Disabled Question of the Day per server preferences
    "cogs.bump_reminder",
    "cogs.welcome",
    "cogs.server_stats",
    "cogs.invites",
    "cogs.booster",
    "cogs.social",
    "cogs.starboard",
    "cogs.profile",
    "cogs.telemetry",
    "cogs.general",
    "cogs.lfg",
    "cogs.stream_alerts",
]

def create_arcade_bot(use_members: bool = True, use_message_content: bool = True) -> commands.Bot:
    intents = discord.Intents.default()
    intents.guilds = True
    if use_members:
        intents.members = True
    if use_message_content:
        intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

    @bot.event
    async def on_ready():
        print(BANNER)
        logger.info(f"🎮 Logged in as: {bot.user.name}#{bot.user.discriminator} ({bot.user.id})")
        logger.info(f"🎮 Powering games and economy across {len(bot.guilds)} server(s)")

        arcade_presences = [
            discord.Activity(type=discord.ActivityType.playing, name="🎮 RAI Arcade • /spin • /party • /lfg"),
            discord.Activity(type=discord.ActivityType.playing, name="🪙 High Rollers Casino • /spin • /blackjack"),
            discord.Activity(type=discord.ActivityType.playing, name="🐾 Virtual Pets & Squads • /pets • /squad"),
            discord.Activity(type=discord.ActivityType.playing, name="🪙 Server Economy • /daily • /shop"),
        ]

        @tasks.loop(minutes=3)
        async def arcade_status_rotator():
            idx = getattr(arcade_status_rotator, "idx", 0)
            try:
                await bot.change_presence(status=discord.Status.online, activity=arcade_presences[idx % len(arcade_presences)])
                arcade_status_rotator.idx = idx + 1
            except Exception:
                pass

        if not hasattr(bot, "_arcade_rotator_started"):
            bot._arcade_rotator_started = True
            arcade_status_rotator.start()

        # Update bot nickname in guilds
        for guild in bot.guilds:
            try:
                me = guild.me or await guild.fetch_member(bot.user.id)
                if me and me.guild_permissions.change_nickname:
                    await me.edit(nick=BOT_NAME)
            except Exception:
                pass

        # Register Persistent Views for instant interaction without 3s timeout
        from cogs.economy import ShopBuyView
        from cogs.exchange import ExchangeBoothView
        from cogs.giveaway import GiveawayView
        from cogs.suggestions import SuggestionVoteView
        from cogs.movie_party import MovieRSVPView
        from cogs.pets import PetCareView
        from cogs.lfg import LFGView
        from cogs.party_games import PartyGamesView
        from cogs.arcade_panel import ArcadeStationView

        views_to_register = [
            ShopBuyView(),
            ExchangeBoothView(),
            GiveawayView(),
            SuggestionVoteView(),
            MovieRSVPView(),
            PetCareView(owner_id=0),
            LFGView(),
            PartyGamesView(),
            ArcadeStationView(),
        ]

        for v in views_to_register:
            try:
                bot.add_view(v)
            except Exception as e:
                logger.debug(f"View init note: {e}")

        # Auto-apply 3D animated banner to RAI PLAY
        banner_path = os.path.join("assets", "rai_play_3d_banner.gif")
        if os.path.exists(banner_path):
            try:
                if not bot.user.banner or not str(bot.user.banner).startswith("a_"):
                    with open(banner_path, "rb") as f:
                        await bot.user.edit(banner=f.read())
                    logger.info("✨ [RAI PLAY] Successfully applied 3D animated GIF profile banner!")
            except Exception as e:
                logger.debug(f"[RAI PLAY] Banner update notice: {e}")

        # Synchronize slash commands:
        # 1. Clear any stale guild-scoped commands to prevent command collisions/shadowing
        # 2. Fast-sync to all current guilds for INSTANT zero-delay availability
        # 3. Synchronize globally
        try:
            for guild in bot.guilds:
                try:
                    bot.tree.clear_commands(guild=guild)
                    await bot.tree.sync(guild=guild)
                except Exception as ge:
                    logger.debug(f"Guild sync note for {guild.id}: {ge}")
            synced = await bot.tree.sync()
            logger.info(f"✨ [RAI ARCADE] Synchronized {len(synced)} global slash commands.")
        except Exception as e:
            logger.error(f"[RAI ARCADE] Command sync notice: {e}")

    @bot.hybrid_command(name="arcade_sync", description="Synchronize and refresh arcade slash commands with Discord.")
    @commands.is_owner()
    async def arcade_sync_cmd(ctx: commands.Context):
        """Owner command to refresh Arcade commands."""
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        try:
            if ctx.guild:
                bot.tree.clear_commands(guild=ctx.guild)
                await bot.tree.sync(guild=ctx.guild)
            synced = await bot.tree.sync()
            msg = f"🎮 Successfully synchronized {len(synced)} Arcade commands with Discord!"
        except Exception as e:
            msg = f"❌ Arcade sync failed: {e}"
        if ctx.interaction:
            await ctx.followup.send(msg, ephemeral=True)
        else:
            await ctx.send(msg)

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        msg = f"⚠️ [RAI ARCADE] An error occurred: {str(error)}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    return bot

async def load_arcade_cogs(bot_instance: commands.Bot):
    for ext in ARCADE_EXTENSIONS:
        try:
            await bot_instance.load_extension(ext)
            logger.info(f"🎮 Loaded arcade extension: {ext}")
        except Exception as e:
            logger.error(f"Failed to load arcade extension {ext}: {e}")

async def start_arcade_bot():
    token = os.getenv("COMMUNITY_BOT_TOKEN") or os.getenv("ARCADE_BOT_TOKEN")
    if not token or token.strip() in ("", "YOUR_COMMUNITY_BOT_TOKEN_HERE"):
        logger.info("ℹ️ [RAI ARCADE] No COMMUNITY_BOT_TOKEN found in .env. Arcade bot will remain idle until token is configured.")
        return

    acquire_instance_lock(59126)
    bot = create_arcade_bot(use_members=True, use_message_content=True)
    async with bot:
        await load_arcade_cogs(bot)
        try:
            await bot.start(token.strip())
        except discord.errors.PrivilegedIntentsRequired:
            logger.warning("[RAI ARCADE] Privileged intents not enabled in portal. Falling back to basic intents.")
            fallback_bot = create_arcade_bot(use_members=False, use_message_content=False)
            async with fallback_bot:
                await load_arcade_cogs(fallback_bot)
                await fallback_bot.start(token.strip())

if __name__ == "__main__":
    try:
        asyncio.run(start_arcade_bot())
    except KeyboardInterrupt:
        print(f"\n[RAI ARCADE 🎮] Shutting down cleanly. Good bye!")
