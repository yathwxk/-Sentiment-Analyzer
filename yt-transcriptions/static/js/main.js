let player;
let currentVideoId = null;
let playerReady = false;

// Initialize YouTube player when API is ready
function onYouTubeIframeAPIReady() {
    initializePlayer();
}

function initializePlayer() {
    player = new YT.Player('player', {
        height: '100%',
        width: '100%',
        videoId: '',
        playerVars: {
            'playsinline': 1,
            'rel': 0,
            'autoplay': 0,
            'controls': 1,
            'modestbranding': 1,
            'showinfo': 1,
            'origin': window.location.origin
        },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange,
            'onError': onPlayerError
        }
    });
}

function onPlayerReady(event) {
    console.log('Player is ready');
    playerReady = true;
    if (currentVideoId) {
        loadVideo(currentVideoId);
    }
}

function onPlayerStateChange(event) {
    console.log('Player state changed:', event.data);
    // Handle player state changes if needed
}

function onPlayerError(event) {
    console.error('Player error:', event.data);
    const errorAlert = document.getElementById('errorAlert');
    let errorMessage = 'Error loading video. Please try again.';
    
    switch(event.data) {
        case 2:
            errorMessage = 'Invalid video ID. Please check the URL.';
            break;
        case 5:
            errorMessage = 'HTML5 player error. Please try refreshing the page.';
            break;
        case 100:
            errorMessage = 'Video not found or removed.';
            break;
        case 101:
        case 150:
            errorMessage = 'Video playback not allowed.';
            break;
    }
    
    errorAlert.textContent = errorMessage;
    errorAlert.classList.remove('d-none');
    setTimeout(() => errorAlert.classList.add('d-none'), 5000);
}

function loadVideo(videoId) {
    if (!player || !playerReady) {
        console.log('Player not ready, queuing video:', videoId);
        currentVideoId = videoId;
        return;
    }

    try {
        console.log('Loading video:', videoId);
        player.loadVideoById({
            videoId: videoId,
            startSeconds: 0
        });
        player.pauseVideo();
        currentVideoId = videoId;
    } catch (error) {
        console.error('Error loading video:', error);
        onPlayerError({ data: 'load_error' });
    }
}

// Extract video ID from YouTube URL
function extractVideoId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : false;
}

// Convert YouTube timestamp to seconds
function convertTimestampToSeconds(timestamp) {
    const parts = timestamp.split(':').reverse();
    let seconds = 0;
    for (let i = 0; i < parts.length; i++) {
        seconds += parseInt(parts[i]) * Math.pow(60, i);
    }
    return seconds;
}

// Handle theme toggle
function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.setAttribute('data-theme', 'dark');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    themeToggle?.addEventListener('click', () => {
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        document.body.setAttribute('data-theme', isDark ? 'light' : 'dark');
        localStorage.setItem('theme', isDark ? 'light' : 'dark');
        themeToggle.innerHTML = isDark ? 
            '<i class="fas fa-moon"></i>' : 
            '<i class="fas fa-sun"></i>';
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const videoForm = document.getElementById('videoForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const results = document.getElementById('results');
    const errorAlert = document.getElementById('errorAlert');
    const summaryText = document.getElementById('summaryText');
    const timestampsList = document.getElementById('timestampsList');
    const audioSource = document.getElementById('audioSource');
    const submitBtn = document.getElementById('submitBtn');
    
    // Initialize theme
    initTheme();

    videoForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const youtubeUrl = document.getElementById('youtubeUrl').value;
        const videoId = extractVideoId(youtubeUrl);
        
        if (!videoId) {
            errorAlert.textContent = 'Invalid YouTube URL';
            errorAlert.classList.remove('d-none');
            return;
        }
        
        loadingSpinner.classList.remove('d-none');
        results.classList.add('d-none');
        errorAlert.classList.add('d-none');
        submitBtn.disabled = true;

        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ youtube_url: youtubeUrl })
            });

            const data = await response.json();

            if (data.status === 'success' || (data.summary && data.important_points)) {
                // Format summary with paragraphs and lists
                const formattedSummary = formatSummary(data.summary);
                summaryText.innerHTML = formattedSummary;

                // Update audio player
                if (data.audio_path) {
                    audioSource.src = data.audio_path;
                    audioSource.parentElement.load();
                }

                // Update timestamps
                updateTimestamps(data.important_points);

                // Show results
                results.classList.remove('d-none');

                // Load video with retry mechanism
                let retryCount = 0;
                const loadVideoWithRetry = () => {
                    if (retryCount < 3) {
                        setTimeout(() => {
                            if (!playerReady) {
                                console.log('Retrying video load, attempt:', retryCount + 1);
                                retryCount++;
                                loadVideoWithRetry();
                            } else {
                                loadVideo(videoId);
                            }
                        }, 1000 * (retryCount + 1));
                    }
                };
                loadVideoWithRetry();
            } else {
                throw new Error(data.message || 'An error occurred while processing the video');
            }
        } catch (error) {
            errorAlert.textContent = error.message;
            errorAlert.classList.remove('d-none');
        } finally {
            loadingSpinner.classList.add('d-none');
            submitBtn.disabled = false;
        }
    });
});

function formatSummary(summary) {
    if (!summary) return '';
    
    // Split into paragraphs
    let formatted = summary.split('\n').map(para => {
        if (para.trim()) {
            // Check if it's a list item
            if (para.trim().startsWith('-') || para.trim().startsWith('•')) {
                return `<li>${para.trim().substring(1).trim()}</li>`;
            }
            // Check if it's a heading
            if (para.trim().startsWith('#')) {
                return `<strong>${para.trim().substring(1).trim()}</strong>`;
            }
            return `<p>${para.trim()}</p>`;
        }
        return '';
    }).join('');
    
    // Wrap lists in ul tags
    formatted = formatted.replace(/<li>.*?<\/li>/g, match => {
        return `<ul>${match}</ul>`;
    });
    
    return formatted;
}

function updateTimestamps(timestamps) {
    const timestampsList = document.getElementById('timestampsList');
    timestampsList.innerHTML = '';
    
    timestamps.forEach(point => {
        const listItem = document.createElement('div');
        listItem.className = 'timestamp-item';
        
        listItem.innerHTML = `
            <div class="timestamp-content">
                <span class="timestamp-time">${point.start_time}</span>
                <p class="timestamp-text">${point.text}</p>
            </div>
        `;
        
        listItem.addEventListener('click', () => {
            if (player && player.seekTo) {
                const seconds = convertTimestampToSeconds(point.start_time);
                player.seekTo(seconds);
                player.playVideo();
            }
        });
        
        timestampsList.appendChild(listItem);
    });
}
