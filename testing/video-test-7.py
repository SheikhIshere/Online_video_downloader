import yt_dlp
import os

def get_unique_filename(folder, base_filename):
    """
    Generates a unique filename by adding incremental suffixes if the file exists.
    Returns the full path to the unique filename.
    
    Args:
        folder: Target directory for the download
        base_filename: The original filename (without path)
    
    Returns:
        str: Full path to a unique filename
    """
    # Split filename and extension
    base, ext = os.path.splitext(base_filename)
    counter = 1
    new_filename = base_filename
    full_path = os.path.join(folder, new_filename)
    
    # Keep incrementing counter until we find a non-existent filename
    while os.path.exists(full_path):
        new_filename = f"{base} ({counter}){ext}"
        full_path = os.path.join(folder, new_filename)
        counter += 1
    
    return full_path

def download_youtube_video(url, download_folder='downloads'):
    """
    Downloads a YouTube video with automatic renaming if the file already exists.
    
    Args:
        url: YouTube video URL to download
        download_folder: Directory to save the download (default: 'downloads')
    
    Returns:
        str: Path to the downloaded file, or None if download failed
    """
    # Create download folder if it doesn't exist
    os.makedirs(download_folder, exist_ok=True)
    
    # Configure yt-dlp options for metadata extraction only
    info_opts = {
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
    }
    
    try:
        # First extract video info to determine filename
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'video')
            
            # Determine the best extension (default to mp4)
            ext = '.mp4'
            if 'requested_formats' in info:
                ext = f".{info['requested_formats'][0]['ext']}"
            elif 'ext' in info:
                ext = f".{info['ext']}"
            
            # Generate the base filename
            base_filename = f"{video_title}{ext}"
            output_path = get_unique_filename(download_folder, base_filename)
            
            # Configure download options
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_path.replace(ext, '.%(ext)s'),  # Maintain dynamic extension
                'merge_output_format': 'mp4',
                'quiet': False,
                'nooverwrites': True,  # Safety measure
                'progress_hooks': [lambda d: print_progress(d)],  # Add progress display
            }
            
            print(f"Downloading: {video_title}")
            print(f"Saving to: {os.path.basename(output_path)}")
            
            # Perform the download
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            ydl.download([url])
            
            print("✅ Download completed successfully!")
            return output_path
            
    except yt_dlp.utils.DownloadError as e:
        print(f"❌ Download failed: {str(e)}")
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
    
    return None

def print_progress(d):
    """Callback function to print download progress"""
    if d['status'] == 'downloading':
        print(f"\rDownloading... {d['_percent_str']} of {d['_total_bytes_str']} at {d['_speed_str']}", end='')
    elif d['status'] == 'finished':
        print("\rDownload complete! Finalizing file...")

def main():
    print("YouTube Video Downloader with Auto-Renaming")
    print("-----------------------------------------")
    print("This script downloads a single YouTube video and automatically renames")
    print("the file if a duplicate exists in the 'downloads' folder.\n")
    
    while True:
        url = input("Enter YouTube video URL (or 'q' to quit): ").strip()
        
        if url.lower() == 'q':
            print("Exiting...")
            break
        
        if not url.startswith(('http://', 'https://')):
            print("❌ Please enter a valid URL starting with http:// or https://")
            continue
        
        if 'youtube.com' not in url and 'youtu.be' not in url:
            print("❌ Please enter a valid YouTube URL")
            continue
        
        download_youtube_video(url)

if __name__ == "__main__":
    main()