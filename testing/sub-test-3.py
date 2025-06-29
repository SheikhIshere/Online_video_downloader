import yt_dlp
import os

# Configuration
url = "https://youtu.be/yIIGQB6EMAM"  # Replace with your URL
output_dir = "downloads"
os.makedirs(output_dir, exist_ok=True)

# Single download with merged audio/video
ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
    'merge_output_format': 'mp4',
    'quiet': False,
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
    }],
}

print("⬇️ Downloading video with audio...")
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=True)
    filename = ydl.prepare_filename(info)
    print(f"✅ Downloaded: {filename}")