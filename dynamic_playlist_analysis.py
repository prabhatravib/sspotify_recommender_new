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
    max_duration = datetime.timedelta(minutes=3)  # Maximum allowed duration
    tracks = []
    track_ids = []

    while True:
        try:
            # Fetch all tracks in the playlist
            results = sp.playlist_items(playlist_id)
            for item in results['items']:
                track = item['track']
                track_ids.append(track['id'])
                track_data = {
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'popularity': track['popularity'],
                    'duration_ms': track['duration_ms']
                }
                tracks.append(track_data)

            # Batch process audio features
            for i in range(0, len(track_ids), 50):  # Batch size limited to 50
                batch_start_time = datetime.datetime.now()
                while True:
                    try:
                        batch_ids = track_ids[i:i+50]
                        features = sp.audio_features(batch_ids)
                        for j, feature in enumerate(features):
                            if feature:
                                tracks[i+j].update({
                                    'danceability': feature['danceability'],
                                    'energy': feature['energy'],
                                    'key': feature['key'],
                                    'loudness': feature['loudness'],
                                    'speechiness': feature['speechiness'],
                                    'acousticness': feature['acousticness'],
                                    'instrumentalness': feature['instrumentalness'],
                                    'liveness': feature['liveness'],
                                    'valence': feature['valence'],
                                    'tempo': feature['tempo'],
                                })
                        # Success: Break out of the retry loop
                        break
                    except spotipy.exceptions.SpotifyException as e:
                        # Check if it is a rate limit error (HTTP 429)
                        if "status: 429" in str(e):
                            current_time = datetime.datetime.now()
                            if current_time - batch_start_time > max_duration:
                                raise Exception("Rate limit error: Could not process the request within the allowed time.")

                            # Extract 'Retry-After' value from the response header
                            retry_after = e.headers.get("Retry-After", 10)  # Default to 10 seconds if header not found
                            print(f"Rate limit hit. Retrying after {retry_after} seconds...")
                            time.sleep(int(retry_after))
                        else:
                            raise e  # Raise other exceptions
                # Add a delay between batches
                time.sleep(2)  # Additional buffer delay between batches

            return pd.DataFrame(tracks)

        except Exception as e:
            current_time = datetime.datetime.now()
            if current_time - start_time > max_duration:
                print("Exceeded maximum retry duration (3 minutes).")
                raise Exception(f"Error: Could not complete the request within the allowed time. Last error: {e}")
            print(f"Error encountered: {e}. Waiting 10 seconds before retrying...")
            time.sleep(10)  # Wait and retry

# Get a song recommendation from OpenAI with retries
def get_recommendation(playlist_data_str):
    start_time = datetime.datetime.now()
    max_duration = datetime.timedelta(minutes=3)

    while True:
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
                            f"Analyze the following playlist data and recommend one new song. "
                            "Check thoroughly to ensure that the recommended song is not present in this playlist. "
                            "It must be a new song. The response should only contain the song name and album in the format 'Song Name - Album Name'.\n\n"
                            f"{playlist_data_str}")
                    }
                ]
            )
            recommendation = response['choices'][0]['message']['content'].strip()
            return recommendation
        except Exception as e:
            current_time = datetime.datetime.now()
            if current_time - start_time > max_duration:
                print("Exceeded maximum retry duration (3 minutes).")
                return "Error: Could not generate a recommendation due to repeated errors."
            print(f"Error encountered: {e}. Waiting 10 seconds before retrying...")
            time.sleep(10)  # Wait and retry

# Main function to process the playlist and recommend a song
def process_playlist_and_recommend_song(playlist_link):
    try:
        playlist_id = extract_playlist_id(playlist_link)
        playlist_df = fetch_playlist_tracks_with_features(playlist_id)

        if playlist_df.empty:
            return {"message": "Error: Could not understand musical taste. No tracks found in the playlist.", "recommendation": None}

        # Convert the playlist to a string format for OpenAI
        playlist_data_str = playlist_df.to_string(index=False)

        # Get a recommendation
        recommendation = get_recommendation(playlist_data_str)
        if recommendation:
            return {"message": "Musical taste understood", "recommendation": f"{recommendation} (Disclaimer: This song may or may not exist on Spotify.)"}
        else:
            return {"message": "No recommendation could be generated.", "recommendation": None}
    except ValueError:
        return {"message": "Invalid Spotify playlist link.", "recommendation": None}
    except Exception as e:
        return {"message": f"An error occurred: {e}", "recommendation": None}
