import pandas as pd
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import openai
import os

# Set up Spotify API credentials
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
openai.api_key = os.getenv("OPENAI_API_KEY")

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

def extract_playlist_id(playlist_link):
    """
    Extracts the playlist ID from a Spotify playlist link.
    """
    match = re.search(r"playlist/([a-zA-Z0-9]+)", playlist_link)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid Spotify playlist link")

def fetch_playlist_tracks_with_features(playlist_id):
    """
    Fetches all tracks and their audio features from a Spotify playlist.
    """
    tracks = []
    features = []
    results = sp.playlist_items(playlist_id)

    while results:
        for item in results['items']:
            track = item['track']
            if track:
                # Collect track metadata
                track_data = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'release_date': track['album']['release_date'],
                    'popularity': track.get('popularity', 0),  # Popularity score
                    'duration_ms': track['duration_ms'],  # Track duration
                    'explicit': track['explicit']  # Explicit content
                }
                tracks.append(track_data)

        if results.get('next'):
            results = sp.next(results)
        else:
            break

    # Fetch audio features for tracks
    track_ids = [track['id'] for track in tracks if track['id'] is not None]
    for i in range(0, len(track_ids), 50):  # Batch requests (Spotify API limit is 50 per request)
        audio_features = sp.audio_features(track_ids[i:i + 50])
        features.extend(audio_features)

    # Combine track metadata and audio features
    tracks_df = pd.DataFrame(tracks)
    features_df = pd.DataFrame(features)

    # Merge the two DataFrames
    full_data = pd.merge(tracks_df, features_df, left_on='id', right_on='id', how='inner')
    return full_data

def get_recommendation(playlist_data_str):
    """
    Generates a song recommendation using OpenAI API.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that analyzes musical taste based on playlist data and recommends songs."
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze the following playlist data and recommend one new song. "
                        "Ensure the song is not already in the playlist. "
                        "Provide the recommendation in the format: 'Song Name - Album Name'.\n\n"
                        f"{playlist_data_str}"
                    )
                }
            ]
        )
        recommendation = response['choices'][0]['message']['content'].strip()
        return recommendation
    except Exception as e:
        return f"Error generating recommendation: {e}"

def process_playlist_and_recommend_song(playlist_link):
    """
    Processes the Spotify playlist and generates a song recommendation.
    """
    try:
        playlist_id = extract_playlist_id(playlist_link)
        tracks_df = fetch_playlist_tracks_with_features(playlist_id)

        if tracks_df.empty:
            return {"message": "No tracks found in the playlist.", "recommendation": None}

        # Convert playlist data to string for OpenAI input
        playlist_data_str = tracks_df.to_string(index=False)

        # Get recommendation from OpenAI
        recommendation = get_recommendation(playlist_data_str)
        return {"message": "Musical taste understood", "recommendation": recommendation}
    except Exception as e:
        return {"message": f"An error occurred: {e}", "recommendation": None}
