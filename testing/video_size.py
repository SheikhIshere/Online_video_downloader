import yt_dlp, re
from urllib.parse import urlparse, parse_qs, urlunparse

def is_valid(u): return any(re.match(p, u) for p in [
    r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}',
    r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+',
    r'^(https?://)?(www\.)?facebook\.com/reel/\d+',
    r'^(https?://)?(www\.)?vimeo\.com/\d+',
    r'^(https?://)?(www\.)?twitter\.com/.+/status/\d+',
])

def format_mb(b): return f"{b / 1048576:.2f} MB" if b else "N/A"

def clean(u):
    p = urlparse(u)
    q = parse_qs(p.query); q.pop('list', None)
    return urlunparse(p._replace(query="&".join(f"{k}={v[0]}" for k,v in q.items())))

url = clean(input("🔗 URL: ").strip())
if not is_valid(url): print("❌ Invalid."); exit()

try:
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        f = ydl.extract_info(url, download=False).get('formats', [])
        vids = {480: 0, 720: 0}
        for i in f:
            h = i.get('height'); s = i.get('filesize') or i.get('filesize_approx') or 0
            if h in vids and s > vids[h]: vids[h] = s

        for res in [720, 480]:
            print(f"🎯 {res}p: {format_mb(vids[res])}" if vids[res] else f"⚠️ {res}p not found.")

except Exception as e:
    print(f"❌ {e}")
