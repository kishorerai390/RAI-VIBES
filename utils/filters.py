import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# FFmpeg audio filter configurations
FILTER_PRESETS = {
    "off": None,
    "bassboost_low": "equalizer=f=60:width_type=h:width=50:g=6",
    "bassboost_medium": "equalizer=f=60:width_type=h:width=50:g=12",
    "bassboost_high": "equalizer=f=60:width_type=h:width=50:g=18",
    "bassboost_extreme": "equalizer=f=60:width_type=h:width=50:g=25",
    "nightcore": "asetrate=48000*1.25,aresample=48000,atempo=1.06",
    "slowed": "atempo=0.85,asetrate=48000*0.9,aresample=48000,aecho=0.8:0.88:60:0.4",
    "8d": "apulsator=hz=0.125",
    "vaporwave": "aresample=48000,asetrate=48000*0.8",
    "treble": "treble=g=6",
    "karaoke": "stereotools=mlev=0.01",
    "pop": "equalizer=f=1000:width_type=h:width=100:g=3",
    "rock": "equalizer=f=100:width_type=h:width=100:g=4,equalizer=f=8000:width_type=h:width=100:g=4",
    "soft": "lowpass=f=1000",
}

def get_filter_string(active_filters: list[str], custom_speed: float = 1.0) -> str:
    """Builds combined FFmpeg audio filter string."""
    filters = []
    
    for f in active_filters:
        if f in FILTER_PRESETS and FILTER_PRESETS[f]:
            filters.append(FILTER_PRESETS[f])

    if custom_speed != 1.0 and 0.5 <= custom_speed <= 2.0:
        filters.append(f"atempo={custom_speed}")

    if not filters:
        return ""

    return "-af " + ",".join(filters)
