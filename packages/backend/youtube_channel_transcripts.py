import os
import re
import time
import logging
import json
import subprocess
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import importlib.metadata

logging.basicConfig(
    filename='transcript_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def parse_channel_url(url):
    """Parse YouTube channel URL to extract handle or ID."""
    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/')
    
    if path.startswith('@'):
        return {'forHandle': path}
    elif path.startswith('channel/'):
        return {'id': path.split('/')[-1]}
    elif 'channel_id' in parsed_url.query:
        return {'id': parse_qs(parsed_url.query)['channel_id'][0]}
    else:
        raise ValueError("Invalid channel URL. Use @handle or /channel/ID format.")

def get_channel_details(api_key, filter_params):
    """Get channel ID, title, and uploads playlist ID."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.channels().list(
        part='id,snippet,contentDetails',
        **filter_params
    )
    response = request.execute()
    
    if not response.get('items'):
        raise ValueError("Channel not found.")
    
    channel = response['items'][0]
    return {
        'id': channel['id'],
        'title': channel['snippet']['title'],
        'uploads_playlist': channel['contentDetails']['relatedPlaylists']['uploads']
    }

def get_all_video_ids(api_key, playlist_id):
    """Fetch all video IDs from the uploads playlist."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    video_ids = []
    next_page_token = None
    
    while True:
        try:
            request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        except HttpError as e:
            if e.resp.status == 403:
                print("API quota exceeded. Waiting 60 seconds before retrying...")
                logging.warning("API quota exceeded. Waiting 60 seconds.")
                time.sleep(60)
                continue
            else:
                raise
    
    return video_ids

def get_video_titles(api_key, video_ids):
    """Fetch video titles in batches of 50."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    title_map = {}
    batch_size = 50
    
    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i + batch_size]
        try:
            request = youtube.videos().list(
                part='snippet',
                id=','.join(batch)
            )
            response = request.execute()
            
            for item in response['items']:
                video_id = item['id']
                title = item['snippet']['title']
                title_map[video_id] = title
                
        except HttpError as e:
            if e.resp.status == 403:
                print("API quota exceeded. Waiting 60 seconds before retrying...")
                logging.warning("API quota exceeded. Waiting 60 seconds.")
                time.sleep(60)
                continue
            else:
                raise
    
    return title_map

def sanitize_filename(filename):
    """Sanitize filename for Linux/Windows by replacing invalid characters."""
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    if len(filename) > 100:
        filename = filename[:100] + "..."
    return filename

def load_progress(progress_file):
    """Load processed video IDs from progress file."""
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            logging.warning(f"Failed to load progress file {progress_file}. Starting fresh.")
            return set()
    return set()

def save_progress(progress_file, processed_ids):
    """Save processed video IDs to progress file."""
    try:
        with open(progress_file, 'w') as f:
            json.dump(list(processed_ids), f)
    except IOError as e:
        logging.warning(f"Could not save progress file: {e}")
        print(f"Warning: Could not save progress file: {e}")

def convert_vtt_to_txt(vtt_file, txt_file):
    """Convert VTT subtitle file to clean text format, removing tags, timestamps, duplicates, and non-speech artifacts."""
    try:
        seen_lines = set() 
        with open(vtt_file, 'r', encoding='utf-8') as vtt, open(txt_file, 'w', encoding='utf-8') as txt:
            for line in vtt:
                line = line.strip()
                if (not line or 
                    line.startswith('WEBVTT') or 
                    line.startswith('Kind:') or 
                    line.startswith('Language:') or 
                    re.match(r'^\d\d:\d\d', line) or
                    '-->' in line):
                    continue
                
                clean_line = re.sub(r'<[^>]+>', '', line)
                clean_line = re.sub(r'&[^;]+;', '', clean_line)
                clean_line = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}', '', clean_line)
                clean_line = re.sub(r'\[.*?\]', '', clean_line)
                clean_line = clean_line.strip()
                
                if not clean_line:
                    continue
                
                if clean_line not in seen_lines:
                    seen_lines.add(clean_line)
                    txt.write(clean_line + '\n')
        
        return True
    except Exception as e:
        logging.error(f"Error converting VTT to TXT: {str(e)}")
        print(f"Error converting VTT to TXT: {str(e)}")
        return False

def fetch_yt_dlp_transcript(video_id, title, output_dir):
    """Use yt-dlp to fetch subtitles."""
    try:
        safe_title = sanitize_filename(title)
        output_pattern = os.path.join(output_dir, f"{safe_title}_{video_id}")
        
        cmd = [
            'yt-dlp',
            '--write-auto-sub',
            '--write-sub',
            '--sub-lang', 'en',
            '--skip-download',
            '--output', output_pattern + '.%(ext)s',
            '--convert-subs', 'vtt',
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        
        vtt_file = output_pattern + '.en.vtt'
        if os.path.exists(vtt_file):
            txt_file = output_pattern + '.txt'
            if convert_vtt_to_txt(vtt_file, txt_file):
                os.remove(vtt_file)  
                logging.info(f"Saved transcript via yt-dlp for '{title}' (ID: {video_id})")
                print(f"✓ Saved transcript via yt-dlp for '{title}' (ID: {video_id})")
                return True
            else:
                logging.warning(f"Conversion failed, keeping VTT file for '{title}' (ID: {video_id})")
                print(f"⚠ Conversion failed, keeping VTT file for '{title}' (ID: {video_id})")
                return True
        
        logging.warning(f"No subtitle file created for '{title}' (ID: {video_id})")
        print(f"⚠ No subtitle file created for '{title}' (ID: {video_id})")
        return False
        
    except subprocess.CalledProcessError as e:
        logging.error(f"yt-dlp failed for '{title}' (ID: {video_id}): {e.stderr}")
        print(f"✗ yt-dlp failed for '{title}' (ID: {video_id}): {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logging.error(f"yt-dlp timed out for '{title}' (ID: {video_id})")
        print(f"✗ yt-dlp timed out for '{title}' (ID: {video_id})")
        return False
    except Exception as e:
        logging.error(f"yt-dlp error for '{title}' (ID: {video_id}): {str(e)}")
        print(f"✗ yt-dlp error for '{title}' (ID: {video_id}): {str(e)}")
        return False

def fetch_and_save_transcript(video_id, title, output_dir, delay=2, processed_ids=None, progress_file=None):
    """Fetch transcript using yt-dlp with retry logic."""
    if video_id in processed_ids:
        print(f"↻ Skipped '{title}' (ID: {video_id}) - Already processed")
        return False
    
    for attempt in range(3):  
        try:
            success = fetch_yt_dlp_transcript(video_id, title, output_dir)
            if success:
                processed_ids.add(video_id)
                save_progress(progress_file, processed_ids)
                return True
            else:
                if attempt < 2:
                    wait_time = 10 * (attempt + 1)  
                    print(f"Retrying after {wait_time}s... (attempt {attempt + 1}/3)")
                    time.sleep(wait_time)
                    continue
                else:
                    processed_ids.add(video_id)
                    save_progress(progress_file, processed_ids)
                    return False
                    
        except Exception as e:
            logging.error(f"Unexpected error for '{title}' (ID: {video_id}): {str(e)}")
            print(f"✗ Unexpected error for '{title}' (ID: {video_id}): {str(e)}")
            if attempt < 2:
                wait_time = 10 * (attempt + 1)
                time.sleep(wait_time)
                continue
            else:
                processed_ids.add(video_id)
                save_progress(progress_file, processed_ids)
                return False
        finally:
            time.sleep(delay)

def main():
    print("YouTube Channel Transcript Scraper")
    print("----------------------------------")
    
    api_key = input("Enter your YouTube API key: ").strip()
    if not api_key:
        print("API key is required.")
        logging.error("No API key provided.")
        return
    
    channel_url = input("Enter the YouTube channel URL (e.g., https://www.youtube.com/@channelhandle): ").strip()
    
    try:
        filter_params = parse_channel_url(channel_url)
        channel_details = get_channel_details(api_key, filter_params)
        channel_title = sanitize_filename(channel_details['title'])
        output_dir = os.path.join(os.getcwd(), channel_title)
        progress_file = os.path.join(os.getcwd(), f"{channel_title}_progress.json")
        
        print(f"Channel: {channel_details['title']} (ID: {channel_details['id']})")
        logging.info(f"Processing channel: {channel_details['title']} (ID: {channel_details['id']})")
        
        print("Loading progress...")
        processed_ids = load_progress(progress_file)
        
        print("Fetching video IDs...")
        video_ids = get_all_video_ids(api_key, channel_details['uploads_playlist'])
        video_ids = [vid for vid in video_ids if vid not in processed_ids]
        print(f"Found {len(video_ids)} new videos to process.")
        logging.info(f"Found {len(video_ids)} new videos to process.")
        
        if not video_ids:
            print("No new videos to process.")
            logging.info("No new videos to process.")
            return
        
        print("Fetching video titles...")
        title_map = get_video_titles(api_key, video_ids)
        
        delay = float(input("Enter delay between transcript fetches (seconds, recommended 2-5): ") or 2)
        if delay < 2:
            print("Warning: Delay < 2s may cause throttling. Proceeding anyway.")
            logging.warning("Delay set to %s seconds, may cause throttling.", delay)
        
        print("Fetching transcripts using yt-dlp...")
        success_count = 0
        for i, video_id in enumerate(video_ids, 1):
            title = title_map.get(video_id, f"Video_{video_id}")
            print(f"Processing {i}/{len(video_ids)}: {title}")
            if fetch_and_save_transcript(video_id, title, output_dir, delay, processed_ids, progress_file):
                success_count += 1
        
        print(f"Done! {success_count}/{len(video_ids)} new transcripts saved to '{output_dir}'.")
        logging.info(f"Completed: {success_count}/{len(video_ids)} new transcripts saved to '{output_dir}'.")
    
    except HttpError as e:
        if e.resp.status == 403:
            print("API Error: Quota exceeded or API key invalid. Check your Google Cloud Console.")
            logging.error("API Error: Quota exceeded or API key invalid.")
        else:
            print(f"API Error: {str(e)}")
            logging.error(f"API Error: {str(e)}")
    except ValueError as e:
        print(f"Error: {str(e)}")
        logging.error(f"ValueError: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()