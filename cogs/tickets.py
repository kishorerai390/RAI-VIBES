import io
import asyncio
import re
import logging
import discord
from discord.ext import commands
from discord import app_commands

import config

logger = logging.getLogger("Tickets")

STAFF_ROLE_IDS = [
    # RAI FAM Staff
    1545494610489643038,  # 👑 ┆ 𝐅𝐎𝐔𝐍𝐃𝐄𝐑 🍷
    1545506927788687470,  # ⚡ ┆ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍 ⚡
    1545494600347680918,  # 🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️
    # ABIJITH 777 Staff
    1550205899069726810,  # 👑 ┆ 𝐅𝐎𝐔𝐍𝐃𝐄𝐑 🍷
    1550205902706049214,  # ⚡ ┆ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍 ⚡
    1550205905830682795,  # 🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️
]
SENTINEL_HQ_CAT_ID = 1545803487093456906  # 🔱 VIP & SENTINEL HQ (RAI FAM)
AUDIT_LOG_CHAN_ID = 1546540192343523399   # 📝｜ᴍᴏᴅᴇʀᴀᴛɪᴏɴ-ʟᴏɢꜱ / audit
SECURITY_LOG_CHAN_ID = 1546593526073135107 # 🚨｜ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ


class TicketCloseConfirmView(discord.ui.View):
    def __init__(self, opener_id: int = None):
        super().__init__(timeout=60)
        self.opener_id = opener_id

    @discord.ui.button(label="Confirm Close & Archive", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="confirm_close_ticket")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **Archiving and deleting ticket channel in 5 seconds...**")
        
        channel = interaction.channel
        guild = interaction.guild
        
        # 1. Compile Rich HTML Transcript
        html_head = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ticket Transcript - #{channel.name}</title>
