from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from youtube_channel_transcripts import process_channel_transcripts

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcript_scraper.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'youtube-transcript-scraper'})

@app.route('/api/scrape-transcripts', methods=['POST'])
def scrape_transcripts():
    """API endpoint to scrape transcripts for a YouTube channel"""
    try:
        data = request.json
        channel_url = data.get('channel_url')
        cookies_file = data.get('cookies_file')
        
        api_key = os.environ.get('YOUTUBE_API_KEY')
        
        if not api_key:
            logging.error("YouTube API key not configured")
            return jsonify({'error': 'YouTube API key not configured'}), 500
            
        if not channel_url:
            logging.error("Channel URL is required")
            return jsonify({'error': 'Channel URL is required'}), 400
        
        if not ('youtube.com' in channel_url or 'youtu.be' in channel_url):
            logging.error(f"Invalid YouTube URL: {channel_url}")
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        delay = float(data.get('delay', 5))
        max_videos = int(data.get('max_videos', 50))
        
        logging.info(f"Processing channel: {channel_url}")
        
        result = process_channel_transcripts(
            api_key=api_key,
            channel_url=channel_url,
            delay=delay,
            max_videos=max_videos,
            cookies_file=cookies_file
        )
        
        logging.info(f"Successfully processed channel: {result['channel_title']}")
        return jsonify({
            'success': True,
            'channel_title': result['channel_title'],
            'videos_processed': result['videos_processed'],
            'total_videos_found': result['total_videos'],
            'output_dir': result['output_dir'],
            'message': result['message']
        })
        
    except ValueError as e:
        logging.error(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', False))