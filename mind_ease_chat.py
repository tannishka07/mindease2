"""MindEase AI chat helpers and Flask routes.

This module is wired into app2.py with register_chat_routes(app, db).
The OpenAI key is read only from the server environment.
"""
import os
from datetime import datetime

from flask import jsonify, request, session


SYSTEM_PROMPT = """You are MindEase AI, a kind, calm and practical student-wellbeing companion.
Use warm, non-judgmental language. Help with everyday student stress, study planning,
motivation, emotional reflection, journaling prompts, and simple grounding ideas.
Ask one gentle question at a time. Keep replies concise and actionable.
You are not a therapist, doctor, or emergency service. Do not diagnose, prescribe,
or claim to provide professional treatment. Do not encourage dependence on you.
If someone may be in immediate danger or describes an imminent plan to hurt themselves
or someone else, encourage them to contact local emergency services now and reach
out to a trusted person nearby. Do not promise secrecy. Do not ask for identifying
details, passwords, or sensitive personal information.
"""

def register_chat_routes(app, db, openai_client):
    chats = db["chat_messages"]

    @app.post("/api/chat")
    def mindease_chat():
        username = session.get("user")
        if not username:
            return jsonify({"error": "Please log in to use MindEase AI."}), 401

        payload = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()
        if not message:
            return jsonify({"error": "Please type a message first."}), 400
        if len(message) > 2000:
            return jsonify({"error": "Please keep each message under 2,000 characters."}), 400

        # Each user's conversation is isolated by the authenticated session username.
        prior = list(
            chats.find({"username": username}, {"_id": 0, "role": 1, "content": 1})
            .sort("_id", -1).limit(12)
        )
        prior.reverse()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(
            {"role": item["role"], "content": item["content"]}
            for item in prior
            if item.get("role") in {"user", "assistant"} and isinstance(item.get("content"), str)
        )
        messages.append({"role": "user", "content": message})

        try:
            completion = openai_client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            answer = (completion.choices[0].message.content or "").strip()
            if not answer:
                raise RuntimeError("Empty response from model")
        except Exception:
            app.logger.exception("MindEase AI request failed")
            return jsonify({"error": "MindEase AI is temporarily unavailable. Please try again."}), 503

        now = datetime.utcnow()
        chats.insert_many([
            {"username": username, "role": "user", "content": message, "created_at": now},
            {"username": username, "role": "assistant", "content": answer, "created_at": now},
        ])
        return jsonify({"reply": answer})

    @app.get("/api/chat/history")
    def mindease_chat_history():
        username = session.get("user")
        if not username:
            return jsonify({"error": "Please log in."}), 401
        rows = list(
            chats.find({"username": username}, {"_id": 0, "role": 1, "content": 1})
            .sort("_id", -1).limit(40)
        )
        rows.reverse()
        return jsonify({"messages": rows})
