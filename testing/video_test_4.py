import yt_dlp
import os
import re
from urllib.parse import urlparse, parse_qs, urlunparse

# Function to clean a URL by removing the 'list' query parameter (often YouTube playlist IDs)
def clean_url(url):
    p = urlparse(url)  # Parse the URL into components
    q = parse_qs(p.query)  # Parse query parameters into a dict
    q.pop('list', None)  # Remove 'list' parameter if present (to avoid playlist downloads)
    # Rebuild URL with cleaned query parameters
    return urlunparse(p._replace(query="&".join(f"{k}={v[0]}" for k, v in q.items())))

# Function to check if a URL is a valid video URL from supported platforms using regex patterns
def is_valid_url(u):
    patterns = [
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}',   # YouTube video URLs
        r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+',                   # Facebook videos
        r'^(https?://)?(www\.)?facebook\.com/reel/\d+',                        # Facebook reels
        r'^(https?://)?(www\.)?vimeo\.com/\d+',                               # Vimeo videos
        r'^(https?://)?(www\.)?twitter\.com/.+/status/\d+',                   # Twitter videos
        r'^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]{11}',  # YouTube shorts
    ]
    # Return True if URL matches any of the patterns
    return any(re.match(p, u) for p in patterns)

# Helper function to format bytes into megabytes string (for display)
def format_mb(b):
    return f"{b / 1048576:.2f} MB" if b else "N/A"

# ----------- Main Program Starts Here -----------

# Collect multiple video URLs from user until they input '!'
video_urls = []
print("🔊 Paste video URLs one by one. Type '!' to continue:\n")
while True:
    url = input("🔗 URL: ").strip()
    if url == '!':
        break
    if is_valid_url(url):
        video_urls.append(clean_url(url))  # Clean and store valid URLs
    else:
        print("❌ Invalid URL.")

# Ask user what to download: video or audio
print("\n💾 1 = Video")
print("🎵 2 = MP3")
choice = input("Pick type: ").strip()

folder = 'downloads'
os.makedirs(folder, exist_ok=True)  # Create downloads folder if it doesn't exist

if choice == '1':
    # ----- Video download flow -----
    available_res = set()  # To store available video resolutions

    # For each URL, fetch video info without downloading to find available resolutions
    for url in video_urls:
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)  # Get metadata only
                formats = info.get('formats', [])
                
                print(f"\n📹 {url}")
                # Iterate over formats to find resolutions and file sizes
                for f in formats:
                    height = f.get('height')  # Video height (resolution)
                    size = f.get('filesize') or f.get('filesize_approx')  # Size in bytes
                    if height and size:
                        print(f"  🎯 {height}p: {format_mb(size)}")
                        available_res.add(height)  # Add resolution to set
        except Exception as e:
            print(f"❌ Error checking: {e}")

    if not available_res:
        print("❌ No available resolutions found.")
        exit()

    # Show sorted list of available resolutions for user to choose from
    print("\n🎞️ Available resolutions:")
    sorted_res = sorted(available_res)
    for i, res in enumerate(sorted_res, 1):
        print(f"{i} = {res}p")

    try:
        sel = int(input("Pick: ").strip())  # User selects desired resolution index
        chosen_res = sorted_res[sel-1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        exit()

    # yt-dlp options configured to:
    # - Download best video at or below chosen resolution with mp4 video format
    # - Download best audio with m4a format
    # - Merge them into an mp4 file
    # - Use FFmpeg for conversion if needed
    ydl_opts = {
        'format': f'bestvideo[height<={chosen_res}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),  # Output filename template
        'merge_output_format': 'mp4',  # Merge video and audio into mp4 container
        'quiet': False,  # Show output logs
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',  # Postprocessor to ensure mp4 conversion if needed
            'preferedformat': 'mp4',        # Preferred output format
        }],
    }

    # Download each video URL with chosen options
    for url in video_urls:
        try:
            print(f"\n⬇️ Downloading {chosen_res}p: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("✅ Done!")
        except Exception as e:
            print(f"❌ Download error: {e}")

elif choice == '2':
    # ----- Audio only download flow -----
    ydl_opts = {
        'format': 'bestaudio/best',  # Best available audio-only format
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Convert audio to mp3
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
