# app.py
import os
import base64
import tempfile
import logging
from flask import Flask, request, jsonify
from elevenlabs.client import ElevenLabs

# -------------------------
# App Setup
# -------------------------
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# -------------------------
# Config & Client
# -------------------------
ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not ELEVEN_KEY:
    raise RuntimeError("Set ELEVENLABS_API_KEY environment variable")

VOICE_ID = os.environ.get("ELEVEN_VOICE_ID", "1qEiC6qsybMkmnNdVMbK")
TTS_MODEL = os.environ.get("ELEVEN_TTS_MODEL", "eleven_multilingual_v2")
STT_MODEL = os.environ.get("ELEVEN_STT_MODEL", "scribe_v1")

client = ElevenLabs(api_key=ELEVEN_KEY)

logger.info("✅ Flask ElevenLabs Backend initialized")
logger.info(f"Using VOICE_ID={VOICE_ID}, TTS_MODEL={TTS_MODEL}, STT_MODEL={STT_MODEL}")


# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET"])
def health_check():
    logger.info("💓 Health check ping received")
    return jsonify({"status": "ok"})


@app.route("/stt", methods=["POST"])
def stt():
    """Speech-to-Text endpoint"""
    logger.info("🎤 [STT] Request received")

    payload = request.get_json(silent=True)
    if not payload or "audio_base64" not in payload:
        logger.warning("⚠️ [STT] Missing 'audio_base64'")
        return jsonify({"error": "Missing 'audio_base64'"}), 400

    try:
        audio_data = base64.b64decode(payload["audio_base64"])
        logger.info("🔊 [STT] Audio decoded successfully (base64 -> bytes)")
    except Exception:
        logger.exception("❌ [STT] Invalid base64 input")
        return jsonify({"error": "Invalid base64"}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_data)
            temp_path = f.name

        logger.info(f"📂 [STT] Temp file written: {temp_path}")

        with open(temp_path, "rb") as fh:
            transcription = client.speech_to_text.convert(
                file=fh, model_id=STT_MODEL
            )

        text = transcription if isinstance(transcription, str) else str(transcription.get("text", transcription))
        logger.info(f"✅ [STT] Transcription complete: {text}")

        return jsonify({"text": text})

    except Exception as e:
        logger.exception("❌ [STT] Failed to process audio")
        return jsonify({"error": str(e)}), 500


@app.route("/tts", methods=["POST"])
def tts():
    """Text-to-Speech endpoint"""
    logger.info("🗣️ [TTS] Request received")

    payload = request.get_json(silent=True)
    if not payload or "text" not in payload:
        logger.warning("⚠️ [TTS] Missing 'text'")
        return jsonify({"error": "Missing 'text'"}), 400

    text = payload["text"]
    logger.info(f"📝 [TTS] Converting text: {text}")

    try:
        generator = client.text_to_speech.convert(
            text=text,
            voice_id=VOICE_ID,
            model_id=TTS_MODEL,
            output_format="mp3_44100_128",
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            for chunk in generator:
                f.write(chunk)
            out_path = f.name

        logger.info(f"📂 [TTS] Audio file generated: {out_path}")

        with open(out_path, "rb") as fh:
            encoded = base64.b64encode(fh.read()).decode("utf-8")

        logger.info("✅ [TTS] Conversion complete, returning base64 audio")

        return jsonify({"audio_base64": encoded})

    except Exception as e:
        logger.exception("❌ [TTS] Failed to generate audio")
        return jsonify({"error": str(e)}), 500


# -------------------------
# Entry Point
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port)
