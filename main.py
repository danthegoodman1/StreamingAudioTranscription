from fastapi import FastAPI, WebSocket
import logging, json
from logging import Formatter
import uvicorn

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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        logger.info(f"Message text was: {data}")
        await websocket.send_text(f"Message text was: {data}")

@app.websocket("/audio")
async def audio_ws(websocket: WebSocket):
    vad_iterator = VADIterator(model)
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            print("got bytes", len(data))
            speech_dict = vad_iterator(data, return_seconds=True)
            print("detected", speech_dict)
            if speech_dict:
                print(speech_dict, end=' ')
                await websocket.send_text(f"Activity: {speech_dict}")
    except:
        vad_iterator.reset_states()  # reset model states after each audio
        # do we even need this if we are throwing it away?
        # should we just have a global one so one instance per websocket?



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_config=None)  # make it use the configured logger
