import asyncio
import os
import re
import json
import glob
import random
import logging
from typing import Union
from functools import partial

import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from AviaxMusic.utils.database import is_on_off
from AviaxMusic.utils.formatters import time_to_seconds


# ========================= CONFIG =========================

YOUTUBE_API_KEY = "AIzaSyCDybVOBUFckPYdZpCsyedFRi8LwcvyVak"
SECOND_API_BASE = "https://yt-vid.hazex.workers.dev"

# Browser-like headers so the second API doesn't block the request
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.youtube.com/",
    "Origin": "https://www.youtube.com",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
}


# ========================= COOKIE HELPER =========================

def cookie_txt_file():
    folder_path = f"{os.getcwd()}/cookies"
    filename = f"{os.getcwd()}/cookies/logs.csv"
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not txt_files:
        raise FileNotFoundError("No .txt files found in the cookies folder.")
    chosen = random.choice(txt_files)
    with open(filename, "a") as f:
        f.write(f"Choosen File : {chosen}\n")
    return f"cookies/{str(chosen).split('/')[-1]}"


# ========================= SYNC API HELPERS =========================
# These are plain synchronous functions called via run_in_executor
# so they don't block the async event loop.

def _yt_search_sync(query: str, limit: int = 5) -> list:
    """
    Search YouTube using the Data API v3.
    Returns a list of raw snippet items from the API response.
    Mirrors the /YouTube endpoint logic from the original TS worker.
    """
    if limit < 1:
        limit = 1
    if limit > 20:
        limit = 20

    url = (
        "https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet"
        f"&q={requests.utils.quote(query)}"
        f"&key={YOUTUBE_API_KEY}"
        f"&maxResults={limit}"
        f"&type=video"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def _get_stream_urls_sync(yt_url: str) -> dict:
    """
    Fetch audio & video stream URLs from the second API
    (https://yt-vid.hazex.workers.dev).
    Mirrors the /Url endpoint logic from the original TS worker.

    Returns a dict with keys:
        audioUrl   – nearest ~128kbps audio stream URL
        videoUrl   – 720p (or best available) video+audio stream URL
        title      – video title (may be None)
        duration   – video duration string (may be None)
        thumbnail  – thumbnail URL (may be None)
    """
    api_url = f"{SECOND_API_BASE}/?url={requests.utils.quote(yt_url, safe='')}"
    resp = requests.get(api_url, headers=BROWSER_HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # ---- Audio: pick format closest to 128 kbps ----
    audio_formats = data.get("audio", [])
    audio_url = None
    if audio_formats:
        best_audio = min(
            audio_formats,
            key=lambda f: abs((f.get("bitrate") or 0) - 128000),
        )
        audio_url = best_audio.get("url")

    # ---- Video: 720p preferred, else highest available ----
    video_formats = data.get("video_with_audio", [])
    video_url = None
    video_720 = next(
        (
            f for f in video_formats
            if f.get("height") == 720
            or "720" in str(f.get("label", ""))
        ),
        None,
    )
    if video_720:
        video_url = video_720.get("url")
    elif video_formats:
        video_url = max(
            video_formats,
            key=lambda f: f.get("height") or 0,
        ).get("url")

    return {
        "audioUrl": audio_url,
        "videoUrl": video_url,
        "title": data.get("title"),
        "duration": data.get("duration"),
        "thumbnail": data.get("thumbnail"),
    }


def _yt_video_details_sync(video_id: str) -> dict:
    """
    Fetch snippet details for a single video from the Data API v3.
    Used to resolve channelName when only a URL is available.
    Returns the snippet dict or {} on failure.
    """
    url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part=snippet"
        f"&id={video_id}"
        f"&key={YOUTUBE_API_KEY}"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return items[0].get("snippet", {}) if items else {}


# ========================= MISC ASYNC HELPERS =========================

async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_txt_file(),
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"Error:\n{stderr.decode()}")
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total = 0
        for fmt in formats:
            if "filesize" in fmt:
                total += fmt["filesize"]
        return total

    info = await get_format_info(link)
    if info is None:
        return None
    formats = info.get("formats", [])
    if not formats:
        print("No formats found.")
        return None
    return parse_size(formats)


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in errorz.decode("utf-8").lower():
            return out.decode("utf-8")
        return errorz.decode("utf-8")
    return out.decode("utf-8")


# ========================= MAIN CLASS =========================

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    # ------------------------------------------------------------------
    # exists
    # ------------------------------------------------------------------
    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    # ------------------------------------------------------------------
    # url  (extract URL from a Pyrogram message)
    # ------------------------------------------------------------------
    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset is None:
            return None
        return text[offset: offset + length]

    # ------------------------------------------------------------------
    # details  — uses youtubesearchpython (unchanged)
    # ------------------------------------------------------------------
    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = 0 if str(duration_min) == "None" else int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    # ------------------------------------------------------------------
    # title
    # ------------------------------------------------------------------
    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    # ------------------------------------------------------------------
    # duration
    # ------------------------------------------------------------------
    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    # ------------------------------------------------------------------
    # thumbnail
    # ------------------------------------------------------------------
    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    # ------------------------------------------------------------------
    # video  — NOW uses the second API instead of yt-dlp subprocess
    # ------------------------------------------------------------------
    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(
                None, partial(_get_stream_urls_sync, link)
            )
            video_url = data.get("videoUrl")
            if video_url:
                return 1, video_url
            return 0, "No video URL found from API."
        except Exception as e:
            return 0, str(e)

    # ------------------------------------------------------------------
    # audio_url  — NEW: returns the best ~128kbps audio stream URL
    # ------------------------------------------------------------------
    async def audio_url(self, link: str, videoid: Union[bool, str] = None):
        """
        Returns (status, url_or_error).
        status = 1 on success, 0 on failure.
        Uses the second API to get the nearest ~128kbps audio stream.
        """
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(
                None, partial(_get_stream_urls_sync, link)
            )
            audio_url = data.get("audioUrl")
            if audio_url:
                return 1, audio_url
            return 0, "No audio URL found from API."
        except Exception as e:
            return 0, str(e)

    # ------------------------------------------------------------------
    # stream_info  — NEW: returns full info dict (title, duration,
    #                thumbnail, audioUrl, videoUrl) for a given URL
    # ------------------------------------------------------------------
    async def stream_info(self, link: str, videoid: Union[bool, str] = None) -> dict:
        """
        Fetches title, duration, thumbnail, audioUrl, and videoUrl
        for a given YouTube URL using the second API + YouTube Data API v3.
        Mirrors the /Url endpoint of the TS worker.
        """
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(
                None, partial(_get_stream_urls_sync, link)
            )
        except Exception as e:
            return {
                "thumbnail": None, "title": None, "duration": None,
                "channelName": "Unknown Channel",
                "audioUrl": None, "videoUrl": None,
                "error": str(e),
            }

        # Resolve channelName via YouTube Data API v3
        channel_name = "Unknown Channel"
        video_id_match = re.search(r"(?:youtu\.be/|v=)([^&?]+)", link)
        if video_id_match:
            video_id = video_id_match.group(1)
            try:
                snippet = await loop.run_in_executor(
                    None, partial(_yt_video_details_sync, video_id)
                )
                channel_name = snippet.get("channelTitle", "Unknown Channel")
            except Exception:
                pass

        return {
            "thumbnail": data.get("thumbnail"),
            "title": data.get("title"),
            "duration": data.get("duration"),
            "channelName": channel_name,
            "audioUrl": data.get("audioUrl"),
            "videoUrl": data.get("videoUrl"),
        }

    # ------------------------------------------------------------------
    # search  — NEW: search YouTube and return stream info for results
    #           Mirrors the /YouTube endpoint of the TS worker.
    # ------------------------------------------------------------------
    async def search(self, query: str, limit: int = 3) -> list:
        """
        Search YouTube and return a list of dicts with:
            thumbnail, title, duration, channelName, audioUrl, videoUrl
        Mirrors the /YouTube endpoint of the original TS worker.
        """
        loop = asyncio.get_running_loop()
        items = await loop.run_in_executor(
            None, partial(_yt_search_sync, query, limit)
        )

        async def _enrich(item):
            video_id = item["id"]["videoId"]
            short_url = f"https://youtu.be/{video_id}"
            snippet = item.get("snippet", {})
            thumbnail = (
                snippet.get("thumbnails", {}).get("high", {}).get("url")
                or snippet.get("thumbnails", {}).get("default", {}).get("url")
            )
            try:
                data = await loop.run_in_executor(
                    None, partial(_get_stream_urls_sync, short_url)
                )
                return {
                    "thumbnail": thumbnail,
                    "title": snippet.get("title"),
                    "duration": data.get("duration"),
                    "channelName": snippet.get("channelTitle", "Unknown Channel"),
                    "audioUrl": data.get("audioUrl"),
                    "videoUrl": data.get("videoUrl"),
                }
            except Exception:
                return {
                    "thumbnail": thumbnail,
                    "title": snippet.get("title"),
                    "duration": None,
                    "channelName": snippet.get("channelTitle", "Unknown Channel"),
                    "audioUrl": None,
                    "videoUrl": None,
                }

        results = await asyncio.gather(*[_enrich(item) for item in items])
        return list(results)

    # ------------------------------------------------------------------
    # playlist
    # ------------------------------------------------------------------
    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_txt_file()} "
            f"--playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [x for x in playlist.split("\n") if x]
        except Exception:
            result = []
        return result

    # ------------------------------------------------------------------
    # track
    # ------------------------------------------------------------------
    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    # ------------------------------------------------------------------
    # formats  — kept with yt-dlp (needs full format list)
    # ------------------------------------------------------------------
    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True, "cookiefile": cookie_txt_file()}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for fmt in r["formats"]:
                try:
                    str(fmt["format"])
                except Exception:
                    continue
                if "dash" in str(fmt["format"]).lower():
                    continue
                try:
                    formats_available.append({
                        "format": fmt["format"],
                        "filesize": fmt["filesize"],
                        "format_id": fmt["format_id"],
                        "ext": fmt["ext"],
                        "format_note": fmt["format_note"],
                        "yturl": link,
                    })
                except Exception:
                    continue
        return formats_available, link

    # ------------------------------------------------------------------
    # slider
    # ------------------------------------------------------------------
    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    # ------------------------------------------------------------------
    # download  — uses API for streaming URL fallback, yt-dlp for files
    # ------------------------------------------------------------------
    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile": cookie_txt_file(),
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile": cookie_txt_file(),
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            ydl_optssx = {
                "format": f"{format_id}+140",
                "outtmpl": f"downloads/{title}",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookie_txt_file(),
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            yt_dlp.YoutubeDL(ydl_optssx).download([link])

        def song_audio_dl():
            ydl_optssx = {
                "format": format_id,
                "outtmpl": f"downloads/{title}.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookie_txt_file(),
                "prefer_ffmpeg": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            yt_dlp.YoutubeDL(ydl_optssx).download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            return f"downloads/{title}.mp4"

        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            return f"downloads/{title}.mp3"

        elif video:
            if await is_on_off(1):
                direct = True
                downloaded_file = await loop.run_in_executor(None, video_dl)
            else:
                # Try second API first for a direct streaming URL
                try:
                    data = await loop.run_in_executor(
                        None, partial(_get_stream_urls_sync, link)
                    )
                    video_url = data.get("videoUrl")
                    if video_url:
                        return video_url, False
                except Exception:
                    pass

                # Fallback: check file size then download
                file_size = await check_file_size(link)
                if not file_size:
                    print("None file Size")
                    return
                total_size_mb = file_size / (1024 * 1024)
                if total_size_mb > 250:
                    print(f"File size {total_size_mb:.2f} MB exceeds the 250MB limit.")
                    return None
                direct = True
                downloaded_file = await loop.run_in_executor(None, video_dl)

        else:
            # Audio download: use yt-dlp to save file locally
            direct = True
            downloaded_file = await loop.run_in_executor(None, audio_dl)

        return downloaded_file, direct

