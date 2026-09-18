# ABIJITH 777 • Server Operations & Setup Suite

This directory contains the dedicated setup, layout enforcement, and administrative tooling specifically for **ABIJITH 777** (`1428058914141900860`).

---

## 📁 Directory Structure

```
ABIJITH 777/
├── config.py              # Guild ID, known roles, channels & styling tokens
├── inspect_server.py      # Audits all roles, categories, and channels in ABIJITH 777
├── setup_admin_suite.py   # Provisions/repairs VIP & Sentinel HQ, channels & permissions
├── apply_font_style.py    # Enforces the unified '| • ' font style
├── deploy_embeds.py       # Refreshes Verification Gate, Ticket Desk, and Staff Directives
├── run_setup.bat          # Interactive one-click Windows batch launcher
└── README.md              # Complete server architecture & command reference
```

---

## 🏛️ Server Architecture & Categories

| Category | Type | Channel Name | Topic / Description |
| :--- | :--- | :--- | :--- |
| **SERVER STATS** | Voice | `\| • ALL MEMBERS: {count}` | Real-time total server member counter |
| | Voice | `\| • MEMBERS: {count}` | Real-time human member counter |
| | Voice | `\| • BOTS: {count}` | Real-time bot counter |
| **VERIFICATION** | Text | `｜・𝖵𝖤𝖱𝖨𝖥𝖸-𝖧𝖤𝖱𝖤` | Official 1-click verification gate |
| **TEXT CHANNELS** | Text | `｜・𝖢𝖧𝖠𝖳` | General community discussion |
| **COMMUNITY AREA** | Voice | `\| • COMMUNITY VC 1` | Community lounge |
| | Voice | `\| • COMMUNITY VC 2` | Community lounge |
| | Voice | `\| • DRAG ME` | Move lounge |
| | Voice | `\| • COMMUNITY VC 3` | Community lounge |
| **CREATE UR OWN VC** | Voice | `\| • JOIN TO CREATE VC` | Dynamic voice generator |
| **GAMING ZONE** | Voice | `\| • GAMING ZONE 1` | Gaming session |
| | Voice | `\| • GAMING ZONE 2` | Gaming session |
| | Voice | `\| • GAMING ZONE 3` | Gaming session |
| **SQUAD AREA** | Voice | `\| • SQUAD 1` | 4-Player squad |
| | Voice | `\| • SQUAD 2` | 4-Player squad |
| | Voice | `\| • SQUAD 3` | 4-Player squad |
| | Voice | `\| • SQUAD 4` | 4-Player squad |
| | Voice | `\| • DUO` | 2-Player duo |
| | Voice | `\| • TRIO` | 3-Player trio |
| **VIP & SENTINEL HQ** | Text | `｜・𝖤𝖷𝖤𝖢𝖴𝖳𝖨𝖵𝖤-𝖫𝖮𝖴𝖭𝖦𝖤` | Private council lounge |
| | Text | `｜・𝖲𝖳𝖠𝖥𝖥-𝖮𝖯𝖤𝖱𝖠𝖳𝖨𝖮𝖭𝖲` | Moderation commands & directives |
| | Text | `｜・𝖠𝖴𝖣𝖨𝖳-𝖫𝖮𝖦𝖲` | Administrative server audit log |
| | Text | `｜・𝖳𝖨𝖢𝖪𝖤𝖳-𝖲𝖴𝖯𝖯𝖮𝖱𝖳` | Public ticket creation desk |
| | Text | `｜・𝖬𝖮𝖣𝖤𝖱𝖠𝖳𝖨𝖮𝖭-𝖫𝖮𝖦𝖲` | Strike, kick, and ban logs |
| | Text | `｜・𝖲𝖤𝖭𝖳𝖨𝖭𝖤𝖫-𝖫𝖮𝖦𝖲` | Anti-raid, anti-spam & anti-nuke telemetry |
| | Voice | `\| • EXECUTIVE SUITE` | VIP staff voice chamber (Limit: 10) |

---

## 🛡️ Role Hierarchy

| Position | Role Name | Role ID | Permissions |
| :---: | :--- | :--- | :--- |
| **1** | `👑 ┆ 𝐅𝐎𝐔𝐍𝐃𝐄𝐑 🍷` | `1550205899069726810` | Full Administrator |
| **2** | `⚡ ┆ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍 ⚡` | `1550205902706049214` | Full Administrator |
| **3** | `🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️` | `1550205905830682795` | Moderate Members, Manage Messages |
| **4** | `✦ ᴠᴇʀɪꜰɪᴇᴅ` | `1550205910218182696` | Verified Member |
| **5** | `@✦ MEMBER` | `1550205915398152364` | Standard Member Access |

---

## ⚡ Staff & Moderation Commands Reference

Staff members can use the following commands inside `#｜・staff-operations` or anywhere permitted:

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/warn` | `/warn <user> <reason>` | Issues a recorded strike to the user's infraction history |
| `/mute` | `/mute <user> <duration> <reason>` | Applies a Discord timeout (e.g. `10m`, `1h`, `1d`) |
| `/unmute` | `/unmute <user>` | Removes timeout from a member |
| `/kick` | `/kick <user> <reason>` | Kicks member from the guild |
| `/ban` | `/ban <user> [delete_days] <reason>` | Bans member and purges recent messages |
| `/unban` | `/unban <user_id>` | Revokes a ban |
| `/modnotes` | `/modnotes <user>` | Inspects past warnings, strikes, and infractions |
| `/modpanel` | `/modpanel <member>` | Interactive button dashboard for one-click action |
| `/purge` | `/purge <amount>` | Mass deletes up to 100 recent messages |
| `/slowmode` | `/slowmode <seconds>` | Sets channel cooldown rate during chat spam |
| `/lockdown` | `/lockdown [duration]` | Locks down current channel from non-staff speaking |
| `/unlock` | `/unlock` | Restores normal speaking access after lockdown |

---

## 🚀 How to Run

1. Open a terminal in `APEX VIBES` or navigate into `ABIJITH 777`.
2. Run `run_setup.bat` or run individual Python tools:
   ```powershell
   python inspect_server.py      # View full server channels and role audit
   python setup_admin_suite.py    # Provision or update VIP & Sentinel HQ
   python apply_font_style.py     # Enforce '| • ' font style
   python deploy_embeds.py        # Re-deploy Verification Gate & Ticket desk
   ```
