import yt_dlp
import os
# storing url here
import re
from urllib.parse import urlparse, parse_qs, urlunparse


def clean_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query.pop('list', None)  # remove playlist part if present
    new_query = "&".join(f"{k}={v[0]}" for k, v in query.items())
    return urlunparse(parsed._replace(query=new_query))


def is_valid_video_url(url):
    patterns = [
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}',
        r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+',
        r'^(https?://)?(www\.)?facebook\.com/reel/\d+',
        r'^(https?://)?(www\.)?vimeo\.com/\d+',
        r'^(https?://)?(www\.)?twitter\.com/.+/status/\d+',
        r'^(https?://)?(www\.)?pornhub\.com/view_video\.php\?viewkey=\w+',
        r'^(https?://)?(www\.)?xvideos\.com/video\d+/.+',
        r'^(https?://)?(www\.)?xnxx\.com/video-\w+/.+',
    ]
    return any(re.match(p, url) for p in patterns)



video_urls = []

print("🔊 Enter YouTube URLs one by one. Type '!' to start downloading:\n")

while True:
    url = input("🔗 Enter URL: ").strip()    
    if url.lower() == '!':
        break
    if is_valid_video_url(url):        
        clean = clean_url(url)
        video_urls.append(clean)
    else:
        print("❌ Invalid YouTube URL. Please try again.")
        continue


print("Method 1 = download video")
print("Method 2 = download mp3")

x = int(input('enter Method: '))

download_folder = 'downloads'
os.makedirs(download_folder, exist_ok=True)

if x == 1:
    print("Quality Options:")
    print("1 = 360p")
    print("2 = 480p")
    print("3 = 720p")
    print("4 = Best (Default)")
    q = input("Choose video quality: ")
    quality_map = {
        '1': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        '2': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        '3': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        '4': 'bestvideo+bestaudio/best',
    }
    selected_format = quality_map.get(q, 'bestvideo+bestaudio/best')
    ydl_opts = {
        'format': selected_format,
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
    }
    for url in video_urls:
        try:
            print(f"🎥 Downloading: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print(f"✅ Download complete!\n📁 Saved to: {os.path.abspath(download_folder)}\n")
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}\n")


elif x==2:
    ydl_opts = {
        'format': 'bestaudio/best',
        # 'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),  # Use YouTube title
        'outtmpl': os.path.join(download_folder, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    for url in video_urls:
        try:
            print(f"🎵 Downloading: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print(f"✅ Download complete!\n")
            print("📁 Saved to:", os.path.abspath(download_folder))

        except Exception as e:
            print(f"❌ Error downloading {url}: {e}\n")

else:
    print("❌ invalid input")