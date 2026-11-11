# MindEase

A Flask-based student wellness application with mood tracking, journaling, music recommendations, breathing exercises, a study planner, and study sessions.

## Setup

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Set `MONGO_URI` and `SECRET_KEY` environment variables.
4. Run `python app2.py`.

The Spotify recommendation endpoint also needs the Spotify Tracks CSV dataset. Place it at `data/spotify_tracks.csv` or configure `MUSIC_CSV`.
