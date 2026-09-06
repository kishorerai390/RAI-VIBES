import os
import sys
import re
import json
import aiohttp
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    HAS_SPOTIPY = bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET)
    if HAS_SPOTIPY:
        sp_client = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
        )
    else:
        sp_client = None
except Exception:
    sp_client = None
    HAS_SPOTIPY = False

SPOTIFY_URL_REGEX = re.compile(
    r"https?://open\.spotify\.com/(?:intl-[a-zA-Z]+/)?(track|album|playlist)/([a-zA-Z0-9]+)"
)

def is_spotify_url(query: str) -> bool:
    """Check if query is a Spotify URL."""
    return bool(SPOTIFY_URL_REGEX.search(query))

def parse_spotify_url(query: str) -> Optional[tuple[str, str]]:
    """Returns (type, id) for a spotify URL, e.g. ('track', '4cOdK2wGLETKBW3PvgPWqT')."""
    match = SPOTIFY_URL_REGEX.search(query)
    if match:
        return match.group(1), match.group(2)
    return None

async def resolve_spotify(query: str) -> List[Dict[str, str]]:
    """
    Extracts track queries from Spotify URLs.
    Supports playlists, albums, and tracks without requiring API credentials.
    Returns a list of dicts with {'title': str, 'artist': str, 'search_query': str, 'source': 'spotify', 'thumbnail': str, 'duration': int}
    """
    parsed = parse_spotify_url(query)
    if not parsed:
        return []

    item_type, item_id = parsed
    tracks: List[Dict[str, str]] = []

    # Method 1: Using spotipy credentials if provided
    if sp_client:
        try:
            if item_type == "track":
                track_data = sp_client.track(item_id)
                artist_name = ", ".join([a["name"] for a in track_data["artists"]])
                title = track_data["name"]
                thumbnail = track_data["album"]["images"][0]["url"] if track_data["album"]["images"] else ""
                dur = int((track_data.get("duration_ms") or 0) / 1000)
                tracks.append({
                    "title": title,
                    "artist": artist_name,
                    "search_query": f"{title} {artist_name} audio",
                    "thumbnail": thumbnail,
                    "duration": dur,
                    "source": "spotify"
                })
            elif item_type == "album":
                album_data = sp_client.album(item_id)
                album_thumb = album_data["images"][0]["url"] if album_data["images"] else ""
                for t in album_data["tracks"]["items"]:
                    artist_name = ", ".join([a["name"] for a in t["artists"]])
                    title = t["name"]
                    dur = int((t.get("duration_ms") or 0) / 1000)
                    tracks.append({
                        "title": title,
                        "artist": artist_name,
                        "search_query": f"{title} {artist_name} audio",
                        "thumbnail": album_thumb,
                        "duration": dur,
                        "source": "spotify"
                    })
            elif item_type == "playlist":
                results = sp_client.playlist_items(item_id, limit=100)
                items = results.get("items", [])
                if results.get("next"):
                    try:
                        next_results = sp_client.next(results)
                        if next_results:
                            items.extend(next_results.get("items", []))
                    except Exception:
                        pass

                for item in items[:200]:
                    t = item.get("track")
                    if not t:
                        continue
                    artist_name = ", ".join([a["name"] for a in t.get("artists", [])])
                    title = t.get("name", "")
                    thumbnail = t.get("album", {}).get("images", [{}])[0].get("url", "")
                    dur = int((t.get("duration_ms") or 0) / 1000)
                    tracks.append({
                        "title": title,
                        "artist": artist_name,
                        "search_query": f"{title} {artist_name} audio",
                        "thumbnail": thumbnail,
                        "duration": dur,
                        "source": "spotify"
                    })
            if tracks:
                return tracks[:200]
        except Exception as e:
            print(f"[Spotify API Warning] Spotipy query failed: {e}. Falling back to public resolver.")

    # Method 2: Public Spotify Embed Web Scraper (Extracts ALL playlist/album tracks!)
    try:
        embed_url = f"https://open.spotify.com/embed/{item_type}/{item_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(embed_url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    
                    # 1. Try __NEXT_DATA__ JSON
                    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', text)
                    if m:
                        try:
                            json_data = json.loads(m.group(1))
                            entity = json_data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
                            cover_url = entity.get("coverArt", {}).get("sources", [{}])[-1].get("url", "")
                            
                            if item_type == "track":
                                title = entity.get("title", "")
                                artist = entity.get("subtitle", "Spotify")
                                dur = int(entity.get("duration", 0) / 1000) if entity.get("duration") else 0
                                if title:
                                    tracks.append({
                                        "title": title,
                                        "artist": artist,
                                        "search_query": f"{title} {artist} audio",
                                        "thumbnail": cover_url,
                                        "duration": dur,
                                        "source": "spotify"
                                    })
                            else:
                                track_list = entity.get("trackList", [])
                                for t in track_list[:200]:
                                    t_title = t.get("title", "")
                                    t_artist = re.sub(r'[\u00a0\xa0\u200b]+', ' ', t.get("subtitle", "Spotify")).strip()
                                    t_dur = int(t.get("duration", 0) / 1000) if t.get("duration") else 0
                                    if t_title:
                                        tracks.append({
                                            "title": t_title,
                                            "artist": t_artist,
                                            "search_query": f"{t_title} {t_artist} audio",
                                            "thumbnail": cover_url,
                                            "duration": t_dur,
                                            "source": "spotify"
                                        })
                            if tracks:
                                return tracks[:200]
                        except Exception as e:
                            print(f"[Spotify NEXT_DATA parse error] {e}")

    except Exception as e:
        print(f"[Spotify Embed Scraper Warning] {e}")

    # Method 3: Public oEmbed Fallback
    try:
        clean_url = f"https://open.spotify.com/{item_type}/{item_id}"
        oembed_url = f"https://open.spotify.com/oembed?url={urllib.parse.quote(clean_url)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(oembed_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    title = data.get("title", "")
                    thumbnail = data.get("thumbnail_url", "")
                    if title:
                        tracks.append({
                            "title": title,
                            "artist": "Spotify",
                            "search_query": f"{title} audio",
                            "thumbnail": thumbnail,
                            "duration": 0,
                            "source": "spotify"
                        })
                        return tracks
    except Exception as e:
        print(f"[Spotify oEmbed Warning] Fallback failed: {e}")

    # Fallback to search query
    tracks.append({
        "title": query,
        "artist": "Spotify",
        "search_query": query,
        "thumbnail": "",
        "duration": 0,
        "source": "spotify"
    })
    return tracks
