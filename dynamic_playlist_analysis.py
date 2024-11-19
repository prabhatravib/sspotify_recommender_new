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
        if not recommendation:
            return {"message": "No recommendation could be generated.", "recommendation": None}

        return {"message": "Musical taste understood", "recommendation": recommendation}
    except Exception as e:
        # Log and return the error message
        print(f"Error in process_playlist_and_recommend_song: {e}")
        return {"message": f"An error occurred: {e}", "recommendation": None}
