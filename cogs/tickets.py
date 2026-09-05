import io
import discord
from discord.ext import commands
from discord import app_commands
import logging

import config

logger = logging.getLogger("Tickets")

class TicketCloseConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Confirm Close & Archive", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="confirm_close_ticket")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **Archiving and deleting ticket channel in 5 seconds...**")
        
        channel = interaction.channel
        guild = interaction.guild
        
        # 1. Compile Transcript
        transcript_lines = [f"--- TICKET TRANSCRIPT FOR #{channel.name} ({guild.name}) ---"]
        try:
            async for msg in channel.history(limit=500, oldest_first=True):
                time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                transcript_lines.append(f"[{time_str}] {msg.author.name}: {msg.clean_content}")
                for att in msg.attachments:
                    transcript_lines.append(f"    [Attachment: {att.url}]")
        except Exception as e:
            transcript_lines.append(f"Error fetching history: {e}")

        transcript_text = "\n".join(transcript_lines)
        transcript_file = discord.File(io.BytesIO(transcript_text.encode("utf-8")), filename=f"transcript-{channel.name}.txt")

        # 2. Send transcript to mod-logs if available
        log_chan = discord.utils.get(guild.text_channels, name="📋・mod-logs") or discord.utils.get(guild.text_channels, name="mod-logs")
        if log_chan:
            embed = discord.Embed(
                title=f"📋 Ticket Closed: #{channel.name}",
                description=f"**Closed By:** {interaction.user.mention} (`{interaction.user.id}`)\n**Channel:** `{channel.name}`",
                color=config.COLOR_PRIMARY
            )
            try:
                await log_chan.send(embed=embed, file=transcript_file)
            except Exception:
                pass

        await discord.utils.sleep_until(discord.utils.utcnow())
        try:
            await channel.delete(reason=f"Ticket closed by {interaction.user.name}")
        except Exception as e:
            logger.error(f"Failed to delete ticket channel: {e}")


