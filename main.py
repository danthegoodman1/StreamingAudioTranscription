from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging, json
from logging import Formatter
import uvicorn
import subprocess
import io
import asyncio
import torch

torch.set_num_threads(1)

model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=True,
                              onnx=False)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils


# https://www.sheshbabu.com/posts/fastapi-structured-json-logging/
class JsonFormatter(Formatter):
    def __init__(self):
        super(JsonFormatter, self).__init__()

    def format(self, record):
        json_record = {}
        json_record["message"] = record.getMessage()
        json_record["level"] = record.levelname
        return json.dumps(json_record)


logger = logging.root
handler = logging.StreamHandler()
# handler.setFormatter(JsonFormatter())
logger.handlers = [handler]
logger.setLevel(logging.DEBUG)

app = FastAPI()


async def save_first_chunk_for_inspection(websocket_data):
    with open("dumped_audio.webm", "wb") as file:
        file.write(websocket_data)
    print("Data dumped for inspection.")

async def convert_opus_to_pcm(audio_buffer: bytes) -> bytes:
    cmd = [
        'ffmpeg',
        '-f', 'webm',
        '-i', 'pipe:0',
        '-ar', '16000',
        '-ac', '1',
        '-f', 's16le',
        '-acodec', 'pcm_s16le',
        'pipe:1'
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE  # Capture stderr
    )
    pcm_audio, stderr = await process.communicate(input=audio_buffer)

    if process.returncode != 0:
        # Log the stderr output for diagnostics
        print(f"FFmpeg stderr: {stderr.decode()}")
        raise Exception("FFmpeg process did not exit cleanly.")

    return pcm_audio


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        logger.info(f"Message text was: {data}")
        await websocket.send_text(f"Message text was: {data}")

@app.websocket("/audio")
async def audio_ws(websocket: WebSocket):
    await websocket.accept()
    vad_iterator = VADIterator(model)

    try:
        while True:
            websocket_data = await websocket.receive_bytes()

            # Convert the incoming Opus audio to PCM
            try:
                pcm_audio = await convert_opus_to_pcm(websocket_data)

                # Process the PCM audio using your VAD model
                window_size_samples = 512
                data = pcm_audio  # This should be an array of PCM samples
                for i in range(0, len(data), window_size_samples):
                    speech_dict = vad_iterator(data[i: i + window_size_samples], return_seconds=True)
                    if speech_dict:
                        # Voice activity detected, process accordingly
                        # For example, you could send a message back to the client:
                        await websocket.send_text("Voice activity detected")

                vad_iterator.reset_states()

            except Exception as e:
                print(f"Error converting or processing audio chunk: {e}")
                # Optional: send error message back to client
                # await websocket.send_text("Error processing audio")

    except WebSocketDisconnect:
        print("WebSocket connection closed")
    finally:
        vad_iterator.reset_states()



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_config=None)  # make it use the configured logger
