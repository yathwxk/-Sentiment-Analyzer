import pandas as pd
from googleapiclient.discovery import build
import streamlit as st
import html
from preprocessing_app import clean_with_timestamp

@st.cache_data
def scraper(api_key,video_url) :
    video_id = video_url.split('v=')[1]
    if "&t" in video_id:
        video_id = video_id.split('&t')[0]
    # Build the YouTube Data API client
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Retrieve comments for the video
    request = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        maxResults=50
    )

    # Create a list to store comments, authors, and likes
    comments_data = []

    while request:
        response = request.execute()

        for thread in response['items']:
            # Extract author's name, comment text, and number of likes
            author_name = thread['snippet']['topLevelComment']['snippet']['authorDisplayName']
            comment_text = thread['snippet']['topLevelComment']['snippet']['textDisplay']
            num_likes = thread['snippet']['topLevelComment']['snippet']['likeCount']
            date_time = thread['snippet']['topLevelComment']['snippet']['publishedAt']
            # Append to the list
            comments_data.append({'author': author_name, 'english_comm': comment_text, 'likes': num_likes,'date_time':date_time})

        request = youtube.commentThreads().list_next(request, response)


    df = pd.DataFrame(comments_data)
    df['date_time'] = pd.to_datetime(df['date_time'])
    df['hour'] = df['date_time'].dt.hour
    df['english_comm'] = df['english_comm'].astype(str).apply(html.unescape)
    df['english_comm'] = df['english_comm'].str.replace(('<br>'),' ')
    df['english_comm'] = df['english_comm'].str.replace(('<b>'),' ')
    df['english_comm'] = df['english_comm'].str.replace('&#39;', "'", regex=False)
    df['english_comm'] = df['english_comm'].apply(clean_with_timestamp)

    return df

