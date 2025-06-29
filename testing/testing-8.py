import yt_dlp
import os
import re
from urllib.parse import urlparse, parse_qs, urlunparse

def sanitize(text):
    # Remove chars invalid in Windows paths like: \ / : * ? " < > | and some unicode pipes
    return re.sub(r'[\\/:*?"<>|｜]+', '', text)


def clean_url(url):
    p = urlparse(url)
    q = parse_qs(p.query)
    q.pop('list', None)
    return urlunparse(p._replace(query="&".join(f"{k}={v[0]}" for k, v in q.items())))

def is_valid_url(u):
    patterns = [
        # YouTube
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}', # normal youtube video
        r'^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]{11}', # youtube shorts
        r'^(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+', # youtube play list
        # Facebook
        r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+', # for feed video
        r'^(https?://)?(www\.)?facebook\.com/share/v/[\w-]+/?$', # for video share
        r'^(https?://)?(www\.)?facebook\.com/watch\?v=\d+', # for video
        r'^(https?://)?(www\.)?facebook\.com/reel/\d+', # for reels
        r'^(https?://)?(www\.)?facebook\.com/share/v/[\w-]+', # for reels share 
        
        # Inatagram
        r'^(https?://)?(www\.)?instagram\.com/reel/[\w-]+/?(\?.*)?$', # for feed share
        r'^(https?://)?(www\.)?instagram\.com/reels?/[\w-]+/?(\?.*)?$', # for reel section

        # Twitter
        r'^(https?://)?(www\.)?(x\.com|twitter\.com)/[\w-]+/status/\d+/?$'

    ]
    return any(re.match(p, u) for p in patterns)

def is_youtube(url):
    return 'youtube.com' in url or 'youtu.be' in url

def format_mb(b):
    return f"{b / 1048576:.2f} MB" if b else "N/A"

# Ask download type
print("🗂️ Download type:")
print("1 = Single video(s)")
print("2 = Playlist")
download_type = input("Select type: ").strip()

video_urls = []


if download_type == '2':
    # downloading playlist from youtube
    print("\n🔊 Paste playlist URL(s) one by one. Type '!' to continue:\n")    
    while True:        
        url = input("🔗 Playlist URL: ").strip()
        if is_valid_url(url):
            video_urls.append(url)        
            break
        else:
            print("❌ Invalid URL.")
            print("🔁 Try again.")
            continue

else: # this for single video url
    print("\n🔊 Paste video URLs one by one. Type '!' to continue:\n")
    while True:
        url = input("🔗 Video URL: ").strip()
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
    if download_type == '2':
        if all(is_youtube(url) for url in video_urls):
            # Ask for resolution only once for the whole playlist
            available_res = set()
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(video_urls[0], download=False)
                    entries = info.get('entries', [])
                    for entry in entries:
                        for f in entry.get('formats', []):
                            height = f.get('height')
                            size = f.get('filesize') or f.get('filesize_approx')
                            if height and size:
                                available_res.add(height)
            except Exception as e:
                print(f"❌ Error getting playlist info: {e}")

            if not available_res:
                print("❌ No resolutions found.")
                exit()

            print("\n🎞️ Available resolutions:")
            sorted_res = sorted(available_res)
            for i, res in enumerate(sorted_res, 1):
                print(f"{i} = {res}p")
            try:
                sel = int(input("Pick: ").strip())
                chosen_res = sorted_res[sel-1]
            except:
                print("❌ Invalid choice.")
                exit()

            # --- Sanitize playlist name and create folder ---
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl_temp:
                playlist_info = ydl_temp.extract_info(video_urls[0], download=False)
                raw_playlist_name = playlist_info.get('title', 'playlist')
                safe_playlist_name = sanitize(raw_playlist_name)

            os.makedirs(os.path.join(folder, safe_playlist_name), exist_ok=True)

            ydl_opts = {
                'format': f'bestvideo[height<={chosen_res}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(folder, safe_playlist_name, '%(playlist_index)s - %(title).50s.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': False,
                'restrictfilenames': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }

    
        else:
            # Other platforms - use best
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(folder, '%(playlist)s/%(playlist_index)s - %(title).50s.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': False,
                'restrictfilenames': True,
                'noplaylist':True,

            }
    

    elif all(is_youtube(url) for url in video_urls):
        # YouTube: allow resolution selection
        available_res = set()
        for url in video_urls:
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    for f in info.get('formats', []):
                        height = f.get('height')
                        size = f.get('filesize') or f.get('filesize_approx')
                        if height and size:
                            print(f"🎯 {height}p: {format_mb(size)}")
                            available_res.add(height)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        if not available_res:
            print("❌ No resolutions found.")
            exit()

        print("\n🎞️ Available resolutions:")
        sorted_res = sorted(available_res)
        for i, res in enumerate(sorted_res, 1):
            print(f"{i} = {res}p")
        try:
            sel = int(input("Pick: ").strip())
            chosen_res = sorted_res[sel-1]
        except:
            print("❌ Invalid choice.")
            exit()

        ydl_opts = {
            'format': f'bestvideo[height<={chosen_res}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': False,
            'restrictfilenames': True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
    else:
        # Other platforms (no resolution choice)
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'quiet': False,
            'restrictfilenames': True,
            'merge_output_format': 'mp4',

        }

    # Final download
    for url in video_urls:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"\n⬇️ Downloading: {info.get('title', 'Unknown Title')}")
                ydl.download([url])
            print("✅ Done!")
        except Exception as e:
            print(f"❌ Download error: {e}")



# downloading mp3
elif choice == '2':
    # Audio (MP3)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    for url in video_urls:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"\n🎵 Converting to MP3: {info.get('title', 'Unknown Title')}")
                ydl.download([url])
            print("✅ Saved!")
        except Exception as e:
            print(f"❌ Audio error: {e}")
else:
    print("❌ Invalid option.")
