import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import discord
import asyncio
from config import TOKEN, GUILD_ID, ROLE_IDS, CHANNELS_VIP_SENTINEL, COLOR_EMERALD, COLOR_GOLD
from cogs.tickets import PersistentTicketLauncherView

async def main():
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as: {client.user}", flush=True)
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print(f"Guild {GUILD_ID} not found!", flush=True)
            await client.close()
            return

        print(f"Syncing Bot Administration Suite on '{guild.name}' ({guild.id})...", flush=True)

        # 1. Resolve Staff Roles
        founder_role = discord.utils.get(guild.roles, id=ROLE_IDS["founder"])
        head_admin_role = discord.utils.get(guild.roles, id=ROLE_IDS["head_admin"])
        mod_role = discord.utils.get(guild.roles, id=ROLE_IDS["moderator"])
        everyone_role = guild.default_role

        staff_roles = [r for r in [founder_role, head_admin_role, mod_role] if r is not None]
        print(f"Resolved staff roles: {[r.name for r in staff_roles]}", flush=True)

        # 2. Setup Category
        cat_name = CHANNELS_VIP_SENTINEL["category"]
        cat = discord.utils.get(guild.categories, name=cat_name) or discord.utils.get(guild.categories, name="🔱 VIP & SENTINEL HQ")

        cat_overwrites = {
            everyone_role: discord.PermissionOverwrite(view_channel=False, read_messages=False, connect=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, connect=True, speak=True, manage_messages=True, manage_channels=True)
        }
        for r in staff_roles:
            cat_overwrites[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, connect=True, speak=True)

        if not cat:
            cat = await guild.create_category(cat_name, overwrites=cat_overwrites, position=len(guild.categories))
            print(f"Created category '{cat_name}'", flush=True)
            await asyncio.sleep(1.0)
        else:
            await cat.edit(name=cat_name, overwrites=cat_overwrites)
            print(f"Updated category '{cat_name}'", flush=True)

        # 3. Setup Channels
        staff_chat_overwrites = {
            everyone_role: discord.PermissionOverwrite(view_channel=False, read_messages=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True, attach_files=True)
        }
        for r in staff_roles:
            staff_chat_overwrites[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, attach_files=True)

        staff_view_only_overwrites = {
            everyone_role: discord.PermissionOverwrite(view_channel=False, read_messages=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, embed_links=True, attach_files=True)
        }
        for r in staff_roles:
            staff_view_only_overwrites[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=False)

        ticket_overwrites = {
            everyone_role: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=False, add_reactions=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
        }
        for r in staff_roles:
            ticket_overwrites[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)

        # Create/find text channels
        channels = {}
        for target_name, topic in CHANNELS_VIP_SENTINEL["text"]:
            ch = discord.utils.get(cat.text_channels, name=target_name)
            if not ch:
                # Find by keyword
                base_kw = target_name.split("・")[-1].replace("-", "")
                for c in guild.text_channels:
                    if base_kw in c.name.replace("-", "").lower():
                        ch = c
                        await ch.edit(category=cat, name=target_name, topic=topic)
                        break

            ow = ticket_overwrites if "ticket" in target_name else (staff_view_only_overwrites if "logs" in target_name else staff_chat_overwrites)
            if not ch:
                ch = await guild.create_text_channel(target_name, category=cat, topic=topic, overwrites=ow)
                print(f"Created text channel '{target_name}'", flush=True)
                await asyncio.sleep(1.0)
            else:
                await ch.edit(overwrites=ow, topic=topic)
                print(f"Synced text channel '{target_name}'", flush=True)
            channels[target_name] = ch

        # Setup voice channel
        vc_name, user_limit = CHANNELS_VIP_SENTINEL["voice"][0]
        vc = discord.utils.get(cat.voice_channels, name=vc_name)
        if not vc:
            vc = await guild.create_voice_channel(vc_name, category=cat, user_limit=user_limit)
            print(f"Created voice channel '{vc_name}'", flush=True)
        else:
            await vc.edit(name=vc_name, user_limit=user_limit)
            print(f"Synced voice channel '{vc_name}'", flush=True)

        # 4. Deploy Panels
        # Ticket Panel
        ticket_ch = channels.get("｜・ticket-support")
        if ticket_ch:
            async for m in ticket_ch.history(limit=10):
                if m.author == client.user:
                    await m.delete()

            ticket_embed = discord.Embed(
                title=f"🎫 {guild.name.upper()} • SUPPORT & HELP DESK",
                description=(
                    f"Welcome to the official **{guild.name}** Support Center!\n\n"
                    "Need assistance, want to report a rule violation, or have questions for server staff?\n"
                    "Click the button below to generate a private support ticket with our Administration Team.\n\n"
                    "📌 **Ticket Guidelines:**\n"
                    "• Please clearly describe your issue or inquiry upon creation.\n"
                    "• Staff will be pinged automatically to assist you.\n"
                    "• Be respectful and adhere to all community guidelines."
                ),
                color=COLOR_EMERALD
            )
            ticket_embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            ticket_embed.set_footer(text=f"{guild.name} • 24/7 Sentinel Support Desk", icon_url=guild.icon.url if guild.icon else None)
            await ticket_ch.send(embed=ticket_embed, view=PersistentTicketLauncherView())
            print("Deployed clean Ticket Support panel.", flush=True)

        print("\nAdmin Suite setup complete!", flush=True)
        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
