from flask import Flask, render_template, request, jsonify, send_from_directory
from youtube_summarizer import YouTubeSummarizer
import os
from pathlib import Path
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create necessary directories
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')

for directory in [AUDIO_DIR, OUTPUT_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Create a thread pool for handling requests
executor = ThreadPoolExecutor(max_workers=3)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('audio', filename)

@app.route('/process', methods=['POST'])
def process_video():
    try:
        youtube_url = request.json['youtube_url']
        
        # Initialize YouTubeSummarizer
        summarizer = YouTubeSummarizer(youtube_url)
        
        # Process the video with optimized pipeline
        result = summarizer.process_video()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
