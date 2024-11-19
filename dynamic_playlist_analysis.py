import pandas as pd
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import openai
import time
import datetime
import os

# Set up your Spotify API credentials
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Authenticate with Spotify
auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Extract playlist ID from Spotify URL
def extract_playlist_id(playlist_link):
    match = re.search(r"playlist/([a-zA-Z0-9]+)", playlist_link)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid Spotify playlist link")

def fetch_playlist_tracks_with_features(playlist_id):
    start_time = datetime.datetime.now()  # Record the start time
    max_duration = datetime.timedelta(minutes=3)  # Maximum allowed duration for a process
    tracks = []
    features = []

    results = sp.playlist_items(playlist_id)
    while results:
        for item in results['items']:
            track = item['track']
            if track:
                tracks.append({
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name']
                })
                try:
                    track_features = sp.audio_features([track['id']])[0]
                    if track_features:
                        features.append(track_features)
                except Exception:
                    continue
        if len(tracks) > 0:
            break

    if datetime.datetime.now() - start_time > max_duration:
        raise TimeoutError("Fetching playlist tracks took too long")

    # Combine tracks with features into a single DataFrame
    df_tracks = pd.DataFrame(tracks)
    df_features = pd.DataFrame(features)
    combined = pd.concat([df_tracks, df_features], axis=1)

    return combined

def generate_recommendations(tracks_df, num_recommendations=5):
    # Placeholder recommendation logic
    if tracks_df.empty:
        return ["No recommendations available"]

    top_tracks = tracks_df.sort_values(by='popularity', ascending=False)
    recommendations = top_tracks.head(num_recommendations)['name'].tolist()
    return recommendations

def process_playlist_and_recommend_song(playlist_link):
    playlist_id = extract_playlist_id(playlist_link)
    tracks_with_features = fetch_playlist_tracks_with_features(playlist_id)
    return generate_recommendations(tracks_with_features)
