# MindEase AI chat endpoint
# Add this import near your other imports in app2.py:
# from openai import OpenAI
#
# Add this initialization after app = Flask(__name__):
# openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# chat_collection = db["chat_messages"]
#
# Add the following routes near the end of app2.py, before if __name__ == "__main__":
#
# @app.route("/api/chat", methods=["POST"])
# def mindease_chat():
#     if "user" not in session:
#         return jsonify({"error": "Please log in to use MindEase AI."}), 401
#     payload = request.get_json(silent=True) or {}
#     message = (payload.get("message") or "").strip()
#     if not message or len(message) > 2000:
#         return jsonify({"error": "Message must be between 1 and 2000 characters."}), 400
#     username = session["user"]
#     history = list(chat_collection.find({"username": username}).sort("_id", -1).limit(12))
#     history.reverse()
#     messages = [{"role": "system", "content": MINDEASE_SYSTEM_PROMPT}]
#     messages.extend({"role": item["role"], "content": item["content"]} for item in history)
#     messages.append({"role": "user", "content": message})
#     try:
#         answer = openai_client.chat.completions.create(
#             model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
#             messages=messages,
#             max_tokens=500,
#             temperature=0.7,
#         ).choices[0].message.content.strip()
#     except Exception:
#         app.logger.exception("MindEase AI request failed")
#         return jsonify({"error": "MindEase AI is temporarily unavailable. Please try again."}), 503
#     chat_collection.insert_many([
#         {"username": username, "role": "user", "content": message, "created_at": datetime.utcnow()},
#         {"username": username, "role": "assistant", "content": answer, "created_at": datetime.utcnow()},
#     ])
#     return jsonify({"reply": answer})
#
# @app.route("/api/chat/history", methods=["GET"])
# def mindease_chat_history():
#     if "user" not in session:
#         return jsonify({"error": "Please log in."}), 401
#     messages = list(chat_collection.find(
#         {"username": session["user"]},
#         {"_id": 0, "role": 1, "content": 1}
#     ).sort("_id", -1).limit(40))
#     messages.reverse()
#     return jsonify({"messages": messages})
#
# IMPORTANT: this is an integration guide only. Apply the code to app2.py as described in README.
