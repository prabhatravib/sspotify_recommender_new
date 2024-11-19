from flask import Flask, request, render_template
from dynamic_playlist_analysis import process_playlist_and_recommend_song
import os

app = Flask(__name__)

# Global variable to store the playlist link
playlist_link = None

@app.route('/')
def home():
    # Render the homepage
    return render_template('index.html')

@app.route('/submit_playlist', methods=['POST'])
def submit_playlist():
    global playlist_link
    playlist_url = request.form.get('playlist_url')
    if not playlist_url:
        return render_template('index.html', error="Please provide a valid playlist URL.")
    
    playlist_link = playlist_url
    return render_template('index.html', success="Musical taste understood! You can now get song recommendations.")

@app.route('/get_recommendation', methods=['POST'])
def get_recommendation():
    global playlist_link
    if not playlist_link:
        return render_template('index.html', error="Please load a playlist first.")
    
    # Generate a recommendation
    result = process_playlist_and_recommend_song(playlist_link)
    if result['recommendation']:
        return render_template('results.html', recommendation=result['recommendation'])
    else:
        return render_template('index.html', error=result['message'])

if __name__ == '__main__':
    # Use host 0.0.0.0 for deployment and PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
