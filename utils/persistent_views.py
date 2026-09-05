import discord
from discord.ui import View, Button, button

ROLE_ID_MAP = {
    # Colors
    "Sakura Pink 🌸": 1545516328016805979,
    "Neon Violet 💜": 1545516370785996882,
    "Cyber Cyan 🩵": 1545516378046337074,
    "Royal Gold 💛": 1545516381426950214,

    # Gaming & Device
    "Free Fire 💥": 1545516397034078269,
    "BGMI ⚡": 1545516399663779871,
    "Roblox 🧸": 1545516402188881991,
    "Mobile Player 📱": 1545516404302811256,
    "PC Player 💻": 1545516406454493257,

    # Notification Pings
    "Movie Alerts 🍿": 1545516408375353376,
    "Giveaways 🎉": 1545516411659620383,
    "Server News 📢": 1545516414016815169,
    "Music Jam 🎵": 1545516416969609296,

    # Identity & Pronouns (inspired by photo 2)
    "Male 🤴": 1545516419121422377,
    "Female 👸": 1545516421583208551,
    "They / Them 🌈": 1545516423789543651,
    "18+ Verified 🔞": 1545516426893197392,
}

ALL_COLOR_ROLES = [
    "Sakura Pink 🌸",
    "Neon Violet 💜",
    "Cyber Cyan 🩵",
    "Royal Gold 💛"
]

def find_role(guild: discord.Guild, role_name: str) -> discord.Role | None:
    role_id = ROLE_ID_MAP.get(role_name)
    if role_id:
        r = guild.get_role(role_id)
        if r:
            return r
    for r in guild.roles:
        if r.name.lower() == role_name.lower() or role_name.lower() in r.name.lower():
            return r
    return None

class ColorRoleButton(Button):
    def __init__(self, role_name: str, label: str, emoji: str, style: discord.ButtonStyle, row: int = 0):
        super().__init__(label=label, emoji=emoji, style=style, row=row, custom_id=f"colorrole_{role_name}")
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        guild = interaction.guild
        member = interaction.user
        role = find_role(guild, self.role_name)
        if not role:
            return await interaction.followup.send(f"❌ Role `{self.role_name}` not found.", ephemeral=True)

        if role in member.roles:
            await member.remove_roles(role)
            return await interaction.followup.send(f"⚪ Removed color: **{role.name}**", ephemeral=True)

        # Remove other color roles first
        roles_to_remove = [r for r in member.roles if r.name in ALL_COLOR_ROLES and r != role]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        await member.add_roles(role)
        await interaction.followup.send(f"🎨 **Equipped Color:** {role.mention}!", ephemeral=True)


class SelfRoleButton(Button):
    def __init__(self, role_name: str, label: str, emoji: str, style: discord.ButtonStyle, row: int = 0):
        super().__init__(label=label, emoji=emoji, style=style, row=row, custom_id=f"selfrole_{role_name}")
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        guild = interaction.guild
        role = find_role(guild, self.role_name)
        if not role:
            return await interaction.followup.send(f"❌ Role `{self.role_name}` not found.", ephemeral=True)

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.followup.send(f"➖ **Removed Role:** {role.name}", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.followup.send(f"➕ **Added Role:** {role.name}", ephemeral=True)


class ColorRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ColorRoleButton("Sakura Pink 🌸", "Sakura Pink", "🌸", discord.ButtonStyle.secondary, row=0))
        self.add_item(ColorRoleButton("Neon Violet 💜", "Neon Violet", "💜", discord.ButtonStyle.primary, row=0))
        self.add_item(ColorRoleButton("Cyber Cyan 🩵", "Cyber Cyan", "🩵", discord.ButtonStyle.secondary, row=0))
        self.add_item(ColorRoleButton("Royal Gold 💛", "Royal Gold", "💛", discord.ButtonStyle.success, row=0))


class GamingRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("Free Fire 💥", "Free Fire", "💥", discord.ButtonStyle.danger, row=0))
        self.add_item(SelfRoleButton("BGMI ⚡", "BGMI", "⚡", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("Roblox 🧸", "Roblox", "🧸", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("Mobile Player 📱", "Mobile Player", "📱", discord.ButtonStyle.secondary, row=1))
        self.add_item(SelfRoleButton("PC Player 💻", "PC Player", "💻", discord.ButtonStyle.secondary, row=1))


class NotificationRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("Movie Alerts 🍿", "Movie Alerts", "🍿", discord.ButtonStyle.danger, row=0))
        self.add_item(SelfRoleButton("Giveaways 🎉", "Giveaways", "🎉", discord.ButtonStyle.success, row=0))
        self.add_item(SelfRoleButton("Server News 📢", "Server News", "📢", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("Music Jam 🎵", "Music Jam", "🎵", discord.ButtonStyle.secondary, row=0))


class IdentityRolesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelfRoleButton("Male 🤴", "Male", "🤴", discord.ButtonStyle.primary, row=0))
        self.add_item(SelfRoleButton("Female 👸", "Female", "👸", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("They / Them 🌈", "They / Them", "🌈", discord.ButtonStyle.secondary, row=0))
        self.add_item(SelfRoleButton("18+ Verified 🔞", "18+ Verified", "🔞", discord.ButtonStyle.danger, row=0))


class VerifyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Verify & Enter Community", emoji="✅", style=discord.ButtonStyle.success, custom_id="verify_member_btn")
    async def verify_button(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        verified_role = (
            discord.utils.get(guild.roles, name="RAI FAMILY 🌸") or
            discord.utils.get(guild.roles, name="🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘") or
            discord.utils.get(guild.roles, name="👥 Verified Member")
        )
        if not verified_role:
            return await interaction.followup.send("❌ Verified role not found.", ephemeral=True)

        if verified_role in interaction.user.roles:
            return await interaction.followup.send(f"✨ You already have {verified_role.mention}!", ephemeral=True)

        try:
            await interaction.user.add_roles(verified_role)
            await interaction.followup.send(f"🎉 **Role Added!** Welcome to **{guild.name}**! 💗🍿🎵", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


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


class TicketCreateView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Open Support Ticket", emoji="📩", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket_button(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name="M O D E R A T O R 🛡️") or discord.utils.get(guild.roles, name="🛡️ ┊ 𝐆𝐔𝐀𝐑𝐃𝐈𝐀𝐍")
        cat = discord.utils.get(guild.categories, name="🛡️ | 𝙎𝙏𝘼𝙁𝙁 𝙕𝙊𝙉𝙀")

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
