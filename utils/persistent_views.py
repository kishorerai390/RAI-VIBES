import unicodedata
import discord
from discord.ui import View, Button, button

ROLE_ID_MAP = {
    # Gaming Squads
    "Free Fire": 1545516397034078269,
    "BGMI": 1545516399663779871,
    "Roblox": 1545516402188881991,
    "PC Gaming": 1546062595293978694,

    # Notifications & Pings
    "Announcements": 1546088542885642324,
    "Giveaways": 1546088546555924534,
    "Tournaments": 1546088548913119323,
    "Movie Nights": 1546062599253135420,

    # Member Identification
    "Male": 1546095934935531520,
    "Female": 1546095937015910434,
    "18+ Adult": 1546095939582828616,
    "Under 18": 1546095941818392647,
}

COLOR_ROLE_IDS = [
    1546088552293728268, # Sakura Pink
    1546088554747142174, # Neon Purple
    1546088557742129232, # Cyber Cyan
    1546088559830634586, # Royal Gold
]

def find_role_by_key(guild: discord.Guild, key: str) -> discord.Role | None:
    role_id = ROLE_ID_MAP.get(key)
    if role_id:
        r = guild.get_role(role_id)
        if r:
            return r
    for r in guild.roles:
        norm = unicodedata.normalize('NFKD', r.name).upper()
        if key.upper() in norm:
            return r
    return None

class SelfRoleButton(Button):
    def __init__(self, key: str, label: str, emoji: str, style: discord.ButtonStyle, row: int = 0):
        super().__init__(label=label, emoji=emoji, style=style, row=row, custom_id=f"selfrole_{key.replace(' ', '_').lower()}")
        self.key = key

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if not guild:
            return await interaction.followup.send("❌ Server error.", ephemeral=True)

        role = find_role_by_key(guild, self.key)
        if not role:
            return await interaction.followup.send(f"❌ Role for `{self.key}` not found.", ephemeral=True)

        member = interaction.user
        if isinstance(member, discord.User):
            member = await guild.fetch_member(interaction.user.id)

        if role in member.roles:
            await member.remove_roles(role, reason="Self-Role Toggle Off")
            await interaction.followup.send(f"⚪ Removed **{role.name}**", ephemeral=True)
        else:
            await member.add_roles(role, reason="Self-Role Toggle On")
            await interaction.followup.send(f"✅ Equipped **{role.name}**!", ephemeral=True)


class ColorRoleButton(Button):
    def __init__(self, key: str, label: str, emoji: str, style: discord.ButtonStyle, row: int = 0):
        super().__init__(label=label, emoji=emoji, style=style, row=row, custom_id=f"colorrole_{key.replace(' ', '_').lower()}")
        self.key = key

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if not guild:
            return await interaction.followup.send("❌ Server error.", ephemeral=True)

        role = find_role_by_key(guild, self.key)
        if not role:
            return await interaction.followup.send(f"❌ Color role for `{self.key}` not found.", ephemeral=True)

        member = interaction.user
        if isinstance(member, discord.User):
            member = await guild.fetch_member(interaction.user.id)

        if role in member.roles:
            await member.remove_roles(role, reason="Removed Color Role")
            return await interaction.followup.send(f"⚪ Removed color: **{role.name}**", ephemeral=True)

        # Remove other active color roles first so member only has 1 name color
        roles_to_strip = [r for r in member.roles if r.id in COLOR_ROLE_IDS and r.id != role.id]
        if roles_to_strip:
            await member.remove_roles(*roles_to_strip, reason="Switching Color Role")

        await member.add_roles(role, reason="Equipped Color Role")
        await interaction.followup.send(f"🎨 **Equipped Name Color:** {role.mention}!", ephemeral=True)


class GamingRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("Free Fire", "Free Fire", "💥", discord.ButtonStyle.danger, row=0))
        self.add_item(SelfRoleButton("BGMI", "BGMI", "⚡", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("GTA RP", "GTA RP", "🔫", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("Roblox", "Roblox", "🧸", discord.ButtonStyle.secondary, row=0))


class NotificationRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("Announcements", "Announcements", "📢", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("Giveaways", "Giveaways", "🎁", discord.ButtonStyle.success, row=0))
        self.add_item(SelfRoleButton("Tournaments", "Tournaments", "🏆", discord.ButtonStyle.danger, row=0))
        self.add_item(SelfRoleButton("Movie Nights", "Movie Nights", "🍿", discord.ButtonStyle.secondary, row=0))


class ColorRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ColorRoleButton("Sakura Pink", "Sakura Pink", "🌸", discord.ButtonStyle.secondary, row=0))
        self.add_item(ColorRoleButton("Neon Purple", "Neon Purple", "💜", discord.ButtonStyle.primary, row=0))
        self.add_item(ColorRoleButton("Cyber Cyan", "Cyber Cyan", "🩵", discord.ButtonStyle.secondary, row=0))
        self.add_item(ColorRoleButton("Royal Gold", "Royal Gold", "💛", discord.ButtonStyle.success, row=0))


class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Close & Delete Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.send_message("🔒 Ticket will be deleted in 3 seconds...", ephemeral=False)
        await discord.utils.sleep_until(discord.utils.utcnow())
        try:
            await interaction.channel.delete(reason="Ticket closed by user/staff")
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to delete ticket: {e}", ephemeral=True)


class IdentityRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("Male", "Male", "👦", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("Female", "Female", "👧", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("18+ Adult", "18+ Adult", "🔞", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("Under 18", "Under 18", "🎒", discord.ButtonStyle.secondary, row=0))


from cogs.verify import VerifyButtonView, VerifiedNextStepsView



class TicketCreateView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Open Support Ticket", emoji="📩", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket_button(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name="🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️") or discord.utils.get(guild.roles, name="M O D E R A T O R 🛡️")
        cat = discord.utils.get(guild.categories, name="🛡️ | 𝑺𝑬𝑵𝑻𝑰𝑵𝑬𝑳 𝑫𝑬𝑭𝑬𝑵𝑺𝑬") or discord.utils.get(guild.categories, name="🛡️ | 𝙎𝙏𝘼𝙁𝙁 𝙕𝙊𝙉𝙀")

        ticket_channel_name = f"ticket-{interaction.user.name.lower()}"
        existing = discord.utils.get(guild.text_channels, name=ticket_channel_name)
        if existing:
            return await interaction.followup.send(f"⚠️ You already have an open ticket: {existing.mention}", ephemeral=True)

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
                description=(
                    f"Hello {interaction.user.mention}! Our staff team has been notified.\n\n"
                    f"Please state your question or issue below.\n"
                    f"Click **`[🔒 Close & Delete Ticket]`** once your issue is resolved!"
                ),
                color=0xFF69B4
            )
            await ticket_chan.send(content=f"{interaction.user.mention} {staff_role.mention if staff_role else ''}", embed=embed, view=TicketCloseView())
            await interaction.followup.send(f"✅ Ticket created! Please go to {ticket_chan.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Could not create ticket: {e}", ephemeral=True)


class ServerGuideSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Dynamic Voice Hub & Ghost Chambers",
                value="guide_voice",
                description="How to generate & manage dynamic voice channels",
                emoji="🎙️"
            ),
            discord.SelectOption(
                label="Audio Studio & Zero-Prefix Requests",
                value="guide_music",
                description="Instant songs in song-requests without commands",
                emoji="🎵"
            ),
            discord.SelectOption(
                label="Community Ideas & Voting Cards",
                value="guide_suggestions",
                description="How suggestions turn into interactive cards",
                emoji="💡"
            ),
            discord.SelectOption(
                label="Economy, Daily Streaks & Shop",
                value="guide_economy",
                description="Earn coins, boost streaks & claim role perks",
                emoji="💰"
            ),
            discord.SelectOption(
                label="Security Gate & Role Customization",
                value="guide_security",
                description="Verification, rules codex & color styles",
                emoji="🛡️"
            ),
            discord.SelectOption(
                label="Virtual Companion Pets & Nickname Badges",
                value="guide_pets",
                description="Adopt pets & display badges beside your nickname",
                emoji="🐾"
            ),
            discord.SelectOption(
                label="Cyber Casino & Minigames Hub",
                value="guide_casino",
                description="Blackjack, Slots, Coinflip & Music Quiz in gaming-hub",
                emoji="🎰"
            ),
            discord.SelectOption(
                label="Voice Clans & Squad Wars",
                value="guide_squads",
                description="Form squads, clan tags, and voice XP leaderboards",
                emoji="👥"
            ),
            discord.SelectOption(
                label="Movie Nights & Aesthetic Quote Cards",
                value="guide_community",
                description="Watch-party RSVPs & quotes in media-gallery",
                emoji="🍿"
            ),
        ]
        super().__init__(
            placeholder="🧭 Select a guide topic to explore...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="server_guide_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        val = self.values[0]

        if val == "guide_voice":
            embed = discord.Embed(
                title="🎙️ Dynamic Voice Hubs & Ghost Chambers",
                description=(
                    "**How to Create Your Voice Suite:**\n"
                    "1. Join **`➕ ┊ ᴊᴏɪɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ`** (Public) or **`🔒 ┊ ᴄʀᴇᴀᴛᴇ ɢʜᴏꜱᴛ ᴠᴄ`** (Hidden).\n"
                    "2. The bot instantly spawns your private channel and moves you in!\n\n"
                    "**🎛️ Voice Panel Controls (`/voicepanel`):**\n"
                    "• **🔒 Lock / 🔓 Unlock**: Allow or disallow server members from joining.\n"
                    "• **👻 Ghost Mode**: Make your room completely invisible to uninvited users.\n"
                    "• **👥 Member Limit**: Cap the maximum squad capacity (0 = unlimited).\n"
                    "• **✉️ Permit / 🚫 Revoke**: Grant or deny channel access to specific friends.\n"
                    "• **👑 Transfer Host**: Pass room ownership to a squadmate.\n\n"
                    "**🔊 VIP Entrance Fanfares (`/entrysound`):**\n"
                    "• `/entrysound preview [theme]` — Listen to available entrance themes.\n"
                    "• `/entrysound set [theme]` — Equip your signature entry & exit sound.\n"
                    "• `/entrysound upload [file]` — VIPs can upload custom audio files (mp3/wav/ogg) directly!"
                ),
                color=0xFF69B4
            )
        elif val == "guide_music":
            embed = discord.Embed(
                title="🎵 Audio Studio & Zero-Prefix Music Queue",
                description=(
                    "**⚡ Zero-Prefix Song Requests:**\n"
                    "Go to **`#🎵・ꜱᴏɴɢ-ʀᴇǫᴜᴇꜱᴛꜱ`** and send **any song name or URL** directly!\n"
                    "*No command prefix needed — our bot automatically detects and queues your track.*\n\n"
                    "**🎚️ Core Music Commands:**\n"
                    "• `/play <query>` — Play or queue audio in your current voice room.\n"
                    "• `/pause` & `/resume` — Pause or resume playback.\n"
                    "• `/skip` — Skip to the next track in queue.\n"
                    "• `/queue` — View upcoming queued tracks.\n"
                    "• `/np` — View now playing track details and live progress bar.\n"
                    "• `/volume <1-150>` — Adjust bot audio playback volume.\n"
                    "• `/filters` — Enable 8D, Bassboost, Nightcore, or Vaporwave audio filters.\n\n"
                    "**🌧️ 24/7 Lo-Fi Chill Zone:**\n"
                    "Hop into **`🌧️ ┊ ʟᴏ-ꜰɪ ᴢᴏɴᴇ`** for 24/7 uninterrupted chill & study beats!"
                ),
                color=0x9B59B6
            )
        elif val == "guide_suggestions":
            embed = discord.Embed(
                title="💡 Community Ideas & Interactive Voting",
                description=(
                    "**Submit Your Feedback & Ideas:**\n"
                    "• Simply send your suggestion in **`#💡・ꜱᴜɢɢᴇꜱᴛɪᴏɴꜱ`** or use `/suggest <idea>`.\n\n"
                    "**🗳️ Interactive Voting Cards:**\n"
                    "• Every proposal is formatted into a Cyber-Pink community card.\n"
                    "• Click **`👍 Upvote`** or **`👎 Downvote`** to cast your vote.\n"
                    "• Votes are recorded persistently and members can adjust their vote anytime.\n\n"
                    "**📈 Community Roadmap Status:**\n"
                    "• 🟡 **Pending Review** — Under active community voting.\n"
                    "• 🟢 **Implemented** — Staff approved and shipped to server!\n"
                    "• 🔴 **Declined** — Rejected or not feasible at this time."
                ),
                color=0x00E5FF
            )
        elif val == "guide_economy":
            embed = discord.Embed(
                title="💰 Economy, Daily Streaks & Server Shop",
                description=(
                    "**🪙 How to Earn Coins & XP:**\n"
                    "• **Daily Bonus (`/daily`)**: Claim free coins every 24 hours. Keep your daily streak going to unlock massive streak multipliers (up to 2x at Day 7+)!\n"
                    "• **Chat Activity**: Earn XP and coins automatically by engaging in text channels.\n"
                    "• **Voice Rewards**: Earn passive coins and XP by hanging out with squadmates in voice channels.\n\n"
                    "**🛒 Server Shop (`#🛒・ꜱᴇʀᴠᴇʀ-ꜱʜᴏᴘ`):**\n"
                    "Spend your earned coins on luxury perks:\n"
                    "• 🎨 **Custom Name Colors**: Sakura Pink, Neon Purple, Cyber Cyan, Royal Gold.\n"
                    "• 🎧 **DJ Pass**: Full bypass control of the server music queue.\n"
                    "• 🔊 **VIP Entrance Themes**: Access to exclusive soundboard fanfares.\n"
                    "• 📁 **Custom Audio Pass**: Upload your own personal sound files directly to Discord!\n\n"
                    "**Check Status:** `/balance`, `/leaderboard`"
                ),
                color=0xFFD700
            )
        elif val == "guide_security":
            embed = discord.Embed(
                title="🛡️ Security Gate, Rules & Identity Customization",
                description=(
                    "**✨ Single-Click Verification:**\n"
                    "Click the verify button in **`#✨・ᴠᴇʀɪꜰʏ-ʜᴇʀᴇ`** to instantly join the `🌸 ✧ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘` and receive a +100 Coins & +50 XP welcome gift.\n\n"
                    "**📜 Divine Codex & Server Rules:**\n"
                    "Check **`#📜・ᴅɪᴠɪɴᴇ-ᴄᴏᴅᴇx`** for server conduct rules, respect guidelines, and anti-toxicity policies.\n\n"
                    "**🎀 Self-Roles & Identity:**\n"
                    "Customize your profile in **`#🎀・ᴘɪᴄᴋ-ʀᴏʟᴇꜱ`**:\n"
                    "• 🎮 **Gaming Squads**: Free Fire, BGMI, GTA RP, Roblox.\n"
                    "• 👤 **Identity**: Gender & Age category.\n"
                    "• 🎨 **Aesthetic Colors**: Customize your username color in chat.\n\n"
                    "**🎫 Support Desk:**\n"
                    "Need assistance from staff? Open a private ticket in **`#🎫・ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ`**."
                ),
                color=0xFF4081
            )
        elif val == "guide_pets":
            embed = discord.Embed(
                title="🐾 Virtual Companion Pets & Nickname Badges",
                description=(
                    "**Adopt Your Personal Companion:**\n"
                    "• `/pet list` — Browse all 8 companion pet species (🐱 Cat, 🦊 Fox, 🐉 Dragon, 🐼 Panda, 🐺 Wolf, 🦅 Phoenix, 🐰 Bunny, 🐸 Frog).\n"
                    "• `/pet adopt [species] [name]` — Adopt and bond with your companion!\n\n"
                    "**🏷️ Nickname Badges (Beside Your Name!):**\n"
                    "• `/pet badge` — Toggle your pet's badge beside your server nickname!\n"
                    "• Formats supported: Suffix (`Kishore 🐾`), Prefix (`[🦊] Kishore`), or Profile-only.\n\n"
                    "**🍖 Pet Care & Evolution:**\n"
                    "• `/pet feed` — Feed your pet delicious treats with coins (+XP, +Happiness).\n"
                    "• `/pet play` — Play fun minigames with your companion.\n"
                    "• `/pet profile` — View your pet's evolution stage (Baby ➔ Juvenile ➔ Mythic) and active coin perks!"
                ),
                color=0x00FFCC
            )
        elif val == "guide_casino":
            embed = discord.Embed(
                title="🎰 Cyber Casino & Minigames Hub",
                description=(
                    "**Play High-Stakes Games in `#🎮・ɢᴀᴍɪɴɢ-ʜᴜʙ`:**\n\n"
                    "**♠️ Blackjack (`/blackjack [bet]`):**\n"
                    "• Challenge the dealer in live 21! Click `[Hit]`, `[Stand]`, or `[Double Down]`. Natural blackjack pays 3:2!\n\n"
                    "**🎰 Cyber-Pink Slots (`/slots [bet]`):**\n"
                    "• Spin the 3-reel neon slots. Match 3 for up to a **10x Mega Jackpot** (`💎💎💎`)!\n\n"
                    "**🪙 Coinflip (`/coinflip [heads/tails] [bet]`):**\n"
                    "• Fast-paced 50/50 double-or-nothing coin toss.\n\n"
                    "**🎵 Music Quiz (`/musicquiz [genre]`):**\n"
                    "• Guess 10-second song clips in VC with 4 button choices! Fastest winner gets +150 Coins!"
                ),
                color=0xFF007F
            )
        elif val == "guide_squads":
            embed = discord.Embed(
                title="👥 Voice Clans & Squad Wars",
                description=(
                    "**Form Your Clan:**\n"
                    "• `/squad create [name] [tag]` — Register your clan squad (e.g. `[AURA]`).\n"
                    "• `/squad join [name]` — Join your friends' squad.\n"
                    "• `/squad tag` — Toggle your squad clan tag in your server nickname!\n\n"
                    "**✨ Collective Voice XP:**\n"
                    "• Hang out in voice lounges with squadmates to earn collective Clan XP.\n"
                    "• Level up your squad and dominate the weekly leaderboard (`/squad leaderboard`) in `#⭐・ʜᴀʟʟ-ᴏꜰ-ꜰᴀᴍᴇ`!"
                ),
                color=0xFFD700
            )
        elif val == "guide_community":
            embed = discord.Embed(
                title="🍿 Movie Nights & Aesthetic Quote Cards",
                description=(
                    "**🍿 Movie Night & Watch-Party RSVPs:**\n"
                    "• `/movie host [title] [time] [description]` — Host a watch-along in `#🍿・ᴍᴏᴠɪᴇ-ɴɪɢʜᴛꜱ`.\n"
                    "• Click **`[Count Me In! 🍿]`** to receive an automatic reminder DM before showtime!\n\n"
                    "**💬 Canvas Quote Cards:**\n"
                    "• Right-click any funny or memorable message ➔ **Apps ➔ 'Create Quote Card'** (or `/quote [message_id]`).\n"
                    "• The bot generates a luxury framed image card and showcases it in `#📸・ᴍᴇᴅɪᴀ-ɢᴀʟʟᴇʀʏ`!"
                ),
                color=0x9B59B6
            )
        else:
            embed = discord.Embed(
                title="🧭 RAI VIBES Server Guide",
                description="Please select a topic from the dropdown menu below.",
                color=0xFF69B4
            )

        embed.set_footer(text="RAI VIBES System Codex • Select another topic anytime")
        await interaction.followup.send(embed=embed, ephemeral=True)


class ServerGuideView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ServerGuideSelect())


