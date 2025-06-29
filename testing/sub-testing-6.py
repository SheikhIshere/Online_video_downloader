import yt_dlp
import os
import re
from urllib.parse import urlparse, parse_qs, urlunparse
from typing import List, Dict

DOWNLOAD_FOLDER = 'downloads'
STANDARD_RESOLUTIONS = {
    144: "144p",
    240: "240p",
    360: "360p",
    480: "480p (SD)",
    576: "576p",
    720: "720p (HD)",
    1080: "1080p (Full HD)",
    1440: "1440p (2K)",
    2160: "2160p (4K)",
    4320: "4320p (8K)"
}
URL_PATTERNS = tuple(re.compile(p) for p in [
    r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}',
    r'^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]{11}',
    r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+',
    r'^(https?://)?(www\.)?facebook\.com/watch\?v=\d+',
    r'^(https?://)?(www\.)?facebook\.com/reel/\d+',
    r'^(https?://)?(www\.)?facebook\.com/share/v/[\w-]+',
    r'^(https?://)?(www\.)?vimeo\.com/\d+',
    r'^(https?://)?(www\.)?twitter\.com/.+/status/\d+',
])

def clean_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query.pop('list', None)
    return parsed._replace(query="&".join(f"{k}={v[0]}" for k, v in query.items())).geturl()

def is_valid_url(url: str) -> bool:
    return any(pattern.match(url) for pattern in URL_PATTERNS)

def is_youtube(url: str) -> bool:
    return 'youtube.com' in url or 'youtu.be' in url

def collect_resolutions(urls: List[str]) -> Dict[int, int]:
    res_count = {}
    for url in urls:
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                for f in formats:
                    height = f.get('height')
                    if height:
                        closest = min(STANDARD_RESOLUTIONS.keys(), key=lambda x: abs(x - height))
                        res_count[closest] = res_count.get(closest, 0) + 1
        except Exception as e:
            print(f"❌ Error checking resolution for {url}: {e}")
    return res_count

def pick_resolution(res_count: Dict[int, int], total: int) -> int:
    sorted_res = sorted(res_count.keys())
    print("\n🎞️ Available resolutions:")
    for i, res in enumerate(sorted_res, 1):
        name = STANDARD_RESOLUTIONS[res]
        note = "(✅ Common)" if res_count[res] == total else "(⚠️ Partial)"
        print(f"{i}. {name} {note}")

    while True:
        try:
            sel = int(input("Pick resolution: ").strip())
            if 1 <= sel <= len(sorted_res):
                return sorted_res[sel - 1]
        except: pass
        print("❌ Invalid input. Try again.")

def get_format_string(res: int, partial_allowed: bool) -> str:
    if partial_allowed:
        # For partial availability, allow fallback to highest per video
        return f'bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else:
        # For full availability, restrict to selected resolution
        return f'bestvideo[height={res}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

def get_video_urls(is_playlist: bool) -> List[str]:
    urls = []
    if is_playlist:
        print("\n🔗 Paste playlist video URLs one by one (type '!' to stop):")
        while True:
            url = input("URL: ").strip()
            if url == '!':
                break
            if is_valid_url(url):
                urls.append(clean_url(url))
            else:
                print("❌ Invalid URL, try again.")
    else:
        print("\n🔗 Paste single video URLs one by one (type '!' to stop):")
        while True:
            url = input("URL: ").strip()
            if url == '!':
                break
            if is_valid_url(url):
                urls.append(clean_url(url) if is_youtube(url) else url)
            else:
                print("❌ Invalid URL, try again.")
    return urls

def main():
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    print("🎬 Download type:")
    print("1 = Single video(s)")
    print("2 = Playlist")
    while True:
        choice = input("Pick type (1 or 2): ").strip()
        if choice in ('1', '2'):
            is_playlist = choice == '2'
            break
        print("❌ Invalid input. Enter 1 or 2.")

    urls = get_video_urls(is_playlist)
    if not urls:
        print("❌ No URLs provided. Exiting.")
        return

    if is_playlist or len(urls) > 1:
        # For playlist or multiple videos, check resolutions collectively
        res_count = collect_resolutions(urls)
        chosen_res = pick_resolution(res_count, len(urls))
        partial_allowed = res_count[chosen_res] != len(urls)
        fmt = get_format_string(chosen_res, partial_allowed)
    else:
        # For single video, get resolutions just for that video
        res_count = collect_resolutions(urls)
        if not res_count:
            print("❌ Could not fetch resolutions, using best quality.")
            fmt = 'bestvideo+bestaudio/best'
        else:
            chosen_res = pick_resolution(res_count, 1)
            fmt = get_format_string(chosen_res, False)

    ydl_opts = {
        'format': fmt,
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': False,
        'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            try:
                print(f"\n⬇️ Downloading: {url}")
                ydl.download([url])
                print("✅ Done!")
            except Exception as e:
                print(f"❌ Error downloading {url}: {e}")

if __name__ == '__main__':
    main()
