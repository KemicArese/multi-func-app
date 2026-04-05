import base64
import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HF_API_KEY = os.getenv("HF_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
HF_IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")

TEACH_SYSTEM_PROMPT = (
    "You are a patient teacher. Explain concepts with simple language, "
    "analogies, and short examples. End with a quick recap and a practice question."
)

MATH_SYSTEM_PROMPT = (
    "You are a precise math tutor. Solve the user's problem step-by-step, "
    "show calculations clearly, and provide the final boxed answer."
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def call_groq_chat(user_prompt: str, mode: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY environment variable.")

    system_prompt = TEACH_SYSTEM_PROMPT if mode == "teach" else MATH_SYSTEM_PROMPT
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def call_hf_image(prompt: str) -> str:
    if not HF_API_KEY:
        raise ValueError("Missing HF_API_KEY environment variable.")

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"inputs": prompt}
    url = f"https://api-inference.huggingface.co/models/{HF_IMAGE_MODEL}"

    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "image/png")
    image_b64 = base64.b64encode(response.content).decode("utf-8")
    return f"data:{content_type};base64,{image_b64}"


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    mode = str(body.get("mode", "teach")).strip().lower()
    user_prompt = str(body.get("prompt", "")).strip()

    if mode not in {"teach", "math"}:
        return jsonify({"error": "Mode must be 'teach' or 'math'."}), 400
    if not user_prompt:
        return jsonify({"error": "Prompt is required."}), 400

    try:
        answer = call_groq_chat(user_prompt, mode)
    except requests.HTTPError as err:
        return jsonify({"error": f"Groq request failed: {err}"}), 502
    except Exception as err:
        return jsonify({"error": str(err)}), 500

    return jsonify(
        {
            "mode": mode,
            "user_prompt": user_prompt,
            "answer": answer,
            "timestamp": utc_timestamp(),
            "image_url": None,
        }
    )


@app.post("/api/image")
def image():
    body = request.get_json(silent=True) or {}
    mode = "image"
    user_prompt = str(body.get("prompt", "")).strip()

    if not user_prompt:
        return jsonify({"error": "Prompt is required."}), 400

    try:
        image_url = call_hf_image(user_prompt)
    except requests.HTTPError as err:
        return jsonify({"error": f"Hugging Face request failed: {err}"}), 502
    except Exception as err:
        return jsonify({"error": str(err)}), 500

    return jsonify(
        {
            "mode": mode,
            "user_prompt": user_prompt,
            "answer": "Image generated successfully.",
            "timestamp": utc_timestamp(),
            "image_url": image_url,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
