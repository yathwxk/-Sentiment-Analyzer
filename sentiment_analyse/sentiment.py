import json
from textblob import TextBlob
import pandas as pd

# Function to perform sentiment analysis using TextBlob
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0:
        return "Positive"
    elif sentiment == 0:
        return "Neutral"
    else:
        return "Negative"

# Read the JSON file containing the comments
with open('www.youtube.com_filtered_comments.json', 'r', encoding='utf-8') as file:
    comments_data = json.load(file)

# List to hold sentiment analysis results
sentiment_results = []

# Process each comment in the JSON file
for comment in comments_data:
    text = comment.get("text", "").strip()  # Get the text field and strip leading/trailing spaces
    sentiment = analyze_sentiment(text)
    
    sentiment_results.append({
        "author": comment.get("author"),
        "author_url": comment.get("author_url"),
        "text": text,
        "sentiment": sentiment,
        "like_count": comment.get("like_count"),
        "time": comment.get("time")
    })

# Convert results to a pandas DataFrame
df = pd.DataFrame(sentiment_results)

# Save the sentiment results to a CSV file
df.to_csv("comments_sentiment_analysis.csv", index=False)

# Print the results
print(df)
