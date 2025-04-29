@echo off
set /p video_url=Enter the YouTube video URL: 

for /f "tokens=2 delims==/" %%a in ("%video_url%") do set video_id=%%a

if "%video_id%"=="" (
    echo Invalid URL or unable to extract video ID. Please try again with a valid YouTube video URL.
    pause
    exit /b 1
)

set comments_file=%video_id%_comments.json
set filtered_comments_file=%video_id%_filtered_comments.json

yt-dlp --write-comments --skip-download --output "%comments_file%" %video_url%

if %ERRORLEVEL% neq 0 (
    echo Error occurred while downloading comments.
    pause
    exit /b 1
)

python filter_comments.py "%comments_file%.info.json" "%filtered_comments_file%"

if %ERRORLEVEL% neq 0 (
    echo Error occurred while processing comments with Python.
    pause
    exit /b 1
)

echo Done! The filtered comments have been saved to %filtered_comments_file%.
pause
