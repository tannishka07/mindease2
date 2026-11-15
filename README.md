# MindEase

A Flask-based student wellness application with mood tracking, journaling, music recommendations, breathing exercises, a study planner, and study sessions.

## Setup

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Set `MONGO_URI` and `SECRET_KEY` environment variables.
4. Run `python app2.py`.

The Spotify recommendation endpoint also needs the Spotify Tracks CSV dataset. Place it at `data/spotify_tracks.csv` or configure `MUSIC_CSV`.


## Streamlit edition (runs alongside Flask)

The original Flask application remains the existing website. A separate Streamlit version is available in `streamlit_app.py`; it uses the same MongoDB database (`mindease`) and compatible collections, so existing mood, journal, planner, and study-session records can be viewed where their fields are supported.

### Run Streamlit locally

1. Activate your existing virtual environment.
2. Install the additional Streamlit dependency:
   `pip install -r requirements-streamlit.txt`
3. Make sure your local `.env` contains `MONGO_URI`. Add `OPENAI_API_KEY` to enable AI chat.
4. Start the new app:
   `streamlit run streamlit_app.py`

Streamlit normally opens at `http://localhost:8501`. The Flask app and its existing `Procfile` are not changed; run the two apps on separate ports.

### Deploy as a separate Render service

Create a **new Web Service** from this same repository and branch, leaving the existing Flask service untouched.

- Build command: `pip install -r requirements-streamlit.txt`
- Start command: `streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port $PORT`
- Add the same `MONGO_URI` and `OPENAI_API_KEY` environment variables as needed. Add a strong `SECRET_KEY` only if a future Streamlit feature requires it.

Do not commit your local `.env` file or paste secret values into GitHub.
