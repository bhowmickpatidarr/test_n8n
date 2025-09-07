# Flask ElevenLabs Backend

A Flask-based backend providing:
- **Speech-to-Text (STT)**
- **Text-to-Speech (TTS)**

## 🚀 Deployment (Render)
1. Fork this repo.
2. Connect repo on [Render](https://render.com/).
3. Add environment variables in Render Dashboard:
   - `ELEVENLABS_API_KEY`
   - (Optional) `ELEVEN_VOICE_ID`, `ELEVEN_TTS_MODEL`, `ELEVEN_STT_MODEL`
4. Deploy!

## 🔧 API Endpoints

### Health Check
`GET /` → `{ "status": "ok" }`

### Speech-to-Text
`POST /stt`
```json
{ "audio_base64": "<base64 string>" }
