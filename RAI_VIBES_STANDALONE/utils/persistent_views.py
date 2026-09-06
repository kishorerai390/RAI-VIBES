import unicodedata
import discord
from discord.ui import View, Button, button

ROLE_ID_MAP = {
    # Gaming Squads
    "Free Fire": 1545516397034078269,
    "BGMI": 1545516399663779871,
    "GTA RP": 1546062595293978694,
    "Roblox": 1545516402188881991,

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


class VerifyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Verify & Enter Community", emoji="✅", style=discord.ButtonStyle.success, custom_id="verify_member_btn")
    async def verify_button(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        if not guild:
            return await interaction.followup.send("❌ Server error.", ephemeral=True)

        verified_role = None
        for r in guild.roles:
            norm_name = unicodedata.normalize('NFKD', r.name).upper()
            if "RAI FAMILY" in norm_name or "FAMILY" in norm_name or "VERIFIED" in norm_name:
                verified_role = r
                break

        if not verified_role:
            verified_role = discord.utils.get(guild.roles, id=1545494584203673740)

        if verified_role and verified_role in interaction.user.roles:
            return await interaction.followup.send("✨ **You are already verified!** Enjoy your stay! 🌸", ephemeral=True)

        if verified_role:
            try:
                member = interaction.user
                if isinstance(member, discord.User):
                    member = await guild.fetch_member(interaction.user.id)
                await member.add_roles(verified_role, reason="Passed Verification Gate")
                await interaction.followup.send(f"🎉 **Verification Successful!** Welcome to **{guild.name}**! 🌸", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ Failed to assign role: {e}", ephemeral=True)
        else:
            await interaction.followup.send("❌ Verification role not found.", ephemeral=True)



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
