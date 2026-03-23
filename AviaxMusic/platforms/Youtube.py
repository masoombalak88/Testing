import asyncio
import os
import re
from typing import Union
from functools import partial

import requests
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from AviaxMusic.utils.formatters import time_to_seconds


# ========================= CONFIG =========================

YOUTUBE_API_KEY = "AIzaSyCDybVOBUFckPYdZpCsyedFRi8LwcvyVak"
SECOND_API_BASE = "https://yt-vid.hazex.workers.dev"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.youtube.com/",
    "Origin": "https://www.youtube.com",
    "Connection": "keep-alive",
}


# ========================= SYNC API HELPERS =========================

def _yt_search_sync(query: str, limit: int = 5) -> list:
    """Search YouTube via Data API v3. Returns list of video items."""
    limit = max(1, min(limit, 20))
    url = (
        "https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&type=video"
        f"&q={requests.utils.quote(query)}"
        f"&maxResults={limit}"
        f"&key={YOUTUBE_API_KEY}"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def _yt_video_details_sync(video_id: str) -> dict:
    """Fetch snippet + contentDetails for a video from Data API v3."""
    url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part=snippet,contentDetails"
        f"&id={video_id}"
        f"&key={YOUTUBE_API_KEY}"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return items[0] if items else {}


def _yt_playlist_sync(playlist_id: str, limit: int = 50) -> list:
    """Fetch video IDs from a playlist via Data API v3."""
    url = (
        "https://www.googleapis.com/youtube/v3/playlistItems"
        f"?part=contentDetails"
        f"&playlistId={playlist_id}"
        f"&maxResults={limit}"
        f"&key={YOUTUBE_API_KEY}"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return [item["contentDetails"]["videoId"] for item in items]


def _get_stream_urls_sync(yt_url: str) -> dict:
    """
    Fetch audio & video stream URLs from yt-vid.hazex.workers.dev.
    Returns: audioUrl, videoUrl, title, duration, thumbnail, allAudio, allVideo
    """
    api_url = f"{SECOND_API_BASE}/?url={requests.utils.quote(yt_url, safe='')}"
    resp = requests.get(api_url, headers=BROWSER_HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Audio: nearest to 128kbps
    audio_formats = data.get("audio", [])
    audio_url = None
    if audio_formats:
        best = min(audio_formats, key=lambda f: abs((f.get("bitrate") or 0) - 128000))
        audio_url = best.get("url")

    # Video: 720p preferred, else highest
    video_formats = data.get("video_with_audio", [])
    video_url = None
    video_720 = next(
        (f for f in video_formats
         if f.get("height") == 720 or "720" in str(f.get("label", ""))),
        None,
    )
    if video_720:
        video_url = video_720.get("url")
    elif video_formats:
        video_url = max(video_formats, key=lambda f: f.get("height") or 0).get("url")

    return {
        "audioUrl":  audio_url,
        "videoUrl":  video_url,
        "title":     data.get("title"),
        "duration":  data.get("duration"),
        "thumbnail": data.get("thumbnail"),
        "allAudio":  audio_formats,
        "allVideo":  video_formats,
    }


def _download_url_to_file(url: str, filepath: str) -> str:
    """Stream-download a direct URL to disk using requests."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with requests.get(url, headers=BROWSER_HEADERS, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
    return filepath


# ========================= MAIN CLASS =========================

class YouTubeAPI:
    def __init__(self):
        self.base     = "https://www.youtube.com/watch?v="
        self.regex    = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    # ------------------------------------------------------------------
    # exists
    # ------------------------------------------------------------------
    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    # ------------------------------------------------------------------
    # url  (extract YouTube URL from a Pyrogram message)
    # ------------------------------------------------------------------
    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text   = ""
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
    # details
    # ------------------------------------------------------------------
    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))

        vid_match    = re.search(r"(?:youtu\.be/|v=)([^&?]+)", link)
        vidid        = vid_match.group(1) if vid_match else ""
        title        = data.get("title") or ""
        duration_str = data.get("duration") or "0:00"
        thumbnail    = data.get("thumbnail") or f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg"

        try:
            duration_sec = int(time_to_seconds(duration_str))
        except Exception:
            duration_sec = 0

        return title, duration_str, duration_sec, thumbnail, vidid

    # ------------------------------------------------------------------
    # title
    # ------------------------------------------------------------------
    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))
        return data.get("title") or ""

    # ------------------------------------------------------------------
    # duration
    # ------------------------------------------------------------------
    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))
        return data.get("duration") or "0:00"

    # ------------------------------------------------------------------
    # thumbnail
    # ------------------------------------------------------------------
    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))
        return data.get("thumbnail") or ""

    # ------------------------------------------------------------------
    # video  — returns direct 720p stream URL
    # ------------------------------------------------------------------
    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))
            video_url = data.get("videoUrl")
            if video_url:
                return 1, video_url
            return 0, "No video URL found."
        except Exception as e:
            return 0, str(e)

    # ------------------------------------------------------------------
    # audio_url  — returns direct ~128kbps audio stream URL
    # ------------------------------------------------------------------
    async def audio_url(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))
            url = data.get("audioUrl")
            if url:
                return 1, url
            return 0, "No audio URL found."
        except Exception as e:
            return 0, str(e)

    # ------------------------------------------------------------------
    # stream_info  — full info dict for a URL
    # ------------------------------------------------------------------
    async def stream_info(self, link: str, videoid: Union[bool, str] = None) -> dict:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))
        except Exception as e:
            return {
                "thumbnail": None, "title": None, "duration": None,
                "channelName": "Unknown Channel",
                "audioUrl": None, "videoUrl": None, "error": str(e),
            }

        channel_name = "Unknown Channel"
        vid_match = re.search(r"(?:youtu\.be/|v=)([^&?]+)", link)
        if vid_match:
            try:
                item = await loop.run_in_executor(
                    None, partial(_yt_video_details_sync, vid_match.group(1))
                )
                channel_name = item.get("snippet", {}).get("channelTitle", "Unknown Channel")
            except Exception:
                pass

        return {
            "thumbnail":   data.get("thumbnail"),
            "title":       data.get("title"),
            "duration":    data.get("duration"),
            "channelName": channel_name,
            "audioUrl":    data.get("audioUrl"),
            "videoUrl":    data.get("videoUrl"),
        }

    # ------------------------------------------------------------------
    # search  — search + stream info for each result
    # ------------------------------------------------------------------
    async def search(self, query: str, limit: int = 3) -> list:
        loop  = asyncio.get_running_loop()
        items = await loop.run_in_executor(None, partial(_yt_search_sync, query, limit))

        async def _enrich(item):
            video_id  = item["id"]["videoId"]
            short_url = f"https://youtu.be/{video_id}"
            snippet   = item.get("snippet", {})
            thumbnail = (
                snippet.get("thumbnails", {}).get("high", {}).get("url")
                or snippet.get("thumbnails", {}).get("default", {}).get("url")
            )
            try:
                data = await loop.run_in_executor(
                    None, partial(_get_stream_urls_sync, short_url)
                )
                return {
                    "thumbnail":   thumbnail,
                    "title":       snippet.get("title"),
                    "duration":    data.get("duration"),
                    "channelName": snippet.get("channelTitle", "Unknown Channel"),
                    "audioUrl":    data.get("audioUrl"),
                    "videoUrl":    data.get("videoUrl"),
                    "vidid":       video_id,
                    "link":        f"https://www.youtube.com/watch?v={video_id}",
                }
            except Exception:
                return {
                    "thumbnail":   thumbnail,
                    "title":       snippet.get("title"),
                    "duration":    None,
                    "channelName": snippet.get("channelTitle", "Unknown Channel"),
                    "audioUrl":    None,
                    "videoUrl":    None,
                    "vidid":       video_id,
                    "link":        f"https://www.youtube.com/watch?v={video_id}",
                }

        return list(await asyncio.gather(*[_enrich(i) for i in items]))

    # ------------------------------------------------------------------
    # track
    # ------------------------------------------------------------------
    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))

        vid_match = re.search(r"(?:youtu\.be/|v=)([^&?]+)", link)
        vidid     = vid_match.group(1) if vid_match else ""

        track_details = {
            "title":        data.get("title") or "",
            "link":         link,
            "vidid":        vidid,
            "duration_min": data.get("duration") or "0:00",
            "thumb":        data.get("thumbnail") or "",
            "audioUrl":     data.get("audioUrl"),
            "videoUrl":     data.get("videoUrl"),
        }
        return track_details, vidid

    # ------------------------------------------------------------------
    # formats  — built from API response
    # ------------------------------------------------------------------
    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))

        formats_available = []

        for fmt in data.get("allAudio", []):
            formats_available.append({
                "format":      f"audio - {(fmt.get('bitrate') or 0) // 1000}kbps",
                "filesize":    fmt.get("filesize") or 0,
                "format_id":   str(fmt.get("itag") or fmt.get("format_id") or ""),
                "ext":         fmt.get("ext") or "webm",
                "format_note": f"{(fmt.get('bitrate') or 0) // 1000}kbps audio",
                "url":         fmt.get("url"),
                "yturl":       link,
            })

        for fmt in data.get("allVideo", []):
            formats_available.append({
                "format":      f"video - {fmt.get('height', '?')}p",
                "filesize":    fmt.get("filesize") or 0,
                "format_id":   str(fmt.get("itag") or fmt.get("format_id") or ""),
                "ext":         fmt.get("ext") or "mp4",
                "format_note": f"{fmt.get('height', '?')}p",
                "url":         fmt.get("url"),
                "yturl":       link,
            })

        return formats_available, link

    # ------------------------------------------------------------------
    # slider
    # ------------------------------------------------------------------
    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        loop  = asyncio.get_running_loop()
        items = await loop.run_in_executor(None, partial(_yt_search_sync, link, 10))

        if query_type >= len(items):
            query_type = 0

        item    = items[query_type]
        snippet = item.get("snippet", {})
        vidid   = item["id"]["videoId"]
        title   = snippet.get("title", "")
        thumb   = (
            snippet.get("thumbnails", {}).get("high", {}).get("url")
            or snippet.get("thumbnails", {}).get("default", {}).get("url")
            or ""
        )

        try:
            data = await loop.run_in_executor(
                None, partial(_get_stream_urls_sync, f"https://youtu.be/{vidid}")
            )
            duration_min = data.get("duration") or "0:00"
        except Exception:
            duration_min = "0:00"

        return title, duration_min, thumb, vidid

    # ------------------------------------------------------------------
    # playlist  — uses YouTube Data API v3
    # ------------------------------------------------------------------
    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]

        pl_match = re.search(r"list=([^&]+)", link)
        if not pl_match:
            return []

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                None, partial(_yt_playlist_sync, pl_match.group(1), limit)
            )
        except Exception:
            return []

    # ------------------------------------------------------------------
    # download  — API for URL, requests for file save
    # ------------------------------------------------------------------
    async def download(
        self,
        link: str,
        mystic,
        video:     Union[bool, str] = None,
        videoid:   Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title:     Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        loop = asyncio.get_running_loop()
        os.makedirs("downloads", exist_ok=True)

        data = await loop.run_in_executor(None, partial(_get_stream_urls_sync, link))

        if songvideo:
            video_url = data.get("videoUrl")
            if not video_url:
                return None
            fpath = f"downloads/{title}.mp4"
            await loop.run_in_executor(None, partial(_download_url_to_file, video_url, fpath))
            return fpath

        elif songaudio:
            audio_url = data.get("audioUrl")
            if not audio_url:
                return None
            # If a specific format was requested, find its URL
            if format_id:
                match = next(
                    (f for f in data.get("allAudio", [])
                     if str(f.get("itag") or f.get("format_id") or "") == str(format_id)),
                    None,
                )
                if match:
                    audio_url = match.get("url", audio_url)
            fpath = f"downloads/{title}.mp3"
            await loop.run_in_executor(None, partial(_download_url_to_file, audio_url, fpath))
            return fpath

        elif video:
            # Return direct stream URL (no file saved) for fast playback
            video_url = data.get("videoUrl")
            if video_url:
                return video_url, False
            return None

        else:
            # Plain audio — return direct stream URL for playback
            audio_url = data.get("audioUrl")
            if audio_url:
                return audio_url, False
            return None

