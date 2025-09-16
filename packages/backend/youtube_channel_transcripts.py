import os
import re
import time
import logging
import json
import subprocess
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcript_scraper.log'),
        logging.StreamHandler()
    ]
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

def get_all_video_ids(api_key, playlist_id, max_videos=50):
    """Fetch video IDs from the uploads playlist with limit."""
    youtube = build('youtube', 'v3', developerKey=api_key)
    video_ids = []
    next_page_token = None
    
    while len(video_ids) < max_videos:
        try:
            request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=min(50, max_videos - len(video_ids)),
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])
                if len(video_ids) >= max_videos:
                    break
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        except HttpError as e:
            if e.resp.status == 403:
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

def convert_vtt_to_txt(vtt_file, txt_file):
    """Convert VTT subtitle file to clean text format."""
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
        return False

def fetch_yt_dlp_transcript(video_id, title, output_dir, cookies_file=None):
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
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
        ]
        
        if cookies_file and os.path.exists(cookies_file):
            cmd.extend(['--cookies', cookies_file])
            logging.info(f"Using cookies file: {cookies_file}")
        else:
            logging.warning("No cookies file provided. This may cause HTTP 429 errors.")
        
        cmd.append(f"https://www.youtube.com/watch?v={video_id}")
        
        logging.info(f"Running yt-dlp command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        
        vtt_file = output_pattern + '.en.vtt'
        if os.path.exists(vtt_file):
            txt_file = output_pattern + '.txt'
            if convert_vtt_to_txt(vtt_file, txt_file):
                os.remove(vtt_file)
                logging.info(f"Saved transcript for '{title}' (ID: {video_id})")
                return True
            else:
                logging.warning(f"Conversion failed for '{title}' (ID: {video_id})")
                return True
        
        logging.warning(f"No subtitle file for '{title}' (ID: {video_id})")
        return False
        
    except subprocess.CalledProcessError as e:
        logging.error(f"yt-dlp failed for '{title}' (ID: {video_id}): {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logging.error(f"yt-dlp timed out for '{title}' (ID: {video_id})")
        return False
    except Exception as e:
        logging.error(f"yt-dlp error for '{title}' (ID: {video_id}): {str(e)}")
        return False

def process_channel_transcripts(api_key, channel_url, delay=2, max_videos=50, cookies_file=None):
    """Main function to process transcripts for a channel."""
    try:
        filter_params = parse_channel_url(channel_url)
        channel_details = get_channel_details(api_key, filter_params)
        channel_title = sanitize_filename(channel_details['title'])
        output_dir = os.path.join(os.getcwd(), channel_title)
        progress_file = os.path.join(os.getcwd(), f"{channel_title}_progress.json")
        
        os.makedirs(output_dir, exist_ok=True)
        
        logging.info(f"Processing channel: {channel_details['title']} (ID: {channel_details['id']})")
        
        processed_ids = load_progress(progress_file)
        
        video_ids = get_all_video_ids(api_key, channel_details['uploads_playlist'], max_videos)
        video_ids = [vid for vid in video_ids if vid not in processed_ids]
        
        if not video_ids:
            return {
                'channel_title': channel_details['title'],
                'videos_processed': 0,
                'total_videos': 0,
                'message': 'No new videos to process',
                'output_dir': output_dir
            }
        
        title_map = get_video_titles(api_key, video_ids)
        
        success_count = 0
        for i, video_id in enumerate(video_ids, 1):
            title = title_map.get(video_id, f"Video_{video_id}")
            logging.info(f"Processing {i}/{len(video_ids)}: {title}")
            
            for attempt in range(3):
                success = fetch_yt_dlp_transcript(video_id, title, output_dir, cookies_file)
                if success:
                    success_count += 1
                    processed_ids.add(video_id)
                    save_progress(progress_file, processed_ids)
                    break
                elif attempt < 2:
                    wait_time = (2 ** attempt) * 10  
                    logging.info(f"Retrying after {wait_time}s... (attempt {attempt + 1}/3)")
                    time.sleep(wait_time)
                    continue
                else:
                    processed_ids.add(video_id)
                    save_progress(progress_file, processed_ids)
                    break
            
            time.sleep(max(2, min(delay, 5)))  
        
        return {
            'channel_title': channel_details['title'],
            'videos_processed': success_count,
            'total_videos': len(video_ids),
            'output_dir': output_dir,
            'message': f"Processed {success_count} out of {len(video_ids)} videos"
        }
    
    except Exception as e:
        logging.error(f"Error processing channel: {str(e)}")
        raise