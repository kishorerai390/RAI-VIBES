import os
import sys
import time
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from aiohttp import web

logger = logging.getLogger("WebDashboard")

START_TIME = time.time()

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAI FAM 💗 • Real-Time Command & Telemetry Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #070510;
            --card-bg: rgba(18, 14, 32, 0.72);
            --card-border: rgba(255, 105, 180, 0.18);
            --pink-accent: #ff69b4;
            --pink-glow: rgba(255, 105, 180, 0.35);
            --cyan-accent: #00f5d4;
            --cyan-glow: rgba(0, 245, 212, 0.35);
            --purple-accent: #8b5cf6;
            --purple-glow: rgba(139, 92, 246, 0.35);
            --gold-accent: #ffd166;
            --danger-accent: #ff3366;
            --success-accent: #00ff88;
            --text-primary: #f8f9fc;
            --text-secondary: #9ea3b5;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg-base);
            background-image: 
                radial-gradient(circle at 10% 15%, rgba(255, 105, 180, 0.14) 0%, transparent 45%),
                radial-gradient(circle at 90% 85%, rgba(0, 245, 212, 0.12) 0%, transparent 45%),
                radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 60%);
            background-attachment: fixed;
            color: var(--text-primary);
            min-height: 100vh;
            padding: 30px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .dashboard-container {
            width: 100%;
            max-width: 1100px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        /* Top Hero Banner */
        .hero-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 32px;
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.55), 0 0 30px rgba(255, 105, 180, 0.12);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
            position: relative;
            overflow: hidden;
        }
        .hero-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--pink-accent), var(--purple-accent), var(--cyan-accent));
        }

        .hero-left {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .server-avatar {
            width: 68px;
            height: 68px;
            border-radius: 20px;
            border: 2px solid var(--pink-accent);
            box-shadow: 0 0 20px var(--pink-glow);
            background: #190e2c;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
        }
        .hero-titles h1 {
            font-size: 26px;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff 0%, #ff69b4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
            letter-spacing: 0.5px;
        }
        .hero-titles p {
            color: var(--text-secondary);
            font-size: 13px;
        }

        .hero-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.35);
            color: var(--success-accent);
            padding: 8px 16px;
            border-radius: 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 600;
            box-shadow: 0 0 16px rgba(0, 255, 136, 0.2);
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success-accent);
            box-shadow: 0 0 8px var(--success-accent);
            animation: pulse-dot 1.8s infinite;
        }
        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }

        /* Top 4 Metric Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 16px;
        }
        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 20px 22px;
            backdrop-filter: blur(16px);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            border-color: var(--pink-accent);
        }
        .stat-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }
        .stat-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 26px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
        }
        .stat-subtext {
            font-size: 12px;
            color: var(--cyan-accent);
        }

        /* Nav Tabs */
        .tab-bar {
            display: flex;
            gap: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 12px;
            overflow-x: auto;
        }
        .tab-btn {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-secondary);
            padding: 10px 18px;
            border-radius: 12px;
            font-family: 'Outfit', sans-serif;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .tab-btn:hover {
            background: rgba(255, 105, 180, 0.12);
            color: #fff;
            border-color: var(--pink-accent);
        }
        .tab-btn.active {
            background: linear-gradient(135deg, rgba(255, 105, 180, 0.2), rgba(139, 92, 246, 0.2));
            color: #fff;
            border-color: var(--pink-accent);
            box-shadow: 0 0 16px var(--pink-glow);
        }

        .tab-content {
            display: none;
            flex-direction: column;
            gap: 20px;
        }
        .tab-content.active {
            display: flex;
        }

        /* Cards Layout */
        .two-column {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
            gap: 20px;
        }
        .panel-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 24px;
            backdrop-filter: blur(18px);
        }
        .panel-title {
            font-size: 16px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .panel-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            background: rgba(0, 245, 212, 0.12);
            color: var(--cyan-accent);
            border: 1px solid rgba(0, 245, 212, 0.3);
            padding: 4px 8px;
            border-radius: 8px;
        }

        /* List Items */
        .data-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .list-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(10, 8, 22, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 12px 16px;
            transition: all 0.2s ease;
        }
        .list-row:hover {
            background: rgba(255, 105, 180, 0.06);
            border-color: rgba(255, 105, 180, 0.3);
        }
        .list-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .list-rank {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 700;
            color: var(--pink-accent);
            min-width: 24px;
        }
        .list-name {
            font-size: 13px;
            font-weight: 600;
            color: #fff;
        }
        .list-meta {
            font-size: 11px;
            color: var(--text-secondary);
        }
        .list-pill {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.06);
            padding: 4px 10px;
            border-radius: 8px;
            color: var(--cyan-accent);
        }

        /* Shield Grid */
        .shield-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }
        .shield-item {
            background: rgba(10, 8, 22, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .shield-name {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
        }
        .shield-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 8px;
            border-radius: 6px;
            width: fit-content;
        }
        .shield-active {
            background: rgba(0, 255, 136, 0.12);
            color: var(--success-accent);
            border: 1px solid rgba(0, 255, 136, 0.3);
        }
        .shield-standby {
            background: rgba(255, 209, 102, 0.12);
            color: var(--gold-accent);
            border: 1px solid rgba(255, 209, 102, 0.3);
        }
        .shield-alert {
            background: rgba(255, 51, 102, 0.15);
            color: var(--danger-accent);
            border: 1px solid rgba(255, 51, 102, 0.4);
        }

        /* Radio Stations Grid */
        .radio-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 14px;
        }
        .station-card {
            background: rgba(10, 8, 22, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            transition: all 0.2s ease;
        }
        .station-card:hover {
            border-color: var(--cyan-accent);
            transform: translateY(-2px);
        }
        .station-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .station-name {
            font-size: 13px;
            font-weight: 700;
            color: #fff;
        }
        .station-desc {
            font-size: 11px;
            color: var(--text-secondary);
            line-height: 1.5;
        }
        .station-cmd {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            background: rgba(255, 105, 180, 0.1);
            color: var(--pink-accent);
            padding: 4px 8px;
            border-radius: 6px;
            width: fit-content;
        }

        /* Commands Section */
        .commands-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 12px;
        }
        .cmd-item {
            background: rgba(10, 8, 22, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 12px 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }
        .cmd-name { color: var(--pink-accent); font-weight: 600; margin-bottom: 4px; }
        .cmd-desc { color: var(--text-secondary); font-family: 'Outfit', sans-serif; font-size: 11px; }

        /* Links Bar */
        .dash-links {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
        }
        .btn-dash {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #fff;
            text-decoration: none;
            padding: 10px 18px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .btn-dash:hover {
            background: rgba(255, 105, 180, 0.15);
            border-color: var(--pink-accent);
            color: var(--pink-accent);
            transform: translateY(-2px);
        }

        footer {
            text-align: center;
            font-size: 12px;
            color: #64748b;
            padding: 10px 0 20px;
            line-height: 1.6;
        }

        @media (max-width: 768px) {
            .two-column {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Hero Header -->
        <div class="hero-card">
            <div class="hero-left">
                <div class="server-avatar">🌸</div>
                <div class="hero-titles">
                    <h1>RAI FAM 💗 • COMMAND CLOUD</h1>
                    <p>High-Fidelity Audio Engine • Autonomous Defense • Real-Time Telemetry</p>
                </div>
            </div>
            <div class="hero-status-pill">
                <div class="status-dot"></div>
                <span id="system-status-text">SYSTEMS 100% ONLINE</span>
            </div>
        </div>

        <!-- Metric Counter Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Voice Lounge Hours</div>
                <div class="stat-value" id="val-voice-hours">0.0 hrs</div>
                <div class="stat-subtext" id="val-tracked-users">Tracking community participation</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Tracks Streamed</div>
                <div class="stat-value" id="val-streams">0 plays</div>
                <div class="stat-subtext">384 kbps Lossless Audio</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Sentinel Defense Shields</div>
                <div class="stat-value" id="val-shields-active">5 Active</div>
                <div class="stat-subtext" id="val-defense-state">Zero-Setup Protection</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Cluster System Uptime</div>
                <div class="stat-value" id="val-uptime">0h 00m</div>
                <div class="stat-subtext" id="val-memory">24/7 Continuous Mode</div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="tab-bar">
            <button class="tab-btn active" onclick="switchTab('telemetry', this)">📊 Audio & Voice Telemetry</button>
            <button class="tab-btn" onclick="switchTab('security', this)">🛡️ Sentinel Security Matrix</button>
            <button class="tab-btn" onclick="switchTab('radio', this)">📻 24/7 Radio Stations & DJ</button>
            <button class="tab-btn" onclick="switchTab('commands', this)">⚡ Command Reference</button>
        </div>

        <!-- TAB 1: TELEMETRY -->
        <div id="tab-telemetry" class="tab-content active">
            <div class="two-column">
                <!-- Top 5 Streamed Tracks -->
                <div class="panel-card">
                    <div class="panel-title">
                        <span>🎵 Most Streamed Tracks</span>
                        <span class="panel-badge">Live Trends</span>
                    </div>
                    <div class="data-list" id="list-top-tracks">
                        <div class="list-row"><span class="list-meta">Loading music analytics...</span></div>
                    </div>
                </div>

                <!-- Top Voice Loungers -->
                <div class="panel-card">
                    <div class="panel-title">
                        <span>👑 Top Voice Loungers</span>
                        <span class="panel-badge">Time Logged</span>
                    </div>
                    <div class="data-list" id="list-top-listeners">
                        <div class="list-row"><span class="list-meta">Loading voice leaderboard...</span></div>
                    </div>
                </div>
            </div>

            <!-- Voice Lounge Distribution -->
            <div class="panel-card">
                <div class="panel-title">
                    <span>🔥 Voice Lounge Activity Distribution</span>
                    <span class="panel-badge">Top Channels</span>
                </div>
                <div class="data-list" id="list-top-lounges">
                    <div class="list-row"><span class="list-meta">Loading channel breakdown...</span></div>
                </div>
            </div>
        </div>

        <!-- TAB 2: SECURITY -->
        <div id="tab-security" class="tab-content">
            <div class="panel-card">
                <div class="panel-title">
                    <span>🛡️ Sentinel Automated Shields</span>
                    <span class="panel-badge" id="badge-lockdown-status">NORMAL COMM</span>
                </div>
                <div class="shield-grid">
                    <div class="shield-item">
                        <div class="shield-name">Anti-Nuke Protection</div>
                        <div class="shield-badge shield-active" id="shield-antinuke">🟢 ACTIVE</div>
                    </div>
                    <div class="shield-item">
                        <div class="shield-name">Anti-Raid Velocity</div>
                        <div class="shield-badge shield-active" id="shield-antiraid">🟢 ACTIVE</div>
                    </div>
                    <div class="shield-item">
                        <div class="shield-name">Anti-Spam Filter</div>
                        <div class="shield-badge shield-active" id="shield-antispam">🟢 ACTIVE</div>
                    </div>
                    <div class="shield-item">
                        <div class="shield-name">Anti-Phishing & Links</div>
                        <div class="shield-badge shield-active" id="shield-antilink">🟢 ACTIVE</div>
                    </div>
                    <div class="shield-item">
                        <div class="shield-name">Anti-Mass Mention</div>
                        <div class="shield-badge shield-active" id="shield-antimention">🟢 ACTIVE</div>
                    </div>
                    <div class="shield-item">
                        <div class="shield-name">Emergency Lockdown</div>
                        <div class="shield-badge shield-standby" id="shield-lockdown">⚪ STANDBY</div>
                    </div>
                </div>
            </div>

            <!-- Security Threat Event Log -->
            <div class="panel-card">
                <div class="panel-title">
                    <span>📝 Recent Sentinel Incidents & Defense Actions</span>
                    <span class="panel-badge">SQLite Audit</span>
                </div>
                <div class="data-list" id="list-security-events">
                    <div class="list-row"><span class="list-meta">No recent threats or defense actions recorded. Server secure.</span></div>
                </div>
            </div>
        </div>

        <!-- TAB 3: RADIO & DJ STATIONS -->
        <div id="tab-radio" class="tab-content">
            <div class="panel-card">
                <div class="panel-title">
                    <span>📻 24/7 Live Themed Radio Stations & Presets</span>
                    <span class="panel-badge">Continuous Audio</span>
                </div>
                <div class="radio-grid" id="grid-radio-stations">
                    <div class="station-card">
                        <div class="station-header">
                            <span class="station-name">📻 Tamil Panpalai Gold 24/7</span>
                        </div>
                        <div class="station-desc">Non-stop golden Tamil hits, evergreen classics & melodies.</div>
                        <div class="station-cmd">/radio station: Tamil Nadu FM Live 24/7</div>
                    </div>
                    <div class="station-card">
                        <div class="station-header">
                            <span class="station-name">☕ SomaFM Groove Salad</span>
                        </div>
                        <div class="station-desc">World-renowned chilled ambient/downtempo beats to study, relax, or vibe to.</div>
                        <div class="station-cmd">/radio station: Global Lofi Hip Hop / Study Beats</div>
                    </div>
                    <div class="station-card">
                        <div class="station-header">
                            <span class="station-name">🧠 432Hz Deep Focus & Binaural Waves</span>
                        </div>
                        <div class="station-desc">Atmospheric soundscapes and deep theta wave focus music for study & productivity.</div>
                        <div class="station-cmd">/radio station: 432Hz Deep Focus & Binaural Study</div>
                    </div>
                    <div class="station-card">
                        <div class="station-header">
                            <span class="station-name">🍜 Tokyo Nights Anime Chill</span>
                        </div>
                        <div class="station-desc">Calming anime instrumental lo-fi, lofi piano, and night city vibes.</div>
                        <div class="station-cmd">/radio station: Tokyo Nights Anime Chill Lo-Fi</div>
                    </div>
                    <div class="station-card">
                        <div class="station-header">
                            <span class="station-name">🏎️ Drift Phonk & Bass Energy</span>
                        </div>
                        <div class="station-desc">High-octane drift phonk, aggressive bass workout, and adrenaline electronic audio.</div>
                        <div class="station-cmd">/radio station: Drift Phonk & Bass Energy</div>
                    </div>
                    <div class="station-card">
                        <div class="station-header">
                            <span class="station-name">🏙️ 80s Tokyo City Pop & Funk</span>
                        </div>
                        <div class="station-desc">Nostalgic 80s groove, retro anime aesthetics, and disco funk.</div>
                        <div class="station-cmd">/radio station: 80s Japanese City Pop & Funk</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 4: COMMAND REFERENCE -->
        <div id="tab-commands" class="tab-content">
            <div class="panel-card">
                <div class="panel-title">
                    <span>⚡ Quick Slash Command Reference</span>
                    <span class="panel-badge">All Bots</span>
                </div>
                <div class="commands-grid">
                    <div class="cmd-item">
                        <div class="cmd-name">/play &lt;song&gt;</div>
                        <div class="cmd-desc">Stream from YouTube, Spotify, or Apple Music</div>
                    </div>
                    <div class="cmd-item">
                        <div class="cmd-name">/radio &lt;station&gt;</div>
                        <div class="cmd-desc">Stream 24/7 themed live stations</div>
                    </div>
                    <div class="cmd-item">
                        <div class="cmd-name">/dj sounddrop &lt;effect&gt;</div>
                        <div class="cmd-desc">Drop instant hype airhorn, scratch, or laser</div>
                    </div>
                    <div class="cmd-item">
                        <div class="cmd-name">/dj stage_announce</div>
                        <div class="cmd-desc">Broadcast live Stage / VC listening party</div>
                    </div>
                    <div class="cmd-item">
                        <div class="cmd-name">/telemetry voice</div>
                        <div class="cmd-desc">Check your voice lounge hours, rank & stats</div>
                    </div>
                    <div class="cmd-item">
                        <div class="cmd-name">/telemetry top</div>
                        <div class="cmd-desc">View server audio leaderboard & top listeners</div>
                    </div>
                    <div class="cmd-item">
                        <div class="cmd-name">/security status</div>
                        <div class="cmd-desc">Inspect anti-nuke, anti-raid & lockdown state</div>
                    </div>
                    <div class="cmd-item">
                        <div class="cmd-name">/security audit</div>
                        <div class="cmd-desc">View recent security incidents & alerts</div>
                    </div>
                    <div class="cmd-item">
                        <div class="cmd-name">/security backup</div>
                        <div class="cmd-desc">Create immediate layout & role snapshot backup</div>
                    </div>
                    <div class="cmd-item">
                        <div class="cmd-name">/stay247 &lt;enable|disable&gt;</div>
                        <div class="cmd-desc">Keep music bot in voice channel 24/7</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- External Bot Directories -->
        <div class="panel-card">
            <div class="panel-title">
                <span>🔗 Server External Dashboards</span>
                <span class="panel-badge">Navigation</span>
            </div>
            <div class="dash-links">
                <a href="https://koya.gg/en/dashboard/1457382179981099090" target="_blank" class="btn-dash">🌸 Koya Dashboard</a>
                <a href="https://dashboard.sapph.xyz/" target="_blank" class="btn-dash">💎 Sapphire Dashboard</a>
                <a href="https://invite-tracker.com" target="_blank" class="btn-dash">📨 Invite Tracker</a>
                <a href="https://wickbot.com" target="_blank" class="btn-dash">🕯️ Wick Dashboard</a>
                <a href="https://disboard.org" target="_blank" class="btn-dash">🌐 Disboard Listing</a>
            </div>
        </div>

        <footer>
            RAI FAM 💗 • Cloud Cluster Online • High Fidelity Audio & Defense Ecosystem<br>
            Multi-Shard Bot Architecture • Real-Time Telemetry & REST API Engine Active
        </footer>
    </div>

    <script>
        function switchTab(tabId, btn) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            const target = document.getElementById('tab-' + tabId);
            if (target) target.classList.add('active');
        }

        async function fetchDashboardData() {
            try {
                // 1. Fetch System Status
                const resStatus = await fetch('/api/status');
                if (resStatus.ok) {
                    const st = await resStatus.json();
                    document.getElementById('val-uptime').innerText = st.uptime_formatted || 'Online';
                    if (st.memory_mb) {
                        document.getElementById('val-memory').innerText = 'RAM: ' + st.memory_mb + ' MB • 24/7 Mode';
                    }
                }

                // 2. Fetch Telemetry
                const resTelem = await fetch('/api/telemetry');
                if (resTelem.ok) {
                    const tm = await resTelem.json();
                    document.getElementById('val-voice-hours').innerText = (tm.total_voice_hours || 0) + ' hrs';
                    document.getElementById('val-streams').innerText = (tm.total_streams || 0) + ' plays';
                    document.getElementById('val-tracked-users').innerText = (tm.total_tracked_users || 0) + ' Active Voice Loungers';

                    // Top Tracks
                    const tracksList = document.getElementById('list-top-tracks');
                    if (tm.top_tracks && tm.top_tracks.length > 0) {
                        tracksList.innerHTML = tm.top_tracks.map((t, idx) => `
                            <div class="list-row">
                                <div class="list-left">
                                    <span class="list-rank">#${idx + 1}</span>
                                    <div>
                                        <div class="list-name">${escapeHtml(t.title)}</div>
                                        <div class="list-meta">Continuous Stream</div>
                                    </div>
                                </div>
                                <span class="list-pill">${t.plays} Plays</span>
                            </div>
                        `).join('');
                    } else {
                        tracksList.innerHTML = '<div class="list-row"><span class="list-meta">Stream songs with /play or in song-requests!</span></div>';
                    }

                    // Top Listeners
                    const listenersList = document.getElementById('list-top-listeners');
                    if (tm.top_listeners && tm.top_listeners.length > 0) {
                        listenersList.innerHTML = tm.top_listeners.map((u, idx) => `
                            <div class="list-row">
                                <div class="list-left">
                                    <span class="list-rank">#${idx + 1}</span>
                                    <div>
                                        <div class="list-name">User ID: ${u.user_id}</div>
                                        <div class="list-meta">Favorite: ${escapeHtml(u.fav_lounge)}</div>
                                    </div>
                                </div>
                                <span class="list-pill">${u.hours} hrs</span>
                            </div>
                        `).join('');
                    } else {
                        listenersList.innerHTML = '<div class="list-row"><span class="list-meta">Join voice lounges to log your hours!</span></div>';
                    }

                    // Top Lounges
                    const loungesList = document.getElementById('list-top-lounges');
                    if (tm.top_lounges && tm.top_lounges.length > 0) {
                        loungesList.innerHTML = tm.top_lounges.map((l, idx) => `
                            <div class="list-row">
                                <div class="list-left">
                                    <span class="list-rank">#${idx + 1}</span>
                                    <div class="list-name">${escapeHtml(l.channel)}</div>
                                </div>
                                <span class="list-pill">${l.hours} hrs (${l.minutes} mins)</span>
                            </div>
                        `).join('');
                    } else {
                        loungesList.innerHTML = '<div class="list-row"><span class="list-meta">No voice lounge activity logged yet.</span></div>';
                    }
                }

                // 3. Fetch Security
                const resSec = await fetch('/api/security');
                if (resSec.ok) {
                    const sec = await resSec.json();
                    const shields = sec.shields || {};
                    const states = sec.states || {};

                    const countActive = Object.values(shields).filter(Boolean).length;
                    document.getElementById('val-shields-active').innerText = countActive + ' Active';

                    const isLockdown = states.lockdown;
                    const isRaid = states.raid_mode;

                    const lockBadge = document.getElementById('badge-lockdown-status');
                    if (isLockdown) {
                        lockBadge.innerText = 'LOCKDOWN ACTIVE';
                        lockBadge.style.color = 'var(--danger-accent)';
                        lockBadge.style.borderColor = 'var(--danger-accent)';
                    } else if (isRaid) {
                        lockBadge.innerText = 'RAID MODE SHIELD';
                        lockBadge.style.color = 'var(--gold-accent)';
                        lockBadge.style.borderColor = 'var(--gold-accent)';
                    } else {
                        lockBadge.innerText = 'SHIELDS ONLINE';
                        lockBadge.style.color = 'var(--success-accent)';
                    }

                    // Events
                    const eventsList = document.getElementById('list-security-events');
                    if (sec.recent_events && sec.recent_events.length > 0) {
                        eventsList.innerHTML = sec.recent_events.map(ev => `
                            <div class="list-row">
                                <div class="list-left">
                                    <span class="list-rank">${ev.severity === 'CRITICAL' ? '🔴' : (ev.severity === 'HIGH' ? '🟠' : '🟡')}</span>
                                    <div>
                                        <div class="list-name">${escapeHtml(ev.event_type)}</div>
                                        <div class="list-meta">${escapeHtml(ev.details)}</div>
                                    </div>
                                </div>
                                <span class="list-pill">${escapeHtml(ev.timestamp.split(' ')[1] || ev.timestamp)}</span>
                            </div>
                        `).join('');
                    }
                }
            } catch (err) {
                console.debug('Dashboard polling notice:', err);
            }
        }

        function escapeHtml(text) {
            if (!text) return '';
            const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
            return String(text).replace(/[&<>"']/g, m => map[m]);
        }

        // Initial fetch and 8s recurring poll
        fetchDashboardData();
        setInterval(fetchDashboardData, 8000);
    </script>
</body>
</html>
"""

def format_uptime(seconds: float) -> str:
    secs = int(seconds)
    days, secs = divmod(secs, 86400)
    hours, secs = divmod(secs, 3600)
    mins, secs = divmod(secs, 60)
    if days > 0:
        return f"{days}d {hours}h {mins}m"
    return f"{hours}h {mins}m"

async def handle_dashboard(request):
    return web.Response(text=HTML_DASHBOARD, content_type="text/html")

async def handle_ping_check(request):
    return web.json_response({"status": "healthy", "service": "RAI-VIBES-CLOUD", "code": 200})

async def handle_api_status(request):
    uptime_sec = time.time() - START_TIME
    
    # Memory check
    mem_mb = None
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb = round(process.memory_info().rss / (1024 * 1024), 1)
    except Exception:
        pass

    return web.json_response({
        "status": "online",
        "service": "RAI-VIBES-ECOSYSTEM",
        "uptime_seconds": int(uptime_sec),
        "uptime_formatted": format_uptime(uptime_sec),
        "memory_mb": mem_mb,
        "timestamp": int(time.time()),
        "active_modules": [
            "Lossless Audio Engine (384 kbps)",
            "Sentinel Autonomous Defense",
            "Voice Lounges Telemetry",
            "24/7 Live Radio FM",
            "Web Command Center"
        ]
    })

async def handle_api_telemetry(request):
    try:
        from cogs.telemetry import get_telemetry_summary
        summary = get_telemetry_summary()
        return web.json_response(summary)
    except Exception as e:
        logger.debug(f"Telemetry API notice: {e}")
        return web.json_response({
            "total_voice_hours": 0.0,
            "total_streams": 0,
            "total_tracked_users": 0,
            "top_listeners": [],
            "top_tracks": [],
            "top_lounges": []
        })

async def handle_api_security(request):
    try:
        import database
        # Guild ID for RAI FAM is 1457382179981099090
        guild_id = 1457382179981099090
        summary = await database.get_security_summary(guild_id)
        return web.json_response(summary)
    except Exception as e:
        logger.debug(f"Security API notice: {e}")
        return web.json_response({
            "guild_id": 1457382179981099090,
            "shields": {
                "antinuke": True,
                "antiraid": True,
                "antispam": True,
                "antilink": True,
                "antimention": True
            },
            "states": {
                "raid_mode": False,
                "lockdown": False,
                "whitelisted_users": 0,
                "whitelisted_roles": 0
            },
            "recent_events": []
        })

async def handle_api_music(request):
    try:
        from cogs.radio import RADIO_STATIONS
        from cogs.dj import DJ
        stations = [
            {
                "key": k,
                "name": v.get("name"),
                "desc": v.get("desc"),
                "thumb": v.get("thumb")
            }
            for k, v in RADIO_STATIONS.items()
        ]
        sounddrops = list(getattr(DJ, "DJ_SOUNDDROPS", {}).keys())
        return web.json_response({
            "stations": stations,
            "sounddrops": sounddrops
        })
    except Exception as e:
        return web.json_response({"stations": [], "sounddrops": []})

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_dashboard)
    app.router.add_get("/health", handle_dashboard)
    app.router.add_get("/ping", handle_ping_check)
    app.router.add_get("/api/status", handle_api_status)
    app.router.add_get("/api/telemetry", handle_api_telemetry)
    app.router.add_get("/api/security", handle_api_security)
    app.router.add_get("/api/music", handle_api_music)
    return app

async def start_web_server(port: Optional[int] = None):
    if port is None:
        port = int(os.getenv("PORT", "10000"))
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 [Web Command Dashboard] Listening on http://0.0.0.0:{port} (Interactive Dashboard Ready)")
    return runner

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    port = int(os.getenv("PORT", "10000"))
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=port)
