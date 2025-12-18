"""
FastAPI TTS app with streaming playback + saving final MP3.

- Endpoint `/stream_create` streams MP3 audio back to the browser while also writing to disk.
- Frontend uses MediaSource Extensions (MSE) for progressive playback and shows live progress.

Requirements:
- Python 3.8+
- fastapi, uvicorn, aiofiles, pydantic
- OpenAI Python SDK >= 1.15.0 (the code assumes `client.audio.speech.with_streaming_response.create` exists)

Run:
    pip install fastapi uvicorn aiofiles openai
    export OPENAI_API_KEY="..."
    python fastapi_tts_app.py

Visit: http://localhost:5000
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import uvicorn
import json
from datetime import datetime
import aiofiles
import re
import asyncio
from openai import OpenAI
from typing import AsyncGenerator

# Initialize app
app = FastAPI(title="VoiceFlow FastAPI TTS (Streaming)")
client = OpenAI()

# Config
UPLOAD_FOLDER = Path("saved_audio")
UPLOAD_FOLDER.mkdir(exist_ok=True)

METADATA_FILE = UPLOAD_FOLDER / "metadata.json"

# Serve static files (saved audio)
app.mount("/audio", StaticFiles(directory=UPLOAD_FOLDER), name="audio")

# ------------------------
# Utilities
# ------------------------

def normalize_text(text: str) -> str:
    replacements = {
        '‘': "'", '’': "'", '“': '"', '”': '"'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()

async def read_json(file: Path):
    if not file.exists():
        return {}
    async with aiofiles.open(file, 'r', encoding='utf-8') as f:
        content = await f.read()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

async def write_json(file: Path, data: dict):
    async with aiofiles.open(file, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))

# ------------------------
# Request model
# ------------------------
class TTSRequest(BaseModel):
    filename: str
    text: str
    voice: str = "alloy"
    group: str = "uncategorized"

# ------------------------
# Streaming generator helper
# ------------------------
async def stream_tts_and_save(text: str, voice: str, target_path: Path) -> AsyncGenerator[bytes, None]:
    """Calls the OpenAI streaming TTS and yields MP3 bytes as they arrive while saving them to disk.

    This function makes a best-effort to support either async or sync streaming interfaces
    from the OpenAI Python SDK. If the SDK doesn't support streaming in your environment,
    it will fall back to a non-streaming call and yield the final bytes at once.
    """

    # Normalize text
    data = text

    # Prepare file writer
    async with aiofiles.open(target_path, 'wb') as afp:
        try:
            # Try streaming API (async)
            # NOTE: The exact streaming interface may vary between SDK versions. We try a couple of common patterns.
            stream = None
            try:
                # Preferred (context manager style) if available
                stream = client.audio.speech.with_streaming_response.create(model="gpt-4o-mini-tts", voice=voice, input=data)
            except Exception:
                # Fallback: try the non-streaming method
                stream = None

            if stream is not None:
                # If stream is an async generator
                try:
                    # Attempt async iteration
                    async for event in stream:
                        # The structure of `event` depends on SDK. We look for bytes or `.audio` or `.data` fields.
                        chunk = None
                        if hasattr(event, 'audio'):
                            chunk = getattr(event, 'audio')
                        elif isinstance(event, (bytes, bytearray)):
                            chunk = bytes(event)
                        elif isinstance(event, dict) and event.get('audio'):
                            chunk = event.get('audio')

                        if chunk:
                            # write to disk
                            await afp.write(chunk)
                            # yield to client
                            yield chunk

                    # streaming finished
                    return
                except TypeError:
                    # stream isn't async iterable; try sync iteration
                    pass

            # If we reach here, streaming isn't available or failed; perform non-streaming call
            # and yield final bytes once
            resp = client.audio.speech.create(model="gpt-4o-mini-tts", voice=voice, input=data)

            # `resp` might be an IO-like object or bytes
            final_bytes = None
            try:
                # If response supports .read()
                if hasattr(resp, 'read'):
                    final_bytes = resp.read()
                elif isinstance(resp, (bytes, bytearray)):
                    final_bytes = bytes(resp)
                elif isinstance(resp, dict) and resp.get('audio'):
                    final_bytes = resp.get('audio')
            except Exception:
                final_bytes = None

            if final_bytes is None:
                # As last resort, convert repr()
                final_bytes = str(resp).encode('utf-8', errors='ignore')

            await afp.write(final_bytes)
            yield final_bytes

        except Exception as e:
            # If any error, send a small error message chunk (so browser can handle it)
            err = f"__ERROR__:{str(e)}".encode('utf-8', errors='ignore')
            yield err

# ------------------------
# Endpoints
# ------------------------
@app.post('/stream_create')
async def stream_create(req: TTSRequest):
    text = normalize_text(req.text)
    if not text:
        return JSONResponse(status_code=400, content={"error": "Text cannot be empty."})

    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", req.filename)
    filename = safe_name + ".mp3"
    file_path = UPLOAD_FOLDER / filename

    # Create streaming response with audio/mpeg content-type
    async def audio_generator():
        async for chunk in stream_tts_and_save(text, req.voice, file_path):
            # If an error chunk is sent, break and stop streaming
            if chunk.startswith(b"__ERROR__:"):
                # yield nothing further and stop
                break
            yield chunk
        # After streaming completes, update metadata
        metadata = await read_json(METADATA_FILE)
        metadata[filename] = {
            "group": req.group,
            "created": datetime.now().isoformat(),
            "voice": req.voice
        }
        await write_json(METADATA_FILE, metadata)

    return StreamingResponse(audio_generator(), media_type='audio/mpeg')

@app.get('/')
async def index():
    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>VoiceFlow TTS - Streaming</title>
      <style>
        body { font-family: Inter, Arial, sans-serif; background: #0f172a; color: #e6eef8; display:flex; flex-direction:column; align-items:center; padding:40px }
        .card { background:#0b1220; padding:20px; border-radius:12px; width:720px; max-width:95%; }
        input, textarea, select { width:100%; padding:10px; margin-top:8px; border-radius:8px; border:none; }
        button{ padding:10px 14px; margin-top:10px; border-radius:8px; background:#6366f1; color:white; border:none; cursor:pointer }
        #status { margin-top:10px }
        audio { width:100%; margin-top:10px }
      </style>
    </head>
    <body>
      <div class="card">
        <h2>🎛️ VoiceFlow TTS (Streaming + Save)</h2>
        <label>File name (no extension)</label>
        <input id="filename" placeholder="my_audio_story">
        <label>Voice</label>
        <select id="voice"><option value="alloy">Alloy</option><option value="verse">Verse</option><option value="nova">Nova</option></select>
        <label>Text</label>
        <textarea id="text" rows="6" placeholder="Type your text here..."></textarea>
        <button id="generate">Generate & Play (Streaming)</button>
        <div id="status"></div>
        <audio id="player" controls></audio>
        <div id="savedLink" style="margin-top:10px"></div>
      </div>

    <script>
    async function streamToPlayer(url, filename) {
        const status = document.getElementById('status');
        const player = document.getElementById('player');
        const savedLink = document.getElementById('savedLink');
        status.textContent = 'Connecting…';
        savedLink.innerHTML = '';

        // Use MediaSource for progressive MP3 playback
        if (!('MediaSource' in window)) {
            status.textContent = 'MediaSource API not supported in this browser. Falling back to download after generation.';
        }

        const mediaSource = new MediaSource();
        player.src = URL.createObjectURL(mediaSource);

        mediaSource.addEventListener('sourceopen', async () => {
            status.textContent = 'Generating audio…';
            const mime = 'audio/mpeg';
            let sourceBuffer;
            try {
                sourceBuffer = mediaSource.addSourceBuffer(mime);
            } catch (e) {
                console.warn('Could not add source buffer', e);
                status.textContent = 'Could not play progressively: browser may not support MP3 MSE. Will download after generation.';
            }

            // Fetch streaming endpoint
            const resp = await fetch(url, { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({filename, text: document.getElementById('text').value, voice: document.getElementById('voice').value}) });
            if (!resp.ok) {
                status.textContent = 'Error from server';
                const err = await resp.json().catch(()=>null);
                status.textContent = err && err.error ? err.error : 'Unknown error';
                return;
            }

            const reader = resp.body.getReader();
            const chunks = [];
            let receivedLength = 0;

            // Read the stream
            while(true) {
                const {done, value} = await reader.read();
                if (done) break;
                if (!value) continue;

                // check for error marker
                const textPreview = new TextDecoder().decode(value.slice(0, 40));
                if (textPreview.startsWith('__ERROR__:')) {
                    const msg = new TextDecoder().decode(value);
                    status.textContent = 'Server error: ' + msg.replace('__ERROR__:', '');
                    break;
                }

                chunks.push(value);
                receivedLength += value.length;

                // Append to MSE buffer if available
                if (sourceBuffer) {
                    // SourceBuffer appendBuffer requires contiguous typed arrays
                    try {
                        sourceBuffer.appendBuffer(value);
                        if (player.paused) player.play().catch(()=>{});
                        status.textContent = 'Streaming… received ' + receivedLength + ' bytes';
                    } catch (e) {
                        // If appendBuffer fails (e.g., not ready), wait a bit and retry
                        await new Promise(r => setTimeout(r, 50));
                        try { sourceBuffer.appendBuffer(value); } catch (e2) { /* ignore */ }
                    }
                } else {
                    status.textContent = 'Receiving… ' + receivedLength + ' bytes';
                }
            }

            // All chunks received — create final blob and make a downloadable link
            const blob = new Blob(chunks, {type: 'audio/mpeg'});
            const urlBlob = URL.createObjectURL(blob);
            savedLink.innerHTML = `<a href="${urlBlob}" download="${filename}.mp3">💾 Download saved audio</a> &nbsp; <a href="/audio/${filename}.mp3" target="_blank">(Open saved file)</a>`;
            status.textContent = 'Completed — saved and available.';

            // End the media source stream if possible
            try { if (mediaSource.readyState === 'open') mediaSource.endOfStream(); } catch (e) {}
        });
    }

    document.getElementById('generate').addEventListener('click', async () => {
        const filename = document.getElementById('filename').value || 'voiceflow_audio_' + Date.now();
        document.getElementById('status').textContent = 'Starting generation...';
        await streamToPlayer('/stream_create', filename);
    });
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# ------------------------
# Run
# ------------------------
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)

