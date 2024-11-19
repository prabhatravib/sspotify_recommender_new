from flask import Flask, render_template, request
from dynamic_playlist_analysis import process_playlist_and_recommend_song  # Import analysis function

app = Flask(__name__)

# Global variable to store the playlist link
playlist_link = None

@app.route("/")
def home():
    # Render the homepage with the existing playlist (if any)
    return render_template('index.html', playlist_link=playlist_link)

@app.route("/submit_playlist", methods=["POST"])
def submit_playlist():
    global playlist_link
    playlist_url = request.form.get("playlist_url")
    if not playlist_url:
        return render_template(
            'index.html',
            error="Please provide a valid playlist URL.",
            playlist_link=playlist_link
        )

    playlist_link = playlist_url
    return render_template(
        'index.html',
        success="Musical taste understood! You can now get song recommendations.",
        playlist_link=playlist_link
    )

@app.route("/get_recommendation", methods=["POST"])
def get_recommendation():
    global playlist_link
    if not playlist_link:
        return render_template(
            'index.html',
            error="Please provide a playlist before getting recommendations.",
            playlist_link=None
        )

    try:
        # Call the function to process the playlist and get a recommendation
        result = process_playlist_and_recommend_song(playlist_link)
        recommendation = result.get("recommendation", None)
        message = result.get("message", "Something went wrong")

        # Debugging: Log the generated recommendation and message
        print(f"Generated Message: {message}")
        print(f"Generated Recommendation: {recommendation}")

        return render_template(
            'results.html',
            message=message,
            recommendation=recommendation,
            playlist_link=playlist_link
        )
    except Exception as e:
        # Log the exception
        print(f"Error: {e}")
        return render_template(
            'index.html',
            error=f"An error occurred while processing the playlist: {e}",
            playlist_link=playlist_link
        )

if __name__ == "__main__":
    app.run(debug=True)
