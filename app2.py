from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, date
from bson import ObjectId
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from mind_ease_chat import register_chat_routes
from journal_api import create_journal_blueprint
from music_recommender import create_music_blueprint

# Load local .env values before initializing MongoDB or OpenAI.
# On Render, environment variables configured in the dashboard take precedence.
load_dotenv()

# MongoDB
client = MongoClient(os.environ.get("MONGO_URI"))
db = client["mindease"]
users_collection = db["users"]

print("✅ Mongo connected")

# Flask
app = Flask(__name__)

# OpenAI is initialized server-side; never expose this key in browser code.
openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip()
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
if openai_client is None:
    app.logger.warning("OPENAI_API_KEY is not configured; MindEase AI will return a setup message.")
register_chat_routes(app, db, openai_client)

# 🔐 SESSION SECRET KEY
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "mindease-local-secret-key-2026"
)
undefined