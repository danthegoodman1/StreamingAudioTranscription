from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import logging, json
from logging import Formatter
import uvicorn

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

html = open("mic.html", "r").read()

@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        logger.info(f"Message text was: {data}")
        await websocket.send_text(f"Message text was: {data}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_config=None) # make it use the configured logger