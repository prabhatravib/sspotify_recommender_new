import pandas as pd
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import openai
import os
import time

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

def fetch_playlist_tracks(playlist_id):
    """
    Fetches all tracks and features from a Spotify playlist.
    """
    tracks = []
    results = sp.playlist_items(playlist_id)
    while results:
        for item in results['items']:
            track = item['track']
            if track:
                tracks.append({
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name']
                })
        if results.get('next'):
            results = sp.next(results)
        else:
            break
    return pd.DataFrame(tracks)

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
                    "content": "You are an assistant helping to analyze musical taste based on playlist data."
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze the following playlist data and recommend one new song. "
                        "Ensure the song is not present in the playlist. "
                        "Respond in the format: 'Song Name - Album Name'.\n\n"
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
    Processes the playlist and generates a recommendation.
    """
    try:
        playlist_id = extract_playlist_id(playlist_link)
        tracks_df = fetch_playlist_tracks(playlist_id)

        if tracks_df.empty:
            return {"message": "No tracks found in the playlist.", "recommendation": None}

        # Convert playlist data to string for OpenAI input
        playlist_data_str = tracks_df.to_string(index=False)

        # Get recommendation from OpenAI
        recommendation = get_recommendation(playlist_data_str)
        return {"message": "Musical taste understood", "recommendation": recommendation}
    except Exception as e:
        return {"message": f"An error occurred: {e}", "recommendation": None}
