# Fire & Ice - private podcast setup

Turn the WAV episodes into a private podcast you can subscribe to in Overcast or
Apple Podcasts (no public directory listing required).

You need three things: MP3 audio, an `feed.xml` RSS file, and a public place to
host them. These scripts handle the first two.

## 0. One-time prerequisite

```
brew install ffmpeg
```

(`ffmpeg` converts the audio; `ffprobe`, included with it, lets the feed builder
read exact episode durations.)

## 1. Convert WAV to MP3

Apple Podcasts does not accept WAV, and WAV files are huge. Convert to MP3 first.

Put your `.wav` files in `daily-podcasts/wav/` (named to match the transcripts,
e.g. `day-01-pod-1-land-of-fire-and-ice.wav`), then:

```
cd podcast-feed
./convert_to_mp3.sh
```

This writes loudness-normalized mono MP3s to `podcast-feed/audio/`. (Edit the
script to change bitrate; 96k is the default, 64k makes smaller files.)

## 2. Pick a host and get your base URL

The MP3s and `feed.xml` must sit at public HTTPS URLs. Two easy options:

- **GitHub Pages (free, simplest).** Make a repo (e.g. `iceland-podcast`), put
  `feed.xml`, `cover.jpg`, and the `audio/` folder in it, enable Pages on the
  main branch. Your base URL becomes
  `https://<your-github-username>.github.io/iceland-podcast`.
  Episodes are ~7-22 MB each, ~300 MB total - well within Pages limits.

- **Cloudflare R2 / an S3 bucket (free egress on R2).** Upload `audio/`,
  `cover.jpg`, and `feed.xml` as public objects; base URL is your bucket's public
  URL. Better if you want it truly private-ish or expect lots of listens.

You do NOT need to submit to Apple's public directory - you'll add the feed by URL.

## 3. Build the feed

Use the base URL from step 2 (no trailing slash):

```
python3 build_feed.py https://<your-username>.github.io/iceland-podcast
```

This scans `audio/`, writes `feed.xml`, and skips any episode whose MP3 is not
there yet (so you can run it again after converting more). The show is marked as
a "serial," with episode numbers 1-23, so apps play it oldest-first in order.

## 4. Add a cover image

Apple wants a square JPG/PNG, 1400x1400 to 3000x3000 px, named `cover.jpg`, sitting
next to `feed.xml`. (Ask Claude to generate one from a trip photo if you like.)

## 5. Upload

Put `feed.xml`, `cover.jpg`, and the whole `audio/` folder at your host so that:
- feed:  `BASE_URL/feed.xml`
- cover: `BASE_URL/cover.jpg`
- audio: `BASE_URL/audio/day-01-pod-1-....mp3`

## 6. Subscribe by URL on your phone

- **Overcast:** tap `+` (top right) -> scroll to the bottom -> **Add URL** ->
  paste `BASE_URL/feed.xml`.
- **Apple Podcasts (iOS):** Library tab -> the `...` menu (top right) ->
  **Add a Show by URL...** -> paste `BASE_URL/feed.xml`.
  (On a Mac: Podcasts app -> File -> Add a Show by URL.)

The series is marked serial, so both apps will offer to play oldest-first. In
Overcast you can also set the podcast's sort to "Oldest to Newest."

## Re-running

Whenever you add or re-export episodes: re-run `convert_to_mp3.sh`, re-run
`build_feed.py`, re-upload the changed files. Podcast apps refresh the feed
automatically and pull in new episodes.
