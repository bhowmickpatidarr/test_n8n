# app.py
import os
import base64
import tempfile
import logging
from flask import Flask, request, jsonify
from elevenlabs.client import ElevenLabs

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not ELEVEN_KEY:
    raise RuntimeError("Set ELEVENLABS_API_KEY environment variable")

# Optional configurable params
VOICE_ID = os.environ.get("ELEVEN_VOICE_ID", "1qEiC6qsybMkmnNdVMbK")
TTS_MODEL = os.environ.get("ELEVEN_TTS_MODEL", "eleven_multilingual_v2")
STT_MODEL = os.environ.get("ELEVEN_STT_MODEL", "scribe_v1")

client = ElevenLabs(api_key=ELEVEN_KEY)


@app.route("/stt", methods=["POST"])
def stt():
    """Speech-to-Text endpoint"""
    payload = request.get_json(silent=True)
    if not payload or "audio_base64" not in payload:
        return jsonify({"error": "Missing 'audio_base64'"}), 400

    try:
        data = base64.b64decode(payload["audio_base64"])
    except Exception:
        app.logger.exception("Invalid base64")
        return jsonify({"error": "Invalid base64"}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(data)
            temp_path = f.name

        with open(temp_path, "rb") as fh:
            transcription = client.speech_to_text.convert(
                file=fh, model_id=STT_MODEL
            )

        text = transcription if isinstance(transcription, str) else str(transcription.get("text", transcription))
        return jsonify({"text": text})

    except Exception as e:
        app.logger.exception("STT failed")
        return jsonify({"error": str(e)}), 500


@app.route("/tts", methods=["POST"])
def tts():
    """Text-to-Speech endpoint"""
    payload = request.get_json(silent=True)
    if not payload or "text" not in payload:
        return jsonify({"error": "Missing 'text'"}), 400

    try:
        generator = client.text_to_speech.convert(
            text=payload["text"],
            voice_id=VOICE_ID,
            model_id=TTS_MODEL,
            output_format="mp3_44100_128",
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            for chunk in generator:
                f.write(chunk)
            out_path = f.name

        with open(out_path, "rb") as fh:
            encoded = base64.b64encode(fh.read()).decode("utf-8")

        return jsonify({"audio_base64": encoded})

    except Exception as e:
        app.logger.exception("TTS failed")
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
