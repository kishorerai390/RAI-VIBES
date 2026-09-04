import os
import sys
import re
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
    Returns a list of dicts with {'title': str, 'artist': str, 'search_query': str, 'source': 'spotify', 'thumbnail': str}
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
                tracks.append({
                    "title": title,
                    "artist": artist_name,
                    "search_query": f"{title} {artist_name} audio",
                    "thumbnail": thumbnail,
                    "source": "spotify"
                })
            elif item_type == "album":
                album_data = sp_client.album(item_id)
                album_thumb = album_data["images"][0]["url"] if album_data["images"] else ""
                for t in album_data["tracks"]["items"]:
                    artist_name = ", ".join([a["name"] for a in t["artists"]])
                    title = t["name"]
                    tracks.append({
                        "title": title,
                        "artist": artist_name,
                        "search_query": f"{title} {artist_name} audio",
                        "thumbnail": album_thumb,
                        "source": "spotify"
                    })
            elif item_type == "playlist":
                # Fetch up to 200 items from Spotify playlist
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
                    tracks.append({
                        "title": title,
                        "artist": artist_name,
                        "search_query": f"{title} {artist_name} audio",
                        "thumbnail": thumbnail,
                        "source": "spotify"
                    })
            if tracks:
                return tracks[:200]
        except Exception as e:
            print(f"[Spotify API Warning] Spotipy query failed: {e}. Falling back to public resolver.")

    # Method 2: Public oEmbed / Scrape Fallback (No API Keys needed!)
    try:
        clean_url = f"https://open.spotify.com/{item_type}/{item_id}"
        oembed_url = f"https://open.spotify.com/oembed?url={urllib.parse.quote(clean_url)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(oembed_url, timeout=10) as resp:
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
        "source": "spotify"
    })
    return tracks
