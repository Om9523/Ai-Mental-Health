from flask import Flask, render_template, request, jsonify , render_template_string
from deepface import DeepFace
import pyttsx3
import datetime
import json
import os
import base64
import cv2
import numpy as np
import mediapipe as mp
import threading
import requests

app = Flask(__name__)
app.secret_key = 'mindmood-secret-key'

# Groq API Configuration
GROQ_API_KEY = "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"
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

MOOD_LOG = "data/mood_log.json"
engine = pyttsx3.init()

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

@app.route("/")
def falana():
    return render_template("home.html")

@app.route("/camera")
def home():
    return render_template("index.html")

@app.route("/music")
def music():
    return render_template("music.html")

@app.route("/analyze_expression", methods=["POST"])
def analyze_expression():
    data = request.get_json()
    image_data = data.get("image")
    feeling = data.get("feeling")

    try:
        if image_data:
            # Decode and process image
            image_bytes = base64.b64decode(image_data.split(",")[1])
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (640, 480))

            result = DeepFace.analyze(img, actions=["emotion"], enforce_detection=False)
            emotion = result[0].get("dominant_emotion") if isinstance(result, list) else result.get("dominant_emotion")

        elif feeling:
            emotion = feeling

        else:
            return jsonify({"error": "No input provided"}), 400

        if emotion:
            message = get_openai_response(emotion)
            log_mood(emotion)
            speak(message)
            return jsonify({"emotion": emotion, "message": message})
        else:
            return jsonify({"emotion": None, "message": "Couldn't detect an emotion."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Load HTML content from file
# with open("mind_relax_games.html", "r") as file:
#     html_content = file.read()

@app.route('/games')
def index():
    # return render_template_string(html_content)
    return render_template("mind_relax_games.html")

def get_openai_response(emotion):
    prompt = f"You are a mental wellness assistant. A user is feeling '{emotion}'. Provide a comforting message."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful AI therapist."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 1
    }

    try:
        response = requests.post(GROQ_BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("Groq API error:", e)
        return "You're doing great. Keep going, I'm here for you!"

def log_mood(emotion):
    entry = {"timestamp": datetime.datetime.now().isoformat(), "emotion": emotion}
    data = []
    if os.path.exists(MOOD_LOG):
        with open(MOOD_LOG, "r") as f:
            data = json.load(f)
    data.append(entry)
    with open(MOOD_LOG, "w") as f:
        json.dump(data, f, indent=2)

def speak(message):
    def _speak():
        engine.say(message)
        engine.runAndWait()
        engine.stop()
    threading.Thread(target=_speak).start()

if __name__ == "__main__":
    app.run(debug=True)
