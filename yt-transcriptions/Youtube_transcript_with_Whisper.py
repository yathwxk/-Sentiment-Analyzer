from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
import yt_dlp
import whisper
import os
import re

def get_video_id(youtube_url):
    """
    Extracts the video ID from the given YouTube URL.
    """
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL format. Unable to extract video ID.")

def fetch_video_title(youtube_url):
    """
    Fetch the video title using yt-dlp.
    """
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get("title", "Unknown_Title").replace(" ", "_").replace("|", "_")
    except Exception as e:
        return f"Error_Fetching_Title_{e}"

def download_audio(youtube_url, save_path):
    """
    Downloads audio from YouTube video in MP3 format.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            audio_filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(audio_filename)
            return base + '.mp3'
    except Exception as e:
        raise Exception(f"Audio download failed: {e}")

def transcribe_audio(audio_path, target_language='en'):
    """
    Transcribes audio using Whisper speech-to-text model.
    """
    try:
        model = whisper.load_model("medium")
        
        if target_language == 'en':
            result = model.transcribe(audio_path, task='translate')
        else:
            result = model.transcribe(audio_path, language=target_language)
        
        return [
            {
                'text': segment['text'].strip(),
                'start': segment['start'],
                'duration': segment['end'] - segment['start']
            }
            for segment in result['segments']
        ]
    except Exception as e:
        raise Exception(f"Transcription failed: {e}")

def fetch_transcripts(youtube_url, target_language='en', save_path="output"):
    """
    Fetches or generates transcripts with fallback to speech-to-text.
    """
    try:
        video_id = get_video_id(youtube_url)
        video_title = fetch_video_title(youtube_url)
        print(f"Video Title: {video_title}")

        try:
            # Try to get transcript in target language
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[target_language])
        except (NoTranscriptFound, TranscriptsDisabled):
            try:
                # Fallback to English + translation
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                if target_language != 'en':
                    transcript = YouTubeTranscriptApi.translate_transcript(transcript, target_language)
            except (NoTranscriptFound, TranscriptsDisabled):
                # Fallback to Whisper transcription
                print("No transcripts available. Generating using speech-to-text...")
                audio_file = download_audio(youtube_url, save_path)
                transcript = transcribe_audio(audio_file, target_language)
                os.remove(audio_file)  # Clean up audio file

        # Format and save transcript
        formatter = SRTFormatter()
        srt_transcript = formatter.format_transcript(transcript)

        os.makedirs(save_path, exist_ok=True)
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", video_title)  # Remove invalid filename characters
        save_file = os.path.join(save_path, f"{sanitized_title}_{target_language}.srt")
        
        with open(save_file, "w", encoding="utf-8") as file:
            file.write(srt_transcript)

        return f"Transcript saved successfully at: {save_file}"

    except Exception as e:
        return f"An error occurred: {e}"