class GamingHubStationView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Play Trivia (+50 Coins)", emoji="🧠", style=discord.ButtonStyle.primary, custom_id="hub_btn_trivia", row=0)
    async def play_trivia(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        from cogs.economy import TRIVIA_QUESTIONS, TriviaView
        import random
        q_data = random.choice(TRIVIA_QUESTIONS)
        embed = discord.Embed(
            title=f"🧠 TRIVIA CHALLENGE • {q_data['category'].upper()}",
            description=(
                f"### {q_data['q']}\n\n"
                f"👉 Click the correct option below!\n"
                f"🎁 **Reward:** `+50 Coins`"
            ),
            color=0x3498DB
        )
        embed.set_footer(text="RAI VIBES • Gaming Hub Arena")
        view = TriviaView(q_data)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @button(label="Coin Flip (Bet 50)", emoji="🪙", style=discord.ButtonStyle.secondary, custom_id="hub_btn_gamble", row=0)
    async def play_gamble(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        import random
        from cogs.economy import get_user_data, update_user_coins, OWNER_ID
        user_data = get_user_data(interaction.user.id)
        coins = user_data.get("coins", 0)
        bet = 50

        if coins < bet and interaction.user.id != OWNER_ID:
            return await interaction.followup.send(
                f"❌ You need at least `{bet}` coins to flip! Current balance: `{coins:,}` Coins.",
                ephemeral=True
            )

        outcome = random.choice(["Heads 👑", "Tails 🪙"])
        won = random.choice([True, False])

        if won:
            new_bal = update_user_coins(interaction.user.id, bet)
            embed = discord.Embed(
                title="🎉 COIN FLIP WON!",
                description=(
                    f"The coin landed on **{outcome}**!\n\n"
                    f"💰 **Profit:** `+{bet}` Coins\n"
                    f"👛 **New Balance:** `{new_bal:,}` Coins"
                ),
                color=0x2ECC71
            )
        else:
            new_bal = update_user_coins(interaction.user.id, -bet)
            embed = discord.Embed(
                title="💀 COIN FLIP MISSED!",
                description=(
                    f"The coin landed on **{outcome}**!\n\n"
                    f"💸 **Loss:** `-{bet}` Coins\n"
                    f"👛 **New Balance:** `{new_bal:,}` Coins"
                ),
                color=0xE74C3C
            )
        embed.set_footer(text="RAI VIBES • Gaming Hub Arena")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @button(label="My Wallet", emoji="👛", style=discord.ButtonStyle.secondary, custom_id="hub_btn_wallet", row=1)
    async def view_wallet(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        from cogs.economy import get_user_data, OWNER_ID
        user_data = get_user_data(interaction.user.id)
        coins = user_data.get("coins", 0)
        streak = user_data.get("streak", 0)
        rep = user_data.get("rep", 0)

        coin_display = "∞ *(Infinite Vault • Server Owner)*" if interaction.user.id == OWNER_ID else f"`{coins:,}` Coins"
        embed = discord.Embed(
            title=f"👛 {interaction.user.display_name.upper()}'S WALLET",
            description=(
                f"🪙 **Coin Balance:** {coin_display}\n"
                f"🔥 **Daily Streak:** `{streak}` Days\n"
                f"⭐ **Community Rep:** `{rep}` Points\n\n"
                f"💡 *Claim `/daily` for streak multipliers or `/shop` to unlock VIP themes!*"
            ),
            color=0xFFD700
        )
        embed.set_footer(text="RAI VIBES • Vault System")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @button(label="Richest Leaderboard", emoji="🏆", style=discord.ButtonStyle.success, custom_id="hub_btn_top", row=1)
    async def view_leaderboard(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        from cogs.economy import load_economy, OWNER_ID
        data = load_economy()
        sorted_users = sorted(data.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:5]

        lines = []
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for idx, (uid, udata) in enumerate(sorted_users):
            medal = medals[idx] if idx < len(medals) else "🔹"
            val = "∞ (Owner Vault)" if int(uid) == OWNER_ID else f"{udata.get('coins', 0):,} Coins"
            lines.append(f"{medal} <@{uid}> — **{val}**")

        embed = discord.Embed(
            title="🏆 TOP 5 RICHEST MEMBERS",
            description="\n".join(lines) if lines else "No data yet.",
            color=0xFFD700
        )
        embed.set_footer(text="RAI VIBES • Hall of Wealth")
        await interaction.followup.send(embed=embed, ephemeral=True)