<style>
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1f22; color: #dbdee1; margin: 0; padding: 24px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  .header {{ background-color: #2b2d31; padding: 20px 24px; border-radius: 12px; margin-bottom: 24px; border-left: 5px solid #5865f2; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }}
  .header h1 {{ margin: 0; font-size: 22px; color: #ffffff; }}
  .header p {{ margin: 6px 0 0; font-size: 13px; color: #949ba4; }}
  .message {{ display: flex; margin-bottom: 18px; padding: 8px 12px; border-radius: 8px; transition: background 0.15s; }}
  .message:hover {{ background-color: #2b2d31; }}
  .avatar {{ width: 42px; height: 42px; border-radius: 50%; margin-right: 16px; flex-shrink: 0; background-color: #5865f2; object-fit: cover; }}
  .msg-body {{ flex-grow: 1; }}
  .msg-meta {{ display: flex; align-items: baseline; margin-bottom: 4px; }}
  .username {{ font-weight: 600; color: #f2f3f5; margin-right: 10px; font-size: 15px; }}
  .timestamp {{ font-size: 12px; color: #949ba4; }}
  .content {{ font-size: 14px; line-height: 1.5; color: #dbdee1; word-break: break-word; }}
  .attachment {{ margin-top: 8px; padding: 8px 12px; background: #232428; border-radius: 6px; display: inline-block; font-size: 12px; color: #00a8fc; text-decoration: none; border: 1px solid #35363c; }}
  .attachment:hover {{ text-decoration: underline; }}
  .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #949ba4; border-top: 1px solid #35363c; padding-top: 16px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🎫 Ticket Transcript: #{channel.name}</h1>
    <p>Guild: <strong>{guild.name}</strong> • Closed by: <strong>{interaction.user.name}</strong> • Closed at: <strong>{discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</strong></p>
  </div>
  <div class="messages">
"""
        msg_blocks = []
        try:
            import html
            async for msg in channel.history(limit=1000, oldest_first=True):
                time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                avatar_url = msg.author.display_avatar.url if hasattr(msg.author, "display_avatar") else ""
                clean_txt = html.escape(msg.clean_content).replace("\n", "<br>")
                
                att_html = ""
                for att in msg.attachments:
                    att_html += f'<br><a class="attachment" href="{att.url}" target="_blank">📎 Attachment: {html.escape(att.filename)}</a>'

                msg_blocks.append(f"""
    <div class="message">
      <img class="avatar" src="{avatar_url}" alt="Avatar" onerror="this.style.display='none'">
      <div class="msg-body">
        <div class="msg-meta">
          <span class="username">{html.escape(msg.author.display_name)}</span>
          <span class="timestamp">{time_str}</span>
        </div>
        <div class="content">{clean_txt}{att_html}</div>
      </div>
    </div>""")
        except Exception as e:
            msg_blocks.append(f'<div class="message"><div class="content" style="color:#f23f43">Error fetching complete history: {e}</div></div>')

        html_footer = f"""
  </div>
  <div class="footer">
    RAI SENTINEL 🛡️ Autonomous Ticket Archival Engine • RAI FAM 💗
  </div>
</div>
</body>
</html>"""

        full_html = html_head + "".join(msg_blocks) + html_footer
        transcript_bytes = full_html.encode("utf-8")

        # 2. Send transcript to mod-logs / audit-logs
        log_chan = (
            discord.utils.get(guild.text_channels, name="📝｜ᴍᴏᴅᴇʀᴀᴛɪᴏɴ-ʟᴏɢꜱ") or
            discord.utils.get(guild.text_channels, name="📋｜ᴀᴜᴅɪᴛ-ʟᴏɢꜱ") or
            discord.utils.get(guild.text_channels, name="🚨｜ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ") or
            guild.get_channel(AUDIT_LOG_CHAN_ID) or
            guild.get_channel(SECURITY_LOG_CHAN_ID) or
            discord.utils.get(guild.text_channels, name="・𝗮𝘂𝗱𝗶𝘁-𝗹𝗼𝗴𝘀・") or
            discord.utils.get(guild.text_channels, name="📋・mod-logs") or
            discord.utils.get(guild.text_channels, name="mod-logs")
        )
        if log_chan:
            embed = discord.Embed(
                title=f"📋 Ticket Closed & Archived • #{channel.name}",
                description=(
                    f"**Ticket:** `#{channel.name}`\n"
                    f"**Closed By:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Timestamp:** <t:{int(discord.utils.utcnow().timestamp())}:F>\n"
                    f"**Format:** Interactive Responsive HTML"
                ),
                color=0x2B2D31
            )
            embed.set_footer(text="RAI SENTINEL 🛡️ Ticket Transcript Service", icon_url=config.RAI_ICON_URL)
            try:
                t_file = discord.File(io.BytesIO(transcript_bytes), filename=f"transcript-{channel.name}.html")
                await log_chan.send(embed=embed, file=t_file)
            except Exception as e:
                logger.warning(f"Failed to send transcript to log channel: {e}")

        # 3. Send copy to ticket opener via DM
        if self.opener_id:
            try:
                opener = guild.get_member(self.opener_id) or await guild.fetch_member(self.opener_id)
                if opener and not opener.bot:
                    dm_embed = discord.Embed(
                        title=f"🎫 Support Ticket Closed • #{channel.name}",
                        description=(
                            f"Hello {opener.mention}, your support ticket in **{guild.name}** has been marked as resolved.\n\n"
                            f"Attached below is your official **interactive HTML transcript** for your records.\n"
                            f"If you ever need further help, feel free to open a new ticket anytime in the support hub!"
                        ),
                        color=config.COLOR_PRIMARY
                    )
                    dm_embed.set_footer(text="RAI FAM Support Team 💗", icon_url=config.RAI_ICON_URL)
                    t_file_dm = discord.File(io.BytesIO(transcript_bytes), filename=f"transcript-{channel.name}.html")
                    await opener.send(embed=dm_embed, file=t_file_dm)
            except Exception:
                pass

        await asyncio.sleep(4)
        try:
            await channel.delete(reason=f"Ticket closed by {interaction.user.name}")
        except Exception as e:
            logger.error(f"Failed to delete ticket channel: {e}")

    @discord.ui.button(label="Cancel", emoji="✖️", style=discord.ButtonStyle.secondary, custom_id="cancel_close_ticket")
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Ticket close cancelled. Channel remains active.", ephemeral=True)


class TicketChannelControlView(discord.ui.View):
    """Control buttons inside active ticket channel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket_ctrl_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        opener_id = None
        if interaction.channel.topic:
            m = re.search(r"\((\d{17,20})\)", interaction.channel.topic)
            if m:
                opener_id = int(m.group(1))
        view = TicketCloseConfirmView(opener_id=opener_id)
        await interaction.response.send_message("⚠️ Are you sure you want to close and archive this ticket?", view=view, ephemeral=True)

    @discord.ui.button(label="Claim Ticket", emoji="🙋‍♂️", style=discord.ButtonStyle.success, custom_id="ticket_ctrl_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_role_ids = {r.id for r in interaction.user.roles}
        is_staff = (
            bool(set(STAFF_ROLE_IDS) & user_role_ids) or
            interaction.user.guild_permissions.manage_channels or
            interaction.user.guild_permissions.administrator
        )
        if not is_staff:
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
        prefix = f"ticket-{user.name.lower()[:10]}"
        for ch in guild.text_channels:
            if ch.name.startswith(prefix):
                return await interaction.followup.send(f"⚠️ You already have an active ticket open: {ch.mention}", ephemeral=True)

        # Staff Category & Overwrites
        staff_cat = (
            discord.utils.get(guild.categories, name="🔱 VIP & SENTINEL HQ") or
            guild.get_channel(SENTINEL_HQ_CAT_ID) or
            discord.utils.get(guild.categories, id=SENTINEL_HQ_CAT_ID) or
            discord.utils.get(guild.categories, name="╭・𝗦𝗘𝗡𝗧𝗜𝗡𝗘𝗟 𝗛𝗤 ✧") or
            discord.utils.get(guild.categories, name="🛡️ | 𝙎𝙏𝘼𝙁𝙁 𝙕𝙊𝙉𝙀") or
            discord.utils.get(guild.categories, name="Staff Zone") or
            discord.utils.get(guild.categories, name="Tickets")
        )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_messages=True)
        }

        # Add staff roles permissions
        staff_pings = []
        for r_id in STAFF_ROLE_IDS:
            r = guild.get_role(r_id)
            if r:
                overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True, attach_files=True)
                staff_pings.append(r.mention)

        # Category colors and headers
        meta = {
            "support": {"color": 0x3498DB, "title": "💬 General Support & Inquiries"},
            "report": {"color": 0xE74C3C, "title": "🚨 Member Violation / Security Report"},
            "partner": {"color": 0x9B59B6, "title": "🤝 Partnership & Collaboration"},
            "vip": {"color": 0xF1C40F, "title": "💎 VIP & Booster Assistance"}
        }.get(category_val, {"color": config.COLOR_PRIMARY, "title": f"📩 Support Ticket • {category_val.upper()}"})

        ticket_chan_name = f"ticket-{user.name.lower()[:10]}-{category_val}"
        try:
            ticket_channel = await guild.create_text_channel(
                name=ticket_chan_name,
                category=staff_cat if isinstance(staff_cat, discord.CategoryChannel) else None,
                overwrites=overwrites,
                topic=f"Support Ticket for {user.name} ({user.id}) | Reason: {category_val.upper()}"
            )

            embed = discord.Embed(
                title=meta["title"],
                description=(
                    f"Hello {user.mention}, welcome to your private support channel!\n\n"
                    f"🛡️ **Category:** `{category_val.title()}`\n"
                    f"📝 **Instructions:** Please describe your inquiry or issue in detail below. Staff members will assist you shortly.\n\n"
                    f"• Click **`[🙋‍♂️ Claim Ticket]`** (Staff only) to assign this case.\n"
                    f"• Click **`[🔒 Close Ticket]`** when your issue has been resolved."
                ),
                color=meta["color"]
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"Ticket ID: {ticket_channel.id} • RAI SENTINEL 🛡️ Support Hub", icon_url=config.RAI_ICON_URL)
            
            pings = f"{user.mention} {' '.join(staff_pings[:2])}"
            await ticket_channel.send(content=pings, embed=embed, view=TicketChannelControlView())
            await interaction.followup.send(f"✅ **Ticket Created!** Please head over to {ticket_channel.mention}", ephemeral=True)
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
