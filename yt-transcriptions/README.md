# Software Engineering Project

## Overview

This is a collection of scripts designed for various tasks, including YouTube video processing, text summarization, and podcast integration.

## Contents

The repository includes the following scripts:

- **extract_pod.py**: Goes through the Json file and generates audio.
- **parl_gen.py**: Generates audio tokens from the JSON file.
- **text_summarization.py**: Summarizes text content generated from the video text.
- **youtube_summarizer.py**: Summarizes YouTube video content.
- **youtube_transcript.py**: Retrieves transcripts from YouTube videos.

## Requirements

Ensure you have Python installed. You may need to install additional packages using `pip`:

```bash
pip install -r requirements.txt

```

# YouTube Video Summarizer

A powerful web application that automatically generates concise summaries, extracts key moments and creates audio versions of YouTube videos. Built with Flask, Edge TTS, and the Groq API.

## 🌟 Features

- **Video Summarization**: Get concise, accurate summaries of any YouTube video
- **Key Moments**: Extract and link to important timestamps in the video
- **Audio Generation**: Convert summaries to natural-sounding speech
- **Interactive UI**: Clean, modern interface with video preview
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- FFmpeg (for audio processing)

### Installing FFmpeg

#### Windows
1. Download FFmpeg from [here](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z)
2. Extract the archive
3. Add the `bin` folder to your system's PATH environment variable
4. Verify installation: `ffmpeg -version`

#### macOS
```bash
# Using Homebrew
brew install ffmpeg

# Verify installation
ffmpeg -version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

## 🚀 Installation

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/youtube-summarizer.git
cd youtube-summarizer
```

2. **Create and Activate Virtual Environment**

Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Set Up Environment Variables**

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key
FLASK_ENV=development
```

Replace `your_groq_api_key` with your actual Groq API key. Get one from [Groq Console](https://console.groq.com).

## 🎮 Usage

1. **Start the Application**

Windows/macOS/Linux:
```bash
python app.py
```

2. **Access the Web Interface**
- Open your browser and go to: `http://localhost:5000`
- Enter a YouTube URL and click "Process Video"
- Wait for the processing to complete
- View the summary, key moments, and listen to the audio version

## 📁 Project Structure

```
youtube-summarizer/
├── app.py                 # Flask application
├── youtube_summarizer.py  # Core summarization logic
├── static/               
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
├── templates/            
│   └── index.html        # Main webpage template
├── temp/                 # Temporary files
└── audio/               # Generated audio files
```

## ⚙️ Configuration

### Customizing the Summarizer

You can modify these parameters in `youtube_summarizer.py`:
- `max_text_length`: Maximum length of text for API processing
- `chunk_size`: Size of caption chunks for processing
- `retry_delay`: Delay between API retries

### Audio Settings

Edge TTS settings in `youtube_summarizer.py`:
- Voice: Currently uses "en-US-AriaNeural"
- Rate: Set to "+50%" for faster playback
- Volume: Set to "+100%" for maximum clarity

## 🔧 Troubleshooting

### Common Issues

1. **Rate Limit Errors**
   - The application automatically handles rate limits with retries
   - If persistent, increase `retry_delay` in `youtube_summarizer.py`

2. **FFmpeg Missing**
   - Error: "FFmpeg not found"
   - Solution: Follow FFmpeg installation instructions above

3. **No Subtitles Available**
   - Some videos may not have subtitles
   - Try another video or use auto-generated captions

4. **Audio Not Playing**
   - Check browser audio settings
   - Ensure FFmpeg is properly installed
   - Try a different browser

## 🛠️ Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
```bash
# Install development dependencies
pip install black flake8

# Format code
black .

# Check style
flake8
```

## 🔐 Security

- Never commit your `.env` file
- Keep your Groq API key secure
- Use HTTPS in production
- Regularly update dependencies

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Edge TTS for audio generation
- Groq API for text processing
- Flask framework
- All contributors and users
