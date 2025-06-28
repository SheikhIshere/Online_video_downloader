import yt_dlp
import os
import re
from urllib.parse import urlparse, parse_qs, urlunparse

def clean_url(url):
    p = urlparse(url)
    q = parse_qs(p.query)
    q.pop('list', None)
    return urlunparse(p._replace(query="&".join(f"{k}={v[0]}" for k, v in q.items())))

def is_valid_url(u):
    patterns = [
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}',
        r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+',
        r'^(https?://)?(www\.)?facebook\.com/reel/\d+',
        r'^(https?://)?(www\.)?vimeo\.com/\d+',
        r'^(https?://)?(www\.)?twitter\.com/.+/status/\d+',
        r'^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]{11}',
    ]
    return any(re.match(p, u) for p in patterns)

def format_mb(b):
    return f"{b / 1048576:.2f} MB" if b else "N/A"

# Get URLs from user
video_urls = []
print("🔊 Paste video URLs one by one. Type '!' to continue:\n")
while True:
    url = input("🔗 URL: ").strip()
    if url == '!':
        break
    if is_valid_url(url):
        video_urls.append(clean_url(url))
    else:
        print("❌ Invalid URL.")

print("\n💾 1 = Video")
print("🎵 2 = MP3")
choice = input("Pick type: ").strip()

folder = 'downloads'
os.makedirs(folder, exist_ok=True)

if choice == '1':
    # Video download logic
    available_res = set()

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
        # Key fix: Use this format selector
        'format': f'bv*[height<={chosen_res}]+ba/b[height<={chosen_res}]',
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        # Important post-processors for merging
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }, {
            'key': 'FFmpegMetadata'
        }],
        # Ensure merging happens
        'merge_output_format': 'mp4',
        # FFmpeg location (auto-detected if None)
        'ffmpeg_location': None,
    }

    for url in video_urls:
        try:
            print(f"\n⬇️ Downloading {chosen_res}p: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("✅ Done!")
        except Exception as e:
            print(f"❌ Download error: {e}")

elif choice == '2':
    # Audio download logic (unchanged as it works fine)
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
            print(f"\n🎵 Converting to MP3: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("✅ Saved!")
        except Exception as e:
            print(f"❌ Audio error: {e}")

else:
    print("❌ Invalid option.")