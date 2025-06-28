import yt_dlp
import os
import re
from urllib.parse import urlparse, parse_qs, urlunparse

def clean_url(url):
    p = urlparse(url)
    q = parse_qs(p.query)
    q.pop('list', None)  # Remove playlist param for single video mode
    return urlunparse(p._replace(query="&".join(f"{k}={v[0]}" for k, v in q.items())))

def is_valid_url(u):
    patterns = [
        # youtube
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}',
        r'^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]{11}',
        
        # facebook
        r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+',
        r'^(https?://)?(www\.)?facebook\.com/watch\?v=\d+'
        r'^(https?://)?(www\.)?facebook\.com/reel/\d+',
        r'^(https?://)?(www\.)?facebook\.com/share/v/[\w-]+',

        r'^(https?://)?(www\.)?vimeo\.com/\d+',
        r'^(https?://)?(www\.)?twitter\.com/.+/status/\d+',
    ]
    return any(re.match(p, u) for p in patterns)

def format_mb(b):
    return f"{b / 1048576:.2f} MB" if b else "N/A"

# Ask if the user wants to download a playlist or single video(s)
print("🗂️ Download type:")
print("1 = Single video(s)")
print("2 = Playlist")
download_type = ''
while True:    
    download_type = input("Select type: ").strip()
    if download_type == '1' or download_type == '2':
        break
    else:
        download_type = input("Select type: ").strip()
        continue

video_urls = []

if download_type == '2':
    # Playlist mode: ask for one playlist URL (or multiple if you want)
    print('\n')
    print("🔊 Paste playlist URL(s) one by one. Type '!' to continue:\n")
    while True:
        url = input("🔗 Playlist URL: ").strip()
        if url == '!':
            break
        if is_valid_url(url):
            # Don't clean URL here, keep the playlist 'list' param to download whole playlist
            video_urls.append(url)
        else:
            print("❌ Invalid URL.")
else:
    # Single video mode
    print("🔊 Paste video URLs one by one. Type '!' to continue:\n")
    while True:
        url = input("🔗 Video URL: ").strip()
        if url == '!':
            break
        if is_valid_url(url):
            video_urls.append(clean_url(url))  # Clean URL to remove playlist param
        else:
            print("❌ Invalid URL.")

print("\n💾 1 = Video")
print("🎵 2 = MP3")
choice = input("Pick type: ").strip()

folder = 'downloads'
os.makedirs(folder, exist_ok=True)

if choice == '1':
    # Video download logic
    # If playlist mode, just download with yt-dlp default (no resolution selection)
    if download_type == '2':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(folder, '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': False,
        }
        for url in video_urls:
            try:
                print(f"\n⬇️ Downloading playlist/video: {url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                print("✅ Done!")
            except Exception as e:
                print(f"❌ Download error: {e}")

    else:
        # Single video(s) mode: prompt for resolution
        available_res = set()
        # this is checking is the formates and their extimating size
        for url in video_urls:
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats = info.get('formats', [])
                    print(f"\n📹 {url}")
                    for f in formats:
                        height = f.get('height')
                        size = f.get('filesize') or f.get('filesize_approx')
                        if height and size:
                            print(f"  🎯 {height}p: {format_mb(size)}")
                            available_res.add(height)
            except Exception as e:
                print(f"❌ Error checking: {e}")

        if not available_res:
            print("❌ No available resolutions found.")
            exit()

        print("\n🎞️ Available resolutions:")
        sorted_res = sorted(available_res)
        for i, res in enumerate(sorted_res, 1):
            print(f"{i} = {res}p")

        try:
            sel = int(input("Pick: ").strip())
            chosen_res = sorted_res[sel-1]
        except (ValueError, IndexError):
            print("❌ Invalid choice.")
            exit()

        ydl_opts = {
            'format': f'bestvideo[height<={chosen_res}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': False,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        
        # Showing the downloading format and name of the content
        for url in video_urls:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)  # extract metadata only
                    print(f"\n⬇️ Downloading {chosen_res}p: {info.get('title', 'Unknown Title')}")
                    ydl.download([url])  # Only one download
                print("✅ Done!")
            except Exception as e:
                print(f"❌ Download error: {e}")


elif choice == '2':
    # Audio download logic (same for both playlist and single)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    for url in video_urls:
        try:
            info = yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False)
            print(f"\n🎵 Converting to MP3: {info.get('title', 'Unknown Title')}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("✅ Saved!")
        except Exception as e:
            print(f"❌ Audio error: {e}")

else:
    print("❌ Invalid option.")
