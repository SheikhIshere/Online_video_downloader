import yt_dlp, os, re
from urllib.parse import urlparse, parse_qs, urlunparse

def clean_url(url):
    p = urlparse(url)
    q = parse_qs(p.query); q.pop('list', None)
    return urlunparse(p._replace(query="&".join(f"{k}={v[0]}" for k, v in q.items())))

def is_valid_url(u): return any(re.match(p, u) for p in [
    r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}',
    r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+',
    r'^(https?://)?(www\.)?facebook\.com/reel/\d+',
    r'^(https?://)?(www\.)?vimeo\.com/\d+',
    r'^(https?://)?(www\.)?twitter\.com/.+/status/\d+',
    r'^(https?://)?(www\.)?pornhub\.com/view_video\.php\?viewkey=\w+',
    r'^(https?://)?(www\.)?xvideos\.com/video\d+/.+',
    r'^(https?://)?(www\.)?xnxx\.com/video-\w+/.+',
])

def format_mb(b): return f"{b / 1048576:.2f} MB" if b else "N/A"

video_urls = []

print("🔊 Paste video URLs one by one. Type '!' to continue:\n")
while True:
    url = input("🔗 URL: ").strip()
    if url == '!': break
    if is_valid_url(url):
        video_urls.append(clean_url(url))
    else:
        print("❌ Invalid URL.")

print("\n💾 1 = Video")
print("🎵 2 = MP3")
x = input("Pick type: ").strip()

folder = 'downloads'
os.makedirs(folder, exist_ok=True)

if x == '1':
    for url in video_urls:
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                f = ydl.extract_info(url, download=False).get('formats', [])
                vids = {360: 0, 480: 0, 720: 0}; best = 0

                for i in f:
                    h = i.get('height'); s = i.get('filesize') or i.get('filesize_approx') or 0
                    if h in vids and s > vids[h]: vids[h] = s
                    if s > best: best = s

                print(f"\n📹 {url}")
                for res in [360, 480, 720]:
                    print(f"  {res}p: {format_mb(vids[res])}" if vids[res] else f"  ⚠️ {res}p not found")
                print(f"  ⭐ Best/raw: {format_mb(best)}")

        except Exception as e:
            print(f"❌ Error checking: {e}")

    print("\n🎞️ Choose quality:")
    print("1 = 360p | 2 = 480p | 3 = 720p | 4 = Best")
    q = input("Pick: ").strip()
    quality_map = {
        '1': 'best[height<=360]',
        '2': 'best[height<=480]',
        '3': 'best[height<=720]',
        '4': 'bestvideo+bestaudio/best',
    }
    fmt = quality_map.get(q, 'bestvideo+bestaudio/best')

    ydl_opts = {
        'format': fmt,
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
    }

    for url in video_urls:
        try:
            print(f"\n⬇️ Downloading: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("✅ Done!\n")
        except Exception as e:
            print(f"❌ Download error: {e}")

elif x == '2':
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(folder, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    for url in video_urls:
        try:
            print(f"\n🎵 MP3: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("✅ Saved!\n")
        except Exception as e:
            print(f"❌ Audio error: {e}")
else:
    print("❌ Invalid option.")