class TicketChannelControlView(discord.ui.View):
    """Buttons inside active ticket channel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket_ctrl_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TicketCloseConfirmView()
        await interaction.response.send_message("⚠️ Are you sure you want to close and delete this ticket?", view=view, ephemeral=True)

    @discord.ui.button(label="Claim Ticket", emoji="🙋‍♂️", style=discord.ButtonStyle.success, custom_id="ticket_ctrl_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = (
            discord.utils.get(interaction.guild.roles, name="🛡️ ┊ 𝐆𝐔𝐀𝐑𝐃𝐈𝐀𝐍") or
            discord.utils.get(interaction.guild.roles, name="Moderator") or
            discord.utils.get(interaction.guild.roles, name="Admin")
        )
        if staff_role and staff_role not in interaction.user.roles and not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Only staff members can claim tickets.", ephemeral=True)

        embed = discord.Embed(
            title="🙋‍♂️ Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}. They will assist you shortly!",
            color=config.COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed)


class TicketCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support & Inquiries", description="Ask questions or get help with server features", emoji="💬", value="support"),
            discord.SelectOption(label="Report a Member / Rule Violation", description="Report harassment, raids, or server misconduct", emoji="🚨", value="report"),
            discord.SelectOption(label="Partnership & Creator Collaboration", description="Inquire about server partnerships or events", emoji="🤝", value="partner"),
            discord.SelectOption(label="VIP / Booster Support", description="Get assistance with custom roles or booster perks", emoji="💎", value="vip"),
        ]
        super().__init__(placeholder="Select the reason for opening a ticket...", min_values=1, max_values=1, custom_id="ticket_category_select", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        category_val = self.values[0]

        # Check existing ticket
        ticket_chan_name = f"ticket-{user.name.lower()[:12]}-{category_val}"
        for ch in guild.text_channels:
            if ch.name.startswith(f"ticket-{user.name.lower()[:12]}"):
                return await interaction.followup.send(f"⚠️ You already have an active ticket open: {ch.mention}", ephemeral=True)

        # Staff Category & Overwrites
        staff_cat = (
            discord.utils.get(guild.categories, name="🛡️ | 𝙎𝙏𝘼𝙁𝙁 𝙕𝙊𝙉𝙀") or
            discord.utils.get(guild.categories, name="Staff Zone") or
            discord.utils.get(guild.categories, name="Tickets")
        )
        staff_role = discord.utils.get(guild.roles, name="🛡️ ┊ 𝐆𝐔𝐀𝐑𝐃𝐈𝐀𝐍") or discord.utils.get(guild.roles, name="Moderator")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_messages=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)

        try:
            ticket_channel = await guild.create_text_channel(
                name=ticket_chan_name,
                category=staff_cat,
                overwrites=overwrites,
                topic=f"Support Ticket for {user.name} ({user.id}) | Reason: {category_val.upper()}"
            )

            embed = discord.Embed(
                title=f"📩 Support Ticket • {category_val.upper()}",
                description=(
                    f"Hello {user.mention}, welcome to your private support channel!\n\n"
                    f"🛡️ **Category:** `{category_val.title()}`\n"
                    f"📝 **Instructions:** Please describe your inquiry or issue in detail below. A staff member will be with you shortly.\n\n"
                    f"• Click **`[🙋‍♂️ Claim Ticket]`** (Staff only) to claim this case.\n"
                    f"• Click **`[🔒 Close Ticket]`** when your issue has been resolved."
                ),
                color=config.COLOR_PRIMARY
            )
            embed.set_footer(text=f"Ticket ID: {ticket_channel.id} • RAI FAM Support Hub", icon_url=config.RAI_ICON_URL)
            
            pings = f"{user.mention} {staff_role.mention if staff_role else ''}"
            await ticket_channel.send(content=pings, embed=embed, view=TicketChannelControlView())
            await interaction.followup.send(f"✅ **Ticket Created!** Please proceed to {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to create ticket channel: {e}", ephemeral=True)


class PersistentTicketLauncherView(discord.ui.View):
    """The main panel view posted in #tickets / #support."""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())


class Tickets(commands.Cog):
    """Interactive Support Ticket & Inquiries System."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ticketsetup", description="Deploy the persistent Support Ticket launch panel.")
    @commands.has_permissions(administrator=True)
    async def ticketsetup(self, ctx: commands.Context, channel: discord.TextChannel = None):
        target_chan = channel or ctx.channel
        
        embed = discord.Embed(
            title="🎫 RAI FAM • OFFICIAL SUPPORT HUB",
            description=(
                "Need assistance from our Staff & Moderation Team?\n"
                "Select a category from the dropdown menu below to create your private ticket channel.\n\n"
                "**📌 Available Categories:**\n"
                "• 💬 **General Support & Inquiries** — Bot questions, server guides, general help\n"
                "• 🚨 **Report a Member / Violation** — Rule breakers, raid alerts, harassment\n"
                "• 🤝 **Partnerships & Creators** — Collaboration and server outreach\n"
                "• 💎 **VIP & Booster Perks** — Role inquiries, perks and awards\n\n"
                "*All tickets are private and only visible to you and our Guardian Staff team.*"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI SENTINEL 🛡️ & RAI VIBES 💗 • Support System", icon_url=config.RAI_ICON_URL)

        await target_chan.send(embed=embed, view=PersistentTicketLauncherView())
        if ctx.interaction:
            await ctx.send(f"✅ Ticket launch panel successfully deployed in {target_chan.mention}!", ephemeral=True)
        else:
            await ctx.send(f"✅ Ticket launch panel successfully deployed in {target_chan.mention}!")


async def setup(bot: commands.Bot):
    bot.add_view(PersistentTicketLauncherView())
    bot.add_view(TicketChannelControlView())
    await bot.add_cog(Tickets(bot))
