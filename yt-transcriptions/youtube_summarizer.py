#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
from typing import Optional, List, Dict
from pathlib import Path
import re
import webvtt
from urllib.parse import quote
import time
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import edge_tts  # pip install edge-tts
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    OUTPUT_DIR_STR, 
    TEMP_DIR_STR,
    AUDIO_DIR_STR
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(OUTPUT_DIR_STR, 'youtube_summarizer.log'))
    ]
)
logger = logging.getLogger(__name__)

GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Cache for API responses
@lru_cache(maxsize=100)
def cached_api_call(text: str, prompt_type: str) -> str:
    """Cache API calls to avoid redundant processing"""
    if prompt_type == "summary":
        return generate_summary_with_groq(text)
    elif prompt_type == "timestamps":
        return extract_important_points_internal(text)
    return None

def generate_summary_with_groq(text: str) -> str:
    """Generate a concise summary using Groq's API"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Create a concise yet comprehensive summary of this video transcript.
    Focus only on the most important points and key takeaways.
    Keep it brief but informative.
    
    Transcript:
    {text}
    
    Format the summary as:
    # Main Topic
    <2-3 sentences overview>
    
    # Key Points
    - <point 1>
    - <point 2>
    - <point 3>
    
    Make it clear and engaging, but keep it short."""

    try:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json={
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {"role": "system", "content": "You are an expert at creating concise, informative video summaries."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000  # Reduced for faster processing
            },
            timeout=30  # Reduced timeout
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            logger.error(f"Groq API error: {response.text}")
            raise Exception(f"Failed to generate summary. Status code: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error in generate_summary_with_groq: {str(e)}")
        raise

def extract_important_points_internal(text: str) -> List[Dict[str, str]]:
    """Internal function for extracting important points with enhanced analysis"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Reduce the size of text to avoid rate limits
    max_text_length = 2000
    if len(text) > max_text_length:
        # Keep first and last parts for context
        text = text[:max_text_length//2] + "\n...\n" + text[-max_text_length//2:]
    
    prompt = f"""Extract 3-4 key moments from this video transcript.
    Focus on the most important insights and revelations.
    Be very concise and brief.
    
    For each key moment, provide:
    1. A short, impactful quote (10-15 words max)
    2. A brief explanation of why it's important
    3. An importance rating (1-5)
    
    Format each moment exactly like this example:
    MOMENT: "This is the key quote from the video"
    REASON: Brief explanation of why this is important
    RATING: 4
    
    Transcript:
    {text}"""
    
    max_retries = 3
    retry_delay = 20  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                GROQ_API_URL,
                headers=headers,
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": "You are an expert at identifying key moments in videos. Extract only the most important points."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500  # Reduced tokens
                },
                timeout=30
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                moments = []
                
                # Parse the response
                current_moment = {}
                for line in content.split('\n'):
                    line = line.strip()
                    if not line:
                        if current_moment:
                            moments.append(current_moment)
                            current_moment = {}
                        continue
                    
                    if line.startswith('MOMENT:'):
                        if current_moment:
                            moments.append(current_moment)
                        current_moment = {'text': line[7:].strip(' "\'')}
                    elif line.startswith('REASON:'):
                        current_moment['reason'] = line[7:].strip()
                    elif line.startswith('RATING:'):
                        try:
                            current_moment['importance'] = int(line[7:].strip())
                        except ValueError:
                            current_moment['importance'] = 3
                
                if current_moment:
                    moments.append(current_moment)
                
                return moments
            elif response.status_code == 429:  # Rate limit error
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    logger.warning(f"Rate limit hit, waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Increase delay for next retry
                    continue
            else:
                logger.error(f"API error: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return []
                
        except Exception as e:
            logger.error(f"Error extracting points: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return []
    
    return []

def extract_important_points(vtt_path: str, video_url: str) -> List[Dict[str, str]]:
    """Extract important timestamps with enhanced filtering and validation"""
    try:
        captions = list(webvtt.read(vtt_path))
        
        # Process captions in chunks to reduce API load
        chunk_size = 50  # Reduced chunk size
        chunks = [captions[i:i + chunk_size] for i in range(0, len(captions), chunk_size)]
        
        all_moments = []
        for chunk in chunks:
            text = ' '.join(c.text for c in chunk)
            moments = extract_important_points_internal(text)
            if moments:
                all_moments.extend(moments)
                time.sleep(2)  # Add delay between chunks
        
        # Match moments with timestamps
        important_points = []
        for moment in all_moments:
            # Find the caption that contains this moment's text
            moment_text = moment['text'].lower()
            best_match = None
            best_ratio = 0
            
            for caption in captions:
                ratio = similar(moment_text, caption.text.lower())
                if ratio > best_ratio and ratio > 0.5:  # Minimum similarity threshold
                    best_ratio = ratio
                    best_match = caption
            
            if best_match:
                important_points.append({
                    "text": moment['text'],
                    "insight": moment.get('reason', 'Important insight from the video'),
                    "start_time": best_match.start,
                    "end_time": best_match.end,
                    "link": f"{video_url}&t={int(best_match.start_in_seconds)}s",
                    "importance": moment.get('importance', 3)
                })
        
        # Sort by importance and return top 5
        important_points.sort(key=lambda x: x['importance'], reverse=True)
        return important_points[:5]
            
    except Exception as e:
        logger.error(f"Failed to extract important points: {str(e)}")
        return []

def similar(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()

class YouTubeSummarizer:
    def __init__(self, youtube_url: str):
        self.youtube_url = youtube_url
        self.video_id = self._extract_video_id()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    def _extract_video_id(self) -> str:
        """Extract YouTube video ID from URL"""
        patterns = [
            r"v=([A-Za-z0-9_\-]{11})",
            r"youtu\.be/([A-Za-z0-9_\-]{11})",
            r"embed/([A-Za-z0-9_\-]{11})",
        ]
        for pattern in patterns:
            if match := re.search(pattern, self.youtube_url):
                return match.group(1)
        raise ValueError("Invalid YouTube URL")

    async def generate_audio(self, text: str, output_path: str) -> None:
        """Generate audio using Edge TTS (faster than gTTS)"""
        try:
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="+50%", volume="+100%")
            await communicate.save(output_path)
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise

    def download_subtitles(self) -> str:
        """Download video subtitles"""
        try:
            # First try to find existing subtitle file with different extensions
            possible_extensions = ['.vtt', '.en.vtt', '.en-US.vtt']
            for ext in possible_extensions:
                output_path = os.path.join(TEMP_DIR_STR, f"{self.video_id}{ext}")
                if os.path.exists(output_path):
                    logger.info(f"Using existing subtitle file: {output_path}")
                    return output_path
            
            # If no existing file found, download new subtitles
            base_output = os.path.join(TEMP_DIR_STR, self.video_id)
            cmd = [
                "yt-dlp",
                "--write-auto-sub",
                "--write-sub",
                "--sub-lang", "en",
                "--skip-download",
                "--sub-format", "vtt",
                f"--output", base_output,
                self.youtube_url
            ]
            
            logger.info(f"Downloading subtitles for video {self.video_id}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"yt-dlp error: {result.stderr}")
                raise Exception("Failed to download subtitles")
            
            # Find the downloaded subtitle file
            for ext in possible_extensions:
                output_path = os.path.join(TEMP_DIR_STR, f"{self.video_id}{ext}")
                if os.path.exists(output_path):
                    logger.info(f"Successfully downloaded subtitles to: {output_path}")
                    return output_path
            
            raise FileNotFoundError("No subtitle file found after download")
            
        except Exception as e:
            logger.error(f"Failed to download subtitles: {str(e)}")
            raise

    def convert_subtitles_to_text(self, subtitle_path: str) -> str:
        """Convert subtitles to plain text"""
        try:
            if not os.path.exists(subtitle_path):
                raise FileNotFoundError(f"Subtitle file not found at: {subtitle_path}")
                
            logger.info(f"Converting subtitles from: {subtitle_path}")
            captions = webvtt.read(subtitle_path)
            text = " ".join([caption.text.replace('\n', ' ') for caption in captions])
            
            # Save the text version for debugging
            text_path = os.path.join(TEMP_DIR_STR, f"{self.video_id}_transcript.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
                
            return text
            
        except Exception as e:
            logger.error(f"Failed to convert subtitles: {str(e)}")
            raise

    def process_video(self) -> Dict:
        """Process video in parallel for faster results"""
        try:
            # Download subtitles with retries
            max_retries = 3
            retry_count = 0
            subtitle_path = None
            
            while retry_count < max_retries:
                try:
                    subtitle_path = self.download_subtitles()
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise
                    logger.warning(f"Retry {retry_count}/{max_retries} for subtitle download")
                    time.sleep(2)
            
            if not subtitle_path or not os.path.exists(subtitle_path):
                raise FileNotFoundError("Failed to obtain subtitle file after retries")
            
            # Convert subtitles to text
            text = self.convert_subtitles_to_text(subtitle_path)
            
            if not text.strip():
                raise ValueError("No text content found in subtitles")
            
            # Process summary and timestamps in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                summary_future = executor.submit(cached_api_call, text, "summary")
                points_future = executor.submit(extract_important_points, subtitle_path, self.youtube_url)
                
                summary = summary_future.result()
                important_points = points_future.result()
            
            # Generate audio from a shorter version of the summary
            audio_text = self.create_audio_script(summary)
            audio_path = os.path.join(AUDIO_DIR_STR, f"{self.video_id}_audio.mp3")
            
            import asyncio
            asyncio.run(self.generate_audio(audio_text, audio_path))
            
            return {
                "status": "success",
                "summary": summary,
                "audio_path": f"/audio/{self.video_id}_audio.mp3",
                "important_points": important_points
            }
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise

    def create_audio_script(self, summary: str) -> str:
        """Create a shorter, more concise version for audio"""
        # Extract main points for shorter audio
        lines = summary.split('\n')
        audio_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith('-'):
                    audio_lines.append(line[1:].strip())
                else:
                    audio_lines.append(line)
        
        return '. '.join(audio_lines)

def main():
    if len(sys.argv) != 2:
        print("Usage: python youtube_summarizer.py <youtube_url>")
        sys.exit(1)

    youtube_url = sys.argv[1]
    summarizer = YouTubeSummarizer(youtube_url)
    
    try:
        # Process video
        result = summarizer.process_video()
        
        # Save summary and important points
        if result['status'] == "success":
            summary_path = os.path.join(OUTPUT_DIR_STR, f"{summarizer.video_id}_summary.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(result['summary'])
            
            if result['important_points']:
                points_path = os.path.join(OUTPUT_DIR_STR, f"{summarizer.video_id}_important_points.txt")
                with open(points_path, "w", encoding="utf-8") as f:
                    for point in result['important_points']:
                        f.write(f"Time: {point['start_time']} - {point['end_time']}\n")
                        f.write(f"Text: {point['text']}\n")
                        f.write(f"Link: {point['link']}\n")
                        f.write("-" * 40 + "\n")
                    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()