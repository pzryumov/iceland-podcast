#!/usr/bin/env python3
"""Build a podcast RSS feed (feed.xml) for the "Fire & Ice" Iceland series.

It scans an audio directory for the episode MP3s, reads each file's size (and,
if ffprobe is available, its exact duration), and writes a valid RSS 2.0 +
iTunes podcast feed that Overcast / Apple Podcasts can subscribe to by URL.

Usage:
    python3 build_feed.py BASE_URL [--audio AUDIO_DIR] [--out feed.xml]

BASE_URL is the public folder where feed.xml, cover.jpg and the audio/ folder
will live, e.g.  https://pzryumov.github.io/iceland-podcast
(no trailing slash needed). Audio files are expected at BASE_URL/audio/<name>.mp3

The show is marked itunes:type=serial with episode numbers 1..23, so apps play
it oldest-first, in order.
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape, quoteattr

SHOW_TITLE = "Fire & Ice: An Iceland Road-Trip Podcast"
SHOW_AUTHOR = "The Zryumov family"
SHOW_OWNER_EMAIL = "pzryumov@gmail.com"
SHOW_DESCRIPTION = (
    "A family travel-and-learning podcast for the drives on a 10-day Iceland "
    "road trip. Two hosts, Anna and Magnus, tell the story of Iceland - "
    "volcanoes, Vikings, glaciers, elves, puffins and more - starting from "
    "zero and building day by day. Made for grown-ups and for kids aged 7 and 9 "
    "in the back seat."
)

# (episode number, transcript/audio basename, episode title, one-line description, label minutes)
EPISODES = [
    (1,  "day-01-pod-1-land-of-fire-and-ice",               "The Land of Fire and Ice",                 "What and where Iceland is: a brand-new island still being built on the Mid-Atlantic Ridge.", 30),
    (2,  "day-01-pod-2-the-vikings-arrive",                 "The Vikings Arrive",                       "How an empty island got its people: Ingolfur Arnarson, the high-seat pillars, and the Althingi.", 30),
    (3,  "day-01-pod-3-waterfalls-and-eyjafjallajokull",    "Waterfalls and a Volcano You Can't Pronounce", "Why Iceland has thousands of waterfalls, plus the 2010 Eyjafjallajokull eruption that grounded airplanes.", 30),
    (4,  "day-02-pod-1-glaciers-and-the-highlands",         "Glaciers and the Highlands",               "Rivers of ice, the valley of Thorsmork, and sudden glacial floods.", 30),
    (5,  "day-02-pod-2-norse-gods-and-the-days-of-the-week","Norse Gods and the Days of the Week",      "Odin, Thor, Loki and Freyja - and why Thursday is literally Thor's day.", 30),
    (6,  "day-03-pod-1-turf-houses-and-old-iceland",        "Turf Houses and How People Survived",      "A thousand years of life in houses made of grass.", 15),
    (7,  "day-03-pod-2-black-sand-basalt-and-stone-trolls", "Black Sand, Basalt Columns, and Stone Trolls", "Reynisfjara's geology and folklore - and its genuinely dangerous waves.", 30),
    (8,  "day-03-pod-3-puffins-and-the-birds-of-iceland",   "Puffins and the Birds of Iceland",         "Sea parrots, pufflings, and the Arctic tern's pole-to-pole journey.", 20),
    (9,  "day-04-pod-1-the-laki-eruption-of-1783",          "The Laki Eruption of 1783",                "The eruption that caused a famine and changed weather across the world.", 30),
    (10, "day-04-pod-2-canyons-moss-and-folklore",          "Carved by Rivers: Canyons, Moss, and Folklore", "The Fjadrargljufur canyon and the legend of the sisters of Klaustur.", 15),
    (11, "day-05-pod-1-vatnajokull-europes-ice-cap",        "Vatnajokull, Europe's Greatest Ice Cap",   "Fire underneath the ice, and a waterfall made of black basalt columns.", 30),
    (12, "day-05-pod-2-icebergs-and-a-warming-world",       "Icebergs and a Warming World",             "The glacier lagoon, why ice glows blue, and a changing climate.", 30),
    (13, "day-05-pod-3-the-hidden-people-and-elves",        "The Hidden People - Elves and Folklore",   "Elves, roads that bend around rocks, and the 13 Yule Lads.", 30),
    (14, "day-06-pod-1-the-sagas",                          "The Sagas",                                "How a tiny, poor, treeless nation wrote some of the world's greatest stories.", 30),
    (15, "day-06-pod-2-welcome-to-reykjavik",              "Welcome to Reykjavik",                     "From a lone Viking farm to the world's northernmost capital.", 15),
    (16, "day-07-pod-1-how-iceland-became-free",            "How Iceland Became Free",                  "Commonwealth to republic, and why June 17 is the country's birthday.", 30),
    (17, "day-07-pod-2-being-a-kid-in-iceland",             "Being a Kid in Iceland",                   "Names with no surnames, the football miracle, and the Viking clap.", 20),
    (18, "day-08-pod-1-thingvellir-two-continents-and-a-nation", "Thingvellir: Two Continents and a Nation", "Standing in the crack between two continents, where Iceland was born as a nation.", 30),
    (19, "day-08-pod-2-geysers-and-geothermal-iceland",     "Geysers and Geothermal Iceland",           "Exploding water on a timer, and tomatoes grown in the Arctic.", 30),
    (20, "day-08-pod-3-the-woman-who-saved-gullfoss",       "The Woman Who Saved Gullfoss",             "Sigridur Tomasdottir's fight to save the Golden Falls.", 15),
    (21, "day-09-pod-1-blue-lagoon-and-reykjanes-volcanoes","The Blue Lagoon and Reykjanes' New Volcanoes", "A spa born from a power plant, on a peninsula making brand-new lava.", 30),
    (22, "day-09-pod-2-pool-culture-and-the-geothermal-life","Pool Culture and the Geothermal Good Life", "Why every Icelandic town has a hot pot - and runs on heat from the ground.", 15),
    (23, "day-10-pod-1-iceland-in-ten-days",                "Iceland in Ten Days",                      "The whole trip tied together, a family quiz, and goodbye.", 30),
]


def ffprobe_duration(path):
    """Return 'HH:MM:SS' from ffprobe, or None if ffprobe is unavailable/fails."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nokey=1", path],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        secs = int(round(float(out)))
        return f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base_url", help="Public base URL (no trailing slash), e.g. https://you.github.io/iceland-podcast")
    ap.add_argument("--audio", default="audio", help="Local audio directory to scan (default: audio)")
    ap.add_argument("--out", default="feed.xml", help="Output feed path (default: feed.xml)")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    base_attr = escape(base)

    # Stable, increasing publish dates so order is preserved (one per day).
    pub_base = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)

    items = []
    missing = []
    for num, basename, title, desc, label_min in EPISODES:
        mp3_path = os.path.join(args.audio, basename + ".mp3")
        if not os.path.exists(mp3_path):
            missing.append(basename + ".mp3")
            continue
        size = os.path.getsize(mp3_path)
        duration = ffprobe_duration(mp3_path) or f"00:{label_min:02d}:00"
        pub = format_datetime(pub_base + timedelta(days=num - 1))
        url = f"{base}/audio/{basename}.mp3"
        items.append(f"""    <item>
      <title>{escape(f'Ep {num}: {title}')}</title>
      <itunes:title>{escape(title)}</itunes:title>
      <itunes:episode>{num}</itunes:episode>
      <itunes:episodeType>full</itunes:episodeType>
      <description>{escape(desc)}</description>
      <itunes:summary>{escape(desc)}</itunes:summary>
      <enclosure url={quoteattr(url)} length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">fireandice-ep{num:02d}</guid>
      <pubDate>{pub}</pubDate>
      <itunes:duration>{duration}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    channel = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{escape(SHOW_TITLE)}</title>
    <link>{base_attr}</link>
    <language>en-us</language>
    <copyright>(c) The Zryumov family</copyright>
    <description>{escape(SHOW_DESCRIPTION)}</description>
    <itunes:summary>{escape(SHOW_DESCRIPTION)}</itunes:summary>
    <itunes:author>{escape(SHOW_AUTHOR)}</itunes:author>
    <itunes:type>serial</itunes:type>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href={quoteattr(base + '/cover.jpg')}/>
    <itunes:category text="Kids &amp; Family">
      <itunes:category text="Education for Kids"/>
    </itunes:category>
    <itunes:owner>
      <itunes:name>{escape(SHOW_AUTHOR)}</itunes:name>
      <itunes:email>{escape(SHOW_OWNER_EMAIL)}</itunes:email>
    </itunes:owner>
{os.linesep.join(items)}
  </channel>
</rss>
"""

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(channel)

    print(f"Wrote {args.out} with {len(items)} episode(s). Base URL: {base}")
    if missing:
        print(f"  NOTE: {len(missing)} audio file(s) not found in '{args.audio}' (skipped):")
        for m in missing:
            print(f"    - {m}")


if __name__ == "__main__":
    main()
